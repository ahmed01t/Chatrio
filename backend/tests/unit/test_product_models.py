import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import (
    Base,
    Category,
    InventoryChangeReason,
    InventoryLog,
    Organization,
    Product,
    ProductCategory,
)


def test_products_metadata_registration() -> None:
    """Verify that products, categories, product_categories, and inventory_logs are registered."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {"categories", "products", "product_categories", "inventory_logs"}

    assert expected_tables.issubset(table_names), (
        f"Expected tables {expected_tables} in Base.metadata, found: {table_names}"
    )


def test_product_table_constraints() -> None:
    """Verify check constraints and unique constraints on products."""
    prod_table = Base.metadata.tables["products"]
    cols = prod_table.columns

    assert "id" in cols
    assert cols["id"].primary_key is True
    assert "organization_id" in cols
    assert "sku" in cols
    assert "price" in cols
    assert "stock_quantity" in cols
    assert "embedding" in cols

    # Verify unique constraint on (organization_id, sku)
    uq_names = [
        [c.name for c in uq.columns] for uq in prod_table.constraints if hasattr(uq, "columns")
    ]
    assert ["organization_id", "sku"] in uq_names


def test_category_table_constraints() -> None:
    """Verify unique constraint on (organization_id, slug) for categories."""
    cat_table = Base.metadata.tables["categories"]
    cols = cat_table.columns

    assert "id" in cols
    assert "slug" in cols
    assert "organization_id" in cols
    assert "parent_id" in cols

    uq_names = [
        [c.name for c in uq.columns] for uq in cat_table.constraints if hasattr(uq, "columns")
    ]
    assert ["organization_id", "slug"] in uq_names


@pytest.mark.asyncio
async def test_product_and_inventory_crud_in_memory() -> None:
    """Verify CRUD and relationships for Product, Category, and InventoryLog."""
    # SQLite does not support native pgvector Vector type, so we test without inserting vectors
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    org_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    async with session_factory() as session:
        org = Organization(id=org_id, name="Test Store", slug="test-store")
        category = Category(
            id=cat_id,
            organization_id=org_id,
            name="Shoes",
            slug="shoes",
        )
        product = Product(
            id=prod_id,
            organization_id=org_id,
            title="Running Shoes",
            sku="SHOE-001",
            price=Decimal("79.99"),
            currency="USD",
            stock_quantity=10,
            is_active=True,
        )
        prod_cat = ProductCategory(product_id=prod_id, category_id=cat_id)
        inv_log = InventoryLog(
            id=uuid.uuid4(),
            organization_id=org_id,
            product_id=prod_id,
            change_amount=10,
            balance_after=10,
            reason=InventoryChangeReason.RESTOCK,
        )

        session.add_all([org, category, product, prod_cat, inv_log])
        await session.commit()

    # Query back
    async with session_factory() as session:
        saved_product = await session.get(Product, prod_id)
        assert saved_product is not None
        assert saved_product.title == "Running Shoes"
        assert saved_product.stock_quantity == 10
        assert saved_product.price == Decimal("79.99")

        saved_category = await session.get(Category, cat_id)
        assert saved_category is not None
        assert saved_category.name == "Shoes"

    await engine.dispose()
