"""
Customer Management API Endpoints.

Provides tenant-scoped endpoints for:
- POST /customers: Create a new customer profile.
- GET /customers: List customers with pagination and search.
- GET /customers/{customer_id}: Retrieve single customer profile.
- PATCH /customers/{customer_id}: Update customer details, metadata, or block status.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentTenant, DBSession
from app.modules.customers.schemas import (
    CustomerCreate,
    CustomerListResponse,
    CustomerRead,
    CustomerUpdate,
)
from app.modules.customers.service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a customer profile",
)
async def create_customer(
    request: CustomerCreate,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> CustomerRead:
    """Explicitly registers a new customer record under the tenant organization."""
    customer = await CustomerService.create_customer(
        session=session,
        organization_id=tenant_context.organization.id,
        request=request,
    )
    return CustomerRead.model_validate(customer)


@router.get(
    "",
    response_model=CustomerListResponse,
    status_code=status.HTTP_200_OK,
    summary="List customers directory",
)
async def list_customers(
    tenant_context: CurrentTenant,
    session: DBSession,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    search: Annotated[str | None, Query(description="Search by phone number or name")] = None,
) -> CustomerListResponse:
    """Lists customers belonging to the tenant with pagination and optional search."""
    items, total = await CustomerService.list_customers(
        session=session,
        organization_id=tenant_context.organization.id,
        page=page,
        page_size=page_size,
        search=search,
    )
    return CustomerListResponse(
        items=[CustomerRead.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerRead,
    status_code=status.HTTP_200_OK,
    summary="Get customer details by ID",
)
async def get_customer(
    customer_id: uuid.UUID,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> CustomerRead:
    """Retrieves a single customer profile, enforcing tenant boundary."""
    customer = await CustomerService.get_customer(
        session=session,
        organization_id=tenant_context.organization.id,
        customer_id=customer_id,
    )
    return CustomerRead.model_validate(customer)


@router.patch(
    "/{customer_id}",
    response_model=CustomerRead,
    status_code=status.HTTP_200_OK,
    summary="Update customer profile",
)
async def update_customer(
    customer_id: uuid.UUID,
    request: CustomerUpdate,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> CustomerRead:
    """Updates customer profile details, metadata, or blocklist status."""
    customer = await CustomerService.update_customer(
        session=session,
        organization_id=tenant_context.organization.id,
        customer_id=customer_id,
        request=request,
    )
    return CustomerRead.model_validate(customer)
