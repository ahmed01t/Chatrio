# Implementation Plan: 005-orders

## 1. Architecture & Entity Relationship

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ ORDERS : "owns"
    CUSTOMERS ||--o{ ORDERS : "places"
    CONVERSATIONS ||--o{ ORDERS : "initiates"
    ORDERS ||--|{ ORDER_ITEMS : "contains"
    PRODUCTS ||--o{ ORDER_ITEMS : "referenced_in"

    ORDERS {
        uuid id PK
        uuid organization_id FK
        uuid customer_id FK
        uuid conversation_id FK "Optional"
        string order_number "Unique per org, e.g. ORD-20261108-ABCD"
        enum status "PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED"
        enum payment_status "UNPAID, PAID, REFUNDED"
        string currency "e.g. USD"
        numeric subtotal
        numeric shipping_cost
        numeric total_amount
        text shipping_address
        text notes
        timestamp created_at
        timestamp updated_at
    }

    ORDER_ITEMS {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        string product_title "Historical snapshot"
        string product_sku "Historical snapshot"
        numeric unit_price "Historical price snapshot"
        int quantity ">= 1"
        numeric total_price "unit_price * quantity"
    }
```

---

## 2. Order State Machine Transition Graph

```mermaid
stateDiagram-v2
    [*] --> PENDING : Customer/Agent places order
    PENDING --> CONFIRMED : Payment verified or merchant confirms
    PENDING --> CANCELLED : Customer cancels / Out of stock
    CONFIRMED --> PROCESSING : Warehouse packing
    CONFIRMED --> CANCELLED : Merchant cancels (stock released)
    PROCESSING --> SHIPPED : Dispatched with courier
    PROCESSING --> CANCELLED : Order cancelled (stock released)
    SHIPPED --> DELIVERED : Customer receives parcel
    SHIPPED --> CANCELLED : Shipment returned/failed (stock released)
    DELIVERED --> [*] : Order completed
    CANCELLED --> [*] : Terminal state
```

---

## 3. Implementation Phases

1. **Phase 1: Domain Models & Database Central Registry**:
   - Define `Order`, `OrderItem`, `OrderStatus`, and `PaymentStatus` in `app/modules/orders/models.py`.
   - Re-export in `app/db/models.py`.
2. **Phase 2: Database Migration**:
   - Create Alembic revision `004_orders_and_order_items.py`.
   - Add unit tests verifying schema creation, foreign key constraints, and downgrade cleanup.
3. **Phase 3: Validation Schemas**:
   - Define Pydantic v2 schemas: `OrderItemCreate`, `OrderItemRead`, `OrderCreate`, `OrderUpdate`, `OrderStatusUpdate`, `OrderRead`, `OrderListResponse`.
4. **Phase 4: Business Services & State Machine**:
   - `OrderService`:
     - `create_order`: Validates tenant products, calculates financial totals, locks inventory via `with_for_update()`, generates unique order number, inserts order and line items.
     - `update_status`: Validates directed state transition graph.
     - `cancel_order`: Transitions status to `CANCELLED` and triggers `InventoryService.adjust_stock(..., change_amount=+qty, reason=ORDER_RELEASE)` to release held stock.
     - `get_order` & `list_orders`: Tenant-scoped queries with eager loaded items and customer details.
5. **Phase 5: REST API Endpoints**:
   - Router `/api/v1/orders` mounted in `app/api/router.py`.
   - Endpoints: `POST /orders`, `GET /orders`, `GET /orders/{id}`, `PATCH /orders/{id}/status`, `POST /orders/{id}/cancel`.
6. **Phase 6: Multi-Tenant Order Isolation & Concurrency Verification**:
   - Verify Tenant A cannot access, modify, or cancel Tenant B's orders.
   - Verify stock reservation and release under concurrent checkout attempts.

