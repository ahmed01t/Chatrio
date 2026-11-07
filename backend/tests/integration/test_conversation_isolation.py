"""
Integration tests for multi-tenant isolation across Customers, Conversations, and Messages.

Validates that:
1. Customer isolation: Tenant A cannot read, list, or modify Tenant B's customers.
2. Identical phone number scoping: Multiple merchants can have the same customer phone
   number without conflict, while intra-tenant duplicates are rejected with 409 Conflict.
3. Conversation inbox isolation: Tenant A cannot see, query, or initiate sessions with
   Tenant B's customers.
4. Human takeover & status isolation: Tenant A cannot tamper with Tenant B's takeover state.
5. Message transcript isolation: Tenant A cannot read or inject messages into Tenant B's
   conversations.
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
async def test_customer_isolation(async_client: AsyncClient) -> None:
    """Verify Tenant A cannot list, view, or update Tenant B's customers."""
    token_a = await register_merchant(async_client, "owner_a@tenant-a.com", "Store A")
    token_b = await register_merchant(async_client, "owner_b@tenant-b.com", "Store B")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Tenant A creates Customer A
    resp_a = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": "+14155551111", "name": "Customer Alpha"},
        headers=headers_a,
    )
    assert resp_a.status_code == 201
    cust_a_id = resp_a.json()["id"]

    # 2. Tenant B creates Customer B
    resp_b = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": "+14155552222", "name": "Customer Beta"},
        headers=headers_b,
    )
    assert resp_b.status_code == 201
    cust_b_id = resp_b.json()["id"]

    # 3. Tenant A lists customers -> Only sees Customer A
    list_a = await async_client.get("/api/v1/customers", headers=headers_a)
    assert list_a.status_code == 200
    assert list_a.json()["total"] == 1
    assert list_a.json()["items"][0]["id"] == cust_a_id

    # 4. Tenant B lists customers -> Only sees Customer B
    list_b = await async_client.get("/api/v1/customers", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json()["total"] == 1
    assert list_b.json()["items"][0]["id"] == cust_b_id

    # 5. Tenant A attempts to view Customer B -> 404 Not Found
    attack_get = await async_client.get(
        f"/api/v1/customers/{cust_b_id}",
        headers=headers_a,
    )
    assert attack_get.status_code == 404
    assert attack_get.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"

    # 6. Tenant A attempts to update Customer B -> 404 Not Found
    attack_patch = await async_client.patch(
        f"/api/v1/customers/{cust_b_id}",
        json={"name": "Hacked Customer"},
        headers=headers_a,
    )
    assert attack_patch.status_code == 404
    assert attack_patch.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"

    # Verify Customer B remains unchanged
    verify_b = await async_client.get(f"/api/v1/customers/{cust_b_id}", headers=headers_b)
    assert verify_b.status_code == 200
    assert verify_b.json()["name"] == "Customer Beta"


@pytest.mark.asyncio
async def test_identical_phone_numbers_allowed_across_tenants(
    async_client: AsyncClient,
) -> None:
    """
    Verify that the same phone number can be registered across multiple tenants,
    but duplicate phones within the same tenant are rejected with 409 Conflict.
    """
    token_1 = await register_merchant(async_client, "shop1@brand.com", "Brand 1")
    token_2 = await register_merchant(async_client, "shop2@brand.com", "Brand 2")

    headers_1 = {"Authorization": f"Bearer {token_1}"}
    headers_2 = {"Authorization": f"Bearer {token_2}"}

    shared_phone = "+14155557777"

    # Brand 1 creates customer with phone
    resp1 = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": shared_phone, "name": "Shopper at Brand 1"},
        headers=headers_1,
    )
    assert resp1.status_code == 201
    assert resp1.json()["phone_number"] == shared_phone

    # Brand 2 creates customer with identical phone -> Must succeed!
    resp2 = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": shared_phone, "name": "Shopper at Brand 2"},
        headers=headers_2,
    )
    assert resp2.status_code == 201
    assert resp2.json()["phone_number"] == shared_phone
    # Ensure distinct customer IDs across tenants
    assert resp1.json()["id"] != resp2.json()["id"]

    # Brand 1 attempts to create another customer with the same phone -> 409 Conflict
    conflict_resp = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": shared_phone, "name": "Duplicate Shopper"},
        headers=headers_1,
    )
    assert conflict_resp.status_code == 409
    assert conflict_resp.json()["error"]["code"] == "CUSTOMER_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_conversation_and_inbox_isolation(
    async_client: AsyncClient,
) -> None:
    """Verify Tenant A cannot view or access Tenant B's conversation sessions."""
    token_a = await register_merchant(async_client, "store_a@chats.com", "Chats A")
    token_b = await register_merchant(async_client, "store_b@chats.com", "Chats B")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Store A creates customer and conversation
    cust_a = (
        await async_client.post(
            "/api/v1/customers",
            json={"phone_number": "+15551113333", "name": "Cust A"},
            headers=headers_a,
        )
    ).json()

    conv_a = (
        await async_client.post(
            "/api/v1/conversations",
            json={"customer_id": cust_a["id"]},
            headers=headers_a,
        )
    ).json()

    # Store B creates customer and conversation
    cust_b = (
        await async_client.post(
            "/api/v1/customers",
            json={"phone_number": "+15552224444", "name": "Cust B"},
            headers=headers_b,
        )
    ).json()

    conv_b = (
        await async_client.post(
            "/api/v1/conversations",
            json={"customer_id": cust_b["id"]},
            headers=headers_b,
        )
    ).json()

    # Store A lists conversations -> Only sees conv_a
    inbox_a = await async_client.get("/api/v1/conversations", headers=headers_a)
    assert inbox_a.status_code == 200
    assert inbox_a.json()["total"] == 1
    assert inbox_a.json()["items"][0]["id"] == conv_a["id"]

    # Store B lists conversations -> Only sees conv_b
    inbox_b = await async_client.get("/api/v1/conversations", headers=headers_b)
    assert inbox_b.status_code == 200
    assert inbox_b.json()["total"] == 1
    assert inbox_b.json()["items"][0]["id"] == conv_b["id"]

    # Store A attempts to fetch Conversation B -> 404 Not Found
    attack_conv = await async_client.get(
        f"/api/v1/conversations/{conv_b['id']}",
        headers=headers_a,
    )
    assert attack_conv.status_code == 404
    assert attack_conv.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"

    # Store A attempts to initiate a conversation using Store B's customer ID -> 404 Not Found
    cross_start = await async_client.post(
        "/api/v1/conversations",
        json={"customer_id": cust_b["id"]},
        headers=headers_a,
    )
    assert cross_start.status_code == 404
    assert cross_start.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"


@pytest.mark.asyncio
async def test_human_takeover_and_status_isolation(
    async_client: AsyncClient,
) -> None:
    """Verify Tenant A cannot modify the takeover or status of Tenant B's conversation."""
    token_a = await register_merchant(async_client, "intruder@domain.com", "Intruder Corp")
    token_b = await register_merchant(async_client, "victim@domain.com", "Victim Corp")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Victim Corp creates customer and active conversation
    cust_b = (
        await async_client.post(
            "/api/v1/customers",
            json={"phone_number": "+15559991111", "name": "Victim Cust"},
            headers=headers_b,
        )
    ).json()

    conv_b = (
        await async_client.post(
            "/api/v1/conversations",
            json={"customer_id": cust_b["id"]},
            headers=headers_b,
        )
    ).json()
    assert conv_b["is_ai_active"] is True
    assert conv_b["status"] == "ACTIVE"

    # Intruder A attempts to toggle human takeover on Victim's conversation
    attack_takeover = await async_client.patch(
        f"/api/v1/conversations/{conv_b['id']}/takeover",
        json={"is_ai_active": False},
        headers=headers_a,
    )
    assert attack_takeover.status_code == 404
    assert attack_takeover.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"

    # Intruder A attempts to close Victim's conversation
    attack_status = await async_client.patch(
        f"/api/v1/conversations/{conv_b['id']}/status",
        json={"status": "CLOSED"},
        headers=headers_a,
    )
    assert attack_status.status_code == 404
    assert attack_status.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"

    # Verify Victim's conversation is completely intact
    verify_b = await async_client.get(
        f"/api/v1/conversations/{conv_b['id']}",
        headers=headers_b,
    )
    assert verify_b.status_code == 200
    assert verify_b.json()["is_ai_active"] is True
    assert verify_b.json()["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_message_transcript_and_injection_isolation(
    async_client: AsyncClient,
) -> None:
    """Verify Tenant A cannot read or inject messages into Tenant B's conversation."""
    token_a = await register_merchant(async_client, "attacker@sec.com", "Attacker Store")
    token_b = await register_merchant(async_client, "legit@sec.com", "Legit Store")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Legit store sets up conversation with a customer message
    cust_b = (
        await async_client.post(
            "/api/v1/customers",
            json={"phone_number": "+15558883333", "name": "Legit Shopper"},
            headers=headers_b,
        )
    ).json()

    conv_b = (
        await async_client.post(
            "/api/v1/conversations",
            json={"customer_id": cust_b["id"]},
            headers=headers_b,
        )
    ).json()

    # Legit merchant posts message
    post_resp = await async_client.post(
        f"/api/v1/conversations/{conv_b['id']}/messages",
        json={
            "sender_type": "HUMAN_AGENT",
            "direction": "OUTBOUND",
            "text_body": "Legitimate secret message",
        },
        headers=headers_b,
    )
    assert post_resp.status_code == 201

    # Attacker attempts to read conversation messages
    attack_read = await async_client.get(
        f"/api/v1/conversations/{conv_b['id']}/messages",
        headers=headers_a,
    )
    assert attack_read.status_code == 404
    assert attack_read.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"

    # Attacker attempts to post a message into Victim's conversation
    attack_post = await async_client.post(
        f"/api/v1/conversations/{conv_b['id']}/messages",
        json={
            "sender_type": "HUMAN_AGENT",
            "direction": "OUTBOUND",
            "text_body": "Injected malicious message",
        },
        headers=headers_a,
    )
    assert attack_post.status_code == 404
    assert attack_post.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"

    # Verify Legit store's conversation only has 1 message (no injected message)
    verify_msgs = await async_client.get(
        f"/api/v1/conversations/{conv_b['id']}/messages",
        headers=headers_b,
    )
    assert verify_msgs.status_code == 200
    msgs = verify_msgs.json()["items"]
    assert len(msgs) == 1
    assert msgs[0]["text_body"] == "Legitimate secret message"

