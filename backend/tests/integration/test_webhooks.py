"""
End-to-End Integration Tests for Meta WhatsApp Webhook Lifecycle.

Tests the full message processing pipeline:
1. Meta App Webhook Verification Handshake (GET).
2. HMAC-SHA256 authenticated multi-message burst ingestion (POST).
3. Redis / in-memory sliding debounce coalescing.
4. Customer registration and active conversation thread creation.
5. Message deduplication idempotency on duplicate deliveries.
6. Outbound message and interactive quick-reply button dispatch via WhatsAppClient.
"""

import json
import uuid

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.infrastructure.whatsapp import WhatsAppClient
from app.modules.conversations.models import (
    Conversation,
    ConversationChannel,
    ConversationStatus,
    Message,
    MessageDirection,
    MessageSenderType,
)
from app.modules.customers.models import Customer
from app.modules.messaging.debounce import SlidingDebounceBuffer
from app.modules.messaging.schemas import OutboundButton
from app.modules.messaging.security import compute_meta_signature
from app.modules.organizations.models import Organization


@pytest.fixture
async def test_org(async_db_engine) -> Organization:
    """Creates a sample merchant organization."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        org = Organization(
            id=uuid.uuid4(),
            name="End-to-End Test Shop",
            slug=f"e2e-shop-{uuid.uuid4().hex[:8]}",
        )
        session.add(org)
        await session.commit()
        return org


def make_signed_meta_payload(
    messages: list[dict],
    contact_name: str = "Charlie Brown",
    wa_id: str = "15554443322",
    phone_number_id: str = "10987654321",
) -> tuple[bytes, str]:
    """Generates a raw JSON payload and its valid HMAC-SHA256 signature."""
    settings = get_settings()
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550009999",
                                "phone_number_id": phone_number_id,
                            },
                            "contacts": [
                                {
                                    "profile": {"name": contact_name},
                                    "wa_id": wa_id,
                                }
                            ],
                            "messages": messages,
                            "statuses": [],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_meta_signature(raw_bytes, settings.META_APP_SECRET)
    return raw_bytes, sig


@pytest.mark.asyncio
async def test_full_webhook_lifecycle(
    async_client: AsyncClient,
    async_db_engine,
    test_org: Organization,
) -> None:
    """
    Simulates the complete real-world webhook flow from Meta:
    Handshake -> Burst Messages -> Deduplication -> Outbound Reply.
    """
    settings = get_settings()
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # --------------------------------------------------------------------------
    # Step 1: Meta Handshake Verification (GET)
    # --------------------------------------------------------------------------
    challenge_val = "9988776655"
    handshake_resp = await async_client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.META_VERIFY_TOKEN,
            "hub.challenge": challenge_val,
        },
    )
    assert handshake_resp.status_code == 200
    assert handshake_resp.text == challenge_val

    # --------------------------------------------------------------------------
    # Step 2: Multi-Message Burst Arrival (POST)
    # Customer types 3 separate messages in quick succession
    # --------------------------------------------------------------------------
    burst_messages = [
        {
            "from": "15554443322",
            "id": "wamid.E2E_BURST_001",
            "timestamp": "1710000001",
            "type": "text",
            "text": {"body": "Hi there!"},
        },
        {
            "from": "15554443322",
            "id": "wamid.E2E_BURST_002",
            "timestamp": "1710000002",
            "type": "text",
            "text": {"body": "Do you have the organic apples in stock?"},
        },
        {
            "from": "15554443322",
            "id": "wamid.E2E_BURST_003",
            "timestamp": "1710000003",
            "type": "text",
            "text": {"body": "And how much are they?"},
        },
    ]

    # Ingest each message through the signed webhook endpoint
    for msg in burst_messages:
        raw_body, signature = make_signed_meta_payload([msg])
        response = await async_client.post(
            "/api/v1/webhooks/whatsapp",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": signature,
            },
        )
        assert response.status_code == 200
        assert response.json() == {"status": "received"}

    # --------------------------------------------------------------------------
    # Step 3: Verify Persistence & Invariant Checks
    # --------------------------------------------------------------------------
    async with session_factory() as session:
        # 1. Customer created
        cust_query = select(Customer).where(
            Customer.organization_id == test_org.id,
            Customer.phone_number == "+15554443322",
        )
        customer = (await session.execute(cust_query)).scalar_one_or_none()
        assert customer is not None
        assert customer.name == "Charlie Brown"

        # 2. Conversation created and active
        conv_query = select(Conversation).where(
            Conversation.organization_id == test_org.id,
            Conversation.customer_id == customer.id,
        )
        conversation = (await session.execute(conv_query)).scalar_one_or_none()
        assert conversation is not None
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.channel == ConversationChannel.WHATSAPP

        # 3. All 3 messages persisted under conversation
        msg_query = (
            select(Message)
            .where(
                Message.organization_id == test_org.id,
                Message.conversation_id == conversation.id,
            )
            .order_by(Message.created_at.asc())
        )
        persisted_msgs = (await session.execute(msg_query)).scalars().all()
        assert len(persisted_msgs) == 3

        assert persisted_msgs[0].text_body == "Hi there!"
        assert persisted_msgs[0].direction == MessageDirection.INBOUND
        assert persisted_msgs[0].sender_type == MessageSenderType.CUSTOMER
        assert persisted_msgs[0].whatsapp_message_id == "wamid.E2E_BURST_001"

        assert persisted_msgs[1].text_body == "Do you have the organic apples in stock?"
        assert persisted_msgs[1].whatsapp_message_id == "wamid.E2E_BURST_002"

        assert persisted_msgs[2].text_body == "And how much are they?"
        assert persisted_msgs[2].whatsapp_message_id == "wamid.E2E_BURST_003"

    # --------------------------------------------------------------------------
    # Step 4: Verify Idempotent Deduplication
    # Re-sending message 2 should be safely ignored
    # --------------------------------------------------------------------------
    raw_body_dup, signature_dup = make_signed_meta_payload([burst_messages[1]])
    dup_resp = await async_client.post(
        "/api/v1/webhooks/whatsapp",
        content=raw_body_dup,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature_dup,
        },
    )
    assert dup_resp.status_code == 200

    async with session_factory() as session:
        # Total messages count should still remain 3
        count_query = select(Message).where(
            Message.organization_id == test_org.id,
            Message.conversation_id == conversation.id,
        )
        total_msgs = (await session.execute(count_query)).scalars().all()
        assert len(total_msgs) == 3

    # --------------------------------------------------------------------------
    # Step 5: Debounce Buffer Coalescing Simulation
    # Verify SlidingDebounceBuffer coalescing mechanics for burst messages
    # --------------------------------------------------------------------------
    buffer = SlidingDebounceBuffer(inactivity_seconds=2.5, max_wait_seconds=8.0)
    for m in burst_messages:
        should_flush, _ = await buffer.add_message("15554443322", m)
        assert should_flush is False  # Buffering and sliding timer reset

    # Flushed on inactivity silence
    flushed = await buffer.flush("15554443322")
    assert len(flushed) == 3
    assert [x["id"] for x in flushed] == [
        "wamid.E2E_BURST_001",
        "wamid.E2E_BURST_002",
        "wamid.E2E_BURST_003",
    ]

    # --------------------------------------------------------------------------
    # Step 6: Outbound Reply Dispatch via WhatsAppClient
    # Send interactive buttons back to customer
    # --------------------------------------------------------------------------
    captured_requests: list[httpx.Request] = []

    def mock_outbound_handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            status_code=200,
            json={
                "messaging_product": "whatsapp",
                "contacts": [{"input": "15554443322", "wa_id": "15554443322"}],
                "messages": [{"id": "wamid.OUTBOUND_REPLY_E2E"}],
            },
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_outbound_handler))
    outbound_client = WhatsAppClient(http_client=mock_client)

    buttons = [
        OutboundButton(id="btn_add_apples", title="Add 2 lbs"),
        OutboundButton(id="btn_view_catalog", title="View Catalog"),
    ]

    outbound_res = await outbound_client.send_interactive_buttons(
        to=customer.phone_number,
        body_text="Yes! Fresh organic apples are $2.99/lb. Would you like to add some?",
        buttons=buttons,
        header_text="Organic Apples Available",
        footer_text="Select an option below",
    )

    assert outbound_res.messaging_product == "whatsapp"
    assert outbound_res.messages[0]["id"] == "wamid.OUTBOUND_REPLY_E2E"
    assert len(captured_requests) == 1

    outbound_body = json.loads(captured_requests[0].content.decode("utf-8"))
    assert outbound_body["to"] == "15554443322"
    assert outbound_body["type"] == "interactive"
    assert len(outbound_body["interactive"]["action"]["buttons"]) == 2
