"""
Deterministic Multi-Tenant Scoped AI Agent Tools.

Provides server-gated tools for the LangGraph agent:
1. `search_catalog`: Semantic & keyword catalog search scoped strictly to `organization_id`.
2. `get_product_details`: In-depth product specification and inventory retrieval.
3. `draft_order`: Server-side price resolution and inventory reservation via OrderService.
4. `request_human_agent`: Toggles `conversation.is_ai_active = False` for human takeover.

Security Guarantees:
- `organization_id` and `customer_id` are injected by the backend runtime, NEVER visible to the LLM.
- The LLM cannot set custom product prices or discounts; all financial figures are calculated
  directly from PostgreSQL.
"""

import json
import uuid
from typing import Any

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.conversations.schemas import ConversationTakeoverUpdate
from app.modules.conversations.service import ConversationService
from app.modules.orders.schemas import OrderCreate, OrderItemCreate
from app.modules.orders.service import OrderService
from app.modules.products.service import ProductService


class SearchCatalogArgs(BaseModel):
    """Arguments for searching the product catalog."""

    query: str = Field(description="Search keyword, product name, or category")


class GetProductDetailsArgs(BaseModel):
    """Arguments for fetching product details."""

    product_id: str = Field(description="UUID string of the product")


class DraftOrderArgs(BaseModel):
    """Arguments for drafting a customer order."""

    items: list[dict[str, Any]] = Field(
        description="List of items with 'product_id' (str) and 'quantity' (int)"
    )
    delivery_address: str | None = Field(
        default=None,
        description="Customer delivery or shipping address if provided",
    )
    notes: str | None = Field(
        default=None,
        description="Optional customer notes or instructions",
    )


class RequestHumanAgentArgs(BaseModel):
    """Arguments for requesting a human agent."""

    reason: str = Field(description="Reason for handing over to a human specialist")


def create_agent_tools(
    session: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> list[BaseTool]:
    """
    Constructs tenant-bound tool instances for the AI agent.

    Args:
        session: Active asynchronous database session.
        organization_id: Authenticated merchant tenant organization UUID.
        customer_id: Verified WhatsApp customer UUID.
        conversation_id: Active conversation session UUID.

    Returns:
        List of LangChain BaseTool instances with closure-bound tenant context.
    """

    @tool("search_catalog", args_schema=SearchCatalogArgs)
    async def search_catalog(query: str) -> str:
        """
        Searches the merchant catalog for active products matching the customer query.
        Returns product titles, IDs, prices, currencies, and stock availability.
        """
        try:
            items, _ = await ProductService.list_products(
                session=session,
                organization_id=organization_id,
                search=query,
                is_active=True,
                page_size=5,
            )
            if not items:
                return json.dumps({"results": [], "message": f"No products found for '{query}'."})

            results: list[dict[str, Any]] = [
                {
                    "product_id": str(p.id),
                    "title": p.title,
                    "price": str(p.price),
                    "currency": p.currency,
                    "in_stock": p.stock_quantity > 0,
                    "available_quantity": p.stock_quantity,
                    "sku": p.sku,
                }
                for p in items
            ]
            return json.dumps({"results": results})
        except Exception as err:
            return json.dumps({"error": f"Failed to search catalog: {err}"})

    @tool("get_product_details", args_schema=GetProductDetailsArgs)
    async def get_product_details(product_id: str) -> str:
        """
        Retrieves detailed information for a specific product including description,
        price, exact inventory stock, and categories.
        """
        try:
            prod_uuid = uuid.UUID(product_id.strip())
        except ValueError:
            return json.dumps({"error": "Invalid product ID format."})

        try:
            product = await ProductService.get_product(
                session=session,
                organization_id=organization_id,
                product_id=prod_uuid,
            )
            if not product.is_active:
                return json.dumps({"error": "This product is currently inactive/unavailable."})

            details = {
                "product_id": str(product.id),
                "title": product.title,
                "description": product.description or "",
                "price": str(product.price),
                "currency": product.currency,
                "stock_quantity": product.stock_quantity,
                "in_stock": product.stock_quantity > 0,
                "sku": product.sku,
                "categories": [c.name for c in product.categories],
            }
            return json.dumps(details)
        except AppException as err:
            return json.dumps({"error": err.message})
        except Exception as err:
            return json.dumps({"error": f"Failed to fetch product details: {err}"})

    @tool("draft_order", args_schema=DraftOrderArgs)
    async def draft_order(
        items: list[dict[str, Any]],
        delivery_address: str | None = None,
        notes: str | None = None,
    ) -> str:
        """
        Creates a verified order draft in the database.
        The backend automatically verifies stock and pulls official prices from the database.
        The LLM CANNOT specify prices or discounts.
        """
        try:
            order_items: list[OrderItemCreate] = []
            for item in items:
                pid_raw = item.get("product_id", "")
                qty_raw = int(item.get("quantity", 1))
                if qty_raw <= 0:
                    return json.dumps({"error": "Quantity must be greater than zero."})
                order_items.append(
                    OrderItemCreate(
                        product_id=uuid.UUID(str(pid_raw).strip()),
                        quantity=qty_raw,
                    )
                )

            order_create = OrderCreate(
                customer_id=customer_id,
                conversation_id=conversation_id,
                items=order_items,
                delivery_address=delivery_address,
                notes=notes,
            )

            order = await OrderService.create_order(
                session=session,
                organization_id=organization_id,
                request=order_create,
            )

            response_data = {
                "order_id": str(order.id),
                "order_number": order.order_number,
                "status": order.status.value,
                "subtotal": str(order.subtotal),
                "shipping_cost": str(order.shipping_cost),
                "total": str(order.total_amount),
                "currency": order.currency,
                "items": [
                    {
                        "product_title": item.product_title,
                        "quantity": item.quantity,
                        "unit_price": str(item.unit_price),
                        "total_price": str(item.total_price),
                    }
                    for item in order.items
                ],
                "message": (
                    f"Order #{order.order_number} created successfully. "
                    f"Total: {order.total_amount} {order.currency}."
                ),
            }
            return json.dumps(response_data)
        except AppException as err:
            return json.dumps({"error": err.message})
        except Exception as err:
            return json.dumps({"error": f"Failed to draft order: {err}"})

    @tool("request_human_agent", args_schema=RequestHumanAgentArgs)
    async def request_human_agent(reason: str) -> str:
        """
        Pauses AI automation for this conversation and transfers the customer to a human agent.
        Use when customer is frustrated, asks for a human, or has an issue you cannot solve.
        """
        try:
            await ConversationService.update_takeover(
                session=session,
                organization_id=organization_id,
                conversation_id=conversation_id,
                request=ConversationTakeoverUpdate(is_ai_active=False),
            )
            return json.dumps(
                {
                    "status": "human_takeover_activated",
                    "reason": reason,
                    "message": (
                        "A human customer service specialist has been notified and will "
                        "join this chat shortly. AI automation is paused."
                    ),
                }
            )
        except AppException as err:
            return json.dumps({"error": err.message})
        except Exception as err:
            return json.dumps({"error": f"Failed to request human agent: {err}"})

    return [search_catalog, get_product_details, draft_order, request_human_agent]
