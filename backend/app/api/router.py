"""
Master API Router for Chatrio Backend (v1).

Combines and mounts all module routers under the `/api/v1` namespace.
"""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.products.router import router as products_router

api_v1_router = APIRouter()

# Mount module routers
api_v1_router.include_router(auth_router)
api_v1_router.include_router(products_router)
