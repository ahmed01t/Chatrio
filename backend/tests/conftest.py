from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import get_db
from app.core.config import Settings
from app.db.models import Base
from app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Provides isolated settings for test runs."""
    return Settings(
        APP_NAME="Chatrio Test API",
        VERSION="0.1.0-test",
        ENVIRONMENT="testing",
        DEBUG=True,
        ALLOWED_ORIGINS="http://testserver",
    )


@pytest.fixture
async def async_db_engine():
    """Creates an in-memory SQLite database engine with all tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def async_client(
    test_settings: Settings,
    async_db_engine,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Yields an AsyncClient for testing FastAPI routes with an in-memory database.
    """
    test_app = create_app(settings=test_settings)
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    test_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    """Synchronous test client for simple endpoint tests."""
    test_app = create_app(settings=test_settings)
    return TestClient(test_app)
