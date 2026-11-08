import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import (
    Base,
    Customer,
    Order,
    OrderItem,
    OrderStatus,
    Organization,
    PaymentStatus,
    Product,
)


def test_orders_metadata_registration() -> None:
    """Verify that orders and order_items tables are registered in Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {"orders", "order_items"}

    assert expected_tables.issubset(table_names), (
        f"Expected tables {expected_tables} in Base.metadata, found: {table_names}"
    )


def test_order_table_constraints() -> None:
    """Verify unique constraint on (organization_id, order_number) and columns for orders."""
    order_table = Base.metadata.tables["orders"]
    cols = order_table.columns

    assert "id" in cols
    assert cols["id"].primary_key is True
    assert "organization_id" in cols
    assert "customer_id" in cols
    assert "conversation_id" in cols
    assert "order_number" in cols
    assert "status" in cols
    assert "payment_status" in cols
    assert "currency" in cols
    assert "subtotal" in cols
    assert "shipping_cost" in cols
    assert "total_amount" in cols
    assert "shipping_address" in cols
    assert "notes" in cols
    assert "metadata" in cols

    # Verify unique constraint on (organization_id, order_number)
    uq_names = [
        [c.name for c in uq.columns] for uq in order_table.constraints if hasattr(uq, "columns")
    ]
    assert ["organization_id", "order_number"] in uq_names


def test_order_item_table_constraints() -> None:
    """Verify columns and check constraints on order_items."""
    item_table = Base.metadata.tables["order_items"]
    cols = item_table.columns

    assert "id" in cols
    assert cols["id"].primary_key is True
    assert "organization_id" in cols
    assert "order_id" in cols
    assert "product_id" in cols
    assert "product_title" in cols
    assert "product_sku" in cols
    assert "unit_price" in cols
    assert "quantity" in cols
    assert "total_price" in cols


@pytest.mark.asyncio
async def test_order_and_items_crud_in_memory() -> None:
    """Verify in-memory creation and relationships for Order and OrderItem."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()
    order_id = uuid.uuid4()
    item_id = uuid.uuid4()

    async with session_factory() as session:
        org = Organization(id=org_id, name="Store 1", slug="store-1")
        customer = Customer(
            id=cust_id,
            organization_id=org_id,
            phone_number="+1234567890",
            name="John Doe",
        )
        product = Product(
            id=prod_id,
            organization_id=org_id,
            title="Sneakers",
            sku="SNK-001",
            price=Decimal("99.99"),
            stock_quantity=50,
        )
        order = Order(
            id=order_id,
            organization_id=org_id,
            customer_id=cust_id,
            order_number="ORD-20261108-0001",
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.UNPAID,
            currency="USD",
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("10.00"),
            total_amount=Decimal("109.99"),
            shipping_address="123 Main St, New York, NY",
            notes="Please leave at the door",
        )
        item = OrderItem(
            id=item_id,
            organization_id=org_id,
            order_id=order_id,
            product_id=prod_id,
            product_title="Sneakers",
            product_sku="SNK-001",
            unit_price=Decimal("99.99"),
            quantity=1,
            total_price=Decimal("99.99"),
        )

        session.add_all([org, customer, product, order, item])
        await session.commit()

    # Query back
    async with session_factory() as session:
        saved_order = await session.get(Order, order_id)
        assert saved_order is not None
        assert saved_order.order_number == "ORD-20261108-0001"
        assert saved_order.status == OrderStatus.PENDING
        assert saved_order.payment_status == PaymentStatus.UNPAID
        assert saved_order.total_amount == Decimal("109.99")
        assert len(saved_order.items) == 1
        assert saved_order.items[0].product_sku == "SNK-001"
        assert saved_order.items[0].quantity == 1

    await engine.dispose()
