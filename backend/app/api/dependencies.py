"""
FastAPI Route Dependencies and Security Guards.

This module provides reusable dependencies:
1. `get_db`: Yields an active asynchronous database session.
2. `get_current_user`: Extracts and validates JWT bearer token, resolving the User.
3. `get_current_tenant`: Enforces tenant boundary isolation and verifies user membership.
4. `require_roles`: Guard ensuring user has one of the allowed MemberRoles.
"""

import uuid
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.db.session import get_async_session
from app.modules.auth.models import User
from app.modules.organizations.models import MemberRole, Organization, OrganizationMember

settings = get_settings()

# OAuth2 scheme for extracting Bearer token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


@dataclass
class TenantContext:
    """Holds active tenant organization, user membership, and permissions."""

    organization: Organization
    member: OrganizationMember
    user: User


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding an active database session for the current request."""
    async for session in get_async_session():
        yield session


# Common reusable type aliases for dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db)]
AuthToken = Annotated[str | None, Depends(oauth2_scheme)]


async def get_current_user(
    token: AuthToken,
    session: DBSession,
) -> User:
    """
    Validates JWT Bearer token and returns authenticated User.

    Raises:
        UnauthorizedException: If token is missing, expired, invalid, or user inactive.
    """
    if not token:
        raise UnauthorizedException(
            code="UNAUTHORIZED",
            message="Authentication credentials were not provided.",
        )

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError as err:
        raise UnauthorizedException(
            code="TOKEN_EXPIRED",
            message="Authentication token has expired. Please log in again.",
        ) from err
    except jwt.InvalidTokenError as err:
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="Invalid authentication token.",
        ) from err

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="Token payload is missing subject identifier.",
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError as err:
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="Invalid user identifier format in token.",
        ) from err

    user = await session.get(User, user_uuid)
    if user is None:
        raise UnauthorizedException(
            code="USER_NOT_FOUND",
            message="User account no longer exists.",
        )

    if not user.is_active:
        raise UnauthorizedException(
            code="ACCOUNT_INACTIVE",
            message="User account has been disabled.",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_tenant(
    token: AuthToken,
    user: CurrentUser,
    session: DBSession,
) -> TenantContext:
    """
    Resolves the active organization tenant from the JWT claims.

    Enforces strict multi-tenant boundary:
    Verifies that the authenticated user is an active member of the organization.

    Raises:
        ForbiddenException: If user does not belong to the requested organization.
    """
    # Token has already been validated by get_current_user, decode payload
    if not token:
        raise UnauthorizedException(
            code="UNAUTHORIZED",
            message="Authentication credentials were not provided.",
        )

    payload = decode_access_token(token)
    org_id_str: str | None = payload.get("org_id")

    if not org_id_str:
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="Token does not contain an active organization context.",
        )

    try:
        org_uuid = uuid.UUID(org_id_str)
    except ValueError as err:
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="Invalid organization identifier in token.",
        ) from err

    # Query membership and organization in one query
    stmt = (
        select(OrganizationMember, Organization)
        .join(Organization, OrganizationMember.organization_id == Organization.id)
        .where(
            OrganizationMember.organization_id == org_uuid,
            OrganizationMember.user_id == user.id,
        )
    )
    result = (await session.execute(stmt)).first()

    if result is None:
        raise ForbiddenException(
            code="FORBIDDEN_TENANT_ACCESS",
            message="You do not have access to this organization.",
        )

    member, organization = result
    return TenantContext(organization=organization, member=member, user=user)


CurrentTenant = Annotated[TenantContext, Depends(get_current_tenant)]


def require_roles(
    allowed_roles: list[MemberRole],
) -> Callable[[TenantContext], TenantContext]:
    """
    Factory creating a role-based access control dependency guard.
    Ensures the user holds one of the specified roles within the active tenant.
    """

    def role_checker(
        tenant_context: CurrentTenant,
    ) -> TenantContext:
        if tenant_context.member.role not in allowed_roles:
            raise ForbiddenException(
                code="INSUFFICIENT_PERMISSIONS",
                message=(
                    f"Action requires one of the following roles: "
                    f"{[r.value for r in allowed_roles]}. "
                    f"Your role is {tenant_context.member.role.value}."
                ),
            )
        return tenant_context

    return role_checker
