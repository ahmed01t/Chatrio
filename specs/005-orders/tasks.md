# Tasks: 005-orders

Each task is atomic, independent, and verifiable.

- [x] **Task 1: Order & OrderItem ORM Models**
  - Files: `backend/app/modules/orders/models.py`, `backend/app/db/models.py`
  - Action: Define `Order` and `OrderItem` models with foreign keys, indexes, check constraints (`quantity > 0`), unique constraints (`(organization_id, order_number)`), and enums (`OrderStatus`, `PaymentStatus`). Re-export in `app/db/models.py`.
  - Verification: Models import cleanly and SQLAlchemy metadata registers all 2 new tables.

- [x] **Task 2: Alembic Database Migration for Orders & Items**
  - File: `backend/migrations/versions/004_orders_and_order_items.py`
  - Action: Create migration script creating `orders` and `order_items` tables with indexes and foreign keys.
  - Verification: Unit test verifies migration script structure and upgrade/downgrade callables.

- [x] **Task 3: Order & OrderItem Pydantic Validation Schemas**
  - File: `backend/app/modules/orders/schemas.py`
  - Action: Define schemas for creating, updating, and reading orders and line items, plus status update payloads.
  - Verification: Schema validation unit tests covering valid input, positive quantities, and financial formatting.

- [x] **Task 4: Order & State Machine Business Service Logic**
  - File: `backend/app/modules/orders/service.py`
  - Action: Implement `OrderService` (atomic order creation with row-level stock locks, historical price snapshotting, state machine transition validation, and automatic stock release on cancellation).
  - Verification: Unit tests verifying order creation, subtotal calculation, invalid state transition rejection, and cancellation stock release.

- [x] **Task 5: FastAPI Order REST Endpoints**
  - Files: `backend/app/modules/orders/router.py`, `backend/app/api/router.py`
  - Action: Implement routes for `/api/v1/orders`, `/api/v1/orders/{id}`, `/api/v1/orders/{id}/status`, and `/api/v1/orders/{id}/cancel`. Mount under master API router.
  - Verification: Integration tests testing endpoint authentication, role restrictions, order placement, and cancellation.

- [x] **Task 6: Multi-Tenant Order Isolation Verification**
  - File: `backend/tests/integration/test_order_isolation.py`
  - Action: Verify Tenant A cannot view, query, modify, or cancel Tenant B's orders. Verify cross-tenant product injection is strictly rejected.
  - Verification: 100% green test suite across all unit and integration tests.

