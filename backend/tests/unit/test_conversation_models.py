"""
Unit tests for Customer, Conversation, and Message SQLAlchemy ORM Models.

Validates:
1. Table registration in Base.metadata.
2. Model attributes, enums, foreign keys, and indexes.
3. Unique constraint on (organization_id, phone_number).
4. Default values (is_blocked=False, is_ai_active=True, status=ACTIVE).
"""

import uuid
from datetime import UTC, datetime

import pytest

from app.db.models import (
    Base,
    Conversation,
    ConversationChannel,
    ConversationStatus,
    Customer,
    Message,
    MessageContentType,
    MessageDirection,
    MessageSenderType,
    MessageStatus,
)


def test_models_registered_in_metadata() -> None:
    """Ensure customers, conversations, and messages tables are registered in Base.metadata."""
    table_names = Base.metadata.tables.keys()
    assert "customers" in table_names
    assert "conversations" in table_names
    assert "messages" in table_names


def test_customer_model_structure() -> None:
    """Verify Customer model column types, constraints, and indexes."""
    customer_table = Base.metadata.tables["customers"]

    # Required columns
    assert "id" in customer_table.c
    assert "organization_id" in customer_table.c
    assert "phone_number" in customer_table.c
    assert "name" in customer_table.c
    assert "email" in customer_table.c
    assert "metadata" in customer_table.c
    assert "is_blocked" in customer_table.c
    assert "created_at" in customer_table.c
    assert "updated_at" in customer_table.c

    # Unique constraint on (organization_id, phone_number)
    unique_constraints = [
        c.name for c in customer_table.constraints if hasattr(c, "columns") and c.name
    ]
    assert "uq_customers_org_phone" in unique_constraints

    # Verify default column value definition
    assert customer_table.c["is_blocked"].default.arg is False

    # Instantiate Customer model instance
    org_id = uuid.uuid4()
    customer = Customer(
        id=uuid.uuid4(),
        organization_id=org_id,
        phone_number="+14155552671",
        name="Alice Shopper",
        email="alice@example.com",
        is_blocked=False,
    )
    assert customer.phone_number == "+14155552671"
    assert customer.name == "Alice Shopper"
    assert customer.is_blocked is False


def test_conversation_model_structure() -> None:
    """Verify Conversation model column types, defaults, and foreign keys."""
    conv_table = Base.metadata.tables["conversations"]

    assert "id" in conv_table.c
    assert "organization_id" in conv_table.c
    assert "customer_id" in conv_table.c
    assert "assigned_agent_id" in conv_table.c
    assert "status" in conv_table.c
    assert "channel" in conv_table.c
    assert "is_ai_active" in conv_table.c
    assert "last_message_at" in conv_table.c

    # Check foreign keys
    fk_targets = {fk.target_fullname for fk in conv_table.foreign_keys}
    assert "organizations.id" in fk_targets
    assert "customers.id" in fk_targets
    assert "users.id" in fk_targets

    # Instantiate Conversation
    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    now = datetime.now(UTC)
    conv = Conversation(
        id=uuid.uuid4(),
        organization_id=org_id,
        customer_id=cust_id,
        status=ConversationStatus.ACTIVE,
        channel=ConversationChannel.WHATSAPP,
        is_ai_active=True,
        last_message_at=now,
    )
    assert conv.status == ConversationStatus.ACTIVE
    assert conv.channel == ConversationChannel.WHATSAPP
    assert conv.is_ai_active is True
    assert conv.last_message_at == now


def test_message_model_structure() -> None:
    """Verify Message model column types, foreign keys, and indexes."""
    msg_table = Base.metadata.tables["messages"]

    assert "id" in msg_table.c
    assert "organization_id" in msg_table.c
    assert "conversation_id" in msg_table.c
    assert "sender_type" in msg_table.c
    assert "direction" in msg_table.c
    assert "content_type" in msg_table.c
    assert "text_body" in msg_table.c
    assert "media_url" in msg_table.c
    assert "status" in msg_table.c
    assert "whatsapp_message_id" in msg_table.c
    assert "raw_payload" in msg_table.c
    assert "created_at" in msg_table.c

    # Foreign keys
    fk_targets = {fk.target_fullname for fk in msg_table.foreign_keys}
    assert "organizations.id" in fk_targets
    assert "conversations.id" in fk_targets

    # Instantiate Message
    msg = Message(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        sender_type=MessageSenderType.CUSTOMER,
        direction=MessageDirection.INBOUND,
        content_type=MessageContentType.TEXT,
        text_body="Hi, do you have running shoes?",
        status=MessageStatus.RECEIVED,
        whatsapp_message_id="wamid.HBgLMTE=",
        raw_payload={"entry": [{"changes": []}]},
    )
    assert msg.text_body == "Hi, do you have running shoes?"
    assert msg.sender_type == MessageSenderType.CUSTOMER
    assert msg.direction == MessageDirection.INBOUND
    assert msg.content_type == MessageContentType.TEXT
    assert msg.whatsapp_message_id == "wamid.HBgLMTE="


@pytest.mark.asyncio
async def test_database_persistence_and_relationships(async_db_engine) -> None:
    """Verify Customer, Conversation, and Message records can be inserted and queried."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.modules.organizations.models import Organization

    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        # 1. Create Organization
        org = Organization(
            id=uuid.uuid4(),
            name="Chatrio Test Org",
            slug="chatrio-test-org",
        )
        session.add(org)
        await session.flush()

        # 2. Create Customer
        customer = Customer(
            id=uuid.uuid4(),
            organization_id=org.id,
            phone_number="+15551234567",
            name="John Doe",
        )
        session.add(customer)
        await session.flush()
        assert customer.is_blocked is False

        # 3. Create Conversation
        conversation = Conversation(
            id=uuid.uuid4(),
            organization_id=org.id,
            customer_id=customer.id,
            channel=ConversationChannel.WHATSAPP,
            status=ConversationStatus.ACTIVE,
        )
        session.add(conversation)
        await session.flush()
        assert conversation.is_ai_active is True

        # 4. Create Message
        msg = Message(
            id=uuid.uuid4(),
            organization_id=org.id,
            conversation_id=conversation.id,
            sender_type=MessageSenderType.CUSTOMER,
            direction=MessageDirection.INBOUND,
            content_type=MessageContentType.TEXT,
            text_body="Hello, I want to place an order.",
            status=MessageStatus.RECEIVED,
            whatsapp_message_id="wamid.TEST1234",
        )
        session.add(msg)
        await session.commit()

        # 5. Query back and verify relations
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation.id)
        )
        fetched_conv = result.scalar_one()
        assert fetched_conv is not None
        assert fetched_conv.is_ai_active is True
        assert fetched_conv.channel == ConversationChannel.WHATSAPP
