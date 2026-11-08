"""
Order and Order Item Data Models.

Defines:
1. `OrderStatus`: State machine states (PENDING, CONFIRMED, PROCESSING,
   SHIPPED, DELIVERED, CANCELLED).
2. `PaymentStatus`: Payment settlement status (UNPAID, PAID, REFUNDED).
3. `Order`: Multi-tenant order header tracking customer, financial totals, and lifecycle.
4. `OrderItem`: Line item snapshot capturing historical product details and prices.
"""

import uuid
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.conversations.models import Conversation
    from app.modules.customers.models import Customer
    from app.modules.organizations.models import Organization
    from app.modules.products.models import Product

# SQLite compatibility fallback for JSONB
JSONType = JSONB().with_variant(JSON(), "sqlite")


class OrderStatus(StrEnum):
    """Lifecycle states of an order."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentStatus(StrEnum):
    """Financial settlement status of an order."""

    UNPAID = "UNPAID"
    PAID = "PAID"
    REFUNDED = "REFUNDED"


class Order(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents an order placed by a customer in a merchant organization.

    Tracks historical financial totals, status transitions, shipping address,
    and line items.
    """

    __tablename__ = "orders"

    # Multi-tenancy foreign key
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant organization that owns this order",
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Customer who placed this order",
    )

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Optional conversation session where this order originated",
    )

    order_number: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Human-readable unique order identifier (e.g. ORD-20261108-ABCD)",
    )

    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, native_enum=False, length=20),
        default=OrderStatus.PENDING,
        nullable=False,
        doc="Current state in the order fulfillment state machine",
    )

    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, native_enum=False, length=20),
        default=PaymentStatus.UNPAID,
        nullable=False,
        doc="Payment settlement status",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        doc="3-letter currency code (e.g. USD, EUR, PKR)",
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Sum of line item totals before shipping and taxes",
    )

    shipping_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Shipping or delivery charge",
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Final total amount charged for the order (subtotal + shipping_cost)",
    )

    shipping_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Customer delivery street address or location details",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Special merchant or customer delivery instructions",
    )

    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONType,
        nullable=True,
        default=dict,
        doc="Optional custom merchant metadata or courier tracking tags",
    )

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "order_number",
            name="uq_orders_org_order_number",
        ),
        Index("ix_orders_org_status", "organization_id", "status"),
        Index("ix_orders_org_customer", "organization_id", "customer_id"),
        Index("ix_orders_org_created_at", "organization_id", "created_at"),
        CheckConstraint("subtotal >= 0", name="chk_orders_subtotal_positive"),
        CheckConstraint("shipping_cost >= 0", name="chk_orders_shipping_positive"),
        CheckConstraint("total_amount >= 0", name="chk_orders_total_positive"),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship()  # this means
    customer: Mapped["Customer"] = relationship()
    conversation: Mapped["Conversation | None"] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItem.created_at.asc()",
        lazy="selectin",
    )


class OrderItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents an individual line item snapshot within an order.

    Preserves historical product title, SKU, and unit price as an immutable
    snapshot at the time of purchase.
    """

    __tablename__ = "order_items"

    # Multi-tenancy foreign key
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant organization that owns this order item",
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Order to which this item belongs",
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Product reference",
    )

    # Historical snapshots
    product_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Snapshot of product title at purchase time",
    )

    product_sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Snapshot of product SKU at purchase time",
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        doc="Snapshot of unit selling price at purchase time",
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Quantity ordered (must be >= 1)",
    )

    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        doc="Line total (unit_price * quantity)",
    )

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_order_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="chk_order_items_unit_price_positive"),
        CheckConstraint("total_price >= 0", name="chk_order_items_total_price_positive"),
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
