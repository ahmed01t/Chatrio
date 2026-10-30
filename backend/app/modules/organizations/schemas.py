"""
Pydantic Schemas for Organizations and Memberships.

This module provides data transfer objects (DTOs) for:
1. `OrganizationRead`: Public representation of a tenant organization.
2. `MemberRead`: Public representation of an organization membership.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.organizations.models import MemberRole


class OrganizationRead(BaseModel):
    """Schema returned when reading organization details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


class MemberRead(BaseModel):
    """Schema returned when reading an organization membership."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: MemberRole
    created_at: datetime
    updated_at: datetime
