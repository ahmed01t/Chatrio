"""002_products_and_inventory

Migration adding categories, products, product_categories, and inventory_logs.
Also enables the PostgreSQL 'vector' extension for semantic AI embeddings.

Revision ID: 002
Revises: 001
Create Date: 2026-11-03 06:55:00.000000 UTC

"""

from collections.abc import Sequence

import pgvector
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --------------------------------------------------------------------------
    # 0. Enable pgvector Extension (PostgreSQL only)
    # --------------------------------------------------------------------------
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --------------------------------------------------------------------------
    # 1. Categories Table
    # --------------------------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "slug", name="uq_categories_org_slug"),
    )
    op.create_index(op.f("ix_categories_id"), "categories", ["id"], unique=False)
    op.create_index(
        op.f("ix_categories_organization_id"),
        "categories",
        ["organization_id"],
        unique=False,
    )
    op.create_index(op.f("ix_categories_parent_id"), "categories", ["parent_id"], unique=False)

    # --------------------------------------------------------------------------
    # 2. Products Table
    # --------------------------------------------------------------------------
    op.create_table(
        "products",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column("stock_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "embedding",
            pgvector.sqlalchemy.Vector(1536),
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
        sa.CheckConstraint("price >= 0", name="chk_products_price_non_negative"),
        sa.CheckConstraint("stock_quantity >= 0", name="chk_products_stock_non_negative"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "sku", name="uq_products_org_sku"),
    )
    op.create_index(op.f("ix_products_id"), "products", ["id"], unique=False)
    op.create_index(
        op.f("ix_products_organization_id"),
        "products",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_products_org_is_active",
        "products",
        ["organization_id", "is_active"],
        unique=False,
    )

    # --------------------------------------------------------------------------
    # 3. Product Categories Junction Table
    # --------------------------------------------------------------------------
    op.create_table(
        "product_categories",
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("product_id", "category_id"),
    )

    # --------------------------------------------------------------------------
    # 4. Inventory Logs Table
    # --------------------------------------------------------------------------
    op.create_table(
        "inventory_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("change_amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=30), nullable=False),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inventory_logs_id"), "inventory_logs", ["id"], unique=False)
    op.create_index(
        op.f("ix_inventory_logs_organization_id"),
        "inventory_logs",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_inventory_logs_product_id"),
        "inventory_logs",
        ["product_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_index(op.f("ix_inventory_logs_product_id"), table_name="inventory_logs")
    op.drop_index(op.f("ix_inventory_logs_organization_id"), table_name="inventory_logs")
    op.drop_index(op.f("ix_inventory_logs_id"), table_name="inventory_logs")
    op.drop_table("inventory_logs")

    op.drop_table("product_categories")

    op.drop_index("ix_products_org_is_active", table_name="products")
    op.drop_index(op.f("ix_products_organization_id"), table_name="products")
    op.drop_index(op.f("ix_products_id"), table_name="products")
    op.drop_table("products")

    op.drop_index(op.f("ix_categories_parent_id"), table_name="categories")
    op.drop_index(op.f("ix_categories_organization_id"), table_name="categories")
    op.drop_index(op.f("ix_categories_id"), table_name="categories")
    op.drop_table("categories")
