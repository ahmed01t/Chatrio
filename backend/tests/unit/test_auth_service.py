import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import decode_access_token
from app.db.models import Base, MemberRole
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.auth.service import AuthService, slugify


@pytest.fixture
async def async_test_session() -> AsyncSession:
    """Creates a temporary in-memory SQLite database and yields an active session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


def test_slugify() -> None:
    """Verify that slugify handles spaces, special characters, and uppercase."""
    assert slugify("Ahmed's Cool Store!") == "ahmeds-cool-store"
    assert slugify("  TECH & Gadgets  ") == "tech-gadgets"
    assert slugify("---Leading and Trailing---") == "leading-and-trailing"


@pytest.mark.asyncio
async def test_register_merchant_success(async_test_session: AsyncSession) -> None:
    """Verify successful merchant registration creates User, Org, Member and JWT."""
    request = RegisterRequest(
        email="merchant@example.com",
        password="SecurePassword123!",
        full_name="Ahmed Khan",
        organization_name="Ahmed Apparel",
    )

    user, org, token = await AuthService.register_merchant(async_test_session, request)

    assert user.email == "merchant@example.com"
    assert user.full_name == "Ahmed Khan"
    assert user.is_active is True
    assert user.password_hash != "SecurePassword123!"

    assert org.name == "Ahmed Apparel"
    assert org.slug == "ahmed-apparel"

    # Decode and verify JWT
    payload = decode_access_token(token)
    assert payload["sub"] == str(user.id)
    assert payload["org_id"] == str(org.id)
    assert payload["role"] == MemberRole.OWNER.value


@pytest.mark.asyncio
async def test_register_merchant_duplicate_email(async_test_session: AsyncSession) -> None:
    """Verify registering with an existing email raises ConflictException."""
    request = RegisterRequest(
        email="duplicate@example.com",
        password="Password123!",
        full_name="First User",
        organization_name="First Store",
    )
    await AuthService.register_merchant(async_test_session, request)

    # Attempt second registration with same email (even with different case)
    duplicate_request = RegisterRequest(
        email="DUPLICATE@example.com",
        password="Password456!",
        full_name="Second User",
        organization_name="Second Store",
    )

    with pytest.raises(ConflictException) as exc_info:
        await AuthService.register_merchant(async_test_session, duplicate_request)

    assert exc_info.value.code == "EMAIL_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_register_merchant_duplicate_explicit_slug(async_test_session: AsyncSession) -> None:
    """Verify requesting an explicitly taken slug raises ConflictException."""
    request1 = RegisterRequest(
        email="user1@example.com",
        password="Password123!",
        full_name="User One",
        organization_name="Store One",
        organization_slug="custom-brand",
    )
    await AuthService.register_merchant(async_test_session, request1)

    request2 = RegisterRequest(
        email="user2@example.com",
        password="Password123!",
        full_name="User Two",
        organization_name="Store Two",
        organization_slug="custom-brand",
    )

    with pytest.raises(ConflictException) as exc_info:
        await AuthService.register_merchant(async_test_session, request2)

    assert exc_info.value.code == "SLUG_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_authenticate_user_success(async_test_session: AsyncSession) -> None:
    """Verify logging in with valid credentials returns user, org, and token."""
    reg_request = RegisterRequest(
        email="login_test@example.com",
        password="MySecretPassword123!",
        full_name="Login User",
        organization_name="Login Org",
    )
    registered_user, org, _ = await AuthService.register_merchant(async_test_session, reg_request)

    login_request = LoginRequest(
        email="LOGIN_TEST@example.com",  # Test case insensitivity
        password="MySecretPassword123!",
    )
    user, active_org, token = await AuthService.authenticate_user(async_test_session, login_request)

    assert user.id == registered_user.id
    assert active_org.id == org.id

    payload = decode_access_token(token)
    assert payload["sub"] == str(user.id)
    assert payload["org_id"] == str(org.id)


@pytest.mark.asyncio
async def test_authenticate_user_invalid_password(async_test_session: AsyncSession) -> None:
    """Verify logging in with incorrect password raises UnauthorizedException."""
    reg_request = RegisterRequest(
        email="wrong_pass@example.com",
        password="CorrectPassword123!",
        full_name="User",
        organization_name="Store",
    )
    await AuthService.register_merchant(async_test_session, reg_request)

    login_request = LoginRequest(
        email="wrong_pass@example.com",
        password="WrongPassword999!",
    )

    with pytest.raises(UnauthorizedException) as exc_info:
        await AuthService.authenticate_user(async_test_session, login_request)

    assert exc_info.value.code == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_authenticate_user_nonexistent_email(async_test_session: AsyncSession) -> None:
    """Verify logging in with non-existent email raises UnauthorizedException."""
    login_request = LoginRequest(
        email="does_not_exist@example.com",
        password="AnyPassword123!",
    )

    with pytest.raises(UnauthorizedException) as exc_info:
        await AuthService.authenticate_user(async_test_session, login_request)

    assert exc_info.value.code == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_authenticate_user_inactive_account(async_test_session: AsyncSession) -> None:
    """Verify inactive user accounts cannot log in."""
    reg_request = RegisterRequest(
        email="inactive@example.com",
        password="Password123!",
        full_name="Inactive User",
        organization_name="Inactive Store",
    )
    user, _, _ = await AuthService.register_merchant(async_test_session, reg_request)

    # Manually deactivate user
    user.is_active = False
    await async_test_session.flush()

    login_request = LoginRequest(
        email="inactive@example.com",
        password="Password123!",
    )

    with pytest.raises(UnauthorizedException) as exc_info:
        await AuthService.authenticate_user(async_test_session, login_request)

    assert exc_info.value.code == "ACCOUNT_INACTIVE"
