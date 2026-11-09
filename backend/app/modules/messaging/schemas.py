"""
Pydantic Schemas for Meta WhatsApp Cloud API Webhooks.

Defines models for:
1. Inbound webhook payloads (contacts, incoming text/interactive messages, delivery statuses).
2. Webhook verification handshake parameters (`hub.mode`, `hub.verify_token`, `hub.challenge`).
3. Outbound messaging payloads (text, interactive quick-reply buttons).
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# 1. Inbound Webhook Payload Structures
# ==============================================================================
class WhatsAppProfile(BaseModel):
    """User profile information sent by Meta."""

    name: str | None = None


class WhatsAppContact(BaseModel):
    """Contact metadata for the customer initiating a message."""

    profile: WhatsAppProfile | None = None
    wa_id: str = Field(description="Customer WhatsApp phone number ID (E.164 without '+')")


class WhatsAppTextMessage(BaseModel):
    """Text body payload."""

    body: str


class WhatsAppButtonReply(BaseModel):
    """Button selection payload from an interactive message."""

    id: str = Field(description="Unique ID of the button pressed by the customer")
    title: str = Field(description="Title text of the selected button")


class WhatsAppInteractive(BaseModel):
    """Interactive response wrapper (buttons, lists)."""

    type: str
    button_reply: WhatsAppButtonReply | None = None


class WhatsAppIncomingMessage(BaseModel):
    """A single incoming message from a customer."""

    model_config = ConfigDict(populate_by_name=True)

    from_: str = Field(alias="from", description="Customer phone number (without '+')")
    id: str = Field(description="Meta unique message ID (wamid)")
    timestamp: str = Field(description="Unix timestamp string")
    type: str = Field(description="Message type: text, interactive, image, etc.")
    text: WhatsAppTextMessage | None = None
    interactive: WhatsAppInteractive | None = None


class WhatsAppStatus(BaseModel):
    """Message delivery receipts (sent, delivered, read, failed)."""

    id: str = Field(description="Meta message ID (wamid)")
    status: str = Field(description="sent, delivered, read, or failed")
    timestamp: str
    recipient_id: str


class WhatsAppMetadata(BaseModel):
    """Business recipient phone metadata."""

    display_phone_number: str | None = None
    phone_number_id: str = Field(description="Meta WhatsApp Business Phone Number ID")


class WhatsAppValue(BaseModel):
    """Value object within a webhook change entry."""

    messaging_product: str = "whatsapp"
    metadata: WhatsAppMetadata | None = None
    contacts: list[WhatsAppContact] = Field(default_factory=list)
    messages: list[WhatsAppIncomingMessage] = Field(default_factory=list)
    statuses: list[WhatsAppStatus] = Field(default_factory=list)


class WhatsAppChange(BaseModel):
    """Change item inside a webhook entry."""

    value: WhatsAppValue
    field: str = "messages"


class WhatsAppEntry(BaseModel):
    """Top-level entry element in Meta webhook."""

    id: str
    changes: list[WhatsAppChange] = Field(default_factory=list)


class WhatsAppWebhookPayload(BaseModel):
    """Complete root payload delivered to POST /api/v1/webhooks/whatsapp."""

    object: str = "whatsapp_business_account"
    entry: list[WhatsAppEntry] = Field(default_factory=list)


# ==============================================================================
# 2. Outbound Message Schemas
# ==============================================================================
class OutboundTextRequest(BaseModel):
    """Request DTO to dispatch a text message via Meta Graph API."""

    to: str = Field(description="Recipient E.164 phone number")
    text: str = Field(description="Message body text")


class OutboundButton(BaseModel):
    """Individual quick-reply button."""

    id: str = Field(max_length=256, description="Developer button ID")
    title: str = Field(max_length=20, description="Button label shown on WhatsApp")


class OutboundInteractiveButtonsRequest(BaseModel):
    """Request DTO to dispatch interactive quick-reply buttons."""

    to: str = Field(description="Recipient E.164 phone number")
    body_text: str = Field(description="Main body text accompanying the buttons")
    buttons: list[OutboundButton] = Field(
        min_length=1,
        max_length=3,
        description="List of 1 to 3 quick-reply buttons",
    )
    header_text: str | None = Field(default=None, description="Optional header text")
    footer_text: str | None = Field(default=None, description="Optional footer text")


class OutboundMessageResponse(BaseModel):
    """Response returned by Meta upon successful message dispatch."""

    messaging_product: str = "whatsapp"
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    messages: list[dict[str, str]] = Field(default_factory=list)

