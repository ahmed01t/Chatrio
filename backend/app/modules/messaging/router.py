"""
Meta WhatsApp Webhook Handshake & Ingestion Router.

Endpoints:
- GET /api/v1/webhooks/whatsapp: Handshake verification endpoint for Meta App dashboard.
- POST /api/v1/webhooks/whatsapp: (Added in Task 5) Sub-50ms ingestion endpoint.
"""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings
from app.core.exceptions import ForbiddenException

router = APIRouter(prefix="/webhooks/whatsapp", tags=["Meta WhatsApp Webhooks"])


@router.get(
    "",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
    summary="Meta Webhook Verification Handshake",
)
async def verify_webhook(
    hub_mode: Annotated[
        str | None,
        Query(alias="hub.mode", description="Subscription mode: 'subscribe'"),
    ] = None,
    hub_verify_token: Annotated[
        str | None,
        Query(alias="hub.verify_token", description="Verification token configured in Meta App"),
    ] = None,
    hub_challenge: Annotated[
        str | None,
        Query(alias="hub.challenge", description="Challenge string to echo back"),
    ] = None,
) -> Response:
    """
    Verification challenge handshake for Meta WhatsApp Cloud API.

    When you configure a webhook URL in Meta Developer Portal, Meta sends a GET request:
    - hub.mode=subscribe
    - hub.verify_token=<your_verify_token>
    - hub.challenge=<random_string_or_integer>

    If the token matches, the server must echo back `hub.challenge` as plain text with 200 OK.
    If the token is invalid or mode is not 'subscribe', responds with 403 Forbidden.
    """
    settings = get_settings()

    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        if hub_challenge is not None:
            return PlainTextResponse(content=hub_challenge, status_code=status.HTTP_200_OK)

    raise ForbiddenException(
        code="WEBHOOK_VERIFICATION_FAILED",
        message="Invalid verification token or subscription mode.",
    )
