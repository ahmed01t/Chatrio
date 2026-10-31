import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_merchant_endpoint_success(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/auth/register creates user, org, and returns 201 with JWT."""
    payload = {
        "email": "ahmed.merchant@example.com",
        "password": "StrongPassword123!",
        "full_name": "Ahmed Khan",
        "organization_name": "Ahmed's Apparel",
    }

    response = await async_client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600
    assert data["user"]["email"] == "ahmed.merchant@example.com"
    assert data["user"]["full_name"] == "Ahmed Khan"
    assert data["organization"]["name"] == "Ahmed's Apparel"
    assert data["organization"]["slug"] == "ahmeds-apparel"


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_conflict(async_client: AsyncClient) -> None:
    """Verify registering with duplicate email returns 409 Conflict with structured error."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "User One",
        "organization_name": "Store One",
    }
    # First registration
    resp1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    # Second registration with same email
    resp2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    error_data = resp2.json()
    assert error_data["error"]["code"] == "EMAIL_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_login_endpoint_success(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/auth/login returns 200 OK and valid access token."""
    reg_payload = {
        "email": "login_user@example.com",
        "password": "SecretPassword123!",
        "full_name": "Login User",
        "organization_name": "Login Store",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "login_user@example.com",
        "password": "SecretPassword123!",
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login_user@example.com"


@pytest.mark.asyncio
async def test_login_invalid_password_returns_401(async_client: AsyncClient) -> None:
    """Verify login with incorrect password returns 401 Unauthorized."""
    reg_payload = {
        "email": "wrong_password@example.com",
        "password": "RealPassword123!",
        "full_name": "User",
        "organization_name": "Store",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrong_password@example.com",
        "password": "IncorrectPassword999!",
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)

    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_get_me_endpoint_success(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/auth/me returns current user profile and active tenant."""
    reg_payload = {
        "email": "me_profile@example.com",
        "password": "ProfilePassword123!",
        "full_name": "Profile Owner",
        "organization_name": "Profile Store",
    }
    reg_resp = await async_client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_resp.json()["access_token"]

    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me_profile@example.com"
    assert data["full_name"] == "Profile Owner"
    assert data["organization_name"] == "Profile Store"
    assert data["role"] == "OWNER"


@pytest.mark.asyncio
async def test_get_me_unauthorized_without_token(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/auth/me without token returns 401 Unauthorized."""
    response = await async_client.get("/api/v1/auth/me")

    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_me_unauthorized_with_invalid_token(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/auth/me with invalid token returns 401 Unauthorized."""
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_TOKEN"
