"""
Integration tests for Customer and Conversation REST Endpoints.
Validates:
1. Customer creation, listing, detail fetch, and updating.
2. Conversation session initiation and inbox listing.
3. Human takeover toggle (is_ai_active=False / True).
4. Sending and listing conversation messages.
5. Conversation status lifecycle transitions.
"""

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
async def test_customer_endpoints(async_client: AsyncClient) -> None:
    """Verify customer creation, directory listing, detail retrieval, and updates."""
    token = await create_auth_token(async_client, "owner_cust@example.com", "Cust Store")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Customer
    payload = {
        "phone_number": "+1 (415) 555-8888",
        "name": "Sarah Connor",
        "email": "sarah@example.com",
        "metadata": {"vip": True},
    }
    create_resp = await async_client.post("/api/v1/customers", json=payload, headers=headers)
    assert create_resp.status_code == 201
    cust_data = create_resp.json()
    assert cust_data["phone_number"] == "+14155558888"
    assert cust_data["name"] == "Sarah Connor"
    assert cust_data["metadata"] == {"vip": True}
    customer_id = cust_data["id"]

    # 2. List Customers
    list_resp = await async_client.get("/api/v1/customers", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["id"] == customer_id

    # 3. Get Customer by ID
    get_resp = await async_client.get(f"/api/v1/customers/{customer_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Sarah Connor"

    # 4. Update Customer Profile
    patch_resp = await async_client.patch(
        f"/api/v1/customers/{customer_id}",
        json={"name": "Sarah J. Connor", "is_blocked": True},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Sarah J. Connor"
    assert patch_resp.json()["is_blocked"] is True


@pytest.mark.asyncio
async def test_conversation_and_messaging_endpoints(async_client: AsyncClient) -> None:
    """Verify conversation lifecycle, takeover mode, and message dispatch."""
    token = await create_auth_token(async_client, "owner_chat@example.com", "Chat Store")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Customer
    cust_resp = await async_client.post(
        "/api/v1/customers",
        json={"phone_number": "+14155559999", "name": "John Wick"},
        headers=headers,
    )
    assert cust_resp.status_code == 201
    customer_id = cust_resp.json()["id"]

    # 2. Start Conversation
    conv_resp = await async_client.post(
        "/api/v1/conversations",
        json={"customer_id": customer_id, "channel": "WHATSAPP"},
        headers=headers,
    )
    assert conv_resp.status_code == 201
    conv_data = conv_resp.json()
    assert conv_data["customer_id"] == customer_id
    assert conv_data["status"] == "ACTIVE"
    assert conv_data["is_ai_active"] is True
    conv_id = conv_data["id"]

    # 3. List Conversations (Inbox)
    inbox_resp = await async_client.get("/api/v1/conversations", headers=headers)
    assert inbox_resp.status_code == 200
    assert inbox_resp.json()["total"] == 1
    assert inbox_resp.json()["items"][0]["id"] == conv_id

    # 4. Human Takeover: Toggle is_ai_active to False
    takeover_resp = await async_client.patch(
        f"/api/v1/conversations/{conv_id}/takeover",
        json={"is_ai_active": False},
        headers=headers,
    )
    assert takeover_resp.status_code == 200
    assert takeover_resp.json()["is_ai_active"] is False

    # 5. Send Outbound Human Message
    send_resp = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={
            "sender_type": "HUMAN_AGENT",
            "direction": "OUTBOUND",
            "content_type": "TEXT",
            "text_body": "Hello Mr. Wick, how can I assist you with your order?",
        },
        headers=headers,
    )
    assert send_resp.status_code == 201
    msg_data = send_resp.json()
    assert msg_data["conversation_id"] == conv_id
    assert msg_data["text_body"] == "Hello Mr. Wick, how can I assist you with your order?"
    assert msg_data["sender_type"] == "HUMAN_AGENT"

    # 6. List Messages History
    msgs_resp = await async_client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=headers,
    )
    assert msgs_resp.status_code == 200
    msgs_data = msgs_resp.json()
    assert msgs_data["total"] == 1
    assert msgs_data["items"][0]["id"] == msg_data["id"]

    # 7. Update Conversation Status to CLOSED
    status_resp = await async_client.patch(
        f"/api/v1/conversations/{conv_id}/status",
        json={"status": "CLOSED"},
        headers=headers,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "CLOSED"
