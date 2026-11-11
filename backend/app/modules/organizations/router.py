"""
Organization & Team Member Management API Endpoints.

Provides tenant-scoped endpoints for:
- GET /organizations/current: Retrieve active organization details & member count.
- PATCH /organizations/current: Update organization name or slug (OWNER/ADMIN).
- GET /organizations/current/members: List all members of the active organization.
- POST /organizations/current/members: Add or provision a team member (OWNER/ADMIN).
- PATCH /organizations/current/members/{member_id}: Change a member's role (OWNER/ADMIN).
- DELETE /organizations/current/members/{member_id}: Remove a member (OWNER/ADMIN).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentTenant, DBSession, TenantContext, require_roles
from app.modules.organizations.models import MemberRole
from app.modules.organizations.schemas import (
    MemberAddRequest,
    MemberListResponse,
    MemberRoleUpdate,
    OrganizationDetailRead,
    OrganizationMemberRead,
    OrganizationUpdate,
)
from app.modules.organizations.service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations & Team"])

AdminTenant = Annotated[
    TenantContext,
    Depends(require_roles([MemberRole.OWNER, MemberRole.ADMIN])),
]


@router.get(
    "/current",
    response_model=OrganizationDetailRead,
    status_code=status.HTTP_200_OK,
    summary="Get active organization details",
)
async def get_current_organization(
    tenant_context: CurrentTenant,
    session: DBSession,
) -> OrganizationDetailRead:
    """Returns details for the currently authenticated tenant organization."""
    return await OrganizationService.get_organization_details(
        session=session,
        organization_id=tenant_context.organization.id,
        current_user_role=tenant_context.member.role,
    )


@router.patch(
    "/current",
    response_model=OrganizationDetailRead,
    status_code=status.HTTP_200_OK,
    summary="Update active organization profile",
)
async def update_current_organization(
    request: OrganizationUpdate,
    tenant_context: AdminTenant,
    session: DBSession,
) -> OrganizationDetailRead:
    """Updates organization display name or unique slug (OWNER or ADMIN only)."""
    return await OrganizationService.update_organization(
        session=session,
        organization_id=tenant_context.organization.id,
        current_user_role=tenant_context.member.role,
        request=request,
    )


@router.get(
    "/current/members",
    response_model=MemberListResponse,
    status_code=status.HTTP_200_OK,
    summary="List organization team members",
)
async def list_organization_members(
    tenant_context: CurrentTenant,
    session: DBSession,
) -> MemberListResponse:
    """Lists all team members belonging strictly to the active tenant organization."""
    items = await OrganizationService.list_members(
        session=session,
        organization_id=tenant_context.organization.id,
    )
    return MemberListResponse(items=items, total=len(items))


@router.post(
    "/current/members",
    response_model=OrganizationMemberRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a member to the organization",
)
async def add_organization_member(
    request: MemberAddRequest,
    tenant_context: AdminTenant,
    session: DBSession,
) -> OrganizationMemberRead:
    """Adds an existing user or creates a new user account in the active organization."""
    return await OrganizationService.add_member(
        session=session,
        organization_id=tenant_context.organization.id,
        actor_role=tenant_context.member.role,
        request=request,
    )


@router.patch(
    "/current/members/{member_id}",
    response_model=OrganizationMemberRead,
    status_code=status.HTTP_200_OK,
    summary="Update a member's organization role",
)
async def update_organization_member_role(
    member_id: uuid.UUID,
    request: MemberRoleUpdate,
    tenant_context: AdminTenant,
    session: DBSession,
) -> OrganizationMemberRead:
    """Changes the RBAC role of a member within the active organization."""
    return await OrganizationService.update_member_role(
        session=session,
        organization_id=tenant_context.organization.id,
        actor_role=tenant_context.member.role,
        member_id=member_id,
        request=request,
    )


@router.delete(
    "/current/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from the organization",
)
async def remove_organization_member(
    member_id: uuid.UUID,
    tenant_context: AdminTenant,
    session: DBSession,
) -> None:
    """Removes a member from the active organization (anti-lockout protected)."""
    await OrganizationService.remove_member(
        session=session,
        organization_id=tenant_context.organization.id,
        actor_user_id=tenant_context.user.id,
        actor_role=tenant_context.member.role,
        member_id=member_id,
    )
