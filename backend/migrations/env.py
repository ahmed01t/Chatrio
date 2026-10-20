"""
Alembic Environment Script (Async SQLAlchemy).

This script is executed by Alembic whenever running migration commands:
- `alembic revision --autogenerate`: Compares `Base.metadata` with database schema.
- `alembic upgrade head`: Applies pending migrations to the database.
- `alembic downgrade -1`: Rolls back the last applied migration.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.db.models import Base

# Alembic Config object, providing access to values in alembic.ini
config = context.config

# Setup Python logging from alembic.ini if configured
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Dynamically set sqlalchemy.url from our application Settings (.env)
# This prevents hardcoding database passwords in alembic.ini
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Target metadata for Alembic 'autogenerate' detection
# Re-exported from app.db.models (contains organizations, users, organization_members)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates raw SQL statements without needing a live database connection.
    Useful for inspecting SQL scripts before running them on production.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Executes migrations synchronously inside an active connection context.
    Called via `connection.run_sync` by the async runner.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Detect column type changes (e.g. String length)
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Async runner for online migrations.

    Creates an async engine using NullPool (connection pooling is not needed
    for one-off migration executions), runs the migration, and cleans up.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live database."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
