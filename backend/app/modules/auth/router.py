"""
Authentication API Endpoints.

Provides public and protected endpoints for:
- POST /register: Register a new merchant and organization.
- POST /login: Authenticate credentials and receive a JWT access token.
- GET /me: Retrieve current authenticated user profile and tenant role.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import TenantContext, get_current_tenant, get_db
from app.core.config import get_settings
from app.modules.auth.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserProfileResponse,
    UserRead,
)
from app.modules.auth.service import AuthService
from app.modules.organizations.schemas import OrganizationRead

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentTenant = Annotated[TenantContext, Depends(get_current_tenant)]


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new merchant organization and owner account",
)
async def register(
    request: RegisterRequest,
    session: DBSession,
) -> AuthResponse:
    """
    Creates an organization, owner user account, and membership
    in a single atomic transaction.
    """
    user, org, access_token = await AuthService.register_merchant(session, request)

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead.model_validate(user),
        organization=OrganizationRead.model_validate(org),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign in with email and password",
)
async def login(
    request: LoginRequest,
    session: DBSession,
) -> AuthResponse:
    """Authenticates email and password credentials, returning a JWT access token."""
    user, org, access_token = await AuthService.authenticate_user(session, request)

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead.model_validate(user),
        organization=OrganizationRead.model_validate(org),
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user profile and active tenant context",
)
async def get_me(
    tenant_context: CurrentTenant,
) -> UserProfileResponse:
    """
    Protected route returning current user profile, active organization,
    and assigned role.
    """
    user = tenant_context.user
    org = tenant_context.organization
    member = tenant_context.member

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        organization_id=org.id,
        organization_name=org.name,
        role=member.role,
    )
