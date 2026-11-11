"""
Pydantic Schemas for Organizations and Memberships.

This module provides data transfer objects (DTOs) for:
1. `OrganizationRead` & `OrganizationDetailRead`: Representation of a tenant organization.
2. `OrganizationUpdate`: Payload for updating organization details.
3. `MemberRead` & `OrganizationMemberRead`: Representation of an organization membership.
4. `MemberAddRequest` & `MemberRoleUpdate`: Payloads for managing team members.
5. `MemberListResponse`: Collection of organization members.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.organizations.models import MemberRole


class OrganizationRead(BaseModel):
    """Schema returned when reading organization details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


class OrganizationDetailRead(OrganizationRead):
    """Extended organization details including member count and caller role."""

    member_count: int = Field(ge=0, description="Total number of members in this organization")
    current_user_role: MemberRole = Field(description="Role of the authenticated user")


class OrganizationUpdate(BaseModel):
    """Schema for updating current organization metadata."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated business display name",
    )
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated URL-friendly identifier",
    )


class MemberRead(BaseModel):
    """Schema returned when reading an organization membership."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: MemberRole
    created_at: datetime
    updated_at: datetime


class OrganizationMemberRead(BaseModel):
    """Schema combining membership metadata with user profile fields."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    role: MemberRole
    created_at: datetime
    updated_at: datetime


class MemberListResponse(BaseModel):
    """Response collection of organization team members."""

    items: list[OrganizationMemberRead]
    total: int


class MemberAddRequest(BaseModel):
    """Schema for adding a new or existing user to the organization."""

    email: EmailStr = Field(description="Email address of the team member")
    role: MemberRole = Field(
        default=MemberRole.AGENT,
        description="Assigned role within the organization",
    )
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Full name (required when creating a brand new user account)",
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Initial password (required when creating a brand new user account)",
    )


class MemberRoleUpdate(BaseModel):
    """Schema for updating an organization member's role."""

    role: MemberRole = Field(description="Target role for the organization member")
