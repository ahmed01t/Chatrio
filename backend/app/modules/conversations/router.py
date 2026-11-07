"""
Conversation and Messaging API Endpoints.

Provides tenant-scoped endpoints for:
- POST /conversations: Initiate a conversation session.
- GET /conversations: List conversations for the merchant inbox.
- GET /conversations/{id}: Get conversation details.
- PATCH /conversations/{id}/takeover: Toggle human takeover (is_ai_active).
- PATCH /conversations/{id}/status: Change conversation lifecycle state.
- GET /conversations/{id}/messages: Chronological message history.
- POST /conversations/{id}/messages: Post human reply into conversation.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentTenant, DBSession
from app.modules.conversations.models import ConversationStatus, MessageSenderType
from app.modules.conversations.schemas import (
    ConversationCreate,
    ConversationListResponse,
    ConversationRead,
    ConversationStatusUpdate,
    ConversationTakeoverUpdate,
    MessageCreate,
    MessageListResponse,
    MessageRead,
)
from app.modules.conversations.service import ConversationService, MessageService

router = APIRouter(prefix="/conversations", tags=["Conversations & Inbox"])


# Conversation Lifecycle & Inbox Endpoints
@router.post(
    "",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new conversation session",
)
async def create_conversation(
    request: ConversationCreate,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> ConversationRead:
    """Initiates a new conversation session for a customer under this tenant."""
    conversation = await ConversationService.create_conversation(
        session=session,
        organization_id=tenant_context.organization.id,
        request=request,
    )
    return ConversationRead.model_validate(conversation)


@router.get(
    "",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List conversations inbox",
)
async def list_conversations(
    tenant_context: CurrentTenant,
    session: DBSession,
    status_filter: Annotated[
        ConversationStatus | None,
        Query(alias="status", description="Filter by status"),
    ] = None,
    is_ai_active: Annotated[
        bool | None,
        Query(description="Filter by AI active / human takeover"),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> ConversationListResponse:
    """Lists conversations for the merchant inbox sorted by last message time."""
    items, total = await ConversationService.list_conversations(
        session=session,
        organization_id=tenant_context.organization.id,
        status=status_filter,
        is_ai_active=is_ai_active,
        page=page,
        page_size=page_size,
    )
    return ConversationListResponse(
        items=[ConversationRead.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationRead,
    status_code=status.HTTP_200_OK,
    summary="Get conversation details by ID",
)
async def get_conversation(
    conversation_id: uuid.UUID,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> ConversationRead:
    """Retrieves conversation details including customer metadata."""
    conversation = await ConversationService.get_conversation(
        session=session,
        organization_id=tenant_context.organization.id,
        conversation_id=conversation_id,
    )
    return ConversationRead.model_validate(conversation)


@router.patch(
    "/{conversation_id}/takeover",
    response_model=ConversationRead,
    status_code=status.HTTP_200_OK,
    summary="Toggle human takeover mode",
)
async def update_takeover(
    conversation_id: uuid.UUID,
    request: ConversationTakeoverUpdate,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> ConversationRead:
    """
    Toggles AI automated replies on or off for this conversation.

    When `is_ai_active=False`, human agent takes over and AI stops generating replies.
    """
    conversation = await ConversationService.update_takeover(
        session=session,
        organization_id=tenant_context.organization.id,
        conversation_id=conversation_id,
        request=request,
    )
    return ConversationRead.model_validate(conversation)


@router.patch(
    "/{conversation_id}/status",
    response_model=ConversationRead,
    status_code=status.HTTP_200_OK,
    summary="Update conversation status",
)
async def update_status(
    conversation_id: uuid.UUID,
    request: ConversationStatusUpdate,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> ConversationRead:
    """Updates the status (ACTIVE, CLOSED, ARCHIVED) of a conversation."""
    conversation = await ConversationService.update_status(
        session=session,
        organization_id=tenant_context.organization.id,
        conversation_id=conversation_id,
        new_status=request.status,
    )
    return ConversationRead.model_validate(conversation)


# ==============================================================================
# Message Endpoints
# ==============================================================================
@router.get(
    "/{conversation_id}/messages",
    response_model=MessageListResponse,
    status_code=status.HTTP_200_OK,
    summary="List messages in a conversation",
)
async def list_messages(
    conversation_id: uuid.UUID,
    tenant_context: CurrentTenant,
    session: DBSession,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=200, description="Items per page")] = 50,
) -> MessageListResponse:
    """Returns chronological message transcript for a conversation."""
    items, total = await MessageService.list_messages(
        session=session,
        organization_id=tenant_context.organization.id,
        conversation_id=conversation_id,
        page=page,
        page_size=page_size,
    )
    return MessageListResponse(
        items=[MessageRead.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message in a conversation",
)
async def send_message(
    conversation_id: uuid.UUID,
    request: MessageCreate,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> MessageRead:
    """Appends an outbound reply from a human staff agent into the conversation."""
    # Ensure default sender type is HUMAN_AGENT if posted via dashboard API
    if not request.sender_type:
        request.sender_type = MessageSenderType.HUMAN_AGENT

    message, _ = await MessageService.append_message(
        session=session,
        organization_id=tenant_context.organization.id,
        conversation_id=conversation_id,
        request=request,
    )
    return MessageRead.model_validate(message)
