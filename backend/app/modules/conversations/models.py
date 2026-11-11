"""
Conversation and Message Data Models.

Defines:
1. `ConversationStatus`: Lifecycle states of a conversation (ACTIVE, CLOSED, ARCHIVED).
2. `ConversationChannel`: Communication channels (WHATSAPP, WEB, API).
3. `MessageSenderType`: Entity sending the message (CUSTOMER, AI_AGENT, HUMAN_AGENT, SYSTEM).
4. `MessageDirection`: INBOUND (from customer) or OUTBOUND (to customer).
5. `MessageContentType`: TEXT, IMAGE, DOCUMENT, LOCATION, INTERACTIVE, TEMPLATE.
6. `MessageStatus`: Lifecycle states of a message (RECEIVED, PROCESSING, SENT, DELIVERED,
   READ, FAILED).
7. `Conversation`: Live chat session between customer and store, with human takeover toggle.
8. `Message`: Individual immutable message records linked to a conversation.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    true,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.auth.models import User
    from app.modules.customers.models import Customer
    from app.modules.organizations.models import Organization

# SQLite compatibility fallback for JSONB
JSONType = JSONB().with_variant(JSON(), "sqlite")


# ==============================================================================
# Enums
# ==============================================================================
class ConversationStatus(StrEnum):
    """Lifecycle state of a conversation."""

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class ConversationChannel(StrEnum):
    """Inbound/outbound channel for the conversation."""

    WHATSAPP = "WHATSAPP"
    INSTAGRAM = "INSTAGRAM"
    WEB = "WEB"
    API = "API"


class MessageSenderType(StrEnum):
    """Entity generating the message."""

    CUSTOMER = "CUSTOMER"
    AI_AGENT = "AI_AGENT"
    HUMAN_AGENT = "HUMAN_AGENT"
    SYSTEM = "SYSTEM"


class MessageDirection(StrEnum):
    """Message direction relative to the platform."""

    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class MessageContentType(StrEnum):
    """Format and type of the message content."""

    TEXT = "TEXT"
    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    LOCATION = "LOCATION"
    INTERACTIVE = "INTERACTIVE"
    TEMPLATE = "TEMPLATE"


class MessageStatus(StrEnum):
    """Delivery and processing status of a message."""

    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"


# ==============================================================================
# Models
# ==============================================================================
class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents an ongoing or archived chat session between a customer and store.

    Key Features:
    - `is_ai_active`: When True, the LangGraph AI responds to incoming messages.
      When False, a human agent has intervened (human takeover), pausing AI generation.
    - `last_message_at`: Allows sorting active conversations in the dashboard inbox.
    """

    __tablename__ = "conversations"

    # Multi-tenancy foreign key
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant organization that owns this conversation",
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Customer participating in this conversation",
    )

    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Optional staff user assigned to handle this conversation",
    )

    status: Mapped[ConversationStatus] = mapped_column(
        SQLEnum(ConversationStatus, native_enum=False, length=20),
        default=ConversationStatus.ACTIVE,
        nullable=False,
        doc="Lifecycle state of the conversation (ACTIVE, CLOSED, ARCHIVED)",
    )

    channel: Mapped[ConversationChannel] = mapped_column(
        SQLEnum(ConversationChannel, native_enum=False, length=20),
        default=ConversationChannel.WHATSAPP,
        nullable=False,
        doc="Channel through which communication occurs",
    )

    is_ai_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
        doc="True if the AI handles incoming messages; False if a human agent took over",
    )

    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of the most recent message in this conversation",
    )

    # Constraints and Indexes
    __table_args__ = (
        Index("ix_conversations_org_status", "organization_id", "status"),
        Index("ix_conversations_org_last_message", "organization_id", "last_message_at"),
        Index("ix_conversations_org_customer", "organization_id", "customer_id"),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship()
    customer: Mapped["Customer"] = relationship(back_populates="conversations")
    assigned_agent: Mapped["User | None"] = relationship()
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at.asc()",
    )


class Message(Base, UUIDPrimaryKeyMixin):
    """
    Represents an immutable message exchanged within a conversation.

    Stores text content, media URLs, external WhatsApp message IDs (for deduplication),
    and raw JSON payloads for complete auditability.
    """

    __tablename__ = "messages"

    # Multi-tenancy foreign key
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant organization that owns this message",
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Conversation session to which this message belongs",
    )

    sender_type: Mapped[MessageSenderType] = mapped_column(
        SQLEnum(MessageSenderType, native_enum=False, length=20),
        nullable=False,
        doc="Sender role (CUSTOMER, AI_AGENT, HUMAN_AGENT, SYSTEM)",
    )

    direction: Mapped[MessageDirection] = mapped_column(
        SQLEnum(MessageDirection, native_enum=False, length=10),
        nullable=False,
        doc="Direction of message: INBOUND (from user) or OUTBOUND (to user)",
    )

    content_type: Mapped[MessageContentType] = mapped_column(
        SQLEnum(MessageContentType, native_enum=False, length=20),
        default=MessageContentType.TEXT,
        nullable=False,
        doc="Format of message content (TEXT, IMAGE, INTERACTIVE, TEMPLATE)",
    )

    text_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Body text of the message",
    )

    media_url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        doc="URL to media attachment if content_type is an image or document",
    )

    status: Mapped[MessageStatus] = mapped_column(
        SQLEnum(MessageStatus, native_enum=False, length=20),
        default=MessageStatus.RECEIVED,
        nullable=False,
        doc="Processing and delivery state of the message",
    )

    whatsapp_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="External Meta message ID (wamid) used for deduplication and receipt updates",
    )

    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONType,
        nullable=True,
        doc="Raw webhook or dispatch payload for audit logging",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when the message was recorded",
    )

    # Constraints and Indexes
    __table_args__ = (
        Index("ix_messages_org_created_at", "organization_id", "created_at"),
        Index("ix_messages_conv_created_at", "conversation_id", "created_at"),
        Index("ix_messages_org_wam_id", "organization_id", "whatsapp_message_id"),
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
