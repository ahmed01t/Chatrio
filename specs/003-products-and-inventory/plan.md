# Implementation Plan: 003-products-and-inventory

## 1. Summary
This plan details the technical steps to implement the product catalog, category taxonomy, real-time inventory management with row-level locks, and semantic search vector storage via PostgreSQL `pgvector` .


---

## 2. Technical Architecture & Database Design

### 2.1 Entity Relationship Diagram

```text
       organizations
      ┌─────────────────────────┐
      │ id (UUID, PK)           │
      └────────────┬────────────┘
                   │ 1
                   │
         ┌─────────┴──────────────────────────────────────┐
         │ N                                              │ N
         ▼                                                ▼
  ┌─────────────────────────┐                      ┌─────────────────────────┐
  │       categories        │                      │        products         │
  ├─────────────────────────┤                      ├─────────────────────────┤
  │ id (UUID, PK)           │                      │ id (UUID, PK)           │
  │ organization_id (FK)    │                      │ organization_id (FK)    │
  │ name (VARCHAR)          │                      │ title (VARCHAR)         │
  │ slug (VARCHAR)          │                      │ description (TEXT)      │
  │ parent_id (FK, Nullable)│                      │ sku (VARCHAR)           │
  └────────────┬────────────┘                      │ price (NUMERIC(10,2))   │
               │ 1                                 │ currency (VARCHAR(3))   │
               │                                   │ stock_quantity (INT)    │
               │ N                                 │ is_active (BOOLEAN)     │
  ┌────────────▼────────────┐                      │ embedding (VECTOR(1536))│
  │   product_categories    │                      │ created_at / updated_at │
  ├─────────────────────────┤                      └────────────┬────────────┘
  │ product_id (FK, PK)     │◄──────────────────────────────────┘ 1
  │ category_id (FK, PK)    │                                     │
  └─────────────────────────┘                                     │ N
                                                   ┌──────────────▼──────────┐
                                                   │     inventory_logs      │
                                                   ├─────────────────────────┤
                                                   │ id (UUID, PK)           │
                                                   │ organization_id (FK)    │
                                                   │ product_id (FK)         │
                                                   │ change_amount (INT)     │
                                                   │ balance_after (INT)     │
                                                   │ reason (VARCHAR/ENUM)   │
                                                   │ created_at (TIMESTAMPTZ)│
                                                   └─────────────────────────┘
```

---

### 2.2 Inventory Concurrency & Locking Strategy
- To prevent race conditions where two simultaneous customers order the last remaining item:
  ```python
  # Row-level lock ensures only 1 transaction modifies stock at a time
  stmt = (
      select(Product)
      .where(Product.id == product_id, Product.organization_id == org_id)
      .with_for_update()
  )
  ```
- If `stock_quantity + change_amount < 0`, the transaction raises `BadRequestException(code="INSUFFICIENT_STOCK")` and rolls back.

---

### 2.3 Semantic Vector Search with pgvector
- Products table includes `embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)`.
- Cosine similarity query:
  ```python
  stmt = (
      select(Product)
      .where(Product.organization_id == org_id, Product.is_active.is_(True))
      .order_by(Product.embedding.cosine_distance(query_vector))
      .limit(limit)
  )
  ```

---

### 2.4 Directory & Module Layout
```text
backend/app/modules/products/
├── models.py       # Product, Category, ProductCategory, InventoryLog
├── schemas.py      # ProductCreate, ProductUpdate, ProductRead, InventoryAdjustment
├── service.py      # ProductService, InventoryService
└── router.py       # REST endpoints for products, categories, inventory
```

