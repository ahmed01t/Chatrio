"""Unit tests for OutboxWorker delivery and retry processing."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import (
    Base,
    Conversation,
    Customer,
    Message,
    MessageContentType,
    MessageDirection,
    MessageSenderType,
    Organization,
    OutboxMessage,
    OutboxMessageType,
    OutboxStatus,
)
from app.infrastructure.whatsapp import WhatsAppClient
from app.modules.messaging.outbox_worker import OutboxWorker


@pytest.fixture
async def async_session() -> AsyncSession:
    """Isolated in-memory SQLite session for outbox worker tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_worker_deliver_text_message_success(async_session: AsyncSession) -> None:
    """Worker delivers a valid text message within 24h window and marks it SENT."""
    org = Organization(name="Delivery Mart", slug="delivery-mart")
    async_session.add(org)
    await async_session.flush()

    customer = Customer(organization_id=org.id, phone_number="+15551112222", name="Alice")
    async_session.add(customer)
    await async_session.flush()

    conv = Conversation(organization_id=org.id, customer_id=customer.id)
    async_session.add(conv)
    await async_session.flush()

    # Active customer message 10 minutes ago
    inbound = Message(
        organization_id=org.id,
        conversation_id=conv.id,
        sender_type=MessageSenderType.CUSTOMER,
        direction=MessageDirection.INBOUND,
        content_type=MessageContentType.TEXT,
        text_body="Hello",
        created_at=datetime.now(UTC) - timedelta(minutes=10),
    )
    async_session.add(inbound)

    outbox = OutboxMessage(
        organization_id=org.id,
        conversation_id=conv.id,
        recipient_phone="+15551112222",
        message_type=OutboxMessageType.TEXT,
        payload={"body": "Hello Alice, how can we help?"},
        status=OutboxStatus.PENDING,
    )
    async_session.add(outbox)
    await async_session.commit()

    mock_client = AsyncMock(spec=WhatsAppClient)
    delivered = await OutboxWorker.deliver_message(
        session=async_session,
        outbox_msg=outbox,
        whatsapp_client=mock_client,
    )

    assert delivered is True
    assert outbox.status == OutboxStatus.SENT
    assert outbox.sent_at is not None
    mock_client.send_text_message.assert_awaited_once_with(
        to="+15551112222",
        text="Hello Alice, how can we help?",
    )


@pytest.mark.asyncio
async def test_worker_policy_violation_fails_without_meta_call(
    async_session: AsyncSession,
) -> None:
    """Worker blocks freeform text outside 24h window without calling Meta API."""
    org = Organization(name="Policy Store", slug="policy-store")
    async_session.add(org)
    await async_session.flush()

    customer = Customer(organization_id=org.id, phone_number="+15553334444", name="Bob")
    async_session.add(customer)
    await async_session.flush()

    conv = Conversation(organization_id=org.id, customer_id=customer.id)
    async_session.add(conv)
    await async_session.flush()

    # Customer texted 30 hours ago (outside 24h window)
    inbound = Message(
        organization_id=org.id,
        conversation_id=conv.id,
        sender_type=MessageSenderType.CUSTOMER,
        direction=MessageDirection.INBOUND,
        content_type=MessageContentType.TEXT,
        text_body="Old message",
        created_at=datetime.now(UTC) - timedelta(hours=30),
    )
    async_session.add(inbound)

    outbox = OutboxMessage(
        organization_id=org.id,
        conversation_id=conv.id,
        recipient_phone="+15553334444",
        message_type=OutboxMessageType.TEXT,
        payload={"body": "Promotional update"},
        status=OutboxStatus.PENDING,
    )
    async_session.add(outbox)
    await async_session.commit()

    mock_client = AsyncMock(spec=WhatsAppClient)
    delivered = await OutboxWorker.deliver_message(
        session=async_session,
        outbox_msg=outbox,
        whatsapp_client=mock_client,
    )

    assert delivered is False
    assert outbox.status == OutboxStatus.FAILED
    assert "24H_WINDOW_EXPIRED" in (outbox.last_error or "")
    mock_client.send_text_message.assert_not_called()


@pytest.mark.asyncio
async def test_worker_template_allowed_outside_24h(async_session: AsyncSession) -> None:
    """Templates are allowed outside the 24h window."""
    org = Organization(name="Template Store", slug="template-store")
    async_session.add(org)
    await async_session.flush()

    outbox = OutboxMessage(
        organization_id=org.id,
        conversation_id=None,
        recipient_phone="+15555556666",
        message_type=OutboxMessageType.TEMPLATE,
        payload={
            "template_name": "shipping_update_v1",
            "language": "en_US",
            "components": [],
        },
        status=OutboxStatus.PENDING,
    )
    async_session.add(outbox)
    await async_session.commit()

    mock_client = AsyncMock(spec=WhatsAppClient)
    delivered = await OutboxWorker.deliver_message(
        session=async_session,
        outbox_msg=outbox,
        whatsapp_client=mock_client,
    )

    assert delivered is True
    assert outbox.status == OutboxStatus.SENT
    mock_client.send_template.assert_awaited_once()


@pytest.mark.asyncio
async def test_worker_retries_on_meta_error(async_session: AsyncSession) -> None:
    """Worker catches transient Meta exceptions and schedules exponential retry."""
    org = Organization(name="Retry Store", slug="retry-store")
    async_session.add(org)
    await async_session.flush()

    customer = Customer(organization_id=org.id, phone_number="+15557778888", name="Charlie")
    async_session.add(customer)
    await async_session.flush()

    conv = Conversation(organization_id=org.id, customer_id=customer.id)
    async_session.add(conv)
    await async_session.flush()

    inbound = Message(
        organization_id=org.id,
        conversation_id=conv.id,
        sender_type=MessageSenderType.CUSTOMER,
        direction=MessageDirection.INBOUND,
        content_type=MessageContentType.TEXT,
        text_body="Hi",
        created_at=datetime.now(UTC) - timedelta(minutes=5),
    )
    async_session.add(inbound)

    outbox = OutboxMessage(
        organization_id=org.id,
        conversation_id=conv.id,
        recipient_phone="+15557778888",
        message_type=OutboxMessageType.TEXT,
        payload={"body": "Hello Charlie"},
        status=OutboxStatus.PENDING,
        max_retries=3,
    )
    async_session.add(outbox)
    await async_session.commit()

    mock_client = AsyncMock(spec=WhatsAppClient)
    mock_client.send_text_message.side_effect = RuntimeError("Meta 429 Rate Limit Exceeded")

    delivered = await OutboxWorker.deliver_message(
        session=async_session,
        outbox_msg=outbox,
        whatsapp_client=mock_client,
    )

    assert delivered is False
    assert outbox.status == OutboxStatus.PENDING
    assert outbox.retry_count == 1
    assert "429" in (outbox.last_error or "")
