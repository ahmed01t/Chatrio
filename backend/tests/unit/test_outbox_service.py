"""Unit tests for OutboxService and Meta 24-Hour Customer Care Policy Engine."""

from datetime import UTC, datetime, timedelta

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
    OutboxMessageType,
    OutboxStatus,
)
from app.modules.messaging.outbox_schemas import OutboxEnqueueRequest
from app.modules.messaging.outbox_service import OutboxService


@pytest.fixture
async def async_session() -> AsyncSession:
    """Provides an isolated SQLite in-memory session for outbox service tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_policy_window_template_always_permitted(async_session: AsyncSession) -> None:
    """Pre-approved WhatsApp templates are exempt from 24h window restriction."""
    result = await OutboxService.check_24h_policy_window(
        session=async_session,
        conversation_id=None,
        message_type=OutboxMessageType.TEMPLATE,
    )
    assert result.is_permitted is True
    assert result.violation_reason is None


@pytest.mark.asyncio
async def test_policy_window_no_inbound_message_rejection(async_session: AsyncSession) -> None:
    """Freeform messages without prior inbound customer messages are blocked."""
    org = Organization(name="Care Store", slug="care-store")
    async_session.add(org)
    await async_session.flush()

    customer = Customer(organization_id=org.id, phone_number="+15550001111", name="Bob")
    async_session.add(customer)
    await async_session.flush()

    conv = Conversation(organization_id=org.id, customer_id=customer.id)
    async_session.add(conv)
    await async_session.commit()

    result = await OutboxService.check_24h_policy_window(
        session=async_session,
        conversation_id=conv.id,
        message_type=OutboxMessageType.TEXT,
    )
    assert result.is_permitted is False
    assert result.violation_reason == "POLICY_VIOLATION_NO_PRIOR_CUSTOMER_MESSAGE"


@pytest.mark.asyncio
async def test_policy_window_active_customer_permitted(async_session: AsyncSession) -> None:
    """Customer messaging within 24 hours permits freeform text/interactive."""
    org = Organization(name="Care Store 2", slug="care-store-2")
    async_session.add(org)
    await async_session.flush()

    customer = Customer(organization_id=org.id, phone_number="+15550002222", name="Charlie")
    async_session.add(customer)
    await async_session.flush()

    conv = Conversation(organization_id=org.id, customer_id=customer.id)
    async_session.add(conv)
    await async_session.flush()

    # Customer texted 2 hours ago
    two_hours_ago = datetime.now(UTC) - timedelta(hours=2)
    inbound_msg = Message(
        organization_id=org.id,
        conversation_id=conv.id,
        sender_type=MessageSenderType.CUSTOMER,
        direction=MessageDirection.INBOUND,
        content_type=MessageContentType.TEXT,
        text_body="Hi there!",
        created_at=two_hours_ago,
    )
    async_session.add(inbound_msg)
    await async_session.commit()

    result = await OutboxService.check_24h_policy_window(
        session=async_session,
        conversation_id=conv.id,
        message_type=OutboxMessageType.TEXT,
    )
    assert result.is_permitted is True
    assert result.is_within_24h_window is True
    assert result.violation_reason is None


@pytest.mark.asyncio
async def test_policy_window_expired_rejection(async_session: AsyncSession) -> None:
    """Customer inactive for >24 hours blocks freeform text to prevent Meta strike."""
    org = Organization(name="Care Store 3", slug="care-store-3")
    async_session.add(org)
    await async_session.flush()

    customer = Customer(organization_id=org.id, phone_number="+15550003333", name="Diana")
    async_session.add(customer)
    await async_session.flush()

    conv = Conversation(organization_id=org.id, customer_id=customer.id)
    async_session.add(conv)
    await async_session.flush()

    # Customer texted 26 hours ago
    twenty_six_hours_ago = datetime.now(UTC) - timedelta(hours=26)
    inbound_msg = Message(
        organization_id=org.id,
        conversation_id=conv.id,
        sender_type=MessageSenderType.CUSTOMER,
        direction=MessageDirection.INBOUND,
        content_type=MessageContentType.TEXT,
        text_body="Old message",
        created_at=twenty_six_hours_ago,
    )
    async_session.add(inbound_msg)
    await async_session.commit()

    result = await OutboxService.check_24h_policy_window(
        session=async_session,
        conversation_id=conv.id,
        message_type=OutboxMessageType.TEXT,
    )
    assert result.is_permitted is False
    assert result.is_within_24h_window is False
    assert result.violation_reason == "POLICY_VIOLATION_24H_WINDOW_EXPIRED"


@pytest.mark.asyncio
async def test_outbox_enqueue_fetch_and_status_transitions(async_session: AsyncSession) -> None:
    """Verifies atomic enqueue, batch fetching, and status updates."""
    org = Organization(name="Outbox Test", slug="outbox-test")
    async_session.add(org)
    await async_session.flush()

    req = OutboxEnqueueRequest(
        organization_id=org.id,
        recipient_phone="+15559998888",
        message_type=OutboxMessageType.TEXT,
        payload={"body": "Order ready for pickup!"},
        max_retries=2,
    )

    outbox_msg = await OutboxService.enqueue_outbox(session=async_session, request=req)
    await async_session.commit()

    # Fetch pending
    batch = await OutboxService.fetch_pending_batch(session=async_session, batch_size=10)
    assert len(batch) == 1
    assert batch[0].id == outbox_msg.id

    # Mark sending
    await OutboxService.mark_as_sending(session=async_session, outbox_id=outbox_msg.id)
    await async_session.commit()
    assert outbox_msg.status == OutboxStatus.SENDING

    # Schedule retry (1st failure)
    status = await OutboxService.schedule_retry(
        session=async_session,
        outbox_id=outbox_msg.id,
        error_message="Meta HTTP 503 Service Unavailable",
    )
    await async_session.commit()
    assert status == OutboxStatus.PENDING
    assert outbox_msg.retry_count == 1
    assert "503" in (outbox_msg.last_error or "")

    # Schedule retry (2nd failure -> exceeds max_retries=2)
    status = await OutboxService.schedule_retry(
        session=async_session,
        outbox_id=outbox_msg.id,
        error_message="Meta HTTP 503 again",
    )
    await async_session.commit()
    assert status == OutboxStatus.FAILED
    assert outbox_msg.status == OutboxStatus.FAILED
