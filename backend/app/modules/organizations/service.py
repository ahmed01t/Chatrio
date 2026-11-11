"""
Organization and Team Member Management Service.

Encapsulates multi-tenant business logic for:
1. Reading and updating the active organization profile.
2. Listing team members within an organization.
3. Adding new or existing users as organization members with RBAC enforcement.
4. Updating member roles and removing members with anti-lockout safeguards.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.auth.service import slugify
from app.modules.organizations.models import MemberRole, Organization, OrganizationMember
from app.modules.organizations.schemas import (
    MemberAddRequest,
    MemberRoleUpdate,
    OrganizationDetailRead,
    OrganizationMemberRead,
    OrganizationUpdate,
)


def _to_member_read(
    member: OrganizationMember,
    user: User,
) -> OrganizationMemberRead:
    """Maps an OrganizationMember and its linked User into an API DTO."""
    return OrganizationMemberRead(
        id=member.id,
        organization_id=member.organization_id,
        user_id=member.user_id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=member.role,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


async def _get_member_with_user(
    session: AsyncSession,
    organization_id: uuid.UUID,
    member_id: uuid.UUID,
) -> tuple[OrganizationMember, User]:
    """Retrieves a tenant-scoped membership joined with its user, or raises 404."""
    stmt = (
        select(OrganizationMember, User)
        .join(User, OrganizationMember.user_id == User.id)
        .where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == organization_id,
        )
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        raise NotFoundException(
            code="MEMBER_NOT_FOUND",
            message="Organization member not found.",
        )
    return row[0], row[1]


async def _count_owners(
    session: AsyncSession,
    organization_id: uuid.UUID,
) -> int:
    """Counts how many OWNER memberships exist for the given organization."""
    stmt = select(func.count(OrganizationMember.id)).where(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.role == MemberRole.OWNER,
    )
    count = (await session.execute(stmt)).scalar_one()
    return int(count)


class OrganizationService:
    """Domain service managing tenant organizations and team memberships."""

    @staticmethod
    async def get_organization_details(
        session: AsyncSession,
        organization_id: uuid.UUID,
        current_user_role: MemberRole,
    ) -> OrganizationDetailRead:
        """Returns the current organization profile along with member count."""
        org = await session.get(Organization, organization_id)
        if org is None:
            raise NotFoundException(
                code="ORGANIZATION_NOT_FOUND",
                message="Organization not found.",
            )

        count_stmt = select(func.count(OrganizationMember.id)).where(
            OrganizationMember.organization_id == organization_id
        )
        member_count = int((await session.execute(count_stmt)).scalar_one())

        return OrganizationDetailRead(
            id=org.id,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
            updated_at=org.updated_at,
            member_count=member_count,
            current_user_role=current_user_role,
        )

    @staticmethod
    async def update_organization(
        session: AsyncSession,
        organization_id: uuid.UUID,
        current_user_role: MemberRole,
        request: OrganizationUpdate,
    ) -> OrganizationDetailRead:
        """Updates organization display name and/or unique slug."""
        org = await session.get(Organization, organization_id)
        if org is None:
            raise NotFoundException(
                code="ORGANIZATION_NOT_FOUND",
                message="Organization not found.",
            )

        if request.name is not None:
            cleaned_name = request.name.strip()
            if not cleaned_name:
                raise BadRequestException(
                    code="INVALID_ORGANIZATION_NAME",
                    message="Organization name cannot be blank.",
                )
            org.name = cleaned_name

        if request.slug is not None:
            normalized_slug = slugify(request.slug)
            existing_stmt = select(Organization).where(
                Organization.slug == normalized_slug,
                Organization.id != organization_id,
            )
            existing_org = (await session.execute(existing_stmt)).scalar_one_or_none()
            if existing_org is not None:
                raise ConflictException(
                    code="SLUG_ALREADY_EXISTS",
                    message=f"The organization slug '{normalized_slug}' is already taken.",
                )
            org.slug = normalized_slug

        await session.flush()
        await session.refresh(org)

        return await OrganizationService.get_organization_details(
            session=session,
            organization_id=organization_id,
            current_user_role=current_user_role,
        )

    @staticmethod
    async def list_members(
        session: AsyncSession,
        organization_id: uuid.UUID,
    ) -> list[OrganizationMemberRead]:
        """Lists all members belonging to the specified tenant organization."""
        stmt = (
            select(OrganizationMember, User)
            .join(User, OrganizationMember.user_id == User.id)
            .where(OrganizationMember.organization_id == organization_id)
            .order_by(OrganizationMember.created_at.asc())
        )
        rows = (await session.execute(stmt)).all()
        return [_to_member_read(member, user) for member, user in rows]

    @staticmethod
    async def add_member(
        session: AsyncSession,
        organization_id: uuid.UUID,
        actor_role: MemberRole,
        request: MemberAddRequest,
    ) -> OrganizationMemberRead:
        """
        Adds an existing platform user or provisions a new user into the organization.
        """
        if request.role == MemberRole.OWNER:
            raise ForbiddenException(
                code="CANNOT_ASSIGN_OWNER",
                message="Cannot assign the OWNER role directly.",
            )

        if actor_role != MemberRole.OWNER and request.role == MemberRole.ADMIN:
            raise ForbiddenException(
                code="INSUFFICIENT_PERMISSIONS",
                message="Only an organization OWNER can add ADMIN members.",
            )

        normalized_email = request.email.strip().lower()
        user_stmt = select(User).where(User.email == normalized_email)
        user = (await session.execute(user_stmt)).scalar_one_or_none()

        if user is not None:
            existing_member_stmt = select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user.id,
            )
            existing_member = (await session.execute(existing_member_stmt)).scalar_one_or_none()
            if existing_member is not None:
                raise ConflictException(
                    code="MEMBER_ALREADY_EXISTS",
                    message="This user is already a member of this organization.",
                )
        else:
            full_name = (request.full_name or "").strip()
            if not full_name or not request.password:
                raise BadRequestException(
                    code="USER_DETAILS_REQUIRED",
                    message=(
                        "Full name and password are required to create a new user account "
                        "for this email."
                    ),
                )
            user = User(
                id=uuid.uuid4(),
                email=normalized_email,
                password_hash=hash_password(request.password),
                full_name=full_name,
                is_active=True,
            )
            session.add(user)
            await session.flush()

        member = OrganizationMember(
            id=uuid.uuid4(),
            organization_id=organization_id,
            user_id=user.id,
            role=request.role,
        )
        session.add(member)
        await session.flush()
        await session.refresh(member)

        return _to_member_read(member, user)

    @staticmethod
    async def update_member_role(
        session: AsyncSession,
        organization_id: uuid.UUID,
        actor_role: MemberRole,
        member_id: uuid.UUID,
        request: MemberRoleUpdate,
    ) -> OrganizationMemberRead:
        """Updates a team member's role within the tenant organization."""
        member, user = await _get_member_with_user(
            session=session,
            organization_id=organization_id,
            member_id=member_id,
        )

        if request.role == MemberRole.OWNER and member.role != MemberRole.OWNER:
            raise ForbiddenException(
                code="CANNOT_ASSIGN_OWNER",
                message="Cannot promote a member to OWNER directly.",
            )

        if actor_role != MemberRole.OWNER and (
            member.role == MemberRole.OWNER or request.role == MemberRole.ADMIN
        ):
            raise ForbiddenException(
                code="INSUFFICIENT_PERMISSIONS",
                message="Only an organization OWNER can manage OWNER or ADMIN roles.",
            )

        if member.role == MemberRole.OWNER and request.role != MemberRole.OWNER:
            owner_count = await _count_owners(session, organization_id)
            if owner_count <= 1:
                raise BadRequestException(
                    code="CANNOT_DEMOTE_LAST_OWNER",
                    message="Cannot demote the sole owner of the organization.",
                )

        member.role = request.role
        await session.flush()
        await session.refresh(member)
        return _to_member_read(member, user)

    @staticmethod
    async def remove_member(
        session: AsyncSession,
        organization_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        actor_role: MemberRole,
        member_id: uuid.UUID,
    ) -> None:
        """Removes a member from the organization with anti-lockout checks."""
        member, _ = await _get_member_with_user(
            session=session,
            organization_id=organization_id,
            member_id=member_id,
        )

        if member.user_id == actor_user_id:
            raise BadRequestException(
                code="CANNOT_REMOVE_SELF",
                message="You cannot remove yourself from the organization.",
            )

        if actor_role != MemberRole.OWNER and member.role in (
            MemberRole.OWNER,
            MemberRole.ADMIN,
        ):
            raise ForbiddenException(
                code="INSUFFICIENT_PERMISSIONS",
                message="Only an organization OWNER can remove OWNER or ADMIN members.",
            )

        if member.role == MemberRole.OWNER:
            owner_count = await _count_owners(session, organization_id)
            if owner_count <= 1:
                raise BadRequestException(
                    code="CANNOT_REMOVE_LAST_OWNER",
                    message="Cannot remove the sole owner of the organization.",
                )

        await session.delete(member)
        await session.flush()
