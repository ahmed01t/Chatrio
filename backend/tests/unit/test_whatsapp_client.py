"""
Unit tests for WhatsApp Cloud API Outbound Client.

Validates:
1. Recipient phone number normalization (strips non-digits).
2. Outbound text message dispatch (payload format, URL, auth headers).
3. Outbound interactive button dispatch (1 to 3 buttons, headers/footers).
4. Validation rule: button counts must be between 1 and 3.
5. Error handling for HTTP 4xx/5xx responses from Meta Graph API.
6. Network timeout / connection error resilience.
7. Async context manager lifecycle.
"""

import json

import httpx
import pytest

from app.infrastructure.whatsapp import WhatsAppAPIError, WhatsAppClient
from app.modules.messaging.schemas import OutboundButton


def test_normalize_phone_number() -> None:
    """Verify phone numbers are stripped to digits only."""
    assert WhatsAppClient.normalize_phone_number("+1 (555) 123-4567") == "15551234567"
    assert WhatsAppClient.normalize_phone_number("+92-300-1234567") == "923001234567"
    assert WhatsAppClient.normalize_phone_number("15551234567") == "15551234567"


@pytest.mark.asyncio
async def test_send_text_message_success() -> None:
    """Verify outbound text message sends correct payload and auth headers."""
    captured_requests: list[httpx.Request] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            status_code=200,
            json={
                "messaging_product": "whatsapp",
                "contacts": [{"input": "15551234567", "wa_id": "15551234567"}],
                "messages": [{"id": "wamid.OUTBOUND_TEXT_001"}],
            },
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    whatsapp_client = WhatsAppClient(
        access_token="test-token-xyz",
        phone_number_id="987654321",
        api_version="v21.0",
        http_client=mock_client,
    )

    result = await whatsapp_client.send_text_message(
        to="+1 (555) 123-4567",
        text="Hello! How can I help you?",
        preview_url=False,
    )

    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert req.method == "POST"
    assert req.url == "https://graph.facebook.com/v21.0/987654321/messages"
    assert req.headers["Authorization"] == "Bearer test-token-xyz"
    assert req.headers["Content-Type"] == "application/json"

    sent_data = json.loads(req.content.decode("utf-8"))
    assert sent_data["messaging_product"] == "whatsapp"
    assert sent_data["recipient_type"] == "individual"
    assert sent_data["to"] == "15551234567"
    assert sent_data["type"] == "text"
    assert sent_data["text"]["body"] == "Hello! How can I help you?"
    assert sent_data["text"]["preview_url"] is False

    assert result.messaging_product == "whatsapp"
    assert result.messages[0]["id"] == "wamid.OUTBOUND_TEXT_001"


@pytest.mark.asyncio
async def test_send_interactive_buttons_success() -> None:
    """Verify outbound interactive buttons sends correct button structures."""
    captured_requests: list[httpx.Request] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            status_code=200,
            json={
                "messaging_product": "whatsapp",
                "contacts": [{"input": "15559876543", "wa_id": "15559876543"}],
                "messages": [{"id": "wamid.OUTBOUND_BTN_002"}],
            },
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    whatsapp_client = WhatsAppClient(
        access_token="test-token-xyz",
        phone_number_id="987654321",
        api_version="v21.0",
        http_client=mock_client,
    )

    buttons = [
        OutboundButton(id="btn_confirm", title="Confirm"),
        OutboundButton(id="btn_cancel", title="Cancel"),
    ]

    result = await whatsapp_client.send_interactive_buttons(
        to="+1-555-987-6543",
        body_text="Would you like to confirm your order?",
        buttons=buttons,
        header_text="Order #1042",
        footer_text="Reply by tapping a button",
    )

    assert len(captured_requests) == 1
    req = captured_requests[0]
    sent_data = json.loads(req.content.decode("utf-8"))

    assert sent_data["to"] == "15559876543"
    assert sent_data["type"] == "interactive"
    interactive = sent_data["interactive"]
    assert interactive["type"] == "button"
    assert interactive["header"]["text"] == "Order #1042"
    assert interactive["footer"]["text"] == "Reply by tapping a button"
    assert interactive["body"]["text"] == "Would you like to confirm your order?"

    sent_buttons = interactive["action"]["buttons"]
    assert len(sent_buttons) == 2
    assert sent_buttons[0]["reply"]["id"] == "btn_confirm"
    assert sent_buttons[0]["reply"]["title"] == "Confirm"
    assert sent_buttons[1]["reply"]["id"] == "btn_cancel"
    assert sent_buttons[1]["reply"]["title"] == "Cancel"

    assert result.messages[0]["id"] == "wamid.OUTBOUND_BTN_002"


@pytest.mark.asyncio
async def test_send_interactive_buttons_invalid_count() -> None:
    """Verify that fewer than 1 or more than 3 buttons raises WhatsAppAPIError."""
    whatsapp_client = WhatsAppClient()

    # Zero buttons
    with pytest.raises(WhatsAppAPIError) as exc_info_zero:
        await whatsapp_client.send_interactive_buttons(
            to="15551234567",
            body_text="Choose an option:",
            buttons=[],
        )
    assert exc_info_zero.value.code == "INVALID_BUTTON_COUNT"

    # Four buttons (exceeds Meta maximum of 3)
    four_buttons = [OutboundButton(id=f"btn_{i}", title=f"Option {i}") for i in range(4)]
    with pytest.raises(WhatsAppAPIError) as exc_info_four:
        await whatsapp_client.send_interactive_buttons(
            to="15551234567",
            body_text="Choose an option:",
            buttons=four_buttons,
        )
    assert exc_info_four.value.code == "INVALID_BUTTON_COUNT"


@pytest.mark.asyncio
async def test_api_error_response() -> None:
    """Verify that HTTP 4xx errors from Meta raise WhatsAppAPIError with details."""

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=400,
            json={
                "error": {
                    "message": "(#100) Param text[body] must be a string",
                    "type": "OAuthException",
                    "code": 100,
                    "fbtrace_id": "ABC123XYZ",
                }
            },
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    whatsapp_client = WhatsAppClient(http_client=mock_client)

    with pytest.raises(WhatsAppAPIError) as exc_info:
        await whatsapp_client.send_text_message(to="15551234567", text="test")

    assert exc_info.value.status_code == 400
    assert "Param text[body] must be a string" in exc_info.value.message
    assert exc_info.value.details.get("code") == 100


@pytest.mark.asyncio
async def test_network_timeout_error() -> None:
    """Verify that connection failures or timeouts raise WhatsAppAPIError with 504."""

    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("Connection timed out to Meta servers")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    whatsapp_client = WhatsAppClient(http_client=mock_client)

    with pytest.raises(WhatsAppAPIError) as exc_info:
        await whatsapp_client.send_text_message(to="15551234567", text="test")

    assert exc_info.value.status_code == 504
    assert exc_info.value.code == "WHATSAPP_NETWORK_ERROR"


@pytest.mark.asyncio
async def test_async_context_manager() -> None:
    """Verify async context manager enters and exits gracefully."""
    async with WhatsAppClient() as client:
        assert client is not None
        assert client.api_version is not None
