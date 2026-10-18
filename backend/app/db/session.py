"""
Database Engine and Asynchronous Session Management.

This module provides:
1. `engine`: Asynchronous SQLAlchemy engine with connection pooling.
2. `async_session_factory`: Session maker creating AsyncSession instances.
3. `get_async_session`: Dependency generator yielding an isolated session per request.
4. `close_db_connection`: Cleanup function to gracefully dispose of connection pools.
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()


def build_engine_kwargs(database_url: str, is_debug: bool = False) -> dict[str, Any]:
    """
    Constructs optimized engine arguments based on database dialect.

    For PostgreSQL:
    - `pool_size`: Number of connections to keep permanently open in the pool.
    - `max_overflow`: Extra connections to open temporarily during traffic spikes.
    - `pool_timeout`: Max seconds to wait for a free connection before throwing an error.
    - `pool_pre_ping`: Checks connection health before using it, preventing stale connection errors.

    For SQLite (used in lightweight unit tests):
    - Connection pooling parameters differ, so we omit pool_size/max_overflow.
    """
    kwargs: dict[str, Any] = {
        "echo": is_debug,
    }

    # SQLite does not support standard QueuePool options like pool_size or max_overflow
    if "sqlite" in database_url.lower():
        return kwargs

    kwargs.update(
        {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_pre_ping": True,
        }
    )
    return kwargs


# Create the shared async database engine using application settings
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    **build_engine_kwargs(settings.DATABASE_URL, settings.DEBUG),
)

# Async session factory: creates new AsyncSession objects for database operations.
# - expire_on_commit=False prevents attributes from expiring after commit,
#   which is essential in async workflows to prevent implicit lazy-loading crashes.
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator for FastAPI and background tasks.

    Provides a clean, isolated database session per request:
    - Commits the transaction if the request finishes without errors.
    - Automatically rolls back the transaction if any unhandled exception occurs.
    - Closes the session and returns the connection to the pool when finished.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connection() -> None:
    """
    Gracefully disposes of all pooled database connections.
    Should be called during application shutdown.
    """
    await engine.dispose()
