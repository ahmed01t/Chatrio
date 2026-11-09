"""005_outbox_messages

Migration adding outbox_messages table.
Supports transactional outbox pattern, at-least-once message delivery,
Meta 24-hour customer care policy window enforcement, and exponential backoff.

Revision ID: 005
Revises: 004
Create Date: 2026-11-10 00:50:00.000000 UTC

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --------------------------------------------------------------------------
    # 1. Outbox Messages Table
    # --------------------------------------------------------------------------
    json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")

    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=True),
        sa.Column("recipient_phone", sa.String(length=32), nullable=False),
        sa.Column("message_type", sa.String(length=20), server_default="TEXT", nullable=False),
        sa.Column("payload", json_type, nullable=False),
        sa.Column("status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_retries", sa.Integer(), server_default="5", nullable=False),
        sa.Column(
            "next_retry_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes
    op.create_index(
        "ix_outbox_messages_id",
        "outbox_messages",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_outbox_messages_organization_id",
        "outbox_messages",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_outbox_messages_conversation_id",
        "outbox_messages",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_outbox_messages_recipient_phone",
        "outbox_messages",
        ["recipient_phone"],
        unique=False,
    )
    op.create_index(
        "ix_outbox_messages_status",
        "outbox_messages",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_outbox_messages_next_retry_at",
        "outbox_messages",
        ["next_retry_at"],
        unique=False,
    )
    op.create_index(
        "ix_outbox_status_next_retry",
        "outbox_messages",
        ["status", "next_retry_at"],
        unique=False,
    )
    op.create_index(
        "ix_outbox_org_status",
        "outbox_messages",
        ["organization_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_org_status", table_name="outbox_messages")
    op.drop_index("ix_outbox_status_next_retry", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_next_retry_at", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_status", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_recipient_phone", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_conversation_id", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_organization_id", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_id", table_name="outbox_messages")
    op.drop_table("outbox_messages")

