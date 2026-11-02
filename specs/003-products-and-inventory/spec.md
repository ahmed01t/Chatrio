# Feature Spec: 003-products-and-inventory

## 1. Objective
Establish the product catalog, inventory tracking, categories, and vector embeddings database foundation for Chatrio. This allows merchants to manage their merchandise, define prices, track real-time stock levels, and store AI vector embeddings (via PostgreSQL `pgvector`) so customers can search products naturally via WhatsApp.

---

## 2. In Scope
1. **Core Data Models & Enums (`app/modules/products/models.py`)**:
   - `Product`: Tenant-bound merchandise with title, description, SKU, price, currency, stock quantity, active status, and `pgvector` embedding column.
   - `Category`: Tenant-bound category grouping (e.g. "Footwear", "Accessories") with slug and parent hierarchy support.
   - `ProductCategory`: Junction table linking products to one or more categories.
   - `InventoryLog`: Immutable audit trail tracking stock mutations (`RESTOCK`, `ORDER_RESERVE`, `ORDER_RELEASE`, `MANUAL_ADJUSTMENT`).
2. **Database Migrations (`migrations/versions/002_products_and_inventory.py`)**:
   - Enable PostgreSQL `vector` extension if not already enabled.
   - Create `categories`, `products`, `product_categories`, and `inventory_logs` tables with appropriate indexes and foreign keys.
   - Create an HNSW or IVFFlat vector index on `products.embedding` for sub-millisecond semantic search.
3. **Pydantic Schemas (`app/modules/products/schemas.py`)**:
   - `ProductCreate`, `ProductUpdate`, `ProductRead`, `ProductListResponse`.
   - `CategoryCreate`, `CategoryRead`.
   - `InventoryAdjustmentRequest`, `InventoryLogRead`.
4. **Service Business Logic (`app/modules/products/service.py`)**:
   - Atomic product creation and SKU uniqueness enforcement per tenant.
   - Inventory stock adjustments with row-level locking (`SELECT ... FOR UPDATE`) to prevent overselling race conditions.
   - Mock/pluggable vector generation hook for semantic product search.
5. **FastAPI Endpoints (`app/modules/products/router.py`)**:
   - `GET /api/v1/products`: List tenant products with pagination, category filter, and search.
   - `POST /api/v1/products`: Create a new product (restricted to `OWNER` or `ADMIN`).
   - `GET /api/v1/products/{product_id}`: Retrieve single product details.
   - `PATCH /api/v1/products/{product_id}`: Update product details, price, or status.
   - `POST /api/v1/products/{product_id}/inventory`: Adjust stock with audit logging.
   - `GET /api/v1/categories`: List tenant product categories.
   - `POST /api/v1/categories`: Create product category.

---

## 3. Out of Scope (Deferred to Future Specs)
- Live OpenAI / Gemini embedding generation API calls (Deferred to Spec 007 - AI Agent).
- WhatsApp catalog message rendering (Deferred to Spec 004/006).
- Customer cart checkout locks (Deferred to Spec 005 - Orders).

---

## 4. Requirements & Invariants

### 4.1 Functional Requirements
1. **Tenant Isolation**:
   - Every product, category, and inventory log MUST be strictly bound to `organization_id`.
   - A SKU (Stock Keeping Unit) must be unique *within* an organization, but different organizations can use the same SKU.
2. **Deterministic Inventory & Race-Condition Safety**:
   - Stock quantities cannot drop below zero (`CHECK (stock_quantity >= 0)`).
   - Any inventory deduction must acquire a row-level lock on the product to prevent concurrent race conditions.
   - Every stock modification must append an immutable entry to `inventory_logs`.
3. **Semantic Vector Search**:
   - Products include a 1536-dimensional vector embedding column (`vector(1536)`).
   - Cosine distance (`<=>`) is used to retrieve top-K matching products for conversational AI search.

### 4.2 Non-Functional Invariants
1. **Type Safety & Validation**: 100% type-annotated Pydantic v2 schemas and SQLAlchemy 2.0 mapped columns.
2. **Database Performance**: Appropriate indexes on `(organization_id, sku)`, `(organization_id, is_active)`, and HNSW index on the embedding column.
3. **Automated Testing**: 100% test coverage covering happy paths, SKU collisions, out-of-stock validation, and tenant isolation.

