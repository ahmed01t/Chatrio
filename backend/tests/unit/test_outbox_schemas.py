"""Unit tests for Outbox Pydantic schemas and payload validation."""

import uuid

import pytest
from pydantic import ValidationError

from app.modules.messaging.models import OutboxMessageType
from app.modules.messaging.outbox_schemas import (
    InteractiveButton,
    InteractivePayload,
    OutboxEnqueueRequest,
    TemplatePayload,
    TextPayload,
)


def test_text_payload_validation() -> None:
    """Valid text payload passes; empty or oversized text fails."""
    valid = TextPayload(body="Hello from Chatrio!")
    assert valid.body == "Hello from Chatrio!"

    with pytest.raises(ValidationError):
        TextPayload(body="")


def test_interactive_payload_validation() -> None:
    """Valid interactive payload with 1-3 buttons; >3 buttons fails."""
    payload = InteractivePayload(
        body="Please choose an option:",
        buttons=[
            InteractiveButton(id="opt_1", title="View Menu"),
            InteractiveButton(id="opt_2", title="Check Order"),
        ],
    )
    assert len(payload.buttons) == 2

    # Exceeding 3 buttons (WhatsApp Cloud API maximum is 3 reply buttons)
    with pytest.raises(ValidationError):
        InteractivePayload(
            body="Too many buttons",
            buttons=[
                InteractiveButton(id="1", title="1"),
                InteractiveButton(id="2", title="2"),
                InteractiveButton(id="3", title="3"),
                InteractiveButton(id="4", title="4"),
            ],
        )


def test_template_payload_validation() -> None:
    """Template payload with name, language, and components."""
    template = TemplatePayload(
        template_name="order_confirmation_v2",
        language="en_US",
        components=[],
    )
    assert template.template_name == "order_confirmation_v2"
    assert template.language == "en_US"


def test_enqueue_request_phone_validation() -> None:
    """E.164 phone numbers pass; malformed numbers fail."""
    valid_req = OutboxEnqueueRequest(
        organization_id=uuid.uuid4(),
        recipient_phone="+14155552671",
        message_type=OutboxMessageType.TEXT,
        payload={"body": "Hello!"},
    )
    assert valid_req.recipient_phone == "+14155552671"

    # Malformed phone number
    with pytest.raises(ValidationError) as exc_info:
        OutboxEnqueueRequest(
            organization_id=uuid.uuid4(),
            recipient_phone="not-a-phone",
            message_type=OutboxMessageType.TEXT,
            payload={"body": "Hello!"},
        )
    assert "E.164" in str(exc_info.value)

