"""
User and Authentication Data Models.

This module defines:
1. `User`: Represents a registered user account in Chatrio.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.organizations.models import OrganizationMember


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents an individual user account in Chatrio.

    Users can sign in with their email and password.
    A user can be linked to one or more Organizations via the `OrganizationMember` table.
    """

    __tablename__ = "users"

    # User email address (unique across the entire platform)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique email address used for login",
    )

    # Securely hashed password (bcrypt) - plain text passwords are NEVER stored
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password",
    )

    # User's full display name (e.g. "Ahmed Khan")
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Full display name of the user",
    )

    # Account status flag: False disables access without deleting data
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the user account is active and allowed to sign in",
    )

    # All organization memberships held by this user
    memberships: Mapped[list["OrganizationMember"]] = relationship(
        "OrganizationMember",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="List of organization memberships associated with this user",
    )
