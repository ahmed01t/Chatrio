"""
Order and Order Fulfillment State Machine Business Logic Service.

Provides mission-critical services:
1. `OrderService`:
   - Atomic order placement with row-level inventory locks (`SELECT ... FOR UPDATE`).
   - Immutable historical line item snapshotting (`product_title`, `product_sku`, `unit_price`).
   - Strict directed graph state machine validation (`PENDING` -> `CONFIRMED` -> ...).
   - Cancellation with automated inventory release (`ORDER_RELEASE`).
   - Multi-tenant isolated order queries and pagination.
"""

import secrets
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.customers.service import CustomerService
from app.modules.orders.models import Order, OrderItem, OrderStatus, PaymentStatus
from app.modules.orders.schemas import (
    OrderCreate,
    OrderStatusUpdate,
    OrderUpdate,
)
from app.modules.products.models import InventoryChangeReason
from app.modules.products.schemas import InventoryAdjustmentRequest
from app.modules.products.service import InventoryService

# ==============================================================================
# State Machine Transition Graph
# ==============================================================================
VALID_ORDER_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
    OrderStatus.DELIVERED: set(),  # Terminal state
    OrderStatus.CANCELLED: set(),  # Terminal state
}


def generate_order_number() -> str:
    """Generates a human-readable unique order number: ORD-YYYYMMDD-XXXX."""
    date_str = datetime.now(UTC).strftime("%Y%m%d")
    random_suffix = secrets.token_hex(3).upper()
    return f"ORD-{date_str}-{random_suffix}"


class OrderService:
    """Service governing order lifecycle, calculations, and state machine transitions."""

    @staticmethod
    async def create_order(
        session: AsyncSession,
        organization_id: uuid.UUID,
        request: OrderCreate,
    ) -> Order:
        """
        Atomically creates a new order and reserves inventory for line items.

        Enforces: # tenant means organization_id must match for customer and conversation.
        1. Tenant validation for customer and optional conversation.
        2. Row-level stock locking & deduction via `InventoryService.adjust_stock`.
        3. Historical snapshotting of product title, SKU, and unit price.
        4. Calculation of subtotal and total amount.

        Raises:
            NotFoundException: If customer, conversation, or product does not exist in tenant.
            BadRequestException: If product is inactive or inventory is insufficient.
        """
        # 1. Validate customer belongs to this tenant
        await CustomerService.get_customer(
            session=session,
            organization_id=organization_id,
            customer_id=request.customer_id,
        )

        # 2. Validate optional conversation belongs to this tenant
        if request.conversation_id is not None:
            from app.modules.conversations.service import ConversationService

            await ConversationService.get_conversation(
                session=session,
                organization_id=organization_id,
                conversation_id=request.conversation_id,
            )

        # 3. Generate unique order number within this tenant
        order_number = generate_order_number()
        order_id = uuid.uuid4()

        # 4. Process line items and reserve inventory stock atomically
        subtotal = Decimal("0.00")
        order_items: list[OrderItem] = []

        for item_in in request.items:
            # Atomically adjust inventory with row-level lock
            # (raises INSUFFICIENT_STOCK if stock is unavailable)
            adjustment_req = InventoryAdjustmentRequest(
                change_amount=-item_in.quantity,
                reason=InventoryChangeReason.ORDER_RESERVE,
                reference_id=order_number,
            )
            product, _ = await InventoryService.adjust_stock(
                session=session,
                organization_id=organization_id,
                product_id=item_in.product_id,
                request=adjustment_req,
            )

            if not product.is_active:
                raise BadRequestException(
                    code="PRODUCT_INACTIVE",
                    message=f"Product '{product.title}' is inactive and cannot be ordered.",
                )

            unit_price = Decimal(str(product.price))
            item_total = unit_price * item_in.quantity
            subtotal += item_total

            order_item = OrderItem(
                id=uuid.uuid4(),
                organization_id=organization_id,
                order_id=order_id,
                product_id=product.id,
                product_title=product.title,
                product_sku=product.sku,
                unit_price=unit_price,
                quantity=item_in.quantity,
                total_price=item_total,
            )
            order_items.append(order_item)

        total_amount = subtotal + request.shipping_cost

        # 5. Build and persist Order
        order = Order(
            id=order_id,
            organization_id=organization_id,
            customer_id=request.customer_id,
            conversation_id=request.conversation_id,
            order_number=order_number,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.UNPAID,
            currency="USD",
            subtotal=subtotal,
            shipping_cost=request.shipping_cost,
            total_amount=total_amount,
            shipping_address=request.shipping_address,
            notes=request.notes,
            metadata_=request.metadata,
        )

        session.add(order)
        session.add_all(order_items)
        await session.flush()

        # Reload with items relation
        return await OrderService.get_order(session, organization_id, order_id)

    @staticmethod
    async def get_order(
        session: AsyncSession,
        organization_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> Order:
        """Retrieves a single order by ID with tenant isolation."""
        query = (
            select(Order)
            .options(selectinload(Order.items))
            .where(
                Order.organization_id == organization_id,
                Order.id == order_id,
            )
        )
        order = (await session.execute(query)).scalar_one_or_none()
        if order is None:
            raise NotFoundException(
                code="ORDER_NOT_FOUND",
                message="Order not found.",
            )
        return order

    @staticmethod
    async def list_orders(
        session: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID | None = None,
        status: OrderStatus | None = None,
        payment_status: PaymentStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], int]:
        """Lists tenant orders with optional filtering and pagination."""
        base_query = select(Order).where(Order.organization_id == organization_id)

        if customer_id is not None:
            base_query = base_query.where(Order.customer_id == customer_id)
        if status is not None:
            base_query = base_query.where(Order.status == status)
        if payment_status is not None:
            base_query = base_query.where(Order.payment_status == payment_status)

        # Count total matches
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await session.execute(count_query)).scalar_one()

        # Paginate results
        offset = (page - 1) * page_size
        items_query = (
            base_query.options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        orders = list((await session.execute(items_query)).scalars().all())

        return orders, total

    @staticmethod
    async def update_order(
        session: AsyncSession,
        organization_id: uuid.UUID,
        order_id: uuid.UUID,
        request: OrderUpdate,
    ) -> Order:
        """Updates delivery address, notes, payment status, or metadata of an order."""
        order = await OrderService.get_order(session, organization_id, order_id)

        if request.shipping_address is not None:
            order.shipping_address = request.shipping_address
        if request.notes is not None:
            order.notes = request.notes
        if request.payment_status is not None:
            order.payment_status = request.payment_status
        if request.metadata is not None:
            order.metadata_ = request.metadata

        await session.flush()
        return await OrderService.get_order(session, organization_id, order_id)

    @staticmethod
    async def update_status(
        session: AsyncSession,
        organization_id: uuid.UUID,
        order_id: uuid.UUID,
        request: OrderStatusUpdate,
    ) -> Order:
        """
        Advances an order's status enforcing the directed state machine.

        If target status is CANCELLED, triggers automatic inventory release.

        Raises:
            BadRequestException: If requested transition is forbidden by state machine rules.
        """
        order = await OrderService.get_order(session, organization_id, order_id)
        current_status = order.status
        target_status = request.status

        if target_status == current_status:
            return order

        allowed_transitions = VALID_ORDER_TRANSITIONS.get(current_status, set())
        if target_status not in allowed_transitions:
            raise BadRequestException(
                code="INVALID_ORDER_STATE_TRANSITION",
                message=f"Cannot transition order from {current_status} to {target_status}.",
                details={
                    "current_status": current_status,
                    "target_status": target_status,
                    "allowed_transitions": [s.value for s in allowed_transitions],
                },
            )

        if target_status == OrderStatus.CANCELLED:
            # Delegate cancellation to release inventory
            return await OrderService.cancel_order(session, organization_id, order_id)

        order.status = target_status
        await session.flush()
        return await OrderService.get_order(session, organization_id, order_id)

    @staticmethod
    async def cancel_order(
        session: AsyncSession,
        organization_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> Order:
        """
        Cancels an order and automatically releases reserved stock back to inventory.

        Raises:
            BadRequestException: If order is already in a terminal state (DELIVERED or CANCELLED).
        """
        order = await OrderService.get_order(session, organization_id, order_id)

        if order.status == OrderStatus.CANCELLED:
            raise BadRequestException(
                code="ORDER_ALREADY_CANCELLED",
                message="Order is already cancelled.",
            )

        if order.status == OrderStatus.DELIVERED:
            raise BadRequestException(
                code="CANNOT_CANCEL_DELIVERED_ORDER",
                message="Delivered orders cannot be cancelled.",
            )

        # Release inventory stock for each line item
        for item in order.items:
            release_req = InventoryAdjustmentRequest(
                change_amount=item.quantity,
                reason=InventoryChangeReason.ORDER_RELEASE,
                reference_id=order.order_number,
            )
            await InventoryService.adjust_stock(
                session=session,
                organization_id=organization_id,
                product_id=item.product_id,
                request=release_req,
            )

        order.status = OrderStatus.CANCELLED
        await session.flush()
        return await OrderService.get_order(session, organization_id, order_id)
