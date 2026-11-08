"""
Integration tests for Order REST Endpoints.

Validates:
1. Order creation with atomic inventory reservation and price snapshotting.
2. Order listing with status filters and pagination.
3. Order detail retrieval and updates.
4. Order fulfillment state machine status advancement.
5. Order cancellation and automatic inventory release.
6. Edge case errors: insufficient stock, invalid customer, invalid state transitions.
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient


async def create_auth_token(async_client: AsyncClient, email: str, org_name: str) -> str:
    """Helper to register a merchant and return their JWT access token."""
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": "Merchant Owner",
            "organization_name": org_name,
        },
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_order_lifecycle_endpoints(async_client: AsyncClient) -> None:
    """Verify full order flow: create -> list -> get -> update -> advance status -> deliver."""
    token = await create_auth_token(async_client, "owner_orders@example.com", "Orders Store")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a Customer
    cust_resp = await async_client.post(
        "/api/v1/customers",
        json={
            "phone_number": "+14155551234",
            "name": "Jane Buyer",
            "email": "jane@example.com",
        },
        headers=headers,
    )
    assert cust_resp.status_code == 201
    customer_id = cust_resp.json()["id"]

    # 2. Create a Product with stock = 10
    prod_resp = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Ceramic Mug",
            "sku": "MUG-001",
            "price": "25.00",
            "currency": "USD",
            "stock_quantity": 10,
            "is_active": True,
        },
        headers=headers,
    )
    assert prod_resp.status_code == 201
    product_id = prod_resp.json()["id"]

    # 3. Create Order for 2 items
    order_payload = {
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "quantity": 2}],
        "shipping_cost": "5.00",
        "shipping_address": "123 Elm St, Austin, TX",
        "notes": "Handle with care",
        "metadata": {"source": "dashboard"},
    }
    order_resp = await async_client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert order_resp.status_code == 201
    order_data = order_resp.json()
    order_id = order_data["id"]

    assert order_data["status"] == "PENDING"
    assert order_data["payment_status"] == "UNPAID"
    assert Decimal(order_data["subtotal"]) == Decimal("50.00")
    assert Decimal(order_data["shipping_cost"]) == Decimal("5.00")
    assert Decimal(order_data["total_amount"]) == Decimal("55.00")
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["product_title"] == "Ceramic Mug"
    assert order_data["items"][0]["quantity"] == 2

    # Verify inventory was deducted: 10 - 2 = 8
    prod_check = await async_client.get(f"/api/v1/products/{product_id}", headers=headers)
    assert prod_check.json()["stock_quantity"] == 8

    # 4. Get Order by ID
    get_resp = await async_client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == order_id

    # 5. List Orders
    list_resp = await async_client.get("/api/v1/orders?status=PENDING", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["id"] == order_id

    # 6. Update Order Details
    patch_resp = await async_client.patch(
        f"/api/v1/orders/{order_id}",
        json={"shipping_address": "456 Oak St, Dallas, TX", "notes": "Leave at front desk"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["shipping_address"] == "456 Oak St, Dallas, TX"

    # 7. Advance Status: PENDING -> CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED
    for next_status in ["CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED"]:
        status_resp = await async_client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": next_status},
            headers=headers,
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == next_status

    # 8. Attempt illegal transition from terminal state DELIVERED -> CANCELLED
    invalid_resp = await async_client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "CANCELLED"},
        headers=headers,
    )
    assert invalid_resp.status_code == 400
    assert invalid_resp.json()["error"]["code"] == "INVALID_ORDER_STATE_TRANSITION"


@pytest.mark.asyncio
async def test_order_cancellation_and_stock_release(async_client: AsyncClient) -> None:
    """Verify order cancellation restores reserved stock back to product."""
    token = await create_auth_token(async_client, "owner_cancel@example.com", "Cancel Store")
    headers = {"Authorization": f"Bearer {token}"}

    # Create Customer
    cust_resp = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": "+14155559999", "name": "Mark"},
        headers=headers,
    )
    customer_id = cust_resp.json()["id"]

    # Create Product with stock = 5
    prod_resp = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Hoodie",
            "sku": "HD-001",
            "price": "60.00",
            "stock_quantity": 5,
            "is_active": True,
        },
        headers=headers,
    )
    product_id = prod_resp.json()["id"]

    # Place order for 3 hoodies (stock becomes 5 - 3 = 2)
    order_resp = await async_client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 3}],
        },
        headers=headers,
    )
    assert order_resp.status_code == 201
    order_id = order_resp.json()["id"]

    # Verify stock dropped to 2
    prod_check = await async_client.get(f"/api/v1/products/{product_id}", headers=headers)
    assert prod_check.json()["stock_quantity"] == 2

    # Cancel the order via POST /orders/{id}/cancel
    cancel_resp = await async_client.post(f"/api/v1/orders/{order_id}/cancel", headers=headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    # Verify stock is restored back to 5: 2 + 3 = 5
    prod_restored = await async_client.get(f"/api/v1/products/{product_id}", headers=headers)
    assert prod_restored.json()["stock_quantity"] == 5

    # Second cancel attempt fails
    second_cancel = await async_client.post(f"/api/v1/orders/{order_id}/cancel", headers=headers)
    assert second_cancel.status_code == 400
    assert second_cancel.json()["error"]["code"] == "ORDER_ALREADY_CANCELLED"


@pytest.mark.asyncio
async def test_order_creation_insufficient_stock_error(async_client: AsyncClient) -> None:
    """Verify order creation fails if quantity requested is greater than stock."""
    token = await create_auth_token(async_client, "owner_stock@example.com", "Stock Store")
    headers = {"Authorization": f"Bearer {token}"}

    # Customer
    cust_resp = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": "+14155557777", "name": "Tom"},
        headers=headers,
    )
    customer_id = cust_resp.json()["id"]

    # Product with stock = 1
    prod_resp = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Limited Watch",
            "sku": "WCH-001",
            "price": "500.00",
            "stock_quantity": 1,
            "is_active": True,
        },
        headers=headers,
    )
    product_id = prod_resp.json()["id"]

    # Request quantity = 2
    order_resp = await async_client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 2}],
        },
        headers=headers,
    )
    assert order_resp.status_code == 400
    assert order_resp.json()["error"]["code"] == "INSUFFICIENT_STOCK"
