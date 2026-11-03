"""
Product, Category, and Inventory Data Models.

Defines:
1. `Category`: Tenant-bound hierarchical product categories.
2. `Product`: Tenant-bound merchandise with pricing, stock, and pgvector embeddings.
3. `ProductCategory`: Many-to-many junction table between Products and Categories.
4. `InventoryChangeReason`: Enum of inventory modification sources.
5. `InventoryLog`: Immutable audit ledger tracking all stock changes.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InventoryChangeReason(StrEnum):
    """Reason for an inventory adjustment."""

    RESTOCK = "RESTOCK"
    ORDER_RESERVE = "ORDER_RESERVE"
    ORDER_RELEASE = "ORDER_RELEASE"
    ORDER_FULFILL = "ORDER_FULFILL"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"
    RETURN = "RETURN"


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents a product category within a tenant organization.
    Supports hierarchical categories via optional `parent_id`.
    """

    __tablename__ = "categories"

    # Multi-tenancy foreign key
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant organization this category belongs to",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Display name of category (e.g. 'Men's Footwear')",
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="URL-friendly slug for category (unique per tenant)",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional category description",
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Parent category ID for nested subcategories",
    )

    # Relationships
    parent: Mapped["Category | None"] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="subcategories",
    )
    subcategories: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
    )
    products: Mapped[list["Product"]] = relationship(
        "Product",
        secondary="product_categories",
        back_populates="categories",
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "slug",
            name="uq_categories_org_slug",
        ),
    )


class ProductCategory(Base):
    """Junction table connecting Products to Categories."""

    __tablename__ = "product_categories"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents a merchandise item in the store's catalog.
    Includes pgvector embedding column for semantic AI search.
    """

    __tablename__ = "products"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant organization this product belongs to",
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name/Title of the product",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed description of the product",
    )

    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Stock Keeping Unit (unique per organization)",
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        doc="Unit price of the product",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        doc="3-letter currency code (e.g. USD, PKR, EUR)",
    )

    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Current available inventory stock quantity",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether product is published and available for sale",
    )

    # 1536-dimensional AI vector embedding for semantic search
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
        doc="1536-dimensional vector embedding for semantic similarity search",
    )

    # Relationships
    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary="product_categories",
        back_populates="products",
    )
    inventory_logs: Mapped[list["InventoryLog"]] = relationship(
        "InventoryLog",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "sku",
            name="uq_products_org_sku",
        ),
        CheckConstraint(
            "stock_quantity >= 0",
            name="chk_products_stock_non_negative",
        ),
        CheckConstraint(
            "price >= 0",
            name="chk_products_price_non_negative",
        ),
        Index("ix_products_org_is_active", "organization_id", "is_active"),
    )


class InventoryLog(Base, UUIDPrimaryKeyMixin):
    """
    Immutable audit ledger of every inventory change.
    Records who/what changed the stock, the delta, and the resulting balance.
    """

    __tablename__ = "inventory_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    change_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Positive for restock, negative for deduction/order",
    )

    balance_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Stock quantity immediately following this adjustment",
    )

    reason: Mapped[InventoryChangeReason] = mapped_column(
        SQLEnum(InventoryChangeReason, native_enum=False, length=30),
        nullable=False,
        doc="Reason category for this stock change",
    )

    reference_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Optional external reference ID (e.g. order_id, shipment_id)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when this inventory log was created",
    )

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="inventory_logs",
    )
