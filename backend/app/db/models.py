"""
Central Database Models Registry.

This module re-exports all SQLAlchemy ORM models across all domain modules.
Importing this module ensures that:
1. All models are loaded into Python memory.
2. `Base.metadata` registers every database table.
3. Alembic migrations can discover all models automatically for auto-generating migrations.
"""

from app.db.base import Base
from app.modules.auth.models import User
from app.modules.organizations.models import MemberRole, Organization, OrganizationMember
from app.modules.products.models import (
    Category,
    InventoryChangeReason,
    InventoryLog,
    Product,
    ProductCategory,
)

__all__ = [
    "Base",
    "Category",
    "InventoryChangeReason",
    "InventoryLog",
    "MemberRole",
    "Organization",
    "OrganizationMember",
    "Product",
    "ProductCategory",
    "User",
]
