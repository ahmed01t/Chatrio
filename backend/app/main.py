"""
Main FastAPI Application Entrypoint.

Initializes FastAPI, registers CORS middleware, custom exception handlers,
and mounts API v1 routes.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.router import api_v1_router
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.db.session import close_db_connection


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and graceful shutdown."""
    yield
    # Gracefully close pooled database connections upon shutdown
    await close_db_connection()


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Factory function to instantiate and configure the FastAPI application.
    """
    current_settings = settings or get_settings()

    app = FastAPI(
        title=current_settings.APP_NAME,
        version=current_settings.VERSION,
        docs_url="/docs" if current_settings.DEBUG else None,
        redoc_url="/redoc" if current_settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Cross-Origin Resource Sharing (CORS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=current_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Standardized Exception Handler for Application Errors
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    # Health check endpoint
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check() -> HealthResponse:
        return HealthResponse(
            status="ok",
            app_name=current_settings.APP_NAME,
            version=current_settings.VERSION,
            environment=current_settings.ENVIRONMENT,
        )

    # Mount API v1 router
    app.include_router(api_v1_router, prefix=current_settings.API_V1_PREFIX)

    return app


app = create_app()
