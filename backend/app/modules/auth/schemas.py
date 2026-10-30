"""
Pydantic Schemas for Authentication and User Accounts.

This module provides validation schemas for:
1. `UserRead`: Public user profile data.
2. `RegisterRequest`: Payload for merchant account registration.
3. `LoginRequest`: Payload for email/password sign-in.
4. `AuthResponse`: Response containing access token, user, and organization.
5. `UserProfileResponse`: Current authenticated user profile with active tenant info.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.organizations.models import MemberRole
from app.modules.organizations.schemas import OrganizationRead


class UserRead(BaseModel):
    """Public representation of a User."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RegisterRequest(BaseModel):
    """Payload required to register a new merchant and organization."""

    email: EmailStr = Field(description="Merchant's email address")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Account password (min 8 characters)",
    )
    full_name: str = Field(
        min_length=1,
        max_length=255,
        description="Full name of merchant owner",
    )
    organization_name: str = Field(
        min_length=1,
        max_length=255,
        description="Name of the business organization",
    )
    organization_slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Optional custom URL slug for the business. Auto-generated if omitted.",
    )


class LoginRequest(BaseModel):
    """Payload required to sign in with email and password."""

    email: EmailStr = Field(description="Registered email address")
    password: str = Field(description="Account password")


class AuthResponse(BaseModel):
    """Response returned upon successful registration or login."""

    access_token: str = Field(description="JWT Bearer token")
    token_type: str = Field(default="bearer", description="Token authentication type")
    expires_in: int = Field(description="Token lifetime in seconds")
    user: UserRead = Field(description="Authenticated user profile")
    organization: OrganizationRead = Field(description="Active organization context")


class UserProfileResponse(BaseModel):
    """Detailed profile returned for the currently authenticated user."""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    organization_id: uuid.UUID
    organization_name: str
    role: MemberRole
