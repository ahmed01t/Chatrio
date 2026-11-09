"""
Meta WhatsApp Webhook Handshake & Ingestion Router.

Endpoints:
- GET /api/v1/webhooks/whatsapp: Handshake verification endpoint for Meta App dashboard.
- POST /api/v1/webhooks/whatsapp: Sub-50ms ingestion endpoint with HMAC-SHA256 verification.
"""

import json
from typing import Annotated

from fastapi import APIRouter, Header, Query, Request, Response, status
from fastapi.responses import PlainTextResponse

from app.api.dependencies import DBSession
from app.core.config import get_settings
from app.core.exceptions import BadRequestException, ForbiddenException, UnauthorizedException
from app.modules.messaging.security import verify_meta_signature
from app.modules.messaging.service import MessagingService

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


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="Meta WhatsApp Webhook Event Ingestion",
)
async def ingest_webhook(
    request: Request,
    session: DBSession,
    x_hub_signature_256: Annotated[
        str | None,
        Header(alias="X-Hub-Signature-256", description="Meta HMAC-SHA256 signature header"),
    ] = None,
) -> dict[str, str]:
    """
    Sub-50ms Meta WhatsApp Webhook Ingestion Endpoint.

    1. Reads raw bytes and validates HMAC-SHA256 signature against META_APP_SECRET.
    2. Parses incoming JSON webhook event.
    3. Resolves tenant organization mapping.
    4. Passes to MessagingService for customer & conversation persistence.
    5. Returns 200 OK immediately to satisfy Meta's response deadline.
    """
    settings = get_settings()
    raw_body = await request.body()

    # 1. HMAC signature verification
    if not verify_meta_signature(
        raw_body=raw_body,
        signature_header=x_hub_signature_256,
        app_secret=settings.META_APP_SECRET,
    ):
        raise UnauthorizedException(
            code="INVALID_SIGNATURE",
            message="Invalid or missing X-Hub-Signature-256 header.",
        )

    # 2. Parse JSON payload
    try:
        payload_data = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        raise BadRequestException(
            code="INVALID_JSON",
            message=f"Failed to parse JSON webhook payload: {e}",
        ) from e

    # 3. Resolve tenant organization
    phone_number_id: str | None = None
    try:
        if "entry" in payload_data and payload_data["entry"]:
            entry_first = payload_data["entry"][0]
            if "changes" in entry_first and entry_first["changes"]:
                val = entry_first["changes"][0].get("value", {})
                metadata = val.get("metadata", {})
                phone_number_id = metadata.get("phone_number_id")
    except Exception:
        phone_number_id = None

    organization_id = await MessagingService.resolve_organization_by_phone_id(
        session=session,
        phone_number_id=phone_number_id,
    )

    # 4. Ingest and persist messages
    if organization_id:
        await MessagingService.process_incoming_payload(
            session=session,
            organization_id=organization_id,
            payload=payload_data,
        )

    return {"status": "received"}
