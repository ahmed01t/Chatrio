"""
Authentication and Merchant Registration Service Logic.

This service encapsulates:
1. `register_merchant`: Atomically provisions Organization, User, and Owner Membership.
2. `authenticate_user`: Verifies credentials and returns active tenant context and JWT.
"""

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.organizations.models import MemberRole, Organization, OrganizationMember


def slugify(text: str) -> str:
    """
    Transforms a business name into a URL-friendly slug.
    Example: "Ahmed's Apparel & Shoes!" -> "ahmeds-apparel-shoes"
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    slug = text.strip("-")
    return slug or "org"


class AuthService:
    """Domain service managing user authentication and tenant registration."""

    @staticmethod
    async def register_merchant(
        session: AsyncSession,
        request: RegisterRequest,
    ) -> tuple[User, Organization, str]:
        """
        Registers a new merchant account within an atomic database transaction.

        Flow:
        1. Validates that the email is not already registered.
        2. Validates/generates a unique organization slug.
        3. Securely hashes the password with bcrypt.
        4. Creates Organization, User, and OrganizationMember (OWNER) records.
        5. Flushes changes to PostgreSQL and generates an active JWT access token.

        Returns:
            A tuple of (User, Organization, access_token).
        """
        normalized_email = request.email.strip().lower()

        # Check if email is already registered
        existing_user_query = select(User).where(User.email == normalized_email)
        existing_user = (await session.execute(existing_user_query)).scalar_one_or_none()
        if existing_user is not None:
            raise ConflictException(
                code="EMAIL_ALREADY_EXISTS",
                message="A user with this email address already exists.",
            )

        # Determine and check organization slug
        if request.organization_slug:
            slug = slugify(request.organization_slug)
        else:
            slug = slugify(request.organization_name)

        existing_slug_query = select(Organization).where(Organization.slug == slug)
        existing_slug = (await session.execute(existing_slug_query)).scalar_one_or_none()
        if existing_slug is not None:
            # If user explicitly requested this slug, return conflict
            if request.organization_slug:
                raise ConflictException(
                    code="SLUG_ALREADY_EXISTS",
                    message=f"The organization slug '{slug}' is already taken.",
                )
            # If auto-generated, append a short unique suffix
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"

        # Hash plain text password
        hashed_password = hash_password(request.password)

        # 1. Create Organization
        organization = Organization(
            id=uuid.uuid4(),
            name=request.organization_name.strip(),
            slug=slug,
        )
        session.add(organization)

        # 2. Create User
        user = User(
            id=uuid.uuid4(),
            email=normalized_email,
            password_hash=hashed_password,
            full_name=request.full_name.strip(),
            is_active=True,
        )
        session.add(user)

        # 3. Create Organization Member (assign OWNER role)
        member = OrganizationMember(
            id=uuid.uuid4(),
            organization_id=organization.id,
            user_id=user.id,
            role=MemberRole.OWNER,
        )
        session.add(member)

        # Flush to generate database records and enforce foreign keys
        await session.flush()

        # 4. Generate JWT Access Token
        token_payload = {
            "sub": str(user.id),
            "org_id": str(organization.id),
            "role": MemberRole.OWNER.value,
        }
        access_token = create_access_token(data=token_payload)

        return user, organization, access_token
# this staic method 
    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        request: LoginRequest,
    ) -> tuple[User, Organization, str]:
        """
        Authenticates user credentials and resolves active organization context.

        Flow:
        1. Looks up user by normalized lowercase email.
        2. Safely verifies bcrypt password hash.
        3. Ensures user account is active.
        4. Resolves user's primary organization membership.
        5. Generates a fresh JWT access token.

        Returns:
            A tuple of (User, Organization, access_token).
        """
        normalized_email = request.email.strip().lower()

        # Look up user
        user_query = select(User).where(User.email == normalized_email)
        user = (await session.execute(user_query)).scalar_one_or_none()

        # Generic error message to prevent email enumeration
        if user is None or not verify_password(request.password, user.password_hash):
            raise UnauthorizedException(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        if not user.is_active:
            raise UnauthorizedException(
                code="ACCOUNT_INACTIVE",
                message="This account is currently disabled. Please contact support.",
            )

        # Resolve organization membership
        membership_query = (
            select(OrganizationMember, Organization)
            .join(Organization, OrganizationMember.organization_id == Organization.id)
            .where(OrganizationMember.user_id == user.id)
        )
        membership_result = (await session.execute(membership_query)).first()

        if membership_result is None:
            raise UnauthorizedException(
                code="NO_ORGANIZATION_MEMBERSHIP",
                message="User account is not linked to any active organization.",
            )

        member, organization = membership_result

        # Generate JWT Access Token
        token_payload = {
            "sub": str(user.id),
            "org_id": str(organization.id),
            "role": member.role.value,
        }
        access_token = create_access_token(data=token_payload)

        return user, organization, access_token
