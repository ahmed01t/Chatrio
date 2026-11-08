import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.exceptions import BadRequestException
from app.db.models import Base, Customer, Organization, Product
from app.modules.orders.models import OrderStatus, PaymentStatus
from app.modules.orders.schemas import (
    OrderCreate,
    OrderItemCreate,
    OrderStatusUpdate,
    OrderUpdate,
)
from app.modules.orders.service import OrderService


@pytest.fixture
async def async_test_session() -> AsyncGenerator[AsyncSession, None]:
    """Creates an in-memory SQLite database and yields an active session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_order_creation_happy_path(async_test_session: AsyncSession) -> None:
    """Verify atomic order creation, stock deduction, and historical price snapshotting."""
    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    org = Organization(id=org_id, name="Shoe Store", slug="shoe-store")
    customer = Customer(
        id=cust_id,
        organization_id=org_id,
        phone_number="+15550001111",
        name="Bob Smith",
    )
    product = Product(
        id=prod_id,
        organization_id=org_id,
        title="Trail Runners",
        sku="TR-001",
        price=Decimal("120.00"),
        stock_quantity=10,
        is_active=True,
    )
    async_test_session.add_all([org, customer, product])
    await async_test_session.commit()

    order_req = OrderCreate(
        customer_id=cust_id,
        items=[OrderItemCreate(product_id=prod_id, quantity=2)],
        shipping_cost=Decimal("10.00"),
        shipping_address="789 Forest Rd",
        notes="Leave on porch",
    )

    order = await OrderService.create_order(async_test_session, org_id, order_req)
    await async_test_session.commit()

    # Assert order fields
    assert order.customer_id == cust_id
    assert order.status == OrderStatus.PENDING
    assert order.payment_status == PaymentStatus.UNPAID
    assert order.subtotal == Decimal("240.00")
    assert order.shipping_cost == Decimal("10.00")
    assert order.total_amount == Decimal("250.00")
    assert order.order_number.startswith("ORD-")
    assert len(order.items) == 1

    # Assert line item historical snapshot
    item = order.items[0]
    assert item.product_id == prod_id
    assert item.product_title == "Trail Runners"
    assert item.product_sku == "TR-001"
    assert item.unit_price == Decimal("120.00")
    assert item.quantity == 2
    assert item.total_price == Decimal("240.00")

    # Assert stock deduction: 10 - 2 = 8
    updated_product = await async_test_session.get(Product, prod_id)
    assert updated_product is not None
    assert updated_product.stock_quantity == 8


@pytest.mark.asyncio
async def test_order_creation_insufficient_stock(async_test_session: AsyncSession) -> None:
    """Verify order creation fails if requested quantity exceeds available stock."""
    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    org = Organization(id=org_id, name="Shoe Store", slug="shoe-store-2")
    customer = Customer(
        id=cust_id,
        organization_id=org_id,
        phone_number="+15550002222",
        name="Alice",
    )
    product = Product(
        id=prod_id,
        organization_id=org_id,
        title="Hiking Boots",
        sku="HB-001",
        price=Decimal("150.00"),
        stock_quantity=2,  # Only 2 in stock
        is_active=True,
    )
    async_test_session.add_all([org, customer, product])
    await async_test_session.commit()

    order_req = OrderCreate(
        customer_id=cust_id,
        items=[OrderItemCreate(product_id=prod_id, quantity=5)],  # Requesting 5
    )

    with pytest.raises(BadRequestException) as exc_info:
        await OrderService.create_order(async_test_session, org_id, order_req)

    assert exc_info.value.code == "INSUFFICIENT_STOCK"

    # Stock must remain unchanged
    unmodified_product = await async_test_session.get(Product, prod_id)
    assert unmodified_product is not None
    assert unmodified_product.stock_quantity == 2


@pytest.mark.asyncio
async def test_order_creation_inactive_product(async_test_session: AsyncSession) -> None:
    """Verify order creation fails if product is inactive."""
    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    org = Organization(id=org_id, name="Shoe Store", slug="shoe-store-3")
    customer = Customer(
        id=cust_id,
        organization_id=org_id,
        phone_number="+15550003333",
        name="Charlie",
    )
    product = Product(
        id=prod_id,
        organization_id=org_id,
        title="Discontinued Boots",
        sku="DB-001",
        price=Decimal("50.00"),
        stock_quantity=10,
        is_active=False,  # Inactive
    )
    async_test_session.add_all([org, customer, product])
    await async_test_session.commit()

    order_req = OrderCreate(
        customer_id=cust_id,
        items=[OrderItemCreate(product_id=prod_id, quantity=1)],
    )

    with pytest.raises(BadRequestException) as exc_info:
        await OrderService.create_order(async_test_session, org_id, order_req)

    assert exc_info.value.code == "PRODUCT_INACTIVE"


@pytest.mark.asyncio
async def test_order_state_machine_valid_transitions(
    async_test_session: AsyncSession,
) -> None:
    """Verify sequential advancement through the order lifecycle state machine."""
    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    org = Organization(id=org_id, name="Shoe Store", slug="shoe-store-4")
    customer = Customer(
        id=cust_id,
        organization_id=org_id,
        phone_number="+15550004444",
        name="David",
    )
    product = Product(
        id=prod_id,
        organization_id=org_id,
        title="Sandals",
        sku="SAN-001",
        price=Decimal("40.00"),
        stock_quantity=20,
        is_active=True,
    )
    async_test_session.add_all([org, customer, product])
    await async_test_session.commit()

    order_req = OrderCreate(
        customer_id=cust_id,
        items=[OrderItemCreate(product_id=prod_id, quantity=1)],
    )
    order = await OrderService.create_order(async_test_session, org_id, order_req)
    await async_test_session.commit()
    assert order.status == OrderStatus.PENDING

    # 1. PENDING -> CONFIRMED
    order = await OrderService.update_status(
        async_test_session,
        org_id,
        order.id,
        OrderStatusUpdate(status=OrderStatus.CONFIRMED),
    )
    assert order.status == OrderStatus.CONFIRMED

    # 2. CONFIRMED -> PROCESSING
    order = await OrderService.update_status(
        async_test_session,
        org_id,
        order.id,
        OrderStatusUpdate(status=OrderStatus.PROCESSING),
    )
    assert order.status == OrderStatus.PROCESSING

    # 3. PROCESSING -> SHIPPED
    order = await OrderService.update_status(
        async_test_session,
        org_id,
        order.id,
        OrderStatusUpdate(status=OrderStatus.SHIPPED),
    )
    assert order.status == OrderStatus.SHIPPED

    # 4. SHIPPED -> DELIVERED
    order = await OrderService.update_status(
        async_test_session,
        org_id,
        order.id,
        OrderStatusUpdate(status=OrderStatus.DELIVERED),
    )
    assert order.status == OrderStatus.DELIVERED


@pytest.mark.asyncio
async def test_order_state_machine_invalid_transitions(
    async_test_session: AsyncSession,
) -> None:
    """Verify invalid state transitions are rejected with BadRequestException."""
    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    org = Organization(id=org_id, name="Shoe Store", slug="shoe-store-5")
    customer = Customer(
        id=cust_id,
        organization_id=org_id,
        phone_number="+15550005555",
        name="Eve",
    )
    product = Product(
        id=prod_id,
        organization_id=org_id,
        title="Slippers",
        sku="SLP-001",
        price=Decimal("25.00"),
        stock_quantity=10,
        is_active=True,
    )
    async_test_session.add_all([org, customer, product])
    await async_test_session.commit()

    order_req = OrderCreate(
        customer_id=cust_id,
        items=[OrderItemCreate(product_id=prod_id, quantity=1)],
    )
    order = await OrderService.create_order(async_test_session, org_id, order_req)
    await async_test_session.commit()
    assert order.status == OrderStatus.PENDING

    # Attempt illegal skip: PENDING -> DELIVERED
    with pytest.raises(BadRequestException) as exc_info:
        await OrderService.update_status(
            async_test_session,
            org_id,
            order.id,
            OrderStatusUpdate(status=OrderStatus.DELIVERED),
        )
    assert exc_info.value.code == "INVALID_ORDER_STATE_TRANSITION"


@pytest.mark.asyncio
async def test_order_cancellation_releases_inventory(
    async_test_session: AsyncSession,
) -> None:
    """Verify cancelling an order releases reserved stock back into inventory."""
    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    org = Organization(id=org_id, name="Shoe Store", slug="shoe-store-6")
    customer = Customer(
        id=cust_id,
        organization_id=org_id,
        phone_number="+15550006666",
        name="Frank",
    )
    product = Product(
        id=prod_id,
        organization_id=org_id,
        title="Running Socks",
        sku="SOX-001",
        price=Decimal("15.00"),
        stock_quantity=20,
        is_active=True,
    )
    async_test_session.add_all([org, customer, product])
    await async_test_session.commit()

    order_req = OrderCreate(
        customer_id=cust_id,
        items=[OrderItemCreate(product_id=prod_id, quantity=5)],
    )
    order = await OrderService.create_order(async_test_session, org_id, order_req)
    await async_test_session.commit()

    # Stock should be 20 - 5 = 15
    prod = await async_test_session.get(Product, prod_id)
    assert prod is not None
    assert prod.stock_quantity == 15

    # Cancel order
    cancelled_order = await OrderService.cancel_order(async_test_session, org_id, order.id)
    await async_test_session.commit()

    assert cancelled_order.status == OrderStatus.CANCELLED

    # Stock should be restored: 15 + 5 = 20
    prod_restored = await async_test_session.get(Product, prod_id)
    assert prod_restored is not None
    assert prod_restored.stock_quantity == 20

    # Second cancel attempt should raise error
    with pytest.raises(BadRequestException) as exc_info:
        await OrderService.cancel_order(async_test_session, org_id, order.id)
    assert exc_info.value.code == "ORDER_ALREADY_CANCELLED"


@pytest.mark.asyncio
async def test_order_update_and_listing(async_test_session: AsyncSession) -> None:
    """Verify order update and listing with pagination and filters."""
    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    org = Organization(id=org_id, name="Shoe Store", slug="shoe-store-7")
    customer = Customer(
        id=cust_id,
        organization_id=org_id,
        phone_number="+15550007777",
        name="Grace",
    )
    product = Product(
        id=prod_id,
        organization_id=org_id,
        title="Insoles",
        sku="INS-001",
        price=Decimal("18.00"),
        stock_quantity=50,
        is_active=True,
    )
    async_test_session.add_all([org, customer, product])
    await async_test_session.commit()

    order_req = OrderCreate(
        customer_id=cust_id,
        items=[OrderItemCreate(product_id=prod_id, quantity=1)],
        shipping_address="100 First St",
    )
    order = await OrderService.create_order(async_test_session, org_id, order_req)
    await async_test_session.commit()

    # Update address and payment status
    updated = await OrderService.update_order(
        async_test_session,
        org_id,
        order.id,
        OrderUpdate(
            shipping_address="200 Second St",
            payment_status=PaymentStatus.PAID,
            notes="Updated note",
        ),
    )
    assert updated.shipping_address == "200 Second St"
    assert updated.payment_status == PaymentStatus.PAID
    assert updated.notes == "Updated note"

    # List orders
    orders, total = await OrderService.list_orders(
        async_test_session,
        organization_id=org_id,
        payment_status=PaymentStatus.PAID,
    )
    assert total == 1
    assert len(orders) == 1
    assert orders[0].id == order.id

    # Filter with non-matching status
    orders_unpaid, total_unpaid = await OrderService.list_orders(
        async_test_session,
        organization_id=org_id,
        payment_status=PaymentStatus.UNPAID,
    )
    assert total_unpaid == 0
    assert len(orders_unpaid) == 0
