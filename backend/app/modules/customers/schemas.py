"""
Pydantic Schemas for Customer Management.

Defines schemas for:
1. Customer creation (with strict E.164 phone normalization).
2. Customer updates (name, email, metadata, blocklist status).
3. Customer retrieval and paginated directory responses.
"""

import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ITU-T E.164 format: starts with +, followed by country code & subscriber number (<= 15 digits)
E164_REGEX = re.compile(r"^\+[1-9]\d{1,14}$")


def normalize_e164_phone(phone: str) -> str:
    """
    Normalizes and validates a phone string into standard ITU-T E.164 format.

    Strips whitespace, parentheses, dashes, and periods.
    Example: ' +1 (415) 555-2671 ' -> '+14155552671'
    """
    cleaned = re.sub(r"[\s\(\)\-\.]", "", phone.strip())
    if not cleaned.startswith("+"):
        cleaned = f"+{cleaned}"

    if not E164_REGEX.match(cleaned):
        raise ValueError(
            f"Invalid phone number format: '{phone}'. "
            "Phone numbers must follow E.164 format (e.g. +14155552671)."
        )
    return cleaned


class CustomerCreate(BaseModel):
    """Schema for registering or upserting a new customer profile."""

    phone_number: str = Field(
        description="Customer phone number in E.164 format (e.g. +14155552671)"
    )
    name: str | None = Field(
        default=None,
        max_length=255,
        description="Customer full name or WhatsApp profile display name",
    )
    email: EmailStr | None = Field(
        default=None,
        description="Optional customer email address for order notifications",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Custom merchant tags, preferences, or properties",
    )
    is_blocked: bool = Field(
        default=False,
        description="Whether this customer is blocked from contacting the store",
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_e164_phone(v)


class CustomerUpdate(BaseModel):
    """Schema for updating an existing customer record."""

    name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    metadata: dict[str, Any] | None = None
    is_blocked: bool | None = None


class CustomerRead(BaseModel):
    """Public customer profile data returned by API endpoints."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    phone_number: str
    name: str | None
    email: str | None
    metadata: dict[str, Any] | None = Field(default=None, alias="metadata_")
    is_blocked: bool
    created_at: datetime
    updated_at: datetime


class CustomerListResponse(BaseModel):
    """Paginated list of customer profiles."""

    items: list[CustomerRead]
    total: int
    page: int
    page_size: int
