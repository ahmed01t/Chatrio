"""
Unit tests for MessagingService.

Validates:
1. Parsing and ingesting standard text messages.
2. Parsing and ingesting interactive button clicks.
3. Deduplication of messages with identical WhatsApp message IDs (idempotency).
4. Status-only payloads without messages are handled smoothly.
5. Tenant resolution fallback to primary organization.
6. Unsupported/media content type fallback parsing.
"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.conversations.models import (
    Conversation,
    Message,
    MessageContentType,
    MessageDirection,
    MessageSenderType,
)
from app.modules.customers.models import Customer
from app.modules.messaging.schemas import WhatsAppIncomingMessage
from app.modules.messaging.service import MessagingService
from app.modules.organizations.models import Organization


@pytest.fixture
async def test_org(async_db_engine) -> Organization:
    """Creates a sample organization for service tests."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        org = Organization(
            id=uuid.uuid4(),
            name="Messaging Test Org",
            slug=f"msg-org-{uuid.uuid4().hex[:8]}",
        )
        session.add(org)
        await session.commit()
        return org


def build_meta_payload(
    messages: list[dict] | None = None,
    statuses: list[dict] | None = None,
    contact_name: str = "Alice Smith",
    wa_id: str = "15551234567",
    phone_number_id: str = "10987654321",
) -> dict:
    """Helper to build realistic Meta webhook payloads."""
    contacts = []
    if messages:
        contacts.append(
            {
                "profile": {"name": contact_name},
                "wa_id": wa_id,
            }
        )

    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550009999",
                                "phone_number_id": phone_number_id,
                            },
                            "contacts": contacts,
                            "messages": messages or [],
                            "statuses": statuses or [],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_process_incoming_text_message(
    async_db_engine,
    test_org: Organization,
) -> None:
    """Verify parsing and persistence of an inbound WhatsApp text message."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    payload_data = build_meta_payload(
        messages=[
            {
                "from": "15551234567",
                "id": "wamid.HBgLMTIzNDU2Nw==",
                "timestamp": "1710000000",
                "type": "text",
                "text": {"body": "Hello, I want to place an order."},
            }
        ],
        contact_name="Alice Smith",
        wa_id="15551234567",
    )

    async with session_factory() as session:
        saved_messages = await MessagingService.process_incoming_payload(
            session=session,
            organization_id=test_org.id,
            payload=payload_data,
        )
        await session.commit()

        assert len(saved_messages) == 1
        msg = saved_messages[0]
        assert msg.text_body == "Hello, I want to place an order."
        assert msg.content_type == MessageContentType.TEXT
        assert msg.sender_type == MessageSenderType.CUSTOMER
        assert msg.direction == MessageDirection.INBOUND
        assert msg.whatsapp_message_id == "wamid.HBgLMTIzNDU2Nw=="

        # Verify customer was created
        cust_query = select(Customer).where(
            Customer.organization_id == test_org.id,
            Customer.phone_number == "+15551234567",
        )
        customer = (await session.execute(cust_query)).scalar_one_or_none()
        assert customer is not None
        assert customer.name == "Alice Smith"

        # Verify active conversation was created
        conv_query = select(Conversation).where(
            Conversation.organization_id == test_org.id,
            Conversation.customer_id == customer.id,
        )
        conversation = (await session.execute(conv_query)).scalar_one_or_none()
        assert conversation is not None
        assert msg.conversation_id == conversation.id


@pytest.mark.asyncio
async def test_process_incoming_interactive_button_reply(
    async_db_engine,
    test_org: Organization,
) -> None:
    """Verify parsing and persistence of an interactive quick-reply button message."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    payload_data = build_meta_payload(
        messages=[
            {
                "from": "15551234567",
                "id": "wamid.BUTTON_REPLY_123",
                "timestamp": "1710000100",
                "type": "interactive",
                "interactive": {
                    "type": "button_reply",
                    "button_reply": {
                        "id": "btn_confirm_order",
                        "title": "Confirm Order",
                    },
                },
            }
        ]
    )

    async with session_factory() as session:
        saved_messages = await MessagingService.process_incoming_payload(
            session=session,
            organization_id=test_org.id,
            payload=payload_data,
        )
        await session.commit()

        assert len(saved_messages) == 1
        msg = saved_messages[0]
        assert msg.text_body == "Confirm Order"
        assert msg.content_type == MessageContentType.INTERACTIVE
        assert msg.sender_type == MessageSenderType.CUSTOMER
        assert msg.direction == MessageDirection.INBOUND
        assert msg.whatsapp_message_id == "wamid.BUTTON_REPLY_123"


@pytest.mark.asyncio
async def test_process_incoming_message_deduplication(
    async_db_engine,
    test_org: Organization,
) -> None:
    """Verify idempotency: re-sending the same WhatsApp message ID does not create duplicates."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    payload_data = build_meta_payload(
        messages=[
            {
                "from": "15551234567",
                "id": "wamid.DUPLICATE_TEST_ID",
                "timestamp": "1710000200",
                "type": "text",
                "text": {"body": "Idempotent message"},
            }
        ]
    )

    async with session_factory() as session:
        # First delivery
        first_res = await MessagingService.process_incoming_payload(
            session=session,
            organization_id=test_org.id,
            payload=payload_data,
        )
        await session.commit()
        assert len(first_res) == 1

        # Second delivery (duplicate retry from Meta)
        second_res = await MessagingService.process_incoming_payload(
            session=session,
            organization_id=test_org.id,
            payload=payload_data,
        )
        await session.commit()
        assert len(second_res) == 1
        assert second_res[0].id == first_res[0].id

        # Total messages in DB should remain exactly 1
        all_msgs = (
            (
                await session.execute(
                    select(Message).where(Message.whatsapp_message_id == "wamid.DUPLICATE_TEST_ID")
                )
            )
            .scalars()
            .all()
        )
        assert len(all_msgs) == 1


@pytest.mark.asyncio
async def test_process_status_payload_no_messages(
    async_db_engine,
    test_org: Organization,
) -> None:
    """Verify status delivery receipts (sent, delivered, read) do not crash or create messages."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    status_payload = build_meta_payload(
        messages=[],
        statuses=[
            {
                "id": "wamid.OUTBOUND_MSG_123",
                "status": "delivered",
                "timestamp": "1710000300",
                "recipient_id": "15551234567",
            }
        ],
    )

    async with session_factory() as session:
        saved_messages = await MessagingService.process_incoming_payload(
            session=session,
            organization_id=test_org.id,
            payload=status_payload,
        )
        await session.commit()

        assert saved_messages == []


@pytest.mark.asyncio
async def test_resolve_organization_by_phone_id(
    async_db_engine,
    test_org: Organization,
) -> None:
    """Verify organization resolution returns the default active merchant organization."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        resolved_id = await MessagingService.resolve_organization_by_phone_id(
            session=session,
            phone_number_id="10987654321",
        )
        assert resolved_id == test_org.id


def test_extract_text_content_fallback() -> None:
    """Verify unsupported media or image messages fallback to label placeholder."""
    msg = WhatsAppIncomingMessage(
        **{
            "from": "15551234567",
            "id": "wamid.IMAGE_123",
            "timestamp": "1710000400",
            "type": "image",
        }
    )
    text, content_type = MessagingService.extract_text_content(msg)
    assert text == "[IMAGE]"
    assert content_type == MessageContentType.TEXT
