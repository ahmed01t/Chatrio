"""
Unit tests for AI Agent Tools.

Validates:
1. search_catalog: Scoped strictly to merchant tenant, returns price & stock.
2. search_catalog: Cross-tenant isolation (foreign tenant products are invisible).
3. get_product_details: Fetches specifications and category metadata.
4. draft_order: Deterministic price calculation directly from DB & stock deduction.
5. draft_order: Handles out-of-stock / insufficient stock gracefully.
6. request_human_agent: Successfully sets is_ai_active = False.
"""

import json
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.ai.tools import create_agent_tools
from app.modules.conversations.models import ConversationChannel
from app.modules.conversations.service import ConversationService
from app.modules.customers.service import CustomerService
from app.modules.organizations.models import Organization
from app.modules.products.schemas import ProductCreate
from app.modules.products.service import ProductService


@pytest.fixture
async def setup_tenant_and_customer(async_db_engine):
    """Sets up an organization, customer, and active conversation."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        org = Organization(
            id=uuid.uuid4(),
            name="AI Tools Test Store",
            slug=f"ai-tools-{uuid.uuid4().hex[:8]}",
        )
        session.add(org)
        await session.flush()

        customer, _ = await CustomerService.get_or_create_customer(
            session=session,
            organization_id=org.id,
            phone_number="+15550001111",
            name="David Miller",
        )

        conversation, _ = await ConversationService.get_or_create_active_conversation(
            session=session,
            organization_id=org.id,
            customer_id=customer.id,
            channel=ConversationChannel.WHATSAPP,
        )

        # Create a test product
        product = await ProductService.create_product(
            session=session,
            organization_id=org.id,
            request=ProductCreate(
                title="Organic Green Apples",
                sku="APPLE-ORG-01",
                price=Decimal("4.50"),
                currency="USD",
                stock_quantity=10,
                is_active=True,
                category_ids=[],
            ),
        )

        await session.commit()
        return org, customer, conversation, product


@pytest.mark.asyncio
async def test_search_catalog_tool(async_db_engine, setup_tenant_and_customer) -> None:
    """Verify search_catalog finds matching active products within the tenant."""
    org, customer, conversation, product = setup_tenant_and_customer
    session_factory = async_sessionmaker(bind=async_db_engine, class_=AsyncSession)

    async with session_factory() as session:
        tools = create_agent_tools(
            session=session,
            organization_id=org.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
        )
        search_tool = next(t for t in tools if t.name == "search_catalog")

        # Search matching keyword
        raw_res = await search_tool.ainvoke({"query": "Apples"})
        data = json.loads(raw_res)

        assert "results" in data
        assert len(data["results"]) == 1
        res_item = data["results"][0]
        assert res_item["title"] == "Organic Green Apples"
        assert res_item["price"] == "4.50"
        assert res_item["in_stock"] is True
        assert res_item["available_quantity"] == 10


@pytest.mark.asyncio
async def test_search_catalog_cross_tenant_isolation(
    async_db_engine,
    setup_tenant_and_customer,
) -> None:
    """Verify foreign tenant products are never visible in search results."""
    org, customer, conversation, _ = setup_tenant_and_customer
    session_factory = async_sessionmaker(bind=async_db_engine, class_=AsyncSession)

    # Create a competitor organization and product
    async with session_factory() as session:
        other_org = Organization(
            id=uuid.uuid4(),
            name="Competitor Shop",
            slug=f"comp-{uuid.uuid4().hex[:8]}",
        )
        session.add(other_org)
        await session.flush()

        await ProductService.create_product(
            session=session,
            organization_id=other_org.id,
            request=ProductCreate(
                title="Competitor Secret Apples",
                sku="COMP-APPLES-01",
                price=Decimal("1.00"),
                currency="USD",
                stock_quantity=50,
                is_active=True,
                category_ids=[],
            ),
        )
        await session.commit()

    # Search from our organization
    async with session_factory() as session:
        tools = create_agent_tools(
            session=session,
            organization_id=org.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
        )
        search_tool = next(t for t in tools if t.name == "search_catalog")
        raw_res = await search_tool.ainvoke({"query": "Competitor"})
        data = json.loads(raw_res)

        assert len(data.get("results", [])) == 0


@pytest.mark.asyncio
async def test_get_product_details_tool(
    async_db_engine,
    setup_tenant_and_customer,
) -> None:
    """Verify get_product_details returns comprehensive product specs."""
    org, customer, conversation, product = setup_tenant_and_customer
    session_factory = async_sessionmaker(bind=async_db_engine, class_=AsyncSession)

    async with session_factory() as session:
        tools = create_agent_tools(
            session=session,
            organization_id=org.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
        )
        details_tool = next(t for t in tools if t.name == "get_product_details")

        raw_res = await details_tool.ainvoke({"product_id": str(product.id)})
        data = json.loads(raw_res)

        assert data["title"] == "Organic Green Apples"
        assert data["price"] == "4.50"
        assert data["sku"] == "APPLE-ORG-01"
        assert data["stock_quantity"] == 10
        assert data["in_stock"] is True


@pytest.mark.asyncio
async def test_draft_order_tool_success(
    async_db_engine,
    setup_tenant_and_customer,
) -> None:
    """Verify draft_order creates an order, calculates DB prices, and locks inventory."""
    org, customer, conversation, product = setup_tenant_and_customer
    session_factory = async_sessionmaker(bind=async_db_engine, class_=AsyncSession)

    async with session_factory() as session:
        tools = create_agent_tools(
            session=session,
            organization_id=org.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
        )
        order_tool = next(t for t in tools if t.name == "draft_order")

        raw_res = await order_tool.ainvoke(
            {
                "items": [{"product_id": str(product.id), "quantity": 2}],
                "delivery_address": "742 Evergreen Terrace",
                "notes": "Leave at front door",
            }
        )
        await session.commit()
        data = json.loads(raw_res)

        assert "order_id" in data
        assert data["status"] == "PENDING"
        # 2 units * $4.50 = $9.00
        assert data["subtotal"] == "9.00"
        assert data["total"] == "9.00"
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 2
        assert data["items"][0]["unit_price"] == "4.50"

        # Verify stock was reduced from 10 to 8
        refreshed_prod = await ProductService.get_product(session, org.id, product.id)
        assert refreshed_prod.stock_quantity == 8


@pytest.mark.asyncio
async def test_draft_order_insufficient_stock(
    async_db_engine,
    setup_tenant_and_customer,
) -> None:
    """Verify draft_order rejects order when requested quantity exceeds available stock."""
    org, customer, conversation, product = setup_tenant_and_customer
    session_factory = async_sessionmaker(bind=async_db_engine, class_=AsyncSession)

    async with session_factory() as session:
        tools = create_agent_tools(
            session=session,
            organization_id=org.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
        )
        order_tool = next(t for t in tools if t.name == "draft_order")

        # Request 99 units (only 10 in stock)
        raw_res = await order_tool.ainvoke(
            {"items": [{"product_id": str(product.id), "quantity": 99}]}
        )
        data = json.loads(raw_res)

        assert "error" in data
        assert "insufficient" in data["error"].lower()


@pytest.mark.asyncio
async def test_request_human_agent_tool(
    async_db_engine,
    setup_tenant_and_customer,
) -> None:
    """Verify request_human_agent tool switches conversation.is_ai_active to False."""
    org, customer, conversation, _ = setup_tenant_and_customer
    session_factory = async_sessionmaker(bind=async_db_engine, class_=AsyncSession)

    async with session_factory() as session:
        tools = create_agent_tools(
            session=session,
            organization_id=org.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
        )
        handoff_tool = next(t for t in tools if t.name == "request_human_agent")

        raw_res = await handoff_tool.ainvoke({"reason": "Customer is requesting a human manager"})
        await session.commit()
        data = json.loads(raw_res)

        assert data["status"] == "human_takeover_activated"

        # Check in DB that is_ai_active is now False
        refreshed_conv = await ConversationService.get_conversation(
            session, org.id, conversation.id
        )
        assert refreshed_conv.is_ai_active is False
