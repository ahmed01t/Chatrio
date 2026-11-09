"""
Transactional Outbox Service & Meta 24-Hour Customer Care Policy Engine.

Provides:
1. `OutboxService.check_24h_policy_window`: Strict enforcement of Meta's 24-hour service window.
2. `OutboxService.enqueue_outbox`: Atomic persistence within the caller's active ACID transaction.
3. `OutboxService.fetch_pending_batch`: Concurrency-safe retrieval with SKIP LOCKED.
4. `OutboxService.mark_as_sent` / `schedule_retry` / `mark_as_failed`: State machine transitions.
"""

import math
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.conversations.models import Message, MessageDirection
from app.modules.messaging.models import (
    OutboxMessage,
    OutboxMessageType,
    OutboxStatus,
)
from app.modules.messaging.outbox_schemas import (
    OutboxEnqueueRequest,
    PolicyCheckResult,
)


class OutboxService:
    """Service managing transactional outbox message persistence and policy checks."""

    # Meta 24-hour window duration in seconds (24 hours = 86,400 seconds)
    META_CARE_WINDOW_SECONDS: int = 86400

    @classmethod
    async def check_24h_policy_window(
        cls,
        session: AsyncSession,
        conversation_id: uuid.UUID | None,
        message_type: OutboxMessageType,
        reference_time: datetime | None = None,
    ) -> PolicyCheckResult:
        """
        Enforces Meta's 24-hour customer care policy window.

        Rules:
        - Within 24 hours of customer's last inbound message: All message types permitted.
        - Outside 24 hours: Only pre-approved WhatsApp Templates (TEMPLATE) permitted.
        - Attempting to send freeform TEXT/INTERACTIVE outside 24h triggers a policy block.
        """
        now = reference_time or datetime.now(UTC)

        # Templates are universally exempt from the 24-hour window restriction
        if message_type == OutboxMessageType.TEMPLATE:
            return PolicyCheckResult(
                is_permitted=True,
                violation_reason=None,
                is_within_24h_window=False,
                seconds_since_last_customer_message=None,
            )

        # Non-template messages require a conversation context with an inbound message history
        if not conversation_id:
            return PolicyCheckResult(
                is_permitted=False,
                violation_reason="POLICY_VIOLATION_CONVERSATION_REQUIRED_FOR_NON_TEMPLATE",
                is_within_24h_window=False,
                seconds_since_last_customer_message=None,
            )

        # Query the most recent INBOUND message from the customer
        query = (
            select(Message.created_at)
            .where(
                Message.conversation_id == conversation_id,
                Message.direction == MessageDirection.INBOUND,
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_inbound_at = (await session.execute(query)).scalar_one_or_none()

        if not last_inbound_at:
            return PolicyCheckResult(
                is_permitted=False,
                violation_reason="POLICY_VIOLATION_NO_PRIOR_CUSTOMER_MESSAGE",
                is_within_24h_window=False,
                seconds_since_last_customer_message=None,
            )

        # Normalize timezone awareness
        if last_inbound_at.tzinfo is None:
            last_inbound_at = last_inbound_at.replace(tzinfo=UTC)

        elapsed_seconds = (now - last_inbound_at).total_seconds()
        is_within_window = elapsed_seconds <= cls.META_CARE_WINDOW_SECONDS

        if not is_within_window:
            return PolicyCheckResult(
                is_permitted=False,
                violation_reason="POLICY_VIOLATION_24H_WINDOW_EXPIRED",
                is_within_24h_window=False,
                seconds_since_last_customer_message=elapsed_seconds,
            )

        return PolicyCheckResult(
            is_permitted=True,
            violation_reason=None,
            is_within_24h_window=True,
            seconds_since_last_customer_message=elapsed_seconds,
        )

    @classmethod
    async def enqueue_outbox(
        cls,
        session: AsyncSession,
        request: OutboxEnqueueRequest,
    ) -> OutboxMessage:
        """
        Enqueues an outbound message within the caller's active database transaction.

        Ensures atomic persistence with business state updates (e.g. order placement).
        """
        outbox_msg = OutboxMessage(
            organization_id=request.organization_id,
            conversation_id=request.conversation_id,
            recipient_phone=request.recipient_phone,
            message_type=request.message_type,
            payload=request.payload,
            status=OutboxStatus.PENDING,
            max_retries=request.max_retries,
        )
        session.add(outbox_msg)
        await session.flush()
        return outbox_msg

    @classmethod
    async def fetch_pending_batch(
        cls,
        session: AsyncSession,
        batch_size: int = 20,
    ) -> list[OutboxMessage]:
        """
        Retrieves pending outbox messages ready for delivery.

        Uses SELECT ... FOR UPDATE SKIP LOCKED when supported (PostgreSQL) to avoid
        worker race conditions.
        """
        now = datetime.now(UTC)
        query = (
            select(OutboxMessage)
            .where(
                OutboxMessage.status == OutboxStatus.PENDING,
                OutboxMessage.next_retry_at <= now,
            )
            .order_by(OutboxMessage.created_at.asc())
            .limit(batch_size)
        )

        # Check if database supports SKIP LOCKED (e.g. PostgreSQL)
        bind = session.get_bind()
        if bind and bind.dialect.name == "postgresql":
            query = query.with_for_update(skip_locked=True)

        result = await session.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def mark_as_sending(
        cls,
        session: AsyncSession,
        outbox_id: uuid.UUID,
    ) -> None:
        """Transitions outbox message state to SENDING."""
        query = select(OutboxMessage).where(OutboxMessage.id == outbox_id)
        msg = (await session.execute(query)).scalar_one_or_none()
        if msg:
            msg.status = OutboxStatus.SENDING
            await session.flush()

    @classmethod
    async def mark_as_sent(
        cls,
        session: AsyncSession,
        outbox_id: uuid.UUID,
    ) -> None:
        """Marks outbox message as successfully delivered (SENT)."""
        query = select(OutboxMessage).where(OutboxMessage.id == outbox_id)
        msg = (await session.execute(query)).scalar_one_or_none()
        if msg:
            msg.status = OutboxStatus.SENT
            msg.sent_at = datetime.now(UTC)
            msg.last_error = None
            await session.flush()

    @classmethod
    async def schedule_retry(
        cls,
        session: AsyncSession,
        outbox_id: uuid.UUID,
        error_message: str,
    ) -> OutboxStatus:
        """
        Handles temporary delivery failure with exponential backoff.

        If retry_count reaches max_retries, transitions to FAILED.
        """
        query = select(OutboxMessage).where(OutboxMessage.id == outbox_id)
        msg = (await session.execute(query)).scalar_one_or_none()
        if not msg:
            return OutboxStatus.FAILED

        msg.retry_count += 1
        msg.last_error = error_message[:1000]

        if msg.retry_count >= msg.max_retries:
            msg.status = OutboxStatus.FAILED
            await session.flush()
            return OutboxStatus.FAILED

        # Exponential backoff: min(300, 2^retry_count * 2) seconds
        delay_seconds = min(300.0, math.pow(2, msg.retry_count) * 2.0)
        msg.status = OutboxStatus.PENDING
        msg.next_retry_at = datetime.now(UTC) + timedelta(seconds=delay_seconds)
        await session.flush()
        return OutboxStatus.PENDING

    @classmethod
    async def mark_as_failed(
        cls,
        session: AsyncSession,
        outbox_id: uuid.UUID,
        reason: str,
    ) -> None:
        """Marks outbox message as permanently FAILED (e.g. policy violation)."""
        query = select(OutboxMessage).where(OutboxMessage.id == outbox_id)
        msg = (await session.execute(query)).scalar_one_or_none()
        if msg:
            msg.status = OutboxStatus.FAILED
            msg.last_error = reason[:1000]
            await session.flush()
