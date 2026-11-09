"""
WhatsApp Webhook Message Ingestion and Processing Service.

Connects incoming Meta webhook events to the internal Customers and Conversations domain:
1. Extracts sender phone number, display name, message timestamp, and message ID.
2. Identifies customer profiles via `CustomerService.get_or_create_customer`.
3. Finds or initiates active conversation threads via
   `ConversationService.get_or_create_active_conversation`.
4. Persists message records via `MessageService.append_message` with
   `whatsapp_message_id` deduplication.
5. `dispatch_ai_turn`: Invokes LangGraph AI Agent to process customer inquiries, execute
   commerce tools, and dispatch outbound WhatsApp replies.
"""

import uuid
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.whatsapp import WhatsAppClient
from app.modules.ai.factory import get_chat_model
from app.modules.ai.graph import build_agent_graph
from app.modules.ai.tools import create_agent_tools
from app.modules.conversations.models import (
    ConversationChannel,
    Message,
    MessageContentType,
    MessageDirection,
    MessageSenderType,
)
from app.modules.conversations.schemas import MessageCreate
from app.modules.conversations.service import ConversationService, MessageService
from app.modules.customers.service import CustomerService
from app.modules.messaging.schemas import (
    WhatsAppIncomingMessage,
    WhatsAppWebhookPayload,
)
from app.modules.organizations.models import Organization


class MessagingService:
    """Service processing raw Meta WhatsApp webhook payloads."""

    @staticmethod
    async def resolve_organization_by_phone_id(
        session: AsyncSession,
        phone_number_id: str | None = None,
    ) -> uuid.UUID | None:
        """
        Resolves the merchant organization UUID mapped to a Meta Phone Number ID.

        Falls back to the primary organization if only one tenant is active.
        """
        # Query first available organization as default tenant fallback
        query = select(Organization.id).order_by(Organization.created_at.asc()).limit(1)
        return (await session.execute(query)).scalar_one_or_none()

    @staticmethod
    def extract_text_content(msg: WhatsAppIncomingMessage) -> tuple[str, MessageContentType]:
        """
        Extracts human-readable body text and content type from an incoming message.
        """
        if msg.type == "text" and msg.text:
            return msg.text.body, MessageContentType.TEXT

        if msg.type == "interactive" and msg.interactive and msg.interactive.button_reply:
            return msg.interactive.button_reply.title, MessageContentType.INTERACTIVE

        # Fallback for images or media
        return f"[{msg.type.upper()}]", MessageContentType.TEXT

    @classmethod
    async def process_incoming_payload(
        cls,
        session: AsyncSession,
        organization_id: uuid.UUID,
        payload: WhatsAppWebhookPayload | dict[str, Any],
        trigger_ai: bool = False,
        whatsapp_client: WhatsAppClient | None = None,
        model: BaseChatModel | None = None,
    ) -> list[Message]:
        """
        Processes an unpacked Meta webhook payload:
        - Extracts all incoming messages.
        - Synchronizes customer profiles.
        - Appends inbound messages with deduplication.
        - Optionally triggers the LangGraph AI agent.

        Returns:
            list[Message]: List of newly saved or deduplicated Message instances.
        """
        # Ensure payload is parsed as Pydantic model
        if isinstance(payload, dict):
            parsed_payload = WhatsAppWebhookPayload.model_validate(payload)
        else:
            parsed_payload = payload

        saved_messages: list[Message] = []
        last_conversation_id: uuid.UUID | None = None
        last_customer_id: uuid.UUID | None = None
        last_text_body: str = ""

        for entry in parsed_payload.entry:
            for change in entry.changes:
                value = change.value
                # Map sender wa_id to contact name
                contacts_map: dict[str, str] = {}
                for contact in value.contacts:
                    if contact.profile and contact.profile.name:
                        contacts_map[contact.wa_id] = contact.profile.name

                for incoming_msg in value.messages:
                    raw_phone = incoming_msg.from_
                    # Ensure E.164 leading '+'
                    phone_number = f"+{raw_phone}" if not raw_phone.startswith("+") else raw_phone
                    sender_name = contacts_map.get(raw_phone)

                    # 1. Look up or register Customer
                    customer, _ = await CustomerService.get_or_create_customer(
                        session=session,
                        organization_id=organization_id,
                        phone_number=phone_number,
                        name=sender_name,
                    )

                    # 2. Get or create active Conversation
                    conversation, _ = await ConversationService.get_or_create_active_conversation(
                        session=session,
                        organization_id=organization_id,
                        customer_id=customer.id,
                        channel=ConversationChannel.WHATSAPP,
                    )

                    # 3. Extract text content & type
                    text_body, content_type = cls.extract_text_content(incoming_msg)

                    # 4. Append message to conversation with deduplication
                    msg_create = MessageCreate(
                        sender_type=MessageSenderType.CUSTOMER,
                        direction=MessageDirection.INBOUND,
                        content_type=content_type,
                        text_body=text_body,
                        whatsapp_message_id=incoming_msg.id,
                        raw_payload=incoming_msg.model_dump(),
                    )
                    message, was_inserted = await MessageService.append_message(
                        session=session,
                        organization_id=organization_id,
                        conversation_id=conversation.id,
                        request=msg_create,
                    )
                    saved_messages.append(message)

                    if was_inserted:
                        last_conversation_id = conversation.id
                        last_customer_id = customer.id
                        last_text_body = text_body

        await session.flush()

        # Trigger AI agent if requested and new messages arrived
        if trigger_ai and last_conversation_id and last_customer_id and last_text_body:
            await cls.dispatch_ai_turn(
                session=session,
                organization_id=organization_id,
                conversation_id=last_conversation_id,
                customer_id=last_customer_id,
                incoming_text=last_text_body,
                whatsapp_client=whatsapp_client,
                model=model,
            )

        return saved_messages

    @classmethod
    async def dispatch_ai_turn(
        cls,
        session: AsyncSession,
        organization_id: uuid.UUID,
        conversation_id: uuid.UUID,
        customer_id: uuid.UUID,
        incoming_text: str,
        whatsapp_client: WhatsAppClient | None = None,
        model: BaseChatModel | None = None,
    ) -> str | None:
        """
        Executes a single AI conversational turn via LangGraph:
        1. Checks whether conversation.is_ai_active is True (respects human takeover).
        2. Retrieves organization metadata (brand name, currency).
        3. Retrieves conversation transcript history.
        4. Binds multi-tenant tools (catalog, details, orders, handoff).
        5. Executes compiled LangGraph agent state machine.
        6. Appends outbound message to database.
        7. Dispatches WhatsApp text message to customer phone via WhatsAppClient.
        """
        # 1. Check human takeover flag
        conversation = await ConversationService.get_conversation(
            session=session,
            organization_id=organization_id,
            conversation_id=conversation_id,
        )
        if not conversation.is_ai_active:
            return None

        # 2. Get organization metadata
        org_query = select(Organization).where(Organization.id == organization_id)
        org = (await session.execute(org_query)).scalar_one_or_none()
        merchant_name = org.name if org else "Our Store"

        # 3. Load recent chat history for context
        history_items, _ = await MessageService.list_messages(
            session=session,
            organization_id=organization_id,
            conversation_id=conversation_id,
            page_size=20,
        )

        lang_messages: list[BaseMessage] = []
        for msg in history_items:
            if msg.direction == MessageDirection.INBOUND:
                lang_messages.append(HumanMessage(content=msg.text_body))
            elif msg.direction == MessageDirection.OUTBOUND:
                lang_messages.append(AIMessage(content=msg.text_body))

        # Ensure latest incoming message is present in context
        if not lang_messages or lang_messages[-1].content != incoming_text:
            lang_messages.append(HumanMessage(content=incoming_text))

        # 4. Construct tenant-scoped tools & compiled LangGraph agent
        tools = create_agent_tools(
            session=session,
            organization_id=organization_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
        )
        llm = model or get_chat_model()
        graph = build_agent_graph(model=llm, tools=tools)

        # 5. Execute LangGraph State Machine
        state_input = {
            "messages": lang_messages,
            "organization_id": organization_id,
            "customer_id": customer_id,
            "conversation_id": conversation_id,
            "merchant_name": merchant_name,
            "currency": "USD",
        }
        result = await graph.ainvoke(state_input)
        ai_reply = str(result.get("final_response", "")).strip()

        # 6. Save outbound response to DB & send to WhatsApp
        if ai_reply:
            outbound_msg_create = MessageCreate(
                sender_type=MessageSenderType.AI_AGENT,
                direction=MessageDirection.OUTBOUND,
                content_type=MessageContentType.TEXT,
                text_body=ai_reply,
            )
            await MessageService.append_message(
                session=session,
                organization_id=organization_id,
                conversation_id=conversation_id,
                request=outbound_msg_create,
            )

            # Send via WhatsApp client
            client = whatsapp_client or WhatsAppClient()
            customer = await CustomerService.get_customer(
                session=session,
                organization_id=organization_id,
                customer_id=customer_id,
            )
            try:
                await client.send_text_message(
                    to=customer.phone_number,
                    text=ai_reply,
                )
            except Exception:
                # Delivery error logged without failing DB state
                pass

        return ai_reply
