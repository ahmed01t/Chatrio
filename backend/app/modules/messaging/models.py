"""
Transactional Outbox Data Models.

Defines:
1. `OutboxStatus`: Processing lifecycle of an outbox message (PENDING, SENDING, SENT, FAILED).
2. `OutboxMessageType`: Format of the outbound message (TEXT, INTERACTIVE, TEMPLATE).
3. `OutboxMessage`: Transactionally staged outbound messages bound to WhatsApp delivery.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.conversations.models import Conversation
    from app.modules.organizations.models import Organization

# SQLite compatibility fallback for JSONB
JSONType = JSONB().with_variant(JSON(), "sqlite")


class OutboxStatus(StrEnum):
    """Lifecycle state of an outbox message."""

    PENDING = "PENDING"
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class OutboxMessageType(StrEnum):
    """Message payload format destined for WhatsApp."""

    TEXT = "TEXT"
    INTERACTIVE = "INTERACTIVE"
    TEMPLATE = "TEMPLATE"


class OutboxMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Transactional Outbox record guaranteeing at-least-once outbound message delivery.

    Enables atomic operations where business state changes (e.g. Order created,
    customer message appended) and outbound notifications commit in the same ACID
    transaction.
    """

    __tablename__ = "outbox_messages"

    # Multi-tenancy foreign key
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant organization that owns this outbox message",
    )

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Associated conversation thread if applicable",
    )

    recipient_phone: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        doc="Destination WhatsApp phone number in E.164 format",
    )

    message_type: Mapped[OutboxMessageType] = mapped_column(
        SQLEnum(OutboxMessageType, native_enum=False, length=20),
        default=OutboxMessageType.TEXT,
        nullable=False,
        doc="Format of message payload (TEXT, INTERACTIVE, TEMPLATE)",
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONType,
        nullable=False,
        doc="Exact payload dictionary containing message body, buttons, or template data",
    )

    status: Mapped[OutboxStatus] = mapped_column(
        SQLEnum(OutboxStatus, native_enum=False, length=20),
        default=OutboxStatus.PENDING,
        nullable=False,
        index=True,
        doc="Current delivery lifecycle status",
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of failed delivery attempts so far",
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
        doc="Maximum retry attempts before marking message as permanently FAILED",
    )

    next_retry_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Next UTC timestamp when this message is eligible for worker processing",
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the message was successfully dispatched to Meta",
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Diagnostic reason or HTTP error from last failed delivery attempt",
    )

    # Composite indexes for high-throughput batch worker polling
    __table_args__ = (
        Index("ix_outbox_status_next_retry", "status", "next_retry_at"),
        Index("ix_outbox_org_status", "organization_id", "status"),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship()
    conversation: Mapped["Conversation | None"] = relationship()

