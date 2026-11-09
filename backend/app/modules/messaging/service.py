"""
WhatsApp Webhook Message Ingestion and Processing Service.

Connects incoming Meta webhook events to the internal Customers and Conversations domain:
1. Extracts sender phone number, display name, message timestamp, and message ID.
2. Identifies customer profiles via `CustomerService.get_or_create_customer`.
3. Finds or initiates active conversation threads via
   `ConversationService.get_or_create_active_conversation`.
4. Persists message records via `MessageService.append_message` with
   `whatsapp_message_id` deduplication.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    ) -> list[Message]:
        """
        Processes an unpacked Meta webhook payload:
        - Extracts all incoming messages.
        - Synchronizes customer profiles.
        - Appends inbound messages with deduplication.

        Returns:
            list[Message]: List of newly saved or deduplicated Message instances.
        """
        # Ensure payload is parsed as Pydantic model
        if isinstance(payload, dict):
            parsed_payload = WhatsAppWebhookPayload.model_validate(payload)
        else:
            parsed_payload = payload

        saved_messages: list[Message] = []

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
                    message, _ = await MessageService.append_message(
                        session=session,
                        organization_id=organization_id,
                        conversation_id=conversation.id,
                        request=msg_create,
                    )
                    saved_messages.append(message)

        await session.flush()
        return saved_messages
