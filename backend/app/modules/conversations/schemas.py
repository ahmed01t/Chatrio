"""
Pydantic Schemas for Conversation and Message Management.

Defines schemas for:
1. Conversation creation, status updates, and human takeover toggles.
2. Conversation list and detail reads (including nested customer metadata).
3. Message creation, delivery status, and history pagination.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.conversations.models import (
    ConversationChannel,
    ConversationStatus,
    MessageContentType,
    MessageDirection,
    MessageSenderType,
    MessageStatus,
)
from app.modules.customers.schemas import CustomerRead


# ==============================================================================
# 1. Message Schemas
# ==============================================================================
class MessageCreate(BaseModel):
    """Schema for posting a new message into a conversation."""

    sender_type: MessageSenderType = Field(
        default=MessageSenderType.HUMAN_AGENT,
        description="Sender identity (HUMAN_AGENT from dashboard, CUSTOMER, or AI_AGENT)",
    )
    direction: MessageDirection = Field(
        default=MessageDirection.OUTBOUND,
        description="Direction of the message: INBOUND or OUTBOUND",
    )
    content_type: MessageContentType = Field(
        default=MessageContentType.TEXT,
        description="Message format (TEXT, IMAGE, INTERACTIVE, TEMPLATE)",
    )
    text_body: str | None = Field(
        default=None,
        max_length=4096,
        description="Text content of the message",
    )
    media_url: str | None = Field(
        default=None,
        max_length=1024,
        description="Optional attachment URL",
    )
    whatsapp_message_id: str | None = Field(
        default=None,
        max_length=255,
        description="Meta external message ID (wamid) for deduplication",
    )
    raw_payload: dict[str, Any] | None = Field(
        default=None,
        description="Raw webhook or dispatch payload for audit logging",
    )


class MessageRead(BaseModel):
    """Schema returned when reading an individual message."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    conversation_id: uuid.UUID
    sender_type: MessageSenderType
    direction: MessageDirection
    content_type: MessageContentType
    text_body: str | None
    media_url: str | None
    status: MessageStatus
    whatsapp_message_id: str | None
    raw_payload: dict[str, Any] | None
    created_at: datetime


class MessageListResponse(BaseModel):
    """Paginated collection of conversation messages."""

    items: list[MessageRead]
    total: int
    page: int
    page_size: int


# ==============================================================================
# 2. Conversation Schemas
# ==============================================================================
class ConversationCreate(BaseModel):
    """Schema for initiating a new conversation session."""

    customer_id: uuid.UUID = Field(description="Target customer profile ID")
    channel: ConversationChannel = Field(
        default=ConversationChannel.WHATSAPP,
        description="Communication channel",
    )
    assigned_agent_id: uuid.UUID | None = Field(
        default=None,
        description="Optional staff agent assigned to this conversation",
    )


class ConversationTakeoverUpdate(BaseModel):
    """Schema for toggling human takeover on or off."""

    is_ai_active: bool = Field(
        description="Set to False for human staff takeover (pausing AI); True to resume AI"
    )
    assigned_agent_id: uuid.UUID | None = Field(
        default=None,
        description="Optional staff user ID taking ownership of the conversation",
    )


class ConversationStatusUpdate(BaseModel):
    """Schema for changing conversation lifecycle state."""

    status: ConversationStatus = Field(description="Target status (ACTIVE, CLOSED, ARCHIVED)")


class ConversationRead(BaseModel):
    """Detailed conversation session data."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    assigned_agent_id: uuid.UUID | None
    status: ConversationStatus
    channel: ConversationChannel
    is_ai_active: bool
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime
    customer: CustomerRead | None = None


class ConversationListResponse(BaseModel):
    """Paginated list of conversations for the merchant inbox."""

    items: list[ConversationRead]
    total: int
    page: int
    page_size: int
