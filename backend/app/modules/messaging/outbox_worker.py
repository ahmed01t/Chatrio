"""
Outbox Worker Engine for Reliable WhatsApp Message Delivery.

Processes pending outbox messages in batches:
1. Validates Meta 24-hour customer care policy window.
2. Dispatches payload via `WhatsAppClient`.
3. Handles transient failures with exponential backoff.
4. Transitions outbox messages to SENT or FAILED.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.whatsapp import WhatsAppClient
from app.modules.messaging.models import (
    OutboxMessage,
    OutboxMessageType,
)
from app.modules.messaging.outbox_service import OutboxService
from app.modules.messaging.schemas import OutboundButton

logger = logging.getLogger(__name__)


class OutboxWorker:
    """Asynchronous worker executing reliable outbox message delivery."""

    @classmethod
    async def deliver_message(
        cls,
        session: AsyncSession,
        outbox_msg: OutboxMessage,
        whatsapp_client: WhatsAppClient,
    ) -> bool:
        """
        Processes and dispatches a single outbox message.

        Steps:
        1. Check Meta 24-hour customer care policy window.
           If expired and not a template, mark FAILED without calling Meta.
        2. Transition status to SENDING.
        3. Dispatch to WhatsApp Cloud API.
        4. On success: Mark SENT.
        5. On temporary failure: Increment retry count and schedule exponential backoff.
        """
        # 1. Enforce 24-hour policy window
        policy = await OutboxService.check_24h_policy_window(
            session=session,
            conversation_id=outbox_msg.conversation_id,
            message_type=outbox_msg.message_type,
        )
        if not policy.is_permitted:
            reason = policy.violation_reason or "POLICY_VIOLATION_UNKNOWN"
            logger.warning(
                "Outbox message %s blocked by Meta policy: %s",
                outbox_msg.id,
                reason,
            )
            await OutboxService.mark_as_failed(
                session=session,
                outbox_id=outbox_msg.id,
                reason=reason,
            )
            return False

        # 2. Mark SENDING
        await OutboxService.mark_as_sending(session=session, outbox_id=outbox_msg.id)

        # 3. Dispatch to WhatsApp
        payload = outbox_msg.payload
        try:
            if outbox_msg.message_type == OutboxMessageType.TEXT:
                text_content = payload.get("body") or payload.get("text") or ""
                await whatsapp_client.send_text_message(
                    to=outbox_msg.recipient_phone,
                    text=text_content,
                )

            elif outbox_msg.message_type == OutboxMessageType.INTERACTIVE:
                raw_buttons = payload.get("buttons", [])
                typed_buttons = [
                    OutboundButton(
                        id=str(btn.get("id", i)),
                        title=str(btn.get("title", "")),
                    )
                    for i, btn in enumerate(raw_buttons)
                ]
                await whatsapp_client.send_interactive_buttons(
                    to=outbox_msg.recipient_phone,
                    body_text=payload.get("body", ""),
                    buttons=typed_buttons,
                    header_text=payload.get("header_text"),
                    footer_text=payload.get("footer_text"),
                )

            elif outbox_msg.message_type == OutboxMessageType.TEMPLATE:
                template_name = payload.get("template_name", "")
                language_code = payload.get("language", "en_US")
                components: list[dict[str, Any]] = payload.get("components", [])
                await whatsapp_client.send_template(
                    to=outbox_msg.recipient_phone,
                    template_name=template_name,
                    language_code=language_code,
                    components=components,
                )

            # 4. Mark SENT
            await OutboxService.mark_as_sent(session=session, outbox_id=outbox_msg.id)
            return True

        except Exception as exc:
            # 5. Transient failure -> schedule exponential backoff retry
            logger.exception(
                "Temporary delivery failure for outbox message %s: %s",
                outbox_msg.id,
                exc,
            )
            await OutboxService.schedule_retry(
                session=session,
                outbox_id=outbox_msg.id,
                error_message=str(exc),
            )
            return False

    @classmethod
    async def process_batch(
        cls,
        session: AsyncSession,
        batch_size: int = 20,
        whatsapp_client: WhatsAppClient | None = None,
    ) -> int:
        """
        Polls and delivers a batch of pending outbox messages.

        Returns:
            int: Number of messages successfully delivered.
        """
        pending_batch = await OutboxService.fetch_pending_batch(
            session=session,
            batch_size=batch_size,
        )
        if not pending_batch:
            return 0

        client = whatsapp_client or WhatsAppClient()
        success_count = 0

        for msg in pending_batch:
            delivered = await cls.deliver_message(
                session=session,
                outbox_msg=msg,
                whatsapp_client=client,
            )
            if delivered:
                success_count += 1
            await session.commit()

        return success_count
