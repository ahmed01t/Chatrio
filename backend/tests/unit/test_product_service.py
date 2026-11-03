import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.db.models import Base, InventoryChangeReason, Organization
from app.modules.products.schemas import (
    CategoryCreate,
    CategoryUpdate,
    InventoryAdjustmentRequest,
    ProductCreate,
    ProductUpdate,
)
from app.modules.products.service import (
    CategoryService,
    InventoryService,
    ProductService,
)


@pytest.fixture
async def async_test_session() -> AsyncSession:
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
async def test_category_service_crud(async_test_session: AsyncSession) -> None:
    """Verify CategoryService creation, duplicate slug check, and hierarchy."""
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Store", slug="test-store")
    async_test_session.add(org)
    await async_test_session.commit()

    # Create root category
    cat_req = CategoryCreate(name="Apparel", slug="apparel")
    cat = await CategoryService.create_category(async_test_session, org_id, cat_req)
    assert cat.name == "Apparel"
    assert cat.slug == "apparel"

    # Attempt duplicate slug
    with pytest.raises(ConflictException) as exc:
        await CategoryService.create_category(async_test_session, org_id, cat_req)
    assert exc.value.code == "CATEGORY_SLUG_EXISTS"

    # Create child category
    sub_req = CategoryCreate(name="Shirts", parent_id=cat.id)
    sub = await CategoryService.create_category(async_test_session, org_id, sub_req)
    assert sub.parent_id == cat.id
    assert sub.slug == "shirts"

    # Update category
    up_req = CategoryUpdate(name="Apparel & Clothing")
    updated = await CategoryService.update_category(async_test_session, org_id, cat.id, up_req)
    assert updated.name == "Apparel & Clothing"

    # List categories
    cats = await CategoryService.list_categories(async_test_session, org_id)
    assert len(cats) == 2


@pytest.mark.asyncio
async def test_product_service_create_and_sku_conflict(async_test_session: AsyncSession) -> None:
    """Verify product creation, category linking, and duplicate SKU prevention."""
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Shoe Store", slug="shoe-store")
    async_test_session.add(org)
    await async_test_session.commit()

    cat = await CategoryService.create_category(
        async_test_session, org_id, CategoryCreate(name="Footwear")
    )

    req1 = ProductCreate(
        title="Nike Air Force",
        sku="NIKE-AF-1",
        price=Decimal("110.00"),
        stock_quantity=20,
        category_ids=[cat.id],
    )
    product = await ProductService.create_product(async_test_session, org_id, req1)
    assert product.sku == "NIKE-AF-1"
    assert product.stock_quantity == 20
    assert len(product.categories) == 1

    # Attempt duplicate SKU in same organization
    req2 = ProductCreate(
        title="Another Shoe",
        sku="NIKE-AF-1",
        price=Decimal("95.00"),
    )
    with pytest.raises(ConflictException) as exc:
        await ProductService.create_product(async_test_session, org_id, req2)
    assert exc.value.code == "SKU_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_product_service_update_and_delete(async_test_session: AsyncSession) -> None:
    """Verify updating product fields and deleting a product."""
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Electronics Store", slug="elec-store")
    async_test_session.add(org)
    await async_test_session.commit()

    prod = await ProductService.create_product(
        async_test_session,
        org_id,
        ProductCreate(title="Old Laptop", sku="LAP-01", price=Decimal("800.00")),
    )

    # Update
    up_req = ProductUpdate(title="New Laptop Pro", price=Decimal("950.00"))
    updated = await ProductService.update_product(async_test_session, org_id, prod.id, up_req)
    assert updated.title == "New Laptop Pro"
    assert updated.price == Decimal("950.00")

    # Delete
    await ProductService.delete_product(async_test_session, org_id, prod.id)
    with pytest.raises(NotFoundException):
        await ProductService.get_product(async_test_session, org_id, prod.id)


@pytest.mark.asyncio
async def test_inventory_service_adjustment_and_lock(async_test_session: AsyncSession) -> None:
    """Verify stock restock, deduction, audit logging, and negative stock prevention."""
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Watch Store", slug="watch-store")
    async_test_session.add(org)
    await async_test_session.commit()

    product = await ProductService.create_product(
        async_test_session,
        org_id,
        ProductCreate(
            title="Rolex Watch",
            sku="ROLX-01",
            price=Decimal("5000.00"),
            stock_quantity=5,
        ),
    )
    assert product.stock_quantity == 5

    # 1. Restock (+10)
    restock_req = InventoryAdjustmentRequest(
        change_amount=10,
        reason=InventoryChangeReason.RESTOCK,
        reference_id="PO-1002",
    )
    updated_prod, log1 = await InventoryService.adjust_stock(
        async_test_session, org_id, product.id, restock_req
    )
    assert updated_prod.stock_quantity == 15
    assert log1.balance_after == 15
    assert log1.change_amount == 10

    # 2. Order fulfillment (-3)
    deduct_req = InventoryAdjustmentRequest(
        change_amount=-3,
        reason=InventoryChangeReason.ORDER_FULFILL,
        reference_id="ORDER-5555",
    )
    updated_prod, log2 = await InventoryService.adjust_stock(
        async_test_session, org_id, product.id, deduct_req
    )
    assert updated_prod.stock_quantity == 12
    assert log2.balance_after == 12
    assert log2.change_amount == -3

    # 3. Prevent oversell: attempt to deduct 20 when only 12 are in stock
    oversell_req = InventoryAdjustmentRequest(
        change_amount=-20,
        reason=InventoryChangeReason.ORDER_FULFILL,
    )
    with pytest.raises(BadRequestException) as exc:
        await InventoryService.adjust_stock(async_test_session, org_id, product.id, oversell_req)
    assert exc.value.code == "INSUFFICIENT_STOCK"

    # 4. Check audit logs history
    logs = await InventoryService.get_inventory_logs(async_test_session, org_id, product.id)
    # 3 logs: 1 initial stock + 1 restock + 1 deduction
    assert len(logs) == 3
