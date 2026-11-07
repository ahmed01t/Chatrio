# Feature Spec: 005-orders

## 1. Objective
Establish the **Orders and State Machine** domain for Chatrio. This module enables merchants to receive, track, and manage customer orders originating from WhatsApp conversational commerce or merchant dashboard creation. It provides price snapshots, order item line tracking, automated subtotal/total calculations, atomic inventory reservations, and a rigorous state machine governing order status transitions.

---

## 2. In Scope
1. **Core Data Models & Enums (`app/modules/orders/models.py`)**:
   - `OrderStatus` Enum: `PENDING`, `CONFIRMED`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`.
   - `PaymentStatus` Enum: `UNPAID`, `PAID`, `REFUNDED`.
   - `Order`: Multi-tenant order header tracking `organization_id`, `customer_id`, optional `conversation_id`, unique `order_number`, lifecycle statuses, currency, financial totals (`subtotal`, `shipping_cost`, `total_amount`), shipping address, and merchant notes.
   - `OrderItem`: Line item snapshot capturing `product_id`, `product_title`, `product_sku`, `unit_price`, `quantity`, and `total_price` at the moment of order placement.
2. **Database Migration (`migrations/versions/004_orders_and_order_items.py`)**:
   - Create tables `orders` and `order_items` with foreign keys, cascading deletion on items, check constraints (`quantity > 0`), and multi-tenant indexes.
   - Enforce composite uniqueness on `(organization_id, order_number)`.
3. **Pydantic Schemas (`app/modules/orders/schemas.py`)**:
   - `OrderItemCreate`, `OrderItemRead`.
   - `OrderCreate`, `OrderUpdate`, `OrderStatusUpdate`, `OrderRead`, `OrderListResponse`.
4. **Service Business Logic & State Machine (`app/modules/orders/service.py`)**:
   - Atomic order placement: Verifies customer and product validity, captures historical price snapshots, computes totals, reserves inventory stock via row-level locks (`SELECT ... FOR UPDATE`), and writes `ORDER_RESERVE` audit logs.
   - State Machine: Enforces valid status transitions (`PENDING` $\rightarrow$ `CONFIRMED` $\rightarrow$ `PROCESSING` $\rightarrow$ `SHIPPED` $\rightarrow$ `DELIVERED`).
   - Order Cancellation: Transitions order to `CANCELLED` and atomically releases reserved stock back to available inventory with `ORDER_RELEASE` audit logs.
5. **FastAPI Endpoints (`app/modules/orders/router.py`)**:
   - `POST /api/v1/orders`: Create a new order.
   - `GET /api/v1/orders`: List store orders with status and customer filtering, sorting, and pagination.
   - `GET /api/v1/orders/{order_id}`: Retrieve full order details including line items and customer information.
   - `PATCH /api/v1/orders/{order_id}/status`: Transition order status according to the state machine.
   - `POST /api/v1/orders/{order_id}/cancel`: Cancel an order and release reserved inventory.

---

## 3. Out of Scope (Deferred to Later Specs)
- Third-party payment gateway webhooks like Stripe/Razorpay (Future Extension).
- WhatsApp order confirmation template dispatch via Meta Cloud API (Spec 006 - Message Processing).
- Automated cart assembly inside conversational agent (Spec 007 - AI Agent).

---

## 4. Requirements & Invariants

### 4.1 Functional Requirements
1. **Tenant Boundary Isolation**:
   - Every order and order item MUST belong strictly to `organization_id`.
   - Orders cannot include products or customers belonging to other merchant tenants.
2. **Immutable Price Snapshots**:
   - When an order item is created, `unit_price`, `product_title`, and `product_sku` MUST be copied as historical snapshots so future catalog price changes never alter past order records.
3. **Atomic Inventory Reservation**:
   - Creating an order atomically deducts available stock using `InventoryService.adjust_stock(..., change_amount=-qty, reason=ORDER_RESERVE)` with pessimistic row-level locking.
   - If any product has insufficient stock, the entire order creation fails with `400 INSUFFICIENT_STOCK` and zero changes are persisted.
4. **Deterministic State Transitions**:
   - Orders follow a strict directed graph:
     - `PENDING` $\rightarrow$ `CONFIRMED` $\rightarrow$ `PROCESSING` $\rightarrow$ `SHIPPED` $\rightarrow$ `DELIVERED`.
     - An order in any state prior to `DELIVERED` may transition to `CANCELLED`.
     - Once `CANCELLED`, no further transitions are permitted.
     - Invalid transitions raise `BadRequestException("INVALID_ORDER_STATE_TRANSITION")`.

### 4.2 Non-Functional Invariants
1. **Type Safety & Validation**: 100% type-annotated Pydantic v2 schemas and SQLAlchemy 2.0 mapped columns.
2. **Database Performance**: Appropriate indexes on `(organization_id, status)`, `(organization_id, customer_id)`, and `(organization_id, order_number)`.
3. **Automated Testing**: 100% green test suite covering happy paths, stock exhaustion, invalid state transitions, cancellation inventory release, and multi-tenant isolation.

