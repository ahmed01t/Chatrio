"""
Integration tests for multi-tenant isolation across Products, Categories, and Inventory.

Validates that:
1. Product isolation: Tenant A cannot read, list, update, or delete Tenant B's products.
2. Category isolation: Tenant A cannot read, list, modify, or link Tenant B's categories.
3. Inventory isolation: Tenant A cannot adjust stock or view logs for Tenant B's products.
4. Identical SKU isolation: Different merchants can create products with identical SKUs
   without conflict, but intra-tenant SKU duplicates are rejected with 409 Conflict.
5. Stock boundary & integrity: Inventory adjustments strictly enforce stock limits and
   prevent overselling.
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
async def test_tenant_cannot_read_or_list_other_tenant_products(
    async_client: AsyncClient,
) -> None:
    """Verify Tenant A and Tenant B product catalogs are strictly isolated."""
    # 1. Register Merchant A and Merchant B
    token_a = await register_merchant(async_client, "owner_a@alpha.com", "Store Alpha")
    token_b = await register_merchant(async_client, "owner_b@beta.com", "Store Beta")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. Merchant A creates Product A
    resp_prod_a = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Alpha Drone X",
            "sku": "DRONE-ALPHA-01",
            "price": "499.00",
            "stock_quantity": 10,
        },
        headers=headers_a,
    )
    assert resp_prod_a.status_code == 201
    prod_a_id = resp_prod_a.json()["id"]

    # 3. Merchant B creates Product B
    resp_prod_b = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Beta Camera 4K",
            "sku": "CAM-BETA-02",
            "price": "799.00",
            "stock_quantity": 5,
        },
        headers=headers_b,
    )
    assert resp_prod_b.status_code == 201
    prod_b_id = resp_prod_b.json()["id"]

    # 4. Merchant A lists products -> Must ONLY see Product A
    list_a = await async_client.get("/api/v1/products", headers=headers_a)
    assert list_a.status_code == 200
    items_a = list_a.json()["items"]
    assert len(items_a) == 1
    assert items_a[0]["id"] == prod_a_id
    assert items_a[0]["title"] == "Alpha Drone X"

    # 5. Merchant B lists products -> Must ONLY see Product B
    list_b = await async_client.get("/api/v1/products", headers=headers_b)
    assert list_b.status_code == 200
    items_b = list_b.json()["items"]
    assert len(items_b) == 1
    assert items_b[0]["id"] == prod_b_id
    assert items_b[0]["title"] == "Beta Camera 4K"

    # 6. Merchant A tries to get Product B by ID -> 404 Not Found
    attack_get = await async_client.get(
        f"/api/v1/products/{prod_b_id}",
        headers=headers_a,
    )
    assert attack_get.status_code == 404
    assert attack_get.json()["error"]["code"] == "PRODUCT_NOT_FOUND"

    # 7. Merchant B tries to get Product A by ID -> 404 Not Found
    attack_get_b = await async_client.get(
        f"/api/v1/products/{prod_a_id}",
        headers=headers_b,
    )
    assert attack_get_b.status_code == 404
    assert attack_get_b.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


@pytest.mark.asyncio
async def test_tenant_cannot_update_or_delete_other_tenant_products(
    async_client: AsyncClient,
) -> None:
    """Verify Tenant A cannot mutate or delete Tenant B's products."""
    token_a = await register_merchant(async_client, "hacker_a@badstore.com", "Bad Store")
    token_b = await register_merchant(async_client, "victim_b@goodstore.com", "Good Store")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Good store creates a product
    resp = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Legit Product",
            "sku": "LEGIT-001",
            "price": "99.00",
            "stock_quantity": 50,
        },
        headers=headers_b,
    )
    assert resp.status_code == 201
    prod_id = resp.json()["id"]

    # Hacker A attempts to modify the price and title of Good Store's product
    tamper_resp = await async_client.patch(
        f"/api/v1/products/{prod_id}",
        json={"title": "Hacked Product", "price": "1.00"},
        headers=headers_a,
    )
    assert tamper_resp.status_code == 404
    assert tamper_resp.json()["error"]["code"] == "PRODUCT_NOT_FOUND"

    # Verify original product remained completely unchanged
    verify_resp = await async_client.get(
        f"/api/v1/products/{prod_id}",
        headers=headers_b,
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["title"] == "Legit Product"
    assert verify_resp.json()["price"] == "99.00"

    # Hacker A attempts to delete Good Store's product
    delete_resp = await async_client.delete(
        f"/api/v1/products/{prod_id}",
        headers=headers_a,
    )
    assert delete_resp.status_code == 404
    assert delete_resp.json()["error"]["code"] == "PRODUCT_NOT_FOUND"

    # Verify product still exists
    verify_resp2 = await async_client.get(
        f"/api/v1/products/{prod_id}",
        headers=headers_b,
    )
    assert verify_resp2.status_code == 200


@pytest.mark.asyncio
async def test_tenant_cannot_adjust_stock_or_view_logs_for_other_tenant(
    async_client: AsyncClient,
) -> None:
    """Verify Tenant A cannot manipulate inventory or view inventory logs of Tenant B."""
    token_a = await register_merchant(async_client, "corp_a@store-a.com", "Corp A")
    token_b = await register_merchant(async_client, "corp_b@store-b.com", "Corp B")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Corp B creates product with 100 stock
    prod_resp = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Corp B Inventory Item",
            "sku": "CORP-B-INV-1",
            "price": "29.99",
            "stock_quantity": 100,
        },
        headers=headers_b,
    )
    assert prod_resp.status_code == 201
    prod_id = prod_resp.json()["id"]

    # Corp A attempts to deduct stock from Corp B's product
    stock_attack = await async_client.post(
        f"/api/v1/products/{prod_id}/inventory",
        json={"change_amount": -50, "reason": "MANUAL_ADJUSTMENT"},
        headers=headers_a,
    )
    assert stock_attack.status_code == 404
    assert stock_attack.json()["error"]["code"] == "PRODUCT_NOT_FOUND"

    # Corp A attempts to read inventory audit logs for Corp B's product
    logs_attack = await async_client.get(
        f"/api/v1/products/{prod_id}/inventory",
        headers=headers_a,
    )
    assert logs_attack.status_code == 404
    assert logs_attack.json()["error"]["code"] == "PRODUCT_NOT_FOUND"

    # Verify Corp B's product stock is still 100
    check_b = await async_client.get(f"/api/v1/products/{prod_id}", headers=headers_b)
    assert check_b.status_code == 200
    assert check_b.json()["stock_quantity"] == 100


@pytest.mark.asyncio
async def test_category_isolation_and_cross_tenant_linking_blocked(
    async_client: AsyncClient,
) -> None:
    """Verify Tenant A cannot access Tenant B's categories or link them to Tenant A's products."""
    token_a = await register_merchant(async_client, "shoes_a@mall.com", "Shoe Mall")
    token_b = await register_merchant(async_client, "gadgets_b@mall.com", "Gadget Mall")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Gadget Mall (Tenant B) creates a category
    cat_b_resp = await async_client.post(
        "/api/v1/categories",
        json={"name": "Smartwatches", "description": "Wearables"},
        headers=headers_b,
    )
    assert cat_b_resp.status_code == 201
    cat_b_id = cat_b_resp.json()["id"]

    # Shoe Mall (Tenant A) lists categories -> Should be empty
    list_cat_a = await async_client.get("/api/v1/categories", headers=headers_a)
    assert list_cat_a.status_code == 200
    assert len(list_cat_a.json()) == 0

    # Shoe Mall (Tenant A) tries to update Gadget Mall's category
    patch_cat_attack = await async_client.patch(
        f"/api/v1/categories/{cat_b_id}",
        json={"name": "Stolen Category"},
        headers=headers_a,
    )
    assert patch_cat_attack.status_code == 404
    assert patch_cat_attack.json()["error"]["code"] == "CATEGORY_NOT_FOUND"

    # Shoe Mall (Tenant A) tries to delete Gadget Mall's category
    del_cat_attack = await async_client.delete(
        f"/api/v1/categories/{cat_b_id}",
        headers=headers_a,
    )
    assert del_cat_attack.status_code == 404
    assert del_cat_attack.json()["error"]["code"] == "CATEGORY_NOT_FOUND"

    # Shoe Mall (Tenant A) tries to create a product associated with Tenant B's category
    link_attack = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Cross Tenant Shoe",
            "sku": "CROSS-001",
            "price": "50.00",
            "stock_quantity": 10,
            "category_ids": [cat_b_id],
        },
        headers=headers_a,
    )
    # Blocked: 404 CATEGORIES_NOT_FOUND because category does not exist in Tenant A
    assert link_attack.status_code == 404
    assert link_attack.json()["error"]["code"] == "CATEGORIES_NOT_FOUND"


@pytest.mark.asyncio
async def test_identical_sku_allowed_across_different_tenants(
    async_client: AsyncClient,
) -> None:
    """
    Verify that identical SKUs are permitted across different tenants,
    but duplicate SKUs within the same tenant are rejected with 409 Conflict.
    """
    token_a = await register_merchant(async_client, "shop1@market.com", "Shop 1")
    token_b = await register_merchant(async_client, "shop2@market.com", "Shop 2")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    shared_sku = "UNIVERSAL-SKU-99"

    # Shop 1 creates product with SKU
    resp_a = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Shop 1 Universal Item",
            "sku": shared_sku,
            "price": "19.99",
            "stock_quantity": 5,
        },
        headers=headers_a,
    )
    assert resp_a.status_code == 201
    assert resp_a.json()["sku"] == shared_sku

    # Shop 2 creates product with the exact same SKU -> Must succeed!
    resp_b = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Shop 2 Universal Item",
            "sku": shared_sku,
            "price": "24.99",
            "stock_quantity": 12,
        },
        headers=headers_b,
    )
    assert resp_b.status_code == 201
    assert resp_b.json()["sku"] == shared_sku

    # Shop 1 tries to create another product with the same SKU -> Must fail with 409 Conflict
    conflict_resp = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Shop 1 Duplicate SKU",
            "sku": shared_sku,
            "price": "15.00",
            "stock_quantity": 2,
        },
        headers=headers_a,
    )
    assert conflict_resp.status_code == 409
    assert conflict_resp.json()["error"]["code"] == "SKU_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_stock_boundary_and_consecutive_adjustments(
    async_client: AsyncClient,
) -> None:
    """Verify stock integrity and audit logging through sequential stock adjustments."""
    token = await register_merchant(async_client, "warehouse@logistics.com", "Logistics Co")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create product with initial stock 10
    create_resp = await async_client.post(
        "/api/v1/products",
        json={
            "title": "Stock Controlled Item",
            "sku": "STOCK-CTRL-01",
            "price": "10.00",
            "stock_quantity": 10,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    prod_id = create_resp.json()["id"]

    # 2. Perform 5 consecutive reductions of 2 items each
    for _ in range(5):
        adj_resp = await async_client.post(
            f"/api/v1/products/{prod_id}/inventory",
            json={"change_amount": -2, "reason": "MANUAL_ADJUSTMENT"},
            headers=headers,
        )
        assert adj_resp.status_code == 200

    # 3. Stock should now be exactly 0
    prod_check = await async_client.get(f"/api/v1/products/{prod_id}", headers=headers)
    assert prod_check.status_code == 200
    assert prod_check.json()["stock_quantity"] == 0

    # 4. Attempt to reduce stock below 0 -> Must return 400 Bad Request
    oversell_resp = await async_client.post(
        f"/api/v1/products/{prod_id}/inventory",
        json={"change_amount": -1, "reason": "MANUAL_ADJUSTMENT"},
        headers=headers,
    )
    assert oversell_resp.status_code == 400
    assert oversell_resp.json()["error"]["code"] == "INSUFFICIENT_STOCK"

    # 5. Check audit logs: 1 initial (10) + 5 sales (-2) = 6 logs total
    logs_resp = await async_client.get(
        f"/api/v1/products/{prod_id}/inventory",
        headers=headers,
    )
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert len(logs) == 6

    change_amounts = [log_entry["change_amount"] for log_entry in logs]
    assert change_amounts.count(-2) == 5
    assert 10 in change_amounts

    # Verify initial creation log details
    initial_log = next(log_entry for log_entry in logs if log_entry["change_amount"] == 10)
    assert initial_log["balance_after"] == 10
    assert initial_log["reason"] == "RESTOCK"
    assert initial_log["reference_id"] == "INITIAL_STOCK"
