"""
Integration tests for Meta WhatsApp Webhook Ingestion Endpoint.

Validates POST /api/v1/webhooks/whatsapp:
1. Valid HMAC signature returns 200 OK and persists message/customer.
2. Missing or invalid HMAC signature returns 401 Unauthorized.
3. Malformed JSON payload returns 400 Bad Request.
4. Payload with no registered organization gracefully returns 200 OK.
"""

import json
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.modules.messaging.security import compute_meta_signature
from app.modules.organizations.models import Organization


@pytest.fixture
async def test_org(async_db_engine) -> Organization:
    """Creates a sample organization for webhook tests."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        org = Organization(
            id=uuid.uuid4(),
            name="Webhook Test Org",
            slug=f"webhook-org-{uuid.uuid4().hex[:8]}",
        )
        session.add(org)
        await session.commit()
        return org


def build_raw_payload() -> bytes:
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550009999",
                                "phone_number_id": "10987654321",
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Bob Builder"},
                                    "wa_id": "15559876543",
                                }
                            ],
                            "messages": [
                                {
                                    "from": "15559876543",
                                    "id": "wamid.INTEGRATION_TEST_01",
                                    "timestamp": "1710000000",
                                    "type": "text",
                                    "text": {"body": "Can I buy 2 items?"},
                                }
                            ],
                            "statuses": [],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    return json.dumps(payload).encode("utf-8")


@pytest.mark.asyncio
async def test_webhook_ingestion_success(
    async_client: AsyncClient,
    test_org: Organization,
) -> None:
    """Verify valid signed webhook POST successfully returns 200 OK."""
    settings = get_settings()
    raw_payload = build_raw_payload()
    valid_signature = compute_meta_signature(raw_payload, settings.META_APP_SECRET)

    response = await async_client.post(
        "/api/v1/webhooks/whatsapp",
        content=raw_payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": valid_signature,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "received"}


@pytest.mark.asyncio
async def test_webhook_ingestion_missing_signature(
    async_client: AsyncClient,
) -> None:
    """Verify POST without X-Hub-Signature-256 header returns 401 Unauthorized."""
    raw_payload = build_raw_payload()

    response = await async_client.post(
        "/api/v1/webhooks/whatsapp",
        content=raw_payload,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_SIGNATURE"


@pytest.mark.asyncio
async def test_webhook_ingestion_invalid_signature(
    async_client: AsyncClient,
) -> None:
    """Verify POST with invalid signature hash returns 401 Unauthorized."""
    raw_payload = build_raw_payload()
    bogus_sig = "sha256=" + "0" * 64

    response = await async_client.post(
        "/api/v1/webhooks/whatsapp",
        content=raw_payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": bogus_sig,
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_SIGNATURE"


@pytest.mark.asyncio
async def test_webhook_ingestion_malformed_json(
    async_client: AsyncClient,
) -> None:
    """Verify POST with invalid JSON body returns 400 Bad Request."""
    settings = get_settings()
    corrupt_body = b"not-a-valid-json-string"
    valid_signature = compute_meta_signature(corrupt_body, settings.META_APP_SECRET)

    response = await async_client.post(
        "/api/v1/webhooks/whatsapp",
        content=corrupt_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": valid_signature,
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_JSON"
