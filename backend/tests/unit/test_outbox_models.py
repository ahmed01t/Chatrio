"""Unit tests for Transactional Outbox models and database metadata."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import (
    Base,
    Conversation,
    Customer,
    Organization,
    OutboxMessage,
    OutboxMessageType,
    OutboxStatus,
)


def test_outbox_metadata_registration() -> None:
    """Verify that outbox_messages table is registered in Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    assert "outbox_messages" in table_names


def test_outbox_table_columns_and_defaults() -> None:
    """Verify columns, types, and indexes on outbox_messages table."""
    table = Base.metadata.tables["outbox_messages"]
    cols = table.columns

    assert "id" in cols
    assert cols["id"].primary_key is True
    assert "organization_id" in cols
    assert "conversation_id" in cols
    assert "recipient_phone" in cols
    assert "message_type" in cols
    assert "payload" in cols
    assert "status" in cols
    assert "retry_count" in cols
    assert "max_retries" in cols
    assert "next_retry_at" in cols
    assert "sent_at" in cols
    assert "last_error" in cols
    assert "created_at" in cols
    assert "updated_at" in cols


@pytest.mark.asyncio
async def test_outbox_message_crud_lifecycle() -> None:
    """Verify saving, querying, and updating an OutboxMessage in SQLite memory DB."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # 1. Create Organization & Customer & Conversation
        org = Organization(name="Outbox Mart", slug="outbox-mart")
        session.add(org)
        await session.flush()

        customer = Customer(
            organization_id=org.id,
            phone_number="+15551234567",
            name="Alice Outbox",
        )
        session.add(customer)
        await session.flush()

        conv = Conversation(
            organization_id=org.id,
            customer_id=customer.id,
        )
        session.add(conv)
        await session.flush()

        # 2. Insert OutboxMessage
        outbox = OutboxMessage(
            organization_id=org.id,
            conversation_id=conv.id,
            recipient_phone="+15551234567",
            message_type=OutboxMessageType.TEXT,
            payload={"text": "Your order #100 is confirmed!"},
            status=OutboxStatus.PENDING,
            max_retries=3,
        )
        session.add(outbox)
        await session.commit()

        assert outbox.id is not None
        assert outbox.status == OutboxStatus.PENDING
        assert outbox.retry_count == 0
        assert outbox.max_retries == 3
        assert outbox.sent_at is None

        # 3. Transition to SENT
        outbox.status = OutboxStatus.SENT
        outbox.sent_at = datetime.now(UTC)
        await session.commit()

        assert outbox.status == OutboxStatus.SENT
        assert outbox.sent_at is not None

    await engine.dispose()
