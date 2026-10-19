"""
Organization and Tenancy Data Models.

This module defines:
1. `MemberRole`: Enum of available roles within an organization (OWNER, ADMIN, AGENT, VIEWER).
2. `Organization`: Represents a business tenant in Chatrio.
3. `OrganizationMember`: Junction table linking Users to Organizations with a specific Role.
"""

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.auth.models import User


class MemberRole(StrEnum):
    """
    Role-Based Access Control (RBAC) levels inside an Organization.

    - OWNER: Full administrative control, billing, organization settings, team invites.
    - ADMIN: Catalog, orders, AI agent settings, customer support.
    - AGENT: Inbox chat handling, order fulfillment, ticket management.
    - VIEWER: Read-only analytics and reports access.
    """

    OWNER = "OWNER"
    ADMIN = "ADMIN"
    AGENT = "AGENT"
    VIEWER = "VIEWER"


class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents an isolated business tenant in Chatrio.

    Every business using Chatrio is an Organization.
    All catalog data, customer contacts, WhatsApp conversations, orders,
    and vector embeddings are strictly partitioned by `organization_id`.
    """

    __tablename__ = "organizations"

    # Business display name (e.g. "Ahmed's Apparel Store")
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable business name",
    )

    # URL-friendly, unique identifier for the tenant (e.g. "ahmeds-apparel")
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique URL slug representing the organization",
    )

    # Relationship to members who belong to this organization
    members: Mapped[list["OrganizationMember"]] = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
        doc="List of user memberships belonging to this organization",
    )


class OrganizationMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Junction table connecting a User to an Organization.

    A user can belong to one or more organizations, with a specific role in each.
    For example:
    - User A can be an OWNER of Organization 1.
    - User A can also be an AGENT in Organization 2.
    """

    __tablename__ = "organization_members"

    # Foreign key pointing to the organization
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Organization ID the member belongs to",
    )

    # Foreign key pointing to the user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User ID associated with this organization membership",
    )

    # Role assigned to the user within this organization
    role: Mapped[MemberRole] = mapped_column(
        SQLEnum(MemberRole, native_enum=False, length=20),
        nullable=False,
        default=MemberRole.VIEWER,
        doc="Role determining permissions within this organization",
    )

    # Bidirectional relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="memberships",
    )

    # Ensure a user cannot be added to the same organization multiple times
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_organization_members_org_user",
        ),
    )
