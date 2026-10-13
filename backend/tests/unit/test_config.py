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


def test_cors_origins_parsing() -> None:
    settings = Settings(ALLOWED_ORIGINS="http://localhost:3000, https://app.example.com")
    origins = settings.cors_origins
    assert len(origins) == 2
    assert "http://localhost:3000" in origins
    assert "https://app.example.com" in origins
