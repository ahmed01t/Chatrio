from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings Model (Pydantic).

    Pydantic automatically reads values from your '.env' file or your system's
    environment variables. It checks that every setting has the correct type
    (e.g. integer, string, boolean) before your server even starts.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra variables in .env without crashing
    )

    # --------------------------------------------------------------------------
    # 1. Basic Application Information
    # --------------------------------------------------------------------------
    APP_NAME: str = Field(default="Chatrio API", description="Name of the application")
    VERSION: str = Field(default="0.1.0", description="Current API release version")
    ENVIRONMENT: str = Field(
        default="development",
        description="Runtime environment: development, staging, or production",
    )
    DEBUG: bool = Field(default=True, description="Debug mode flag")
    API_V1_PREFIX: str = Field(default="/api/v1", description="Prefix for v1 routes")

    # --------------------------------------------------------------------------
    # 2. CORS (Cross-Origin Resource Sharing)
    # --------------------------------------------------------------------------
    # Frontend URLs that are permitted to send requests to this backend.
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    # --------------------------------------------------------------------------
    # 3. Database & Cache Connections
    # --------------------------------------------------------------------------
    # Connection string for PostgreSQL (using the asynchronous asyncpg driver).
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgrespassword@localhost:5432/chatrio_db",
        description="PostgreSQL async connection string",
    )

    # Connection string for Redis (used for BullMQ queues and message debouncing).
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # --------------------------------------------------------------------------
    # 4. Authentication & Security (JWT)
    # --------------------------------------------------------------------------
    # Secret key used to sign JSON Web Tokens (digital keycards).
    JWT_SECRET: str = Field(
        default="dev-super-secret-jwt-key-change-this-in-production-min-32-chars-long",
        description="Secret key for signing JWT tokens",
    )
    # Algorithm used to sign JWT tokens (HS256 is the standard HMAC-SHA256).
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT cryptographic algorithm",
    )
    # How many minutes an access token remains valid before the user must re-authenticate.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="Access token expiration window in minutes",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Converts the comma-separated ALLOWED_ORIGINS string into a clean Python list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings object.
    Using @lru_cache ensures the .env file is read once, not on every incoming request.
    """
    return Settings()
