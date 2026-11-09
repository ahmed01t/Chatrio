"""
Pydantic Schemas for Transactional Outbox Engine & Meta Policy Validation.
"""

import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.messaging.models import OutboxMessageType, OutboxStatus

E164_PHONE_REGEX = re.compile(r"^\+?[1-9]\d{6,14}$")


class TextPayload(BaseModel):
    """Payload for standard text messages."""

    model_config = ConfigDict(extra="forbid")

    body: str = Field(..., min_length=1, max_length=4096, description="Text message content")


class InteractiveButton(BaseModel):
    """WhatsApp interactive reply button descriptor."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, max_length=256, description="Button unique ID")
    title: str = Field(..., min_length=1, max_length=20, description="Button label text")


class InteractivePayload(BaseModel):
    """Payload for WhatsApp interactive quick-reply buttons."""

    model_config = ConfigDict(extra="forbid")

    body: str = Field(..., min_length=1, max_length=1024, description="Prompt text")
    buttons: list[InteractiveButton] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="1 to 3 interactive reply buttons",
    )


class TemplateComponent(BaseModel):
    """WhatsApp HSM template component parameters."""

    type: str = Field(..., description="Component type e.g. 'body', 'header', 'button'")
    parameters: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Dynamic template parameter values",
    )


class TemplatePayload(BaseModel):
    """Payload for pre-approved WhatsApp message templates (outside 24h window)."""

    model_config = ConfigDict(extra="forbid")

    template_name: str = Field(..., min_length=1, max_length=512, description="Meta template name")
    language: str = Field(default="en_US", description="Template language code")
    components: list[TemplateComponent] = Field(
        default_factory=list,
        description="Dynamic components and parameters",
    )


class OutboxEnqueueRequest(BaseModel):
    """Request model for atomically enqueuing an outbound message."""

    organization_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    recipient_phone: str = Field(..., description="Destination phone number in E.164 format")
    message_type: OutboxMessageType = Field(default=OutboxMessageType.TEXT)
    payload: dict[str, Any] = Field(..., description="Raw dictionary or validated payload")
    max_retries: int = Field(default=5, ge=1, le=10)

    @field_validator("recipient_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        clean = v.strip()
        if not E164_PHONE_REGEX.match(clean):
            raise ValueError(
                f"Phone number '{v}' is invalid. Must be in E.164 format (e.g. +14155552671)."
            )
        return clean


class OutboxMessageResponse(BaseModel):
    """Response representation of an outbox record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    conversation_id: uuid.UUID | None
    recipient_phone: str
    message_type: OutboxMessageType
    payload: dict[str, Any]
    status: OutboxStatus
    retry_count: int
    max_retries: int
    next_retry_at: datetime
    sent_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class PolicyCheckResult(BaseModel):
    """Result of Meta 24-hour customer care policy window evaluation."""

    is_permitted: bool
    violation_reason: str | None = None
    is_within_24h_window: bool
    seconds_since_last_customer_message: float | None = None

