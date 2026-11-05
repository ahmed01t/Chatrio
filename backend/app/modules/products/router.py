"""
Product Catalog, Category, and Inventory API Endpoints.

Provides tenant-scoped endpoints for:
- Categories: POST /categories, GET /categories, GET /categories/{id},
              PATCH /categories/{id}, DELETE /categories/{id}
- Products: POST /products, GET /products, GET /products/{id},
            PATCH /products/{id}, DELETE /products/{id}
- Inventory: POST /products/{id}/inventory, GET /products/{id}/inventory
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import CurrentTenant, DBSession, require_roles
from app.modules.organizations.models import MemberRole
from app.modules.products.schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    InventoryAdjustmentRequest,
    InventoryLogRead,
    ProductCreate,
    ProductListResponse,
    ProductRead,
    ProductUpdate,
)
from app.modules.products.service import (
    CategoryService,
    InventoryService,
    ProductService,
)

router = APIRouter(tags=["Products & Inventory"])

# Role guards:
# - Admin or Owner can create, update, or delete products and categories
RequireManager = Annotated[
    CurrentTenant,
    Depends(require_roles([MemberRole.OWNER, MemberRole.ADMIN])),
]


# ==============================================================================
# Category Endpoints
# ==============================================================================
@router.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product category",
)
async def create_category(
    request: CategoryCreate,
    tenant_context: RequireManager,
    session: DBSession,
) -> CategoryRead:
    """Creates a new category for the active tenant organization."""
    category = await CategoryService.create_category(
        session=session,
        organization_id=tenant_context.organization.id,
        request=request,
    )
    return CategoryRead.model_validate(category)


@router.get(
    "/categories",
    response_model=list[CategoryRead],
    status_code=status.HTTP_200_OK,
    summary="List all product categories for active store",
)
async def list_categories(
    tenant_context: CurrentTenant,
    session: DBSession,
) -> list[CategoryRead]:
    """Lists all product categories belonging to the authenticated tenant."""
    categories = await CategoryService.list_categories(
        session=session,
        organization_id=tenant_context.organization.id,
    )
    return [CategoryRead.model_validate(cat) for cat in categories]


@router.get(
    "/categories/{category_id}",
    response_model=CategoryRead,
    status_code=status.HTTP_200_OK,
    summary="Get category details by ID",
)
async def get_category(
    category_id: uuid.UUID,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> CategoryRead:
    """Retrieves a single category by ID."""
    category = await CategoryService.get_category(
        session=session,
        organization_id=tenant_context.organization.id,
        category_id=category_id,
    )
    return CategoryRead.model_validate(category)


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryRead,
    status_code=status.HTTP_200_OK,
    summary="Update category details",
)
async def update_category(
    category_id: uuid.UUID,
    request: CategoryUpdate,
    tenant_context: RequireManager,
    session: DBSession,
) -> CategoryRead:
    """Updates a category belonging to the organization."""
    category = await CategoryService.update_category(
        session=session,
        organization_id=tenant_context.organization.id,
        category_id=category_id,
        request=request,
    )
    return CategoryRead.model_validate(category)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
)
async def delete_category(
    category_id: uuid.UUID,
    tenant_context: RequireManager,
    session: DBSession,
) -> None:
    """Deletes a category belonging to the organization."""
    await CategoryService.delete_category(
        session=session,
        organization_id=tenant_context.organization.id,
        category_id=category_id,
    )


# ==============================================================================
# Product Endpoints
# ==============================================================================
@router.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new catalog product",
)
async def create_product(
    request: ProductCreate,
    tenant_context: RequireManager,
    session: DBSession,
) -> ProductRead:
    """
    Creates a new product in the store catalog with initial stock and categories.
    Restricted to OWNER and ADMIN roles.
    """
    product = await ProductService.create_product(
        session=session,
        organization_id=tenant_context.organization.id,
        request=request,
    )
    return ProductRead.model_validate(product)


@router.get(
    "/products",
    response_model=ProductListResponse,
    status_code=status.HTTP_200_OK,
    summary="List store products with pagination and filters",
)
async def list_products(
    tenant_context: CurrentTenant,
    session: DBSession,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    category_id: Annotated[uuid.UUID | None, Query(description="Filter by category")] = None,
    is_active: Annotated[bool | None, Query(description="Filter by active status")] = None,
    search: Annotated[str | None, Query(description="Search in title or SKU")] = None,
) -> ProductListResponse:
    """Lists products belonging to the store with pagination and filtering."""
    items, total = await ProductService.list_products(
        session=session,
        organization_id=tenant_context.organization.id,
        page=page,
        page_size=page_size,
        category_id=category_id,
        is_active=is_active,
        search=search,
    )
    return ProductListResponse(
        items=[ProductRead.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductRead,
    status_code=status.HTTP_200_OK,
    summary="Get product details by ID",
)
async def get_product(
    product_id: uuid.UUID,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> ProductRead:
    """Retrieves full details of a single product."""
    product = await ProductService.get_product(
        session=session,
        organization_id=tenant_context.organization.id,
        product_id=product_id,
    )
    return ProductRead.model_validate(product)


@router.patch(
    "/products/{product_id}",
    response_model=ProductRead,
    status_code=status.HTTP_200_OK,
    summary="Update product details",
)
async def update_product(
    product_id: uuid.UUID,
    request: ProductUpdate,
    tenant_context: RequireManager,
    session: DBSession,
) -> ProductRead:
    """Updates product title, description, price, status, or category assignments."""
    product = await ProductService.update_product(
        session=session,
        organization_id=tenant_context.organization.id,
        product_id=product_id,
        request=request,
    )
    return ProductRead.model_validate(product)


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
)
async def delete_product(
    product_id: uuid.UUID,
    tenant_context: RequireManager,
    session: DBSession,
) -> None:
    """Deletes a product from the organization's catalog."""
    await ProductService.delete_product(
        session=session,
        organization_id=tenant_context.organization.id,
        product_id=product_id,
    )


# ==============================================================================
# Inventory Endpoints
# ==============================================================================
@router.post(
    "/products/{product_id}/inventory",
    response_model=ProductRead,
    status_code=status.HTTP_200_OK,
    summary="Adjust product stock quantity with audit logging",
)
async def adjust_inventory(
    product_id: uuid.UUID,
    request: InventoryAdjustmentRequest,
    tenant_context: RequireManager,
    session: DBSession,
) -> ProductRead:
    """
    Adjusts inventory with row-level locks and writes to immutable audit ledger.
    Restricted to OWNER and ADMIN.
    """
    product, _ = await InventoryService.adjust_stock(
        session=session,
        organization_id=tenant_context.organization.id,
        product_id=product_id,
        request=request,
    )
    return ProductRead.model_validate(product)


@router.get(
    "/products/{product_id}/inventory",
    response_model=list[InventoryLogRead],
    status_code=status.HTTP_200_OK,
    summary="Get inventory audit log history for a product",
)
async def get_inventory_logs(
    product_id: uuid.UUID,
    tenant_context: CurrentTenant,
    session: DBSession,
    limit: Annotated[int, Query(ge=1, le=100, description="Max logs to return")] = 50,
) -> list[InventoryLogRead]:
    """Retrieves the immutable audit log history for a product."""
    logs = await InventoryService.get_inventory_logs(
        session=session,
        organization_id=tenant_context.organization.id,
        product_id=product_id,
        limit=limit,
    )
    return [InventoryLogRead.model_validate(log) for log in logs]
