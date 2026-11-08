"""004_orders_and_order_items

Migration adding orders and order_items tables.
Supports multi-tenant order workflows, historical line item price snapshots,
state machine status tracking, and financial calculations.

Revision ID: 004
Revises: 003
Create Date: 2026-11-08 15:30:00.000000 UTC

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --------------------------------------------------------------------------
    # 1. Orders Table
    # --------------------------------------------------------------------------
    op.create_table(
        "orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=True),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("payment_status", sa.String(length=20), server_default="UNPAID", nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column(
            "subtotal", sa.Numeric(precision=10, scale=2), server_default="0.00", nullable=False
        ),
        sa.Column(
            "shipping_cost",
            sa.Numeric(precision=10, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(precision=10, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column("shipping_address", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "order_number",
            name="uq_orders_org_order_number",
        ),
        sa.CheckConstraint("subtotal >= 0", name="chk_orders_subtotal_positive"),
        sa.CheckConstraint("shipping_cost >= 0", name="chk_orders_shipping_positive"),
        sa.CheckConstraint("total_amount >= 0", name="chk_orders_total_positive"),
    )
    op.create_index(op.f("ix_orders_id"), "orders", ["id"], unique=False)
    op.create_index(
        op.f("ix_orders_organization_id"),
        "orders",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_orders_customer_id"),
        "orders",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_orders_conversation_id"),
        "orders",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_orders_org_status",
        "orders",
        ["organization_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_orders_org_customer",
        "orders",
        ["organization_id", "customer_id"],
        unique=False,
    )
    op.create_index(
        "ix_orders_org_created_at",
        "orders",
        ["organization_id", "created_at"],
        unique=False,
    )

    # --------------------------------------------------------------------------
    # 2. Order Items Table
    # --------------------------------------------------------------------------
    op.create_table(
        "order_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("product_title", sa.String(length=255), nullable=False),
        sa.Column("product_sku", sa.String(length=100), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("total_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantity > 0", name="chk_order_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="chk_order_items_unit_price_positive"),
        sa.CheckConstraint("total_price >= 0", name="chk_order_items_total_price_positive"),
    )
    op.create_index(op.f("ix_order_items_id"), "order_items", ["id"], unique=False)
    op.create_index(
        op.f("ix_order_items_organization_id"),
        "order_items",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_order_items_order_id"),
        "order_items",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_order_items_product_id"),
        "order_items",
        ["product_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index(op.f("ix_order_items_product_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_organization_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_id"), table_name="order_items")
    op.drop_table("order_items")

    op.drop_index("ix_orders_org_created_at", table_name="orders")
    op.drop_index("ix_orders_org_customer", table_name="orders")
    op.drop_index("ix_orders_org_status", table_name="orders")
    op.drop_index(op.f("ix_orders_conversation_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_customer_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_organization_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_id"), table_name="orders")
    op.drop_table("orders")
