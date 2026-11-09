"""
Central Database Models Registry.

This module re-exports all SQLAlchemy ORM models across all domain modules.
Importing this module ensures that:
1. All models are loaded into Python memory.
2. `Base.metadata` registers every database table.
3. Alembic migrations can discover all models automatically for auto-generating migrations.
"""

from app.db.base import Base
from app.modules.auth.models import User
from app.modules.conversations.models import (
    Conversation,
    ConversationChannel,
    ConversationStatus,
    Message,
    MessageContentType,
    MessageDirection,
    MessageSenderType,
    MessageStatus,
)
from app.modules.customers.models import Customer
from app.modules.messaging.models import (
    OutboxMessage,
    OutboxMessageType,
    OutboxStatus,
)
from app.modules.orders.models import (
    Order,
    OrderItem,
    OrderStatus,
    PaymentStatus,
)
from app.modules.organizations.models import MemberRole, Organization, OrganizationMember
from app.modules.products.models import (
    Category,
    InventoryChangeReason,
    InventoryLog,
    Product,
    ProductCategory,
)

__all__ = [
    "Base",
    "Category",
    "Conversation",
    "ConversationChannel",
    "ConversationStatus",
    "Customer",
    "InventoryChangeReason",
    "InventoryLog",
    "MemberRole",
    "Message",
    "MessageContentType",
    "MessageDirection",
    "MessageSenderType",
    "MessageStatus",
    "Order",
    "OrderItem",
    "OrderStatus",
    "Organization",
    "OrganizationMember",
    "OutboxMessage",
    "OutboxMessageType",
    "OutboxStatus",
    "PaymentStatus",
    "Product",
    "ProductCategory",
    "User",
]
