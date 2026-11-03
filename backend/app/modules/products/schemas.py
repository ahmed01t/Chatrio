"""
Pydantic Validation Schemas for Products, Categories, and Inventory.

This module provides DTOs for:
1. Categories: CategoryCreate, CategoryUpdate, CategoryRead.
2. Products: ProductCreate, ProductUpdate, ProductRead, ProductListResponse.
3. Inventory: InventoryAdjustmentRequest, InventoryLogRead.
4. AI Search: SemanticSearchRequest, ProductSearchResult.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.products.models import InventoryChangeReason


# ==============================================================================
# 1. Category Schemas
# ==============================================================================
class CategoryCreate(BaseModel):
    """Schema for creating a new product category."""

    name: str = Field(min_length=1, max_length=255, description="Category display name")
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="URL-friendly slug (auto-generated if omitted)",
    )
    description: str | None = Field(default=None, description="Optional category description")
    parent_id: uuid.UUID | None = Field(
        default=None, description="Parent category ID for nested subcategories"
    )


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    # uuid.UUID is Python's built-in 128-bit unique identifier class
    parent_id: uuid.UUID | None = None


class CategoryRead(BaseModel):
    """Schema returned when reading category details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    parent_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# 2. Product Schemas
# ==============================================================================
class ProductCreate(BaseModel):
    """Schema for creating a new catalog product."""

    title: str = Field(min_length=1, max_length=255, description="Product title / name")
    description: str | None = Field(default=None, description="Detailed product description")
    sku: str = Field(min_length=1, max_length=100, description="Stock Keeping Unit identifier")
    price: Decimal = Field(ge=0, decimal_places=2, description="Unit price (must be >= 0)")
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="3-letter currency code (e.g. USD, EUR, PKR)",
    )
    stock_quantity: int = Field(
        default=0, ge=0, description="Initial stock quantity (must be >= 0)"
    )
    is_active: bool = Field(default=True, description="Whether the item is published for sale")
    category_ids: list[uuid.UUID] = Field(
        default_factory=list,
        description="List of category IDs to associate with this product",
    )


class ProductUpdate(BaseModel):
    """Schema for updating an existing product."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_active: bool | None = None
    category_ids: list[uuid.UUID] | None = None


class ProductRead(BaseModel):
    """Public representation of a Product with associated categories."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    description: str | None
    sku: str
    price: Decimal
    currency: str
    stock_quantity: int
    is_active: bool
    categories: list[CategoryRead] = []
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    """Paginated list of products."""

    items: list[ProductRead]
    total: int
    page: int
    page_size: int


# ==============================================================================
# 3. Inventory Schemas
# ==============================================================================
class InventoryAdjustmentRequest(BaseModel):
    """Payload to adjust stock quantity with audit reason."""

    change_amount: int = Field(
        description="Stock adjustment delta: positive to add stock, negative to deduct stock"
    )
    reason: InventoryChangeReason = Field(description="Operational reason for stock adjustment")
    reference_id: str | None = Field(
        default=None,
        max_length=255,
        description="Optional external order ID, return ID, or shipment ID",
    )


class InventoryLogRead(BaseModel):
    """Audit log entry for an inventory change."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    product_id: uuid.UUID
    change_amount: int
    balance_after: int
    reason: InventoryChangeReason
    reference_id: str | None
    created_at: datetime


# ==============================================================================
# 4. Semantic Search Schemas
# ==============================================================================
class SemanticSearchRequest(BaseModel):
    """Query payload for vector-based semantic product search."""

    query: str = Field(min_length=1, description="Natural language search query from customer")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum number of items to return")
    min_similarity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold (0.0 to 1.0)",
    )


class ProductSearchResult(BaseModel):
    """Product result matching a semantic search query with similarity score."""

    product: ProductRead
    similarity: float = Field(description="Cosine similarity score (0.0 to 1.0)")
