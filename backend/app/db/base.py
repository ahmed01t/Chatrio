"""
SQLAlchemy Base Model and Common Mixins.

This module defines:
1. `Base`: The root DeclarativeBase class that all database tables inherit from.
2. `UUIDPrimaryKeyMixin`: Adds a unique UUID primary key (`id`) to any model.
3. `TimestampMixin`: Adds timezone-aware `created_at` and `updated_at` fields.
4. `SoftDeleteMixin`: Adds an optional `deleted_at` field for soft deletion.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Root base class for all SQLAlchemy ORM models.

    In SQLAlchemy 2.0, DeclarativeBase acts as the central registry.
    It tracks all tables, columns, and relationships defined across the application,
    allowing Alembic to automatically detect changes and generate migrations.
    """

    pass


class UUIDPrimaryKeyMixin:
    """
    Mixin that provides a standardized UUID primary key.

    Why UUID instead of auto-incrementing integers (1, 2, 3)?
    1. Security: Attackers cannot guess or enumerate IDs (e.g. /users/1, /users/2).
    2. Multi-tenancy: UUIDs are globally unique across distributed databases and tenants.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
        doc="Globally unique identifier (UUID v4) for the record",
    )


class TimestampMixin:
    """
    Mixin that provides audit timestamps for row creation and updates.

    All timestamps are stored in UTC with timezone information (TIMESTAMPTZ in PostgreSQL).
    - `created_at` is set automatically when the row is first inserted.
    - `updated_at` is updated automatically whenever the row changes.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when the record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="UTC timestamp when the record was last modified",
    )


class SoftDeleteMixin:
    """
    Optional mixin for tables that require soft-delete support.

    Instead of permanently deleting a record from the database,
    we set `deleted_at` to the current UTC timestamp.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="UTC timestamp when the record was marked as deleted, or None if active",
    )
