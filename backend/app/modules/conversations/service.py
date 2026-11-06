"""
Conversation and Message Business Service Layer.

Implements business logic for:
1. Conversation session lifecycle (get-or-create, creation, list inbox).
2. Human takeover state transitions (is_ai_active toggle and agent assignment).
3. Message appending with WhatsApp message deduplication (idempotency).
4. Message delivery receipt updates and pagination.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.modules.conversations.models import (
    Conversation,
    ConversationChannel,
    ConversationStatus,
    Message,
    MessageStatus,
)
from app.modules.conversations.schemas import (
    ConversationCreate,
    ConversationTakeoverUpdate,
    MessageCreate,
)
from app.modules.customers.service import CustomerService


class ConversationService:
    """Service handling multi-tenant Conversation session operations."""

    @staticmethod
    async def get_or_create_active_conversation(
        session: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID,
        channel: ConversationChannel = ConversationChannel.WHATSAPP,
    ) -> tuple[Conversation, bool]:
        """
        Retrieves the active conversation for a customer or creates a new one.

        Returns:
            tuple[Conversation, bool]: (conversation_instance, was_created_flag)
        """
        # Ensure customer belongs to this organization
        await CustomerService.get_customer(session, organization_id, customer_id)

        # Check for existing ACTIVE conversation
        query = (
            select(Conversation)
            .options(selectinload(Conversation.customer))
            .where(
                Conversation.organization_id == organization_id,
                Conversation.customer_id == customer_id,
                Conversation.status == ConversationStatus.ACTIVE,
            )
            .order_by(Conversation.created_at.desc())
        )
        existing = (await session.execute(query)).scalars().first()

        if existing is not None:
            return existing, False

        # Create new active conversation
        conversation = Conversation(
            id=uuid.uuid4(),
            organization_id=organization_id,
            customer_id=customer_id,
            channel=channel,
            status=ConversationStatus.ACTIVE,
            is_ai_active=True,
            last_message_at=datetime.now(UTC),
        )
        session.add(conversation)
        await session.flush()
        return await ConversationService.get_conversation(
            session, organization_id, conversation.id
        ), True

    @staticmethod # why static method because no dependency on state, only input arguments are used 
    async def create_conversation(
        session: AsyncSession,
        organization_id: uuid.UUID,
        request: ConversationCreate,
    ) -> Conversation:
        """Explicitly starts a new conversation session for a customer."""
        # Ensure customer exists in this tenant
        await CustomerService.get_customer(session, organization_id, request.customer_id)

        conversation = Conversation(
            id=uuid.uuid4(),
            organization_id=organization_id,
            customer_id=request.customer_id,
            channel=request.channel,
            assigned_agent_id=request.assigned_agent_id,
            status=ConversationStatus.ACTIVE,
            is_ai_active=True,
            last_message_at=datetime.now(UTC),
        )
        session.add(conversation)
        await session.flush()
        return await ConversationService.get_conversation(session, organization_id, conversation.id)

    @staticmethod
    async def get_conversation(
        session: AsyncSession,
        organization_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Conversation:
        """Retrieves a single conversation by ID with eager loaded customer relation."""
        query = (
            select(Conversation)
            .options(selectinload(Conversation.customer))
            .where(
                Conversation.organization_id == organization_id,
                Conversation.id == conversation_id,
            )
        )
        conversation = (await session.execute(query)).scalar_one_or_none()
        if conversation is None:
            raise NotFoundException(
                code="CONVERSATION_NOT_FOUND",
                message="Conversation not found.",
            )
        return conversation

    @staticmethod
    async def list_conversations(
        session: AsyncSession,
        organization_id: uuid.UUID,
        status: ConversationStatus | None = None,
        is_ai_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Conversation], int]:
        """Lists conversations for the merchant inbox with filtering and pagination."""
        base_query = (
            select(Conversation)
            .options(selectinload(Conversation.customer))
            .where(Conversation.organization_id == organization_id)
        )

        if status is not None:
            base_query = base_query.where(Conversation.status == status)
        if is_ai_active is not None:
            base_query = base_query.where(Conversation.is_ai_active == is_ai_active)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await session.execute(count_query)).scalar_one()

        # Paginate with most recent messages first
        offset = (page - 1) * page_size
        items_query = (
            base_query.order_by(
                Conversation.last_message_at.desc().nullslast(),
                Conversation.created_at.desc(),
            )
            .offset(offset)
            .limit(page_size)
        )
        items = (await session.execute(items_query)).scalars().all()
        return items, total

    @staticmethod
    async def update_takeover(
        session: AsyncSession,
        organization_id: uuid.UUID,
        conversation_id: uuid.UUID,
        request: ConversationTakeoverUpdate,
    ) -> Conversation:
        """Toggles human takeover mode on or off for a conversation."""
        conversation = await ConversationService.get_conversation(
            session, organization_id, conversation_id
        )

        conversation.is_ai_active = request.is_ai_active
        if request.assigned_agent_id is not None:
            conversation.assigned_agent_id = request.assigned_agent_id

        await session.flush()
        return await ConversationService.get_conversation(session, organization_id, conversation_id)

    @staticmethod
    async def update_status(
        session: AsyncSession,
        organization_id: uuid.UUID,
        conversation_id: uuid.UUID,
        new_status: ConversationStatus,
    ) -> Conversation:
        """Updates the status (ACTIVE, CLOSED, ARCHIVED) of a conversation."""
        conversation = await ConversationService.get_conversation(
            session, organization_id, conversation_id
        )

        conversation.status = new_status
        await session.flush()
        return await ConversationService.get_conversation(session, organization_id, conversation_id)


class MessageService:
    """Service handling multi-tenant Message audit logging and delivery tracking."""

    @staticmethod
    async def append_message(
        session: AsyncSession,
        organization_id: uuid.UUID,
        conversation_id: uuid.UUID,
        request: MessageCreate,
    ) -> tuple[Message, bool]:
        """
        Appends an inbound or outbound message to a conversation.

        Guarantees idempotency: If a message with the same `whatsapp_message_id`
        already exists for this organization, returns the existing record without duplicating.

        Returns:
            tuple[Message, bool]: (message_instance, was_inserted_flag)
        """
        # Ensure conversation exists in this tenant
        conversation = await ConversationService.get_conversation(
            session, organization_id, conversation_id
        )

        # Idempotency check on whatsapp_message_id
        if request.whatsapp_message_id:
            dedup_query = select(Message).where(
                Message.organization_id == organization_id,
                Message.whatsapp_message_id == request.whatsapp_message_id,
            )
            existing_msg = (await session.execute(dedup_query)).scalar_one_or_none()
            if existing_msg is not None:
                return existing_msg, False

        # Create message
        now = datetime.now(UTC)
        msg = Message(
            id=uuid.uuid4(),
            organization_id=organization_id,
            conversation_id=conversation_id,
            sender_type=request.sender_type,
            direction=request.direction,
            content_type=request.content_type,
            text_body=request.text_body,
            media_url=request.media_url,
            status=MessageStatus.RECEIVED,
            whatsapp_message_id=request.whatsapp_message_id,
            raw_payload=request.raw_payload,
            created_at=now,
        )
        session.add(msg)

        # Bump last_message_at on conversation
        conversation.last_message_at = now

        await session.flush()
        await session.refresh(msg)
        return msg, True

    @staticmethod
    async def list_messages(
        session: AsyncSession,
        organization_id: uuid.UUID,
        conversation_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[Sequence[Message], int]:
        """Lists messages for a conversation in chronological order."""
        # Ensure conversation belongs to this tenant
        await ConversationService.get_conversation(session, organization_id, conversation_id)

        base_query = select(Message).where(
            Message.organization_id == organization_id,
            Message.conversation_id == conversation_id,
        )

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await session.execute(count_query)).scalar_one()

        # Paginate chronologically (oldest first for chat transcripts)
        offset = (page - 1) * page_size
        items_query = base_query.order_by(Message.created_at.asc()).offset(offset).limit(page_size)
        items = (await session.execute(items_query)).scalars().all()
        return items, total

    @staticmethod
    async def update_message_status(
        session: AsyncSession,
        organization_id: uuid.UUID,
        whatsapp_message_id: str,
        new_status: MessageStatus,
    ) -> Message | None:
        """
        Updates delivery receipt status (SENT, DELIVERED, READ, FAILED)
        by external WhatsApp message ID.
        """
        query = select(Message).where(
            Message.organization_id == organization_id,
            Message.whatsapp_message_id == whatsapp_message_id,
        )
        msg = (await session.execute(query)).scalar_one_or_none()
        if msg is not None:
            msg.status = new_status
            await session.flush()
            await session.refresh(msg)
        return msg
