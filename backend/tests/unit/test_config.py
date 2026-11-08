from app.core.config import Settings


def test_settings_default_values() -> None:
    settings = Settings(
        APP_NAME="Chatrio API",
        VERSION="0.1.0",
        ENVIRONMENT="development",
    )
    assert settings.APP_NAME == "Chatrio API"
    assert settings.VERSION == "0.1.0"
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is True
    assert settings.API_V1_PREFIX == "/api/v1"
    assert "postgresql+asyncpg://" in settings.DATABASE_URL
    assert "redis://" in settings.REDIS_URL
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
    # Meta WhatsApp settings
    assert settings.META_API_VERSION == "v21.0"
    assert settings.META_VERIFY_TOKEN == "chatrio-webhook-verify-token-dev"
    assert settings.META_APP_SECRET == "dev-meta-app-secret-placeholder"
    # Sliding window debounce settings
    assert settings.WHATSAPP_DEBOUNCE_SECONDS == 2.5
    assert settings.WHATSAPP_DEBOUNCE_MAX_WAIT_SECONDS == 8.0


def test_cors_origins_parsing() -> None:
    settings = Settings(ALLOWED_ORIGINS="http://localhost:3000, https://app.example.com")
    origins = settings.cors_origins
    assert len(origins) == 2
    assert "http://localhost:3000" in origins
    assert "https://app.example.com" in origins
