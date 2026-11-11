"""
Master API Router for Chatrio Backend (v1).
Combines and mounts all module routers under the `/api/v1` namespace.
"""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.conversations.router import router as conversations_router
from app.modules.customers.router import router as customers_router
from app.modules.messaging.router import router as messaging_router
from app.modules.orders.router import router as orders_router
from app.modules.organizations.router import router as organizations_router
from app.modules.products.router import router as products_router

api_v1_router = APIRouter()

# Mount module routers
api_v1_router.include_router(auth_router)
api_v1_router.include_router(organizations_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(customers_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(messaging_router)
