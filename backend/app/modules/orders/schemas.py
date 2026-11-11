"""
Pydantic Validation Schemas for Orders and Order Items.

Provides DTOs for:
1. `OrderItemCreate`, `OrderItemRead`
2. `OrderCreate`, `OrderUpdate`, `OrderStatusUpdate`, `OrderRead`, `OrderListResponse`
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.modules.orders.models import OrderStatus, PaymentStatus


# ==============================================================================
# 1. Order Item Schemas
# ==============================================================================
class OrderItemCreate(BaseModel):
    """Schema for adding a line item when placing an order."""

    product_id: uuid.UUID = Field(
        description="UUID of the product being purchased",
    )
    quantity: int = Field(
        default=1,
        ge=1,
        description="Quantity ordered (must be at least 1)",
    )


class OrderItemRead(BaseModel):
    """Schema for reading an order line item snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    order_id: uuid.UUID
    product_id: uuid.UUID
    product_title: str
    product_sku: str
    unit_price: Decimal
    quantity: int
    total_price: Decimal
    created_at: datetime


# ==============================================================================
# 2. Order Schemas
# ==============================================================================
class OrderCreate(BaseModel):
    """Schema for creating a new order."""

    model_config = ConfigDict(populate_by_name=True)

    customer_id: uuid.UUID = Field(
        description="UUID of the customer placing the order",
    )
    conversation_id: uuid.UUID | None = Field(
        default=None,
        description="Optional origin conversation UUID",
    )
    items: list[OrderItemCreate] = Field(
        min_length=1,
        description="List of order line items (must contain at least 1 item)",
    )
    shipping_cost: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        description="Shipping and handling charge",
    )
    shipping_address: str | None = Field(
        default=None,
        max_length=1000,
        description="Street address or delivery location",
    )
    notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Delivery instructions or merchant notes",
    )
    channel: str | None = Field(
        default=None,
        description="Optional origin channel (e.g. WHATSAPP, INSTAGRAM)",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="metadata_",
        description="Custom merchant tags or courier tracking data",
    )


class OrderUpdate(BaseModel):
    """Schema for updating order delivery notes or payment status."""

    shipping_address: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated delivery address",
    )
    notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated notes",
    )
    payment_status: PaymentStatus | None = Field(
        default=None,
        description="Updated payment status",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="metadata_",
        description="Updated metadata tags",
    )


class OrderStatusUpdate(BaseModel):
    """Schema for advancing an order's lifecycle status."""

    status: OrderStatus = Field(
        description="Target order fulfillment status",
    )


class OrderRead(BaseModel):
    """Schema for reading complete order details."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    conversation_id: uuid.UUID | None
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    currency: str
    subtotal: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    shipping_address: str | None
    notes: str | None
    metadata: dict[str, Any] | None = Field(default=None, validation_alias="metadata_")
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead] = Field(default_factory=list)

    @computed_field
    def channel(self) -> str:
        """Origin commerce channel (WHATSAPP, INSTAGRAM, WEB, API)."""
        if self.metadata and isinstance(self.metadata, dict):
            ch = self.metadata.get("channel")
            if ch:
                return str(ch).upper()
        return "WHATSAPP"


class OrderListResponse(BaseModel):
    """Paginated collection of orders."""

    items: list[OrderRead]
    total: int
    page: int
    page_size: int
