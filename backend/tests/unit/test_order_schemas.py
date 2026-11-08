import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.orders.models import OrderStatus, PaymentStatus
from app.modules.orders.schemas import (
    OrderCreate,
    OrderItemCreate,
    OrderItemRead,
    OrderListResponse,
    OrderRead,
    OrderStatusUpdate,
    OrderUpdate,
)


def test_order_item_create_valid() -> None:
    """Test valid OrderItemCreate instantiation."""
    prod_id = uuid.uuid4()
    item = OrderItemCreate(product_id=prod_id, quantity=3)
    assert item.product_id == prod_id
    assert item.quantity == 3

    # Default quantity is 1
    item_default = OrderItemCreate(product_id=prod_id)
    assert item_default.quantity == 1


def test_order_item_create_invalid_quantity() -> None:
    """Test validation failure when quantity is zero or negative."""
    prod_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        OrderItemCreate(product_id=prod_id, quantity=0)

    with pytest.raises(ValidationError):
        OrderItemCreate(product_id=prod_id, quantity=-2)


def test_order_create_valid() -> None:
    """Test valid OrderCreate payload."""
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()
    order = OrderCreate(
        customer_id=cust_id,
        items=[OrderItemCreate(product_id=prod_id, quantity=2)],
        shipping_cost=Decimal("15.50"),
        shipping_address="123 Ocean Ave",
        notes="Ring doorbell",
        metadata={"channel": "web"},
    )
    assert order.customer_id == cust_id
    assert len(order.items) == 1
    assert order.shipping_cost == Decimal("15.50")
    assert order.shipping_address == "123 Ocean Ave"
    assert order.metadata == {"channel": "web"}


def test_order_create_empty_items_rejected() -> None:
    """Test that OrderCreate requires at least one item."""
    cust_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        OrderCreate(customer_id=cust_id, items=[])


def test_order_create_negative_shipping_rejected() -> None:
    """Test that shipping_cost cannot be negative."""
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        OrderCreate(
            customer_id=cust_id,
            items=[OrderItemCreate(product_id=prod_id, quantity=1)],
            shipping_cost=Decimal("-5.00"),
        )


def test_order_status_update_valid_and_invalid() -> None:
    """Test valid and invalid OrderStatusUpdate values."""
    update = OrderStatusUpdate(status=OrderStatus.CONFIRMED)
    assert update.status == OrderStatus.CONFIRMED

    # Invalid status value
    with pytest.raises(ValidationError):
        OrderStatusUpdate.model_validate({"status": "NON_EXISTENT_STATUS"})


def test_order_update_optional_fields() -> None:
    """Test OrderUpdate accepts partial updates."""
    update = OrderUpdate(
        shipping_address="456 New St",
        payment_status=PaymentStatus.PAID,
    )
    assert update.shipping_address == "456 New St"
    assert update.payment_status == PaymentStatus.PAID
    assert update.notes is None


def test_order_read_serialization() -> None:
    """Test OrderRead and OrderItemRead serialization from dict / ORM mapping."""
    now = datetime.now(UTC)
    order_id = uuid.uuid4()
    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()
    item_id = uuid.uuid4()

    item_data = {
        "id": item_id,
        "organization_id": org_id,
        "order_id": order_id,
        "product_id": prod_id,
        "product_title": "Running Shoes",
        "product_sku": "SHOE-001",
        "unit_price": Decimal("80.00"),
        "quantity": 2,
        "total_price": Decimal("160.00"),
        "created_at": now,
    }
    item_read = OrderItemRead.model_validate(item_data)
    assert item_read.total_price == Decimal("160.00")

    order_data = {
        "id": order_id,
        "organization_id": org_id,
        "customer_id": cust_id,
        "conversation_id": None,
        "order_number": "ORD-20261108-XYZ1",
        "status": OrderStatus.PENDING,
        "payment_status": PaymentStatus.UNPAID,
        "currency": "USD",
        "subtotal": Decimal("160.00"),
        "shipping_cost": Decimal("10.00"),
        "total_amount": Decimal("170.00"),
        "shipping_address": "123 Main St",
        "notes": "Fragile",
        "metadata_": {"source": "whatsapp"},
        "created_at": now,
        "updated_at": now,
        "items": [item_data],
    }

    order_read = OrderRead.model_validate(order_data)
    assert order_read.order_number == "ORD-20261108-XYZ1"
    assert order_read.total_amount == Decimal("170.00")
    assert len(order_read.items) == 1
    assert order_read.metadata == {"source": "whatsapp"}

    # Also test OrderListResponse
    list_response = OrderListResponse(
        items=[order_read],
        total=1,
        page=1,
        page_size=20,
    )
    assert list_response.total == 1
    assert len(list_response.items) == 1
