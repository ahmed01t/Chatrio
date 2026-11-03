import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.products.models import InventoryChangeReason
from app.modules.products.schemas import (
    CategoryCreate,
    InventoryAdjustmentRequest,
    ProductCreate,
    SemanticSearchRequest,
)


def test_product_create_schema_valid() -> None:
    """Verify that a valid ProductCreate passes validation."""
    cat_id = uuid.uuid4()
    prod = ProductCreate(
        title="Nike Air Zoom",
        description="Comfortable running shoes",
        sku="NIKE-AZ-42",
        price=Decimal("129.99"),
        currency="USD",
        stock_quantity=50,
        is_active=True,
        category_ids=[cat_id],
    )
    assert prod.title == "Nike Air Zoom"
    assert prod.price == Decimal("129.99")
    assert prod.stock_quantity == 50
    assert prod.category_ids == [cat_id]


def test_product_create_schema_negative_price_rejected() -> None:
    """Verify that negative prices raise ValidationError."""
    with pytest.raises(ValidationError):
        ProductCreate(
            title="Invalid Shoe",
            sku="SHOE-001",
            price=Decimal("-10.00"),
            stock_quantity=5,
        )


def test_product_create_schema_negative_stock_rejected() -> None:
    """Verify that negative stock quantities raise ValidationError."""
    with pytest.raises(ValidationError):
        ProductCreate(
            title="Invalid Stock",
            sku="SHOE-002",
            price=Decimal("10.00"),
            stock_quantity=-5,
        )


def test_category_create_schema_defaults() -> None:
    """Verify CategoryCreate defaults."""
    cat = CategoryCreate(name="Summer Apparel")
    assert cat.name == "Summer Apparel"
    assert cat.slug is None
    assert cat.parent_id is None


def test_inventory_adjustment_schema_delta() -> None:
    """Verify InventoryAdjustmentRequest allows positive and negative deltas."""
    restock = InventoryAdjustmentRequest(
        change_amount=25,
        reason=InventoryChangeReason.RESTOCK,
    )
    assert restock.change_amount == 25
    assert restock.reason == InventoryChangeReason.RESTOCK

    deduction = InventoryAdjustmentRequest(
        change_amount=-5,
        reason=InventoryChangeReason.ORDER_FULFILL,
        reference_id="ORDER-9999",
    )
    assert deduction.change_amount == -5
    assert deduction.reference_id == "ORDER-9999"


def test_semantic_search_request_bounds() -> None:
    """Verify limit and similarity bounds on SemanticSearchRequest."""
    req = SemanticSearchRequest(query="warm winter jackets", limit=10, min_similarity=0.7)
    assert req.limit == 10
    assert req.min_similarity == 0.7

    # Limit too high
    with pytest.raises(ValidationError):
        SemanticSearchRequest(query="test", limit=100)

    # Similarity out of range
    with pytest.raises(ValidationError):
        SemanticSearchRequest(query="test", min_similarity=1.5)
