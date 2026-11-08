"""
Order Management & Fulfillment API Endpoints.

Provides tenant-scoped endpoints for:
- POST /orders: Place a new order with atomic inventory reservation.
- GET /orders: List tenant orders with status/customer filters and pagination.
- GET /orders/{id}: Retrieve detailed order records with snapshots and items.
- PATCH /orders/{id}: Update order delivery address, notes, or payment status.
- PATCH /orders/{id}/status: Advance state machine status.
- POST /orders/{id}/cancel: Cancel order and release reserved inventory.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentTenant, DBSession
from app.modules.orders.models import OrderStatus, PaymentStatus
from app.modules.orders.schemas import (
    OrderCreate,
    OrderListResponse,
    OrderRead,
    OrderStatusUpdate,
    OrderUpdate,
)
from app.modules.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders & Fulfillment"])


@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
)
async def create_order(
    request: OrderCreate,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> OrderRead:
    """
    Creates a new order with row-level stock locks and price snapshotting.

    Atomically deducts available inventory stock. If stock is insufficient,
    the entire operation fails with a 400 error.
    """
    order = await OrderService.create_order(
        session=session,
        organization_id=tenant_context.organization.id,
        request=request,
    )
    return OrderRead.model_validate(order)


@router.get(
    "",
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="List store orders",
)
async def list_orders(
    tenant_context: CurrentTenant,
    session: DBSession,
    customer_id: Annotated[
        uuid.UUID | None, Query(description="Filter orders by customer UUID")
    ] = None,
    order_status: Annotated[
        OrderStatus | None,
        Query(alias="status", description="Filter by order lifecycle status"),
    ] = None,
    payment_status: Annotated[
        PaymentStatus | None,
        Query(description="Filter by payment settlement status"),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> OrderListResponse:
    """Lists orders belonging strictly to the active tenant organization."""
    orders, total = await OrderService.list_orders(
        session=session,
        organization_id=tenant_context.organization.id,
        customer_id=customer_id,
        status=order_status,
        payment_status=payment_status,
        page=page,
        page_size=page_size,
    )
    return OrderListResponse(
        items=[OrderRead.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{order_id}",
    response_model=OrderRead,
    status_code=status.HTTP_200_OK,
    summary="Get order details",
)
async def get_order(
    order_id: uuid.UUID,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> OrderRead:
    """Retrieves full order details including line item price snapshots."""
    order = await OrderService.get_order(
        session=session,
        organization_id=tenant_context.organization.id,
        order_id=order_id,
    )
    return OrderRead.model_validate(order)


@router.patch(
    "/{order_id}",
    response_model=OrderRead,
    status_code=status.HTTP_200_OK,
    summary="Update order details",
)
async def update_order(
    order_id: uuid.UUID,
    request: OrderUpdate,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> OrderRead:
    """Updates shipping address, delivery notes, or payment status."""
    order = await OrderService.update_order(
        session=session,
        organization_id=tenant_context.organization.id,
        order_id=order_id,
        request=request,
    )
    return OrderRead.model_validate(order)


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    status_code=status.HTTP_200_OK,
    summary="Advance order status",
)
async def update_order_status(
    order_id: uuid.UUID,
    request: OrderStatusUpdate,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> OrderRead:
    """
    Advances the order's status along the state machine.

    If target status is CANCELLED, reserved stock is automatically released.
    """
    order = await OrderService.update_status(
        session=session,
        organization_id=tenant_context.organization.id,
        order_id=order_id,
        request=request,
    )
    return OrderRead.model_validate(order)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderRead,
    status_code=status.HTTP_200_OK,
    summary="Cancel order and release stock",
)
async def cancel_order(
    order_id: uuid.UUID,
    tenant_context: CurrentTenant,
    session: DBSession,
) -> OrderRead:
    """
    Cancels an active order and releases reserved inventory back to available stock.
    """
    order = await OrderService.cancel_order(
        session=session,
        organization_id=tenant_context.organization.id,
        order_id=order_id,
    )
    return OrderRead.model_validate(order)
