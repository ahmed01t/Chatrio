"""Integration tests for End-to-End Transactional Outbox pipeline."""

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from sqlalchemy import select
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
    OutboxStatus,
)
from app.infrastructure.whatsapp import WhatsAppClient
from app.modules.messaging.outbox_worker import OutboxWorker
from app.modules.messaging.service import MessagingService


class StubChatModel(BaseChatModel):
    """Stub model returning deterministic test responses."""

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content="Welcome to Outbox Superstore! How can I help?")
                )
            ]
        )

    @property
    def _llm_type(self) -> str:
        return "stub_chat_model"

    def bind_tools(self, tools: list[Any], **kwargs: Any) -> "StubChatModel":
        return self


@pytest.fixture
async def async_session() -> AsyncSession:
    """Isolated in-memory SQLite session for integration testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_end_to_end_outbox_success(async_session: AsyncSession) -> None:
    """Verifies that dispatch_ai_turn atomically enqueues and dispatches an outbox message."""
    org = Organization(name="Outbox Store", slug="outbox-store")
    async_session.add(org)
    await async_session.flush()

    customer = Customer(
        organization_id=org.id,
        phone_number="+15551239999",
        name="Integration Customer",
    )
    async_session.add(customer)
    await async_session.flush()

    conv = Conversation(
        organization_id=org.id,
        customer_id=customer.id,
        is_ai_active=True,
    )
    async_session.add(conv)
    await async_session.flush()

    # Pre-populate inbound message to open 24h care window
    inbound = Message(
        organization_id=org.id,
        conversation_id=conv.id,
        sender_type=MessageSenderType.CUSTOMER,
        direction=MessageDirection.INBOUND,
        content_type=MessageContentType.TEXT,
        text_body="Hello store!",
    )
    async_session.add(inbound)
    await async_session.commit()

    mock_client = AsyncMock(spec=WhatsAppClient)

    # Dispatch AI turn
    reply = await MessagingService.dispatch_ai_turn(
        session=async_session,
        organization_id=org.id,
        conversation_id=conv.id,
        customer_id=customer.id,
        incoming_text="Hello store!",
        whatsapp_client=mock_client,
        model=StubChatModel(),
    )

    await async_session.commit()

    assert reply is not None
    assert "Outbox Superstore" in reply

    # Verify Outbox record was created and marked SENT
    outbox_query = select(OutboxMessage).where(OutboxMessage.conversation_id == conv.id)
    outbox_records = list((await async_session.execute(outbox_query)).scalars().all())

    assert len(outbox_records) == 1
    outbox = outbox_records[0]
    assert outbox.status == OutboxStatus.SENT
    assert outbox.sent_at is not None
    assert outbox.recipient_phone == "+15551239999"
    assert outbox.payload.get("body") == reply

    mock_client.send_text_message.assert_awaited_once_with(
        to="+15551239999",
        text=reply,
    )


@pytest.mark.asyncio
async def test_end_to_end_outbox_resilience_to_meta_failure(async_session: AsyncSession) -> None:
    """
    If Meta Cloud API is unavailable, the outbox record is safely preserved in DB
    and scheduled for retry with zero lost messages.
    """
    org = Organization(name="Fault Tolerant Store", slug="ft-store")
    async_session.add(org)
    await async_session.flush()

    customer = Customer(
        organization_id=org.id,
        phone_number="+15551238888",
        name="Resilient Customer",
    )
    async_session.add(customer)
    await async_session.flush()

    conv = Conversation(
        organization_id=org.id,
        customer_id=customer.id,
        is_ai_active=True,
    )
    async_session.add(conv)
    await async_session.flush()

    inbound = Message(
        organization_id=org.id,
        conversation_id=conv.id,
        sender_type=MessageSenderType.CUSTOMER,
        direction=MessageDirection.INBOUND,
        content_type=MessageContentType.TEXT,
        text_body="Are you open?",
    )
    async_session.add(inbound)
    await async_session.commit()

    # Meta client raises network error
    failing_client = AsyncMock(spec=WhatsAppClient)
    failing_client.send_text_message.side_effect = ConnectionResetError("Meta Connection Reset")

    reply = await MessagingService.dispatch_ai_turn(
        session=async_session,
        organization_id=org.id,
        conversation_id=conv.id,
        customer_id=customer.id,
        incoming_text="Are you open?",
        whatsapp_client=failing_client,
        model=StubChatModel(),
    )
    await async_session.commit()

    # Message must NOT be lost: Outbox record is PENDING with retry scheduled
    outbox_query = select(OutboxMessage).where(OutboxMessage.conversation_id == conv.id)
    outbox = (await async_session.execute(outbox_query)).scalar_one()

    assert outbox.status == OutboxStatus.PENDING
    assert outbox.retry_count == 1
    assert "Connection Reset" in (outbox.last_error or "")

    # Fast-forward retry timer to simulate backoff elapse
    outbox.next_retry_at = datetime.now(UTC) - timedelta(seconds=1)
    await async_session.commit()

    # Now Meta recovers: Worker processes pending batch successfully
    healthy_client = AsyncMock(spec=WhatsAppClient)
    delivered_count = await OutboxWorker.process_batch(
        session=async_session,
        whatsapp_client=healthy_client,
    )

    assert delivered_count == 1
    assert outbox.status == OutboxStatus.SENT
    healthy_client.send_text_message.assert_awaited_once_with(
        to="+15551238888",
        text=reply,
    )
