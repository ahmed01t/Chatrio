import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, MemberRole, Organization, OrganizationMember, User


def test_models_metadata_registration() -> None:
    """Verify that all 3 models register their tables in Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {"organizations", "users", "organization_members"}

    assert expected_tables.issubset(table_names), (
        f"Expected tables {expected_tables} to be in Base.metadata, found: {table_names}"
    )


def test_organization_table_structure() -> None:
    """Verify organization columns, primary key, and slug constraints."""
    org_table = Base.metadata.tables["organizations"]
    cols = org_table.columns

    assert "id" in cols
    assert cols["id"].primary_key is True
    assert "name" in cols
    assert cols["name"].nullable is False
    assert "slug" in cols
    assert cols["slug"].unique is True
    assert "created_at" in cols
    assert "updated_at" in cols


def test_user_table_structure() -> None:
    """Verify user columns, primary key, and email constraints."""
    user_table = Base.metadata.tables["users"]
    cols = user_table.columns

    assert "id" in cols
    assert cols["id"].primary_key is True
    assert "email" in cols
    assert cols["email"].unique is True
    assert "password_hash" in cols
    assert "full_name" in cols
    assert "is_active" in cols
    assert "created_at" in cols
    assert "updated_at" in cols


def test_organization_member_table_structure() -> None:
    """Verify organization_members columns, foreign keys, and unique constraint."""
    member_table = Base.metadata.tables["organization_members"]
    cols = member_table.columns

    assert "id" in cols
    assert cols["id"].primary_key is True
    assert "organization_id" in cols
    assert "user_id" in cols
    assert "role" in cols

    # Verify foreign keys
    fk_targets = {fk.target_fullname for fk in member_table.foreign_keys}
    assert "organizations.id" in fk_targets
    assert "users.id" in fk_targets

    # Verify unique constraint on (organization_id, user_id)
    unique_constraints = [
        [c.name for c in uq.columns] for uq in member_table.constraints if hasattr(uq, "columns")
    ]
    assert ["organization_id", "user_id"] in unique_constraints


@pytest.mark.asyncio
async def test_in_memory_model_crud_and_relationships() -> None:
    """Verify creating records and querying relationships using an in-memory SQLite database."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    # Create all tables in memory
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    org_id = uuid.uuid4()
    user_id = uuid.uuid4()

    async with test_session_factory() as session:
        org = Organization(
            id=org_id,
            name="Ahmed Tech Store",
            slug="ahmed-tech-store",
        )
        user = User(
            id=user_id,
            email="ahmed@example.com",
            password_hash="fake_bcrypt_hash",
            full_name="Ahmed Khan",
            is_active=True,
        )
        membership = OrganizationMember(
            organization_id=org_id,
            user_id=user_id,
            role=MemberRole.OWNER,
        )

        session.add_all([org, user, membership])
        await session.commit()

    # Query back and verify records
    async with test_session_factory() as session:
        db_org = await session.get(Organization, org_id)
        assert db_org is not None
        assert db_org.name == "Ahmed Tech Store"
        assert db_org.slug == "ahmed-tech-store"

        db_user = await session.get(User, user_id)
        assert db_user is not None
        assert db_user.email == "ahmed@example.com"
        assert db_user.is_active is True

    await test_engine.dispose()
