"""001_initial_tenancy_and_auth

Initial migration creating organizations, users, and organization_members tables.

Revision ID: 001
Revises: None
Create Date: 2026-10-20 18:25:00.000000 UTC

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --------------------------------------------------------------------------
    # 1. Organizations Table
    # --------------------------------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organizations_id"), "organizations", ["id"], unique=False)
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True)

    # --------------------------------------------------------------------------
    # 2. Users Table
    # --------------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # --------------------------------------------------------------------------
    # 3. Organization Members Junction Table
    # --------------------------------------------------------------------------
    op.create_table(
        "organization_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_organization_members_org_user",
        ),
    )
    op.create_index(
        op.f("ix_organization_members_id"),
        "organization_members",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_members_organization_id"),
        "organization_members",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_members_user_id"),
        "organization_members",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse order to respect foreign key constraints
    op.drop_index(
        op.f("ix_organization_members_user_id"),
        table_name="organization_members",
    )
    op.drop_index(
        op.f("ix_organization_members_organization_id"),
        table_name="organization_members",
    )
    op.drop_index(op.f("ix_organization_members_id"), table_name="organization_members")
    op.drop_table("organization_members")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_id"), table_name="organizations")
    op.drop_table("organizations")
