"""
Customer Data Model.

Represents an individual consumer or shopper belonging to a tenant organization.
Customers are identified primarily by their normalized phone number (E.164 format)
for WhatsApp messaging interactions.
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint, false
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.conversations.models import Conversation
    from app.modules.organizations.models import Organization

# SQLite compatibility fallback for JSONB
JSONType = JSONB().with_variant(JSON(), "sqlite")


class Customer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents a customer profile within a tenant organization.

    Every customer is strictly partitioned by `organization_id`.
    The same phone number (e.g. +14155552671) can exist independently in
    different tenant stores without cross-talk or data leakage.
    """

    __tablename__ = "customers"

    # Multi-tenancy foreign key
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant organization that owns this customer profile",
    )

    # Core contact information
    phone_number: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Normalized phone number in E.164 format (e.g. +14155552671)",
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Customer full name or WhatsApp profile display name",
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Optional customer email address for order notifications",
    )

    # Arbitrary tags, preferences, and custom properties
    # Named metadata_ in Python to prevent collision with DeclarativeBase.metadata
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONType,
        nullable=True,
        default=dict,
        doc="Custom merchant tags, preferences, or metadata",
    )

    # Operational status
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
        doc="Whether this customer is blocked from placing orders or contacting the store",
    )

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "phone_number",
            name="uq_customers_org_phone",
        ),
        Index("ix_customers_org_phone", "organization_id", "phone_number"),
        Index("ix_customers_org_created_at", "organization_id", "created_at"),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship()
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )
