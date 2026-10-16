from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import Settings, get_settings


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
#create a function and all settings from .env file is imported into this function and it will be called when the app is started for configuration fast api with settings and middleware and routes
# create_app is used for creating app and it will be called when the app is started for configuration fast api with settings and middleware and routes
def create_app(settings: Settings | None = None) -> FastAPI:
    current_settings = settings or get_settings()

    app = FastAPI(
        title=current_settings.APP_NAME,
        version=current_settings.VERSION,
        docs_url="/docs" if current_settings.DEBUG else None,
        redoc_url="/redoc" if current_settings.DEBUG else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=current_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check() -> HealthResponse:
        return HealthResponse(
            status="ok",
            app_name=current_settings.APP_NAME,
            version=current_settings.VERSION,
            environment=current_settings.ENVIRONMENT,
        )

    return app


app = create_app()
