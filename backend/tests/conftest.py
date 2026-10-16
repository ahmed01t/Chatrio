import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
#A fixture provides reusable data or setup for tests, such as a database connection, test user, or test client. You don't need to call the fixture function yourself; pytest manages it.
# fixture is used to provide test data to the tests and it will be called when the app is started for configuration fast api with settings and middleware and routes
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
