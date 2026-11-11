import pytest
from httpx import AsyncClient


async def register_merchant(
    async_client: AsyncClient,
    email: str,
    org_name: str,
    full_name: str = "Store Owner",
    password: str = "SecurePassword123!",
) -> dict:
    """Helper to register a merchant and return full auth response."""
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "organization_name": org_name,
        },
    )
    assert resp.status_code == 201
    return resp.json()


async def login_user(async_client: AsyncClient, email: str, password: str) -> str:
    """Helper to sign in a user and return their bearer access token."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_get_and_update_organization_success(async_client: AsyncClient) -> None:
    """Verify GET and PATCH /api/v1/organizations/current work for OWNER."""
    auth = await register_merchant(async_client, "org_owner@example.com", "Original Store")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    get_resp = await async_client.get("/api/v1/organizations/current", headers=headers)
    assert get_resp.status_code == 200
    org_data = get_resp.json()
    assert org_data["name"] == "Original Store"
    assert org_data["slug"] == "original-store"
    assert org_data["member_count"] == 1
    assert org_data["current_user_role"] == "OWNER"

    patch_resp = await async_client.patch(
        "/api/v1/organizations/current",
        json={"name": "Updated Flagship Store", "slug": "updated flagship"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["name"] == "Updated Flagship Store"
    assert updated["slug"] == "updated-flagship"


@pytest.mark.asyncio
async def test_update_organization_duplicate_slug_conflict(async_client: AsyncClient) -> None:
    """Verify updating an organization slug to another tenant's slug returns 409 Conflict."""
    await register_merchant(async_client, "tenant_a@example.com", "Alpha Shop")
    auth_b = await register_merchant(async_client, "tenant_b@example.com", "Beta Shop")
    headers_b = {"Authorization": f"Bearer {auth_b['access_token']}"}

    resp = await async_client.patch(
        "/api/v1/organizations/current",
        json={"slug": "alpha-shop"},
        headers=headers_b,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "SLUG_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_organization_members_crud_lifecycle(async_client: AsyncClient) -> None:
    """Verify adding, listing, role-updating, and removing organization members."""
    auth = await register_merchant(async_client, "team_owner@example.com", "Team Store")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    # 1. Add a new AGENT user
    add_resp = await async_client.post(
        "/api/v1/organizations/current/members",
        json={
            "email": "support.agent@example.com",
            "full_name": "Sara Agent",
            "password": "AgentPassword123!",
            "role": "AGENT",
        },
        headers=headers,
    )
    assert add_resp.status_code == 201
    member_data = add_resp.json()
    assert member_data["email"] == "support.agent@example.com"
    assert member_data["full_name"] == "Sara Agent"
    assert member_data["role"] == "AGENT"
    member_id = member_data["id"]

    # 2. New user can log in and access their organization context
    agent_token = await login_user(async_client, "support.agent@example.com", "AgentPassword123!")
    agent_headers = {"Authorization": f"Bearer {agent_token}"}
    me_resp = await async_client.get("/api/v1/auth/me", headers=agent_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "AGENT"

    # 3. List members returns both OWNER and AGENT
    list_resp = await async_client.get("/api/v1/organizations/current/members", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 2

    # 4. Update member role from AGENT to ADMIN
    role_resp = await async_client.patch(
        f"/api/v1/organizations/current/members/{member_id}",
        json={"role": "ADMIN"},
        headers=headers,
    )
    assert role_resp.status_code == 200
    assert role_resp.json()["role"] == "ADMIN"

    # 5. Delete member
    del_resp = await async_client.delete(
        f"/api/v1/organizations/current/members/{member_id}",
        headers=headers,
    )
    assert del_resp.status_code == 204

    list_after = await async_client.get("/api/v1/organizations/current/members", headers=headers)
    assert list_after.json()["total"] == 1


@pytest.mark.asyncio
async def test_member_management_edge_cases_and_rbac(async_client: AsyncClient) -> None:
    """Verify RBAC restrictions, self-removal block, duplicate member, and sole owner guard."""
    auth = await register_merchant(async_client, "rbac_owner@example.com", "RBAC Store")
    owner_headers = {"Authorization": f"Bearer {auth['access_token']}"}

    # Find owner's membership ID
    members_resp = await async_client.get(
        "/api/v1/organizations/current/members", headers=owner_headers
    )
    owner_member_id = members_resp.json()["items"][0]["id"]

    # Edge 1: Cannot demote sole OWNER
    demote_resp = await async_client.patch(
        f"/api/v1/organizations/current/members/{owner_member_id}",
        json={"role": "ADMIN"},
        headers=owner_headers,
    )
    assert demote_resp.status_code == 400
    assert demote_resp.json()["error"]["code"] == "CANNOT_DEMOTE_LAST_OWNER"

    # Edge 2: Cannot remove self
    self_del_resp = await async_client.delete(
        f"/api/v1/organizations/current/members/{owner_member_id}",
        headers=owner_headers,
    )
    assert self_del_resp.status_code == 400
    assert self_del_resp.json()["error"]["code"] == "CANNOT_REMOVE_SELF"

    # Edge 3: Missing full_name/password for non-existent user fails with 400
    missing_resp = await async_client.post(
        "/api/v1/organizations/current/members",
        json={"email": "brandnew@example.com", "role": "VIEWER"},
        headers=owner_headers,
    )
    assert missing_resp.status_code == 400
    assert missing_resp.json()["error"]["code"] == "USER_DETAILS_REQUIRED"

    # Edge 4: Cannot assign OWNER directly
    owner_assign_resp = await async_client.post(
        "/api/v1/organizations/current/members",
        json={
            "email": "coowner@example.com",
            "full_name": "Co Owner",
            "password": "Password123!",
            "role": "OWNER",
        },
        headers=owner_headers,
    )
    assert owner_assign_resp.status_code == 403
    assert owner_assign_resp.json()["error"]["code"] == "CANNOT_ASSIGN_OWNER"

    # Add a VIEWER and verify VIEWER cannot add members or edit organization
    await async_client.post(
        "/api/v1/organizations/current/members",
        json={
            "email": "viewer@example.com",
            "full_name": "View Only",
            "password": "ViewerPassword123!",
            "role": "VIEWER",
        },
        headers=owner_headers,
    )
    viewer_token = await login_user(async_client, "viewer@example.com", "ViewerPassword123!")
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    # Duplicate member conflict
    dup_resp = await async_client.post(
        "/api/v1/organizations/current/members",
        json={"email": "viewer@example.com", "role": "AGENT"},
        headers=owner_headers,
    )
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"]["code"] == "MEMBER_ALREADY_EXISTS"

    # VIEWER blocked from updating org
    viewer_patch = await async_client.patch(
        "/api/v1/organizations/current",
        json={"name": "Hijacked"},
        headers=viewer_headers,
    )
    assert viewer_patch.status_code == 403
    assert viewer_patch.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"


@pytest.mark.asyncio
async def test_member_cross_tenant_isolation(async_client: AsyncClient) -> None:
    """Verify Organization A cannot modify or delete Organization B's members."""
    auth_a = await register_merchant(async_client, "iso_a@example.com", "Tenant A")
    auth_b = await register_merchant(async_client, "iso_b@example.com", "Tenant B")
    headers_a = {"Authorization": f"Bearer {auth_a['access_token']}"}
    headers_b = {"Authorization": f"Bearer {auth_b['access_token']}"}

    add_b = await async_client.post(
        "/api/v1/organizations/current/members",
        json={
            "email": "b_staff@example.com",
            "full_name": "Tenant B Staff",
            "password": "StaffPassword123!",
            "role": "AGENT",
        },
        headers=headers_b,
    )
    assert add_b.status_code == 201
    b_member_id = add_b.json()["id"]

    # Tenant A tries to update Tenant B's member
    cross_patch = await async_client.patch(
        f"/api/v1/organizations/current/members/{b_member_id}",
        json={"role": "VIEWER"},
        headers=headers_a,
    )
    assert cross_patch.status_code == 404
    assert cross_patch.json()["error"]["code"] == "MEMBER_NOT_FOUND"

    # Tenant A tries to delete Tenant B's member
    cross_del = await async_client.delete(
        f"/api/v1/organizations/current/members/{b_member_id}",
        headers=headers_a,
    )
    assert cross_del.status_code == 404
    assert cross_del.json()["error"]["code"] == "MEMBER_NOT_FOUND"

