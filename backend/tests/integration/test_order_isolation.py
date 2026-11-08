"""
Integration tests for Multi-Tenant Order Isolation.

Validates that:
1. Tenant A cannot see or query Tenant B's orders in the order listing.
2. Tenant A cannot read Tenant B's order by ID (returns 404 ORDER_NOT_FOUND).
3. Tenant A cannot update, advance status, or cancel Tenant B's orders.
4. Cross-tenant customer injection is rejected (returns 404 CUSTOMER_NOT_FOUND).
5. Cross-tenant product injection is rejected (returns 404 PRODUCT_NOT_FOUND)
   and does not tamper with Tenant B's stock inventory.
"""

import pytest
from httpx import AsyncClient


async def register_merchant(
    async_client: AsyncClient,
    email: str,
    org_name: str,
) -> str:
    """Helper function to register a new tenant and return an access token."""
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": f"Owner of {org_name}",
            "organization_name": org_name,
        },
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_order_listing_and_detail_isolation(async_client: AsyncClient) -> None:
    """Verify Tenant A and Tenant B order listings and detail endpoints are isolated."""
    token_a = await register_merchant(async_client, "owner_a_ord@store-a.com", "Store A")
    token_b = await register_merchant(async_client, "owner_b_ord@store-b.com", "Store B")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Setup Tenant A Customer and Product
    cust_a = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": "+14155550001", "name": "Buyer A"},
        headers=headers_a,
    )
    prod_a = await async_client.post(
        "/api/v1/products",
        json={"title": "Product A", "sku": "SKU-A", "price": "10.00", "stock_quantity": 20},
        headers=headers_a,
    )
    order_a = await async_client.post(
        "/api/v1/orders",
        json={
            "customer_id": cust_a.json()["id"],
            "items": [{"product_id": prod_a.json()["id"], "quantity": 1}],
        },
        headers=headers_a,
    )
    assert order_a.status_code == 201
    order_a_id = order_a.json()["id"]

    # Setup Tenant B Customer and Product
    cust_b = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": "+14155550002", "name": "Buyer B"},
        headers=headers_b,
    )
    prod_b = await async_client.post(
        "/api/v1/products",
        json={"title": "Product B", "sku": "SKU-B", "price": "20.00", "stock_quantity": 20},
        headers=headers_b,
    )
    order_b = await async_client.post(
        "/api/v1/orders",
        json={
            "customer_id": cust_b.json()["id"],
            "items": [{"product_id": prod_b.json()["id"], "quantity": 1}],
        },
        headers=headers_b,
    )
    assert order_b.status_code == 201
    order_b_id = order_b.json()["id"]

    # 1. Listing Isolation: Tenant A sees only Order A
    list_a = await async_client.get("/api/v1/orders", headers=headers_a)
    assert list_a.status_code == 200
    assert list_a.json()["total"] == 1
    assert list_a.json()["items"][0]["id"] == order_a_id

    # 2. Listing Isolation: Tenant B sees only Order B
    list_b = await async_client.get("/api/v1/orders", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json()["total"] == 1
    assert list_b.json()["items"][0]["id"] == order_b_id

    # 3. Direct Detail Fetch Isolation: Tenant A attempts to fetch Order B -> 404
    attack_a = await async_client.get(f"/api/v1/orders/{order_b_id}", headers=headers_a)
    assert attack_a.status_code == 404
    assert attack_a.json()["error"]["code"] == "ORDER_NOT_FOUND"

    # 4. Direct Detail Fetch Isolation: Tenant B attempts to fetch Order A -> 404
    attack_b = await async_client.get(f"/api/v1/orders/{order_a_id}", headers=headers_b)
    assert attack_b.status_code == 404
    assert attack_b.json()["error"]["code"] == "ORDER_NOT_FOUND"


@pytest.mark.asyncio
async def test_order_mutation_isolation(async_client: AsyncClient) -> None:
    """Verify Tenant A cannot update, advance status, or cancel Tenant B's order."""
    token_a = await register_merchant(async_client, "owner_a_mut@store-a.com", "Mut A")
    token_b = await register_merchant(async_client, "owner_b_mut@store-b.com", "Mut B")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant B creates Customer, Product, and Order
    cust_b = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": "+14155550003", "name": "Buyer B"},
        headers=headers_b,
    )
    prod_b = await async_client.post(
        "/api/v1/products",
        json={"title": "Widget B", "sku": "WDG-B", "price": "15.00", "stock_quantity": 10},
        headers=headers_b,
    )
    order_b = await async_client.post(
        "/api/v1/orders",
        json={
            "customer_id": cust_b.json()["id"],
            "items": [{"product_id": prod_b.json()["id"], "quantity": 2}],
        },
        headers=headers_b,
    )
    assert order_b.status_code == 201
    order_b_id = order_b.json()["id"]

    # 1. Tenant A attempts to update notes on Order B -> 404
    patch_attack = await async_client.patch(
        f"/api/v1/orders/{order_b_id}",
        json={"notes": "Hacked delivery instructions"},
        headers=headers_a,
    )
    assert patch_attack.status_code == 404
    assert patch_attack.json()["error"]["code"] == "ORDER_NOT_FOUND"

    # 2. Tenant A attempts to advance status of Order B -> 404
    status_attack = await async_client.patch(
        f"/api/v1/orders/{order_b_id}/status",
        json={"status": "CONFIRMED"},
        headers=headers_a,
    )
    assert status_attack.status_code == 404
    assert status_attack.json()["error"]["code"] == "ORDER_NOT_FOUND"

    # 3. Tenant A attempts to cancel Order B -> 404
    cancel_attack = await async_client.post(
        f"/api/v1/orders/{order_b_id}/cancel",
        headers=headers_a,
    )
    assert cancel_attack.status_code == 404
    assert cancel_attack.json()["error"]["code"] == "ORDER_NOT_FOUND"


@pytest.mark.asyncio
async def test_cross_tenant_injection_prevention(async_client: AsyncClient) -> None:
    """Verify cross-tenant customer and product references are strictly rejected."""
    token_a = await register_merchant(async_client, "owner_a_inj@store-a.com", "Inj A")
    token_b = await register_merchant(async_client, "owner_b_inj@store-b.com", "Inj B")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant A setup
    cust_a = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": "+14155550004", "name": "Buyer A"},
        headers=headers_a,
    )
    prod_a = await async_client.post(
        "/api/v1/products",
        json={"title": "Apple", "sku": "APL-01", "price": "1.00", "stock_quantity": 50},
        headers=headers_a,
    )
    cust_a_id = cust_a.json()["id"]
    prod_a_id = prod_a.json()["id"]

    # Tenant B setup
    cust_b = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": "+14155550005", "name": "Buyer B"},
        headers=headers_b,
    )
    prod_b = await async_client.post(
        "/api/v1/products",
        json={"title": "Banana", "sku": "BAN-01", "price": "2.00", "stock_quantity": 30},
        headers=headers_b,
    )
    cust_b_id = cust_b.json()["id"]
    prod_b_id = prod_b.json()["id"]

    # 1. Tenant A attempts to place order for Tenant B's Customer -> 404
    cross_cust_resp = await async_client.post(
        "/api/v1/orders",
        json={
            "customer_id": cust_b_id,
            "items": [{"product_id": prod_a_id, "quantity": 1}],
        },
        headers=headers_a,
    )
    assert cross_cust_resp.status_code == 404
    assert cross_cust_resp.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"

    # 2. Tenant A attempts to place order containing Tenant B's Product -> 404
    cross_prod_resp = await async_client.post(
        "/api/v1/orders",
        json={
            "customer_id": cust_a_id,
            "items": [{"product_id": prod_b_id, "quantity": 5}],
        },
        headers=headers_a,
    )
    assert cross_prod_resp.status_code == 404
    assert cross_prod_resp.json()["error"]["code"] == "PRODUCT_NOT_FOUND"

    # Verify Tenant B's product stock remained untouched: 30
    prod_b_check = await async_client.get(f"/api/v1/products/{prod_b_id}", headers=headers_b)
    assert prod_b_check.json()["stock_quantity"] == 30
