"""003_conversations_and_customers

Migration adding customers, conversations, and messages tables.
Supports multi-tenant customer profiles, live chat threads, human takeover flags,
and WhatsApp message audit logging.

Revision ID: 003
Revises: 002
Create Date: 2026-11-06 17:45:00.000000 UTC

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --------------------------------------------------------------------------
    # 1. Customers Table
    # --------------------------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column("is_blocked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "phone_number", name="uq_customers_org_phone"),
    )
    op.create_index(op.f("ix_customers_id"), "customers", ["id"], unique=False)
    op.create_index(
        op.f("ix_customers_organization_id"),
        "customers",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_customers_org_phone",
        "customers",
        ["organization_id", "phone_number"],
        unique=False,
    )
    op.create_index(
        "ix_customers_org_created_at",
        "customers",
        ["organization_id", "created_at"],
        unique=False,
    )

    # --------------------------------------------------------------------------
    # 2. Conversations Table
    # --------------------------------------------------------------------------
    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("assigned_agent_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("channel", sa.String(length=20), server_default="WHATSAPP", nullable=False),
        sa.Column("is_ai_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_agent_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversations_id"), "conversations", ["id"], unique=False)
    op.create_index(
        op.f("ix_conversations_organization_id"),
        "conversations",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversations_customer_id"),
        "conversations",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversations_assigned_agent_id"),
        "conversations",
        ["assigned_agent_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_org_status",
        "conversations",
        ["organization_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_org_last_message",
        "conversations",
        ["organization_id", "last_message_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_org_customer",
        "conversations",
        ["organization_id", "customer_id"],
        unique=False,
    )

    # --------------------------------------------------------------------------
    # 3. Messages Table
    # --------------------------------------------------------------------------
    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("sender_type", sa.String(length=20), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("content_type", sa.String(length=20), server_default="TEXT", nullable=False),
        sa.Column("text_body", sa.Text(), nullable=True),
        sa.Column("media_url", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="RECEIVED", nullable=False),
        sa.Column("whatsapp_message_id", sa.String(length=255), nullable=True),
        sa.Column(
            "raw_payload",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_id"), "messages", ["id"], unique=False)
    op.create_index(
        op.f("ix_messages_organization_id"),
        "messages",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_messages_conversation_id"),
        "messages",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_messages_whatsapp_message_id"),
        "messages",
        ["whatsapp_message_id"],
        unique=False,
    )
    op.create_index(
        "ix_messages_org_created_at",
        "messages",
        ["organization_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_messages_conv_created_at",
        "messages",
        ["conversation_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_messages_org_wam_id",
        "messages",
        ["organization_id", "whatsapp_message_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index("ix_messages_org_wam_id", table_name="messages")
    op.drop_index("ix_messages_conv_created_at", table_name="messages")
    op.drop_index("ix_messages_org_created_at", table_name="messages")
    op.drop_index(op.f("ix_messages_whatsapp_message_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_organization_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_id"), table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_conversations_org_customer", table_name="conversations")
    op.drop_index("ix_conversations_org_last_message", table_name="conversations")
    op.drop_index("ix_conversations_org_status", table_name="conversations")
    op.drop_index(op.f("ix_conversations_assigned_agent_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_customer_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_organization_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_id"), table_name="conversations")
    op.drop_table("conversations")

    op.drop_index("ix_customers_org_created_at", table_name="customers")
    op.drop_index("ix_customers_org_phone", table_name="customers")
    op.drop_index(op.f("ix_customers_organization_id"), table_name="customers")
    op.drop_index(op.f("ix_customers_id"), table_name="customers")
    op.drop_table("customers")

