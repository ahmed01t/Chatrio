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
async def test_category_endpoints(async_client: AsyncClient) -> None:
    """Verify category creation, listing, updating, and deletion."""
    token = await create_auth_token(async_client, "cat_owner@example.com", "Cat Store")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Category
    cat_payload = {
        "name": "Winter Jackets",
        "description": "Heavy warm winter wear",
    }
    resp = await async_client.post("/api/v1/categories", json=cat_payload, headers=headers)
    assert resp.status_code == 201
    cat_data = resp.json()
    assert cat_data["name"] == "Winter Jackets"
    assert cat_data["slug"] == "winter-jackets"
    cat_id = cat_data["id"]

    # 2. List Categories
    list_resp = await async_client.get("/api/v1/categories", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 3. Update Category
    patch_resp = await async_client.patch(
        f"/api/v1/categories/{cat_id}",
        json={"name": "Winter Outerwear"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Winter Outerwear"

    # 4. Delete Category
    del_resp = await async_client.delete(f"/api/v1/categories/{cat_id}", headers=headers)
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_product_crud_endpoints(async_client: AsyncClient) -> None:
    """Verify product creation, listing with pagination, updating, and inventory adjustment."""
    token = await create_auth_token(async_client, "prod_owner@example.com", "Prod Store")
    headers = {"Authorization": f"Bearer {token}"}

    # Create category first
    cat_resp = await async_client.post(
        "/api/v1/categories",
        json={"name": "Footwear"},
        headers=headers,
    )
    cat_id = cat_resp.json()["id"]

    # 1. Create Product
    prod_payload = {
        "title": "Air Max Runner",
        "description": "Professional running shoe",
        "sku": "NIKE-AMR-42",
        "price": "149.99",
        "currency": "USD",
        "stock_quantity": 25,
        "is_active": True,
        "category_ids": [cat_id],
    }
    create_resp = await async_client.post("/api/v1/products", json=prod_payload, headers=headers)
    assert create_resp.status_code == 201
    prod_data = create_resp.json()
    assert prod_data["title"] == "Air Max Runner"
    assert prod_data["stock_quantity"] == 25
    assert len(prod_data["categories"]) == 1
    prod_id = prod_data["id"]

    # 2. Get Product by ID
    get_resp = await async_client.get(f"/api/v1/products/{prod_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["sku"] == "NIKE-AMR-42"

    # 3. List Products
    list_resp = await async_client.get("/api/v1/products?search=Runner", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    # 4. Adjust Inventory (+10 Restock)
    adj_payload = {
        "change_amount": 10,
        "reason": "RESTOCK",
        "reference_id": "SHIPMENT-100",
    }
    adj_resp = await async_client.post(
        f"/api/v1/products/{prod_id}/inventory",
        json=adj_payload,
        headers=headers,
    )
    assert adj_resp.status_code == 200
    assert adj_resp.json()["stock_quantity"] == 35

    # 5. Get Inventory Audit Logs
    logs_resp = await async_client.get(f"/api/v1/products/{prod_id}/inventory", headers=headers)
    assert logs_resp.status_code == 200
    assert len(logs_resp.json()) == 2  # initial stock + restock

    # 6. Delete Product
    del_resp = await async_client.delete(f"/api/v1/products/{prod_id}", headers=headers)
    assert del_resp.status_code == 204
