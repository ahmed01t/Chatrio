"""
Integration tests for Meta WhatsApp Webhook Handshake Verification.

Validates GET /api/v1/webhooks/whatsapp:
1. Valid hub.mode, hub.verify_token, and hub.challenge returns 200 with challenge echo.
2. Invalid hub.verify_token returns 403 Forbidden.
3. Missing or incorrect hub.mode returns 403 Forbidden.
"""

import pytest
from httpx import AsyncClient

from app.core.config import get_settings


@pytest.mark.asyncio
async def test_webhook_handshake_success(async_client: AsyncClient) -> None:
    """Verify Meta handshake echoes hub.challenge with 200 OK when token matches."""
    settings = get_settings()
    challenge_val = "1158201244"

    response = await async_client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.META_VERIFY_TOKEN,
            "hub.challenge": challenge_val,
        },
    )

    assert response.status_code == 200
    assert response.text == challenge_val


@pytest.mark.asyncio
async def test_webhook_handshake_invalid_token(async_client: AsyncClient) -> None:
    """Verify Meta handshake rejects invalid verify_token with 403 Forbidden."""
    response = await async_client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token-12345",
            "hub.challenge": "1158201244",
        },
    )

    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "WEBHOOK_VERIFICATION_FAILED"


@pytest.mark.asyncio
async def test_webhook_handshake_invalid_mode(async_client: AsyncClient) -> None:
    """Verify Meta handshake rejects invalid mode (not 'subscribe') with 403 Forbidden."""
    settings = get_settings()

    response = await async_client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "publish",
            "hub.verify_token": settings.META_VERIFY_TOKEN,
            "hub.challenge": "1158201244",
        },
    )

    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "WEBHOOK_VERIFICATION_FAILED"


@pytest.mark.asyncio
async def test_webhook_handshake_missing_params(async_client: AsyncClient) -> None:
    """Verify Meta handshake rejects requests missing required hub parameters with 403."""
    response = await async_client.get("/api/v1/webhooks/whatsapp")

    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "WEBHOOK_VERIFICATION_FAILED"
