import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.session import build_engine_kwargs, get_async_session


class DummyModel(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "dummy_test_table"

    name: Mapped[str] = mapped_column(nullable=False)


def test_base_and_mixins_structure() -> None:
    """Verify that Base and mixins configure expected columns and types."""
    assert issubclass(Base, DeclarativeBase)

    table = DummyModel.__table__
    columns = table.columns

    # Verify ID column
    assert "id" in columns
    assert columns["id"].primary_key is True

    # Verify Timestamp columns
    assert "created_at" in columns
    assert "updated_at" in columns

    # Verify Soft Delete column
    assert "deleted_at" in columns
    assert columns["deleted_at"].nullable is True


def test_build_engine_kwargs_postgres() -> None:
    """Verify connection pool settings are enabled for PostgreSQL."""
    pg_url = "postgresql+asyncpg://user:pass@localhost:5432/dbname"
    kwargs = build_engine_kwargs(pg_url, is_debug=True)

    assert kwargs["echo"] is True
    assert kwargs["pool_size"] == 10
    assert kwargs["max_overflow"] == 20
    assert kwargs["pool_timeout"] == 30
    assert kwargs["pool_pre_ping"] is True


def test_build_engine_kwargs_sqlite() -> None:
    """Verify SQLite disables standard QueuePool options."""
    sqlite_url = "sqlite+aiosqlite:///:memory:"
    kwargs = build_engine_kwargs(sqlite_url, is_debug=False)

    assert kwargs["echo"] is False
    assert "pool_size" not in kwargs
    assert "max_overflow" not in kwargs


@pytest.mark.asyncio
async def test_async_session_generation() -> None:
    """Verify async session generation with an in-memory SQLite database."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    test_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with test_session_factory() as session:
        assert isinstance(session, AsyncSession)
        assert session.is_active is True

    await test_engine.dispose()


@pytest.mark.asyncio
async def test_get_async_session_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify get_async_session dependency yields session and closes cleanly."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    test_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Monkeypatch the module session factory to use our lightweight in-memory engine
    monkeypatch.setattr("app.db.session.async_session_factory", test_session_factory)

    async_gen = get_async_session()
    session = await anext(async_gen)

    assert isinstance(session, AsyncSession)

    # Clean up generator
    try:
        await anext(async_gen)
    except StopAsyncIteration:
        pass

    await test_engine.dispose()
