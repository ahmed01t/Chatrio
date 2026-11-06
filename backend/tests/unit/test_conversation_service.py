"""
Unit tests for Customer, Conversation, and Message Services.

Validates:
1. Customer get-or-create and normalized phone handling.
2. Conflict handling for duplicate customer phones within a tenant.
3. Customer profile updates (name, email, metadata, blocking).
4. Active conversation session retrieval and creation.
5. Human takeover state toggles (is_ai_active).
6. Message appending with WhatsApp message ID deduplication (idempotency).
7. Message delivery receipt status updates.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.exceptions import ConflictException
from app.modules.conversations.models import (
    ConversationChannel,
    ConversationStatus,
    MessageContentType,
    MessageDirection,
    MessageSenderType,
    MessageStatus,
)
from app.modules.conversations.schemas import (
    ConversationTakeoverUpdate,
    MessageCreate,
)
from app.modules.conversations.service import ConversationService, MessageService
from app.modules.customers.schemas import CustomerCreate, CustomerUpdate
from app.modules.customers.service import CustomerService
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
            name="Service Test Org",
            slug=f"service-test-{uuid.uuid4().hex[:8]}",
        )
        session.add(org)
        await session.commit()
        return org


@pytest.mark.asyncio
async def test_customer_get_or_create(async_db_engine, test_org: Organization) -> None:
    """Verify Customer get-or-create logic and phone normalization."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        # First call creates customer
        customer1, created1 = await CustomerService.get_or_create_customer(
            session=session,
            organization_id=test_org.id,
            phone_number="+1 (555) 123-4567",
            name="Alice",
        )
        await session.commit()
        assert created1 is True
        assert customer1.phone_number == "+15551234567"
        assert customer1.name == "Alice"

        # Second call returns existing customer
        customer2, created2 = await CustomerService.get_or_create_customer(
            session=session,
            organization_id=test_org.id,
            phone_number="  +15551234567  ",
        )
        assert created2 is False
        assert customer2.id == customer1.id


@pytest.mark.asyncio
async def test_customer_create_duplicate_conflict(
    async_db_engine,
    test_org: Organization,
) -> None:
    """
    Verify that explicitly creating a customer with an existing phone
    raises ConflictException.
    """
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        req = CustomerCreate(phone_number="+15558889999", name="Bob")
        await CustomerService.create_customer(session, test_org.id, req)
        await session.commit()

        # Duplicate phone inside same tenant
        with pytest.raises(ConflictException) as exc:
            await CustomerService.create_customer(session, test_org.id, req)
        assert exc.value.code == "CUSTOMER_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_customer_update_fields(
    async_db_engine,
    test_org: Organization,
) -> None:
    """Verify updating name, email, metadata, and blocked state."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        customer = await CustomerService.create_customer(
            session,
            test_org.id,
            CustomerCreate(phone_number="+15553334444", name="Charlie"),
        )
        await session.commit()

        update_req = CustomerUpdate(
            name="Charlie Brown",
            email="charlie@example.com",
            metadata={"preferred_language": "en"},
            is_blocked=True,
        )
        updated = await CustomerService.update_customer(
            session, test_org.id, customer.id, update_req
        )
        await session.commit()

        assert updated.name == "Charlie Brown"
        assert updated.email == "charlie@example.com"
        assert updated.metadata_ == {"preferred_language": "en"}
        assert updated.is_blocked is True


@pytest.mark.asyncio
async def test_conversation_get_or_create_active(
    async_db_engine,
    test_org: Organization,
) -> None:
    """Verify active conversation retrieval and creation."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        customer = await CustomerService.create_customer(
            session,
            test_org.id,
            CustomerCreate(phone_number="+15557778888", name="David"),
        )
        await session.commit()

        # First call creates active conversation
        conv1, created1 = await ConversationService.get_or_create_active_conversation(
            session, test_org.id, customer.id, ConversationChannel.WHATSAPP
        )
        await session.commit()
        assert created1 is True
        assert conv1.status == ConversationStatus.ACTIVE
        assert conv1.is_ai_active is True

        # Second call returns existing active conversation
        conv2, created2 = await ConversationService.get_or_create_active_conversation(
            session, test_org.id, customer.id, ConversationChannel.WHATSAPP
        )
        assert created2 is False
        assert conv2.id == conv1.id


@pytest.mark.asyncio
async def test_conversation_human_takeover_toggle(
    async_db_engine,
    test_org: Organization,
) -> None:
    """Verify toggling human takeover pauses AI, and resuming turns AI back on."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        customer = await CustomerService.create_customer(
            session,
            test_org.id,
            CustomerCreate(phone_number="+15556667777", name="Eva"),
        )
        conv, _ = await ConversationService.get_or_create_active_conversation(
            session, test_org.id, customer.id
        )
        await session.commit()
        assert conv.is_ai_active is True

        # 1. Human merchant takes over
        agent_id = uuid.uuid4()
        takeover = await ConversationService.update_takeover(
            session,
            test_org.id,
            conv.id,
            ConversationTakeoverUpdate(is_ai_active=False, assigned_agent_id=agent_id),
        )
        await session.commit()
        assert takeover.is_ai_active is False
        assert takeover.assigned_agent_id == agent_id

        # 2. Release back to AI
        resumed = await ConversationService.update_takeover(
            session,
            test_org.id,
            conv.id,
            ConversationTakeoverUpdate(is_ai_active=True),
        )
        await session.commit()
        assert resumed.is_ai_active is True


@pytest.mark.asyncio
async def test_message_idempotency_and_status(
    async_db_engine,
    test_org: Organization,
) -> None:
    """Verify appending messages with deduplication by whatsapp_message_id and status update."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        customer = await CustomerService.create_customer(
            session,
            test_org.id,
            CustomerCreate(phone_number="+15551112222", name="Frank"),
        )
        conv, _ = await ConversationService.get_or_create_active_conversation(
            session, test_org.id, customer.id
        )
        await session.commit()

        wam_id = "wamid.TEST_DEDUP_123"
        msg_req = MessageCreate(
            sender_type=MessageSenderType.CUSTOMER,
            direction=MessageDirection.INBOUND,
            content_type=MessageContentType.TEXT,
            text_body="Do you have size 10 shoes?",
            whatsapp_message_id=wam_id,
        )

        # 1. First append -> Inserted
        msg1, inserted1 = await MessageService.append_message(
            session, test_org.id, conv.id, msg_req
        )
        await session.commit()
        assert inserted1 is True
        assert msg1.text_body == "Do you have size 10 shoes?"

        # 2. Duplicate webhook with same whatsapp_message_id -> Ignored & returned existing
        msg2, inserted2 = await MessageService.append_message(
            session, test_org.id, conv.id, msg_req
        )
        assert inserted2 is False
        assert msg2.id == msg1.id

        # 3. Update delivery receipt status
        updated_msg = await MessageService.update_message_status(
            session, test_org.id, wam_id, MessageStatus.DELIVERED
        )
        await session.commit()
        assert updated_msg is not None
        assert updated_msg.status == MessageStatus.DELIVERED
