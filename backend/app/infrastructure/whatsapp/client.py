"""
WhatsApp Cloud API Outbound Client.

Provides an asynchronous HTTP client to dispatch messages via Meta Graph API:
1. `send_text_message`: Delivers outbound conversational text replies.
2. `send_interactive_buttons`: Delivers interactive quick-reply button sets.
3. Phone number normalization to E.164 digits format required by Meta.
4. Robust error handling, timeouts, and sanitized logging.
"""

import re
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.modules.messaging.schemas import (
    OutboundButton,
    OutboundMessageResponse,
)


class WhatsAppAPIError(AppException):
    """Raised when the Meta WhatsApp Graph API returns an error or fails."""

    def __init__(
        self,
        message: str,
        code: str = "WHATSAPP_API_ERROR",
        status_code: int = 502,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, code=code, message=message, details=details)


class WhatsAppClient:
    """
    Asynchronous client for sending messages via Meta WhatsApp Cloud API.
    """

    def __init__(
        self,
        access_token: str | None = None,
        phone_number_id: str | None = None,
        api_version: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 10.0,
    ) -> None:
        settings = get_settings()
        self.access_token = access_token or settings.META_ACCESS_TOKEN
        self.phone_number_id = phone_number_id or settings.META_PHONE_NUMBER_ID
        self.api_version = api_version or settings.META_API_VERSION
        self.timeout = timeout
        self._http_client = http_client
        self._owns_client = http_client is None

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns the active AsyncClient instance."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
            self._owns_client = True
        return self._http_client

    async def close(self) -> None:
        """Closes the underlying HTTP client session if owned."""
        if self._owns_client and self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> "WhatsAppClient":
        await self._get_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """
        Normalizes a recipient phone number for Meta WhatsApp Cloud API.

        Meta requires plain digits without leading '+' or special characters.
        Example: '+1 (555) 123-4567' -> '15551234567'.
        """
        return re.sub(r"\D", "", phone)

    def _get_endpoint_url(self, phone_number_id: str | None = None) -> str:
        """Constructs the Meta Graph API message endpoint URL."""
        pid = phone_number_id or self.phone_number_id
        return f"https://graph.facebook.com/{self.api_version}/{pid}/messages"

    def _get_headers(self) -> dict[str, str]:
        """Constructs authorization and content-type headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def _send_request(
        self,
        payload: dict[str, Any],
        phone_number_id: str | None = None,
    ) -> OutboundMessageResponse:
        """
        Dispatches an HTTP POST payload to Meta Graph API and processes the response.
        """
        client = await self._get_client()
        url = self._get_endpoint_url(phone_number_id)
        headers = self._get_headers()

        try:
            response = await client.post(url=url, headers=headers, json=payload)
        except (httpx.TimeoutException, httpx.RequestError) as err:
            raise WhatsAppAPIError(
                message=f"WhatsApp Cloud API connection error: {err}",
                code="WHATSAPP_NETWORK_ERROR",
                status_code=504,
            ) from err

        if response.status_code >= 400:
            error_details: dict[str, Any] = {}
            try:
                error_body = response.json()
                error_details = error_body.get("error", {})
            except Exception:
                error_details = {"raw": response.text}

            error_message = error_details.get("message", response.text)
            raise WhatsAppAPIError(
                message=f"WhatsApp Cloud API request failed: {error_message}",
                code="WHATSAPP_API_ERROR",
                status_code=response.status_code,
                details=error_details,
            )

        response_data = response.json()
        return OutboundMessageResponse.model_validate(response_data)

    async def send_text_message(
        self,
        to: str,
        text: str,
        preview_url: bool = False,
        phone_number_id: str | None = None,
    ) -> OutboundMessageResponse:
        """
        Sends a standard text message to a customer.

        Args:
            to: Recipient phone number (E.164 or digits).
            text: Text body to deliver.
            preview_url: Whether to render link previews in WhatsApp.
            phone_number_id: Optional specific business phone number ID override.

        Returns:
            OutboundMessageResponse containing Meta message IDs.
        """
        normalized_to = self.normalize_phone_number(to)
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalized_to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": text,
            },
        }
        return await self._send_request(payload, phone_number_id=phone_number_id)

    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: list[OutboundButton],
        header_text: str | None = None,
        footer_text: str | None = None,
        phone_number_id: str | None = None,
    ) -> OutboundMessageResponse:
        """
        Sends an interactive quick-reply button message (1 to 3 buttons).

        Args:
            to: Recipient phone number.
            body_text: Accompanying message text.
            buttons: List of 1 to 3 OutboundButton items.
            header_text: Optional header line.
            footer_text: Optional footer line.
            phone_number_id: Optional phone number ID override.

        Returns:
            OutboundMessageResponse containing Meta message IDs.
        """
        if not (1 <= len(buttons) <= 3):
            raise WhatsAppAPIError(
                message="WhatsApp interactive buttons must contain between 1 and 3 buttons.",
                code="INVALID_BUTTON_COUNT",
                status_code=400,
            )

        normalized_to = self.normalize_phone_number(to)
        interactive_obj: dict[str, Any] = {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn.id,
                            "title": btn.title,
                        },
                    }
                    for btn in buttons
                ]
            },
        }

        if header_text:
            interactive_obj["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive_obj["footer"] = {"text": footer_text}

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalized_to,
            "type": "interactive",
            "interactive": interactive_obj,
        }
        return await self._send_request(payload, phone_number_id=phone_number_id)
