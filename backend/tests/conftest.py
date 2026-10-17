import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


# A fixture provides reusable test setup (e.g. database connection or test client).
# Pytest automatically injects fixtures into test functions when requested.
@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        APP_NAME="Chatrio Test API",
        VERSION="0.1.0-test",
        ENVIRONMENT="testing",
        DEBUG=True,
        ALLOWED_ORIGINS="http://testserver",
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    test_app = create_app(settings=test_settings)
    return TestClient(test_app)
