"""
Unit tests for Customer and Conversation Pydantic Schemas.

Validates:
1. Phone normalization to E.164 standard.
2. Rejection of invalid phone numbers and emails.
3. Customer creation, update, and read models.
4. Conversation takeover toggles and status schemas.
5. Message creation constraints, defaults, and list responses.
"""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.modules.conversations.models import (
    MessageContentType,
    MessageDirection,
    MessageSenderType,
    MessageStatus,
)
from app.modules.conversations.schemas import (
    ConversationTakeoverUpdate,
    MessageCreate,
    MessageRead,
)
from app.modules.customers.schemas import (
    CustomerCreate,
    CustomerRead,
    normalize_e164_phone,
)


def test_normalize_e164_phone_valid() -> None:
    """Verify various valid phone formats normalize to standard E.164."""
    # US format with formatting
    assert normalize_e164_phone("+1 (415) 555-2671") == "+14155552671"
    # International without leading plus
    assert normalize_e164_phone("442079460958") == "+442079460958"
    # Dashes and periods
    assert normalize_e164_phone("+92-300-1234567") == "+923001234567"
    # Leading/trailing whitespace
    assert normalize_e164_phone("  +14155552671  ") == "+14155552671"


def test_normalize_e164_phone_invalid() -> None:
    """Verify malformed or invalid phone numbers raise ValidationError / ValueError."""
    # Letters
    with pytest.raises(ValueError, match="Invalid phone number format"):
        normalize_e164_phone("not-a-phone")

    # Starts with 0 (E.164 country codes cannot start with 0)
    with pytest.raises(ValueError, match="Invalid phone number format"):
        normalize_e164_phone("+0123456789")

    # Empty string
    with pytest.raises(ValueError):
        normalize_e164_phone("")


def test_customer_create_and_read_schema() -> None:
    """Verify CustomerCreate schema normalizes phone and validates email."""
    payload = {
        "phone_number": "+1 (555) 987-6543",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "metadata": {"vip": True, "source": "whatsapp"},
    }
    customer_in = CustomerCreate(**payload)
    assert customer_in.phone_number == "+15559876543"
    assert customer_in.name == "Jane Doe"
    assert customer_in.is_blocked is False

    # Invalid email fails
    with pytest.raises(ValidationError):
        CustomerCreate(phone_number="+15559876543", email="invalid-email-address")

    # CustomerRead parsing
    now = datetime.now(UTC)
    read_data = {
        "id": uuid.uuid4(),
        "organization_id": uuid.uuid4(),
        "phone_number": "+15559876543",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "metadata_": {"vip": True},
        "is_blocked": False,
        "created_at": now,
        "updated_at": now,
    }
    customer_out = CustomerRead.model_validate(read_data)
    assert customer_out.phone_number == "+15559876543"
    assert customer_out.metadata == {"vip": True}


def test_conversation_takeover_schema() -> None:
    """Verify human takeover toggle and agent assignment schema."""
    agent_id = uuid.uuid4()
    takeover_payload = {
        "is_ai_active": False,
        "assigned_agent_id": agent_id,
    }
    takeover_req = ConversationTakeoverUpdate(**takeover_payload)
    assert takeover_req.is_ai_active is False
    assert takeover_req.assigned_agent_id == agent_id

    # Resume AI
    resume_req = ConversationTakeoverUpdate(is_ai_active=True)
    assert resume_req.is_ai_active is True
    assert resume_req.assigned_agent_id is None


def test_message_create_and_read_schema() -> None:
    """Verify MessageCreate defaults and max bounds."""
    msg = MessageCreate(text_body="Hello world!")
    assert msg.sender_type == MessageSenderType.HUMAN_AGENT
    assert msg.direction == MessageDirection.OUTBOUND
    assert msg.content_type == MessageContentType.TEXT
    assert msg.text_body == "Hello world!"

    # Text body too long (>4096 chars)
    with pytest.raises(ValidationError):
        MessageCreate(text_body="A" * 4097)

    # MessageRead validation
    now = datetime.now(UTC)
    read_data = {
        "id": uuid.uuid4(),
        "organization_id": uuid.uuid4(),
        "conversation_id": uuid.uuid4(),
        "sender_type": MessageSenderType.CUSTOMER,
        "direction": MessageDirection.INBOUND,
        "content_type": MessageContentType.TEXT,
        "text_body": "Looking for jackets",
        "media_url": None,
        "status": MessageStatus.RECEIVED,
        "whatsapp_message_id": "wamid.12345",
        "raw_payload": None,
        "created_at": now,
    }
    msg_out = MessageRead.model_validate(read_data)
    assert msg_out.text_body == "Looking for jackets"
    assert msg_out.status == MessageStatus.RECEIVED
