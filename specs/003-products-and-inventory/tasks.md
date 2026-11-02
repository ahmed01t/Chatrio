# Tasks: 003-products-and-inventory

Each task is atomic, independent, and verifiable.

- [ ] **Task 1: Product, Category & Inventory ORM Models**
  - Files: `backend/app/modules/products/models.py`, `backend/app/db/models.py`
  - Action: Define `Product`, `Category`, `ProductCategory`, and `InventoryLog` models with foreign keys, indexes, check constraints (`stock_quantity >= 0`), and `pgvector` column. Re-export in `app/db/models.py`.
  - Verification: Models import cleanly and SQLAlchemy metadata registers all 4 new tables.

- [ ] **Task 2: Alembic Database Migration for Products & pgvector**
  - Files: `backend/migrations/versions/002_products_and_inventory.py`
  - Action: Create migration script that enables `vector` extension and creates `categories`, `products`, `product_categories`, and `inventory_logs` tables with indexes.
  - Verification: Unit test verifies migration script structure and upgrade/downgrade callables.

- [ ] **Task 3: Product & Inventory Pydantic Validation Schemas**
  - File: `backend/app/modules/products/schemas.py`
  - Action: Define schemas for creating, updating, and reading products, categories, inventory logs, and vector search queries.
  - Verification: Schema validation unit tests covering valid input, negative stock prevention, and price formatting.

- [ ] **Task 4: Product & Inventory Business Service Logic**
  - File: `backend/app/modules/products/service.py`
  - Action: Implement `ProductService` (CRUD, SKU uniqueness per tenant, vector search) and `InventoryService` (atomic stock adjustment with `with_for_update()` row-level locks and audit logging).
  - Verification: Unit tests verifying stock adjustment, race-condition safety, and SKU conflict detection.

- [ ] **Task 5: FastAPI Product & Inventory REST Endpoints**
  - Files: `backend/app/modules/products/router.py`, `backend/app/api/router.py`
  - Action: Implement routes for `/api/v1/products`, `/api/v1/categories`, and `/api/v1/products/{id}/inventory`. Mount under master API router.
  - Verification: Integration tests testing endpoint authentication, role restrictions, and inventory adjustments.

- [ ] **Task 6: Multi-Tenant Product & Inventory Isolation Verification**
  - File: `backend/tests/integration/test_product_isolation.py`
  - Action: Verify that Tenant A can never query, modify, or adjust stock for Tenant B's products. Test concurrent stock updates.
  - Verification: 100% green test suite across all unit and integration tests.

