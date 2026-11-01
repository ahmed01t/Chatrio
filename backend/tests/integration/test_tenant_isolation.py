"""
Tenant Boundary and Isolation Integration Tests.

Validates:
1. Cross-tenant access is strictly denied (403 Forbidden).
2. Forged or mismatched organization tokens are rejected.
3. Expired tokens are rejected (401 Unauthorized).
4. Deactivated accounts cannot access tenant resources.
5. Multi-tenant members correctly resolve their active organization context.
"""

import uuid
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.modules.auth.models import User
from app.modules.organizations.models import MemberRole, Organization, OrganizationMember


@pytest.mark.asyncio
async def test_cross_tenant_access_blocked(
    async_client: AsyncClient,
) -> None:
    """
    Verify that User A cannot access Organization B resources even if they
    forge or alter the org_id in their JWT token.
    """
    # 1. Register Merchant A (Org A)
    resp_a = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner_a@store-a.com",
            "password": "Password123!",
            "full_name": "Owner A",
            "organization_name": "Store Alpha",
        },
    )
    assert resp_a.status_code == 201
    user_a_id = resp_a.json()["user"]["id"]

    # 2. Register Merchant B (Org B)
    resp_b = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner_b@store-b.com",
            "password": "Password123!",
            "full_name": "Owner B",
            "organization_name": "Store Beta",
        },
    )
    assert resp_b.status_code == 201
    org_b_id = resp_b.json()["organization"]["id"]

    # 3. User A attempts to forge a token with User A's ID but Org B's ID!
    forged_token = create_access_token(
        data={
            "sub": user_a_id,
            "org_id": org_b_id,
            "role": "OWNER",
        }
    )

    # 4. User A attempts to access protected endpoint with the forged token
    attack_response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged_token}"},
    )

    # Strict isolation: 403 Forbidden
    assert attack_response.status_code == 403
    data = attack_response.json()
    assert data["error"]["code"] == "FORBIDDEN_TENANT_ACCESS"


@pytest.mark.asyncio
async def test_expired_token_rejected_at_route(
    async_client: AsyncClient,
) -> None:
    """Verify that an expired JWT token receives 401 TOKEN_EXPIRED."""
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "expired_test@example.com",
            "password": "Password123!",
            "full_name": "Expired Test",
            "organization_name": "Expired Org",
        },
    )
    user_id = resp.json()["user"]["id"]
    org_id = resp.json()["organization"]["id"]

    # Generate token that expired 10 minutes ago
    expired_token = create_access_token(
        data={"sub": user_id, "org_id": org_id, "role": "OWNER"},
        expires_delta=timedelta(minutes=-10),
    )

    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_inactive_user_token_rejected_at_route(
    async_client: AsyncClient,
    async_db_engine,
) -> None:
    """
    Verify that if a user account is deactivated, their existing valid token
    is immediately rejected upon the next request.
    """
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "deactivated_user@example.com",
            "password": "Password123!",
            "full_name": "Deactivated User",
            "organization_name": "Deactivated Org",
        },
    )
    token = resp.json()["access_token"]
    user_id = uuid.UUID(resp.json()["user"]["id"])

    # Deactivate user directly in the database
    async with AsyncSession(async_db_engine) as session:
        user = await session.get(User, user_id)
        assert user is not None
        user.is_active = False
        await session.commit()

    # Attempt request with the previously valid token
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "ACCOUNT_INACTIVE"


@pytest.mark.asyncio
async def test_multi_tenant_user_switching(
    async_client: AsyncClient,
    async_db_engine,
) -> None:
    """
    Verify that when a user is a member of multiple organizations,
    they can access both organizations using tokens scoped to each org.
    """
    # 1. Register primary organization (Store 1)
    resp1 = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "multi_user@example.com",
            "password": "Password123!",
            "full_name": "Multi Tenant User",
            "organization_name": "Store One",
        },
    )
    user_id = uuid.UUID(resp1.json()["user"]["id"])
    org1_id = uuid.UUID(resp1.json()["organization"]["id"])

    # 2. Add user as an AGENT to a second organization (Store 2) in the database
    org2_id = uuid.uuid4()
    async with AsyncSession(async_db_engine) as session:
        org2 = Organization(
            id=org2_id,
            name="Store Two",
            slug="store-two",
        )
        member2 = OrganizationMember(
            id=uuid.uuid4(),
            organization_id=org2_id,
            user_id=user_id,
            role=MemberRole.AGENT,
        )
        session.add_all([org2, member2])
        await session.commit()

    # 3. Access with Store 1 token (Role should be OWNER)
    token_org1 = create_access_token(
        data={"sub": str(user_id), "org_id": str(org1_id), "role": "OWNER"}
    )
    resp_org1 = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_org1}"},
    )
    assert resp_org1.status_code == 200
    assert resp_org1.json()["organization_name"] == "Store One"
    assert resp_org1.json()["role"] == "OWNER"

    # 4. Access with Store 2 token (Role should be AGENT)
    token_org2 = create_access_token(
        data={"sub": str(user_id), "org_id": str(org2_id), "role": "AGENT"}
    )
    resp_org2 = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_org2}"},
    )
    assert resp_org2.status_code == 200
    assert resp_org2.json()["organization_name"] == "Store Two"
    assert resp_org2.json()["role"] == "AGENT"
