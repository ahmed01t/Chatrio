/**
 * Organizations & Team Member Management Service.
 *
 * Direct client mapping to backend router:
 * backend/app/modules/organizations/router.py
 *
 * Endpoints:
 * - GET    /api/v1/organizations/current                      -> getCurrentOrganization()
 * - PATCH  /api/v1/organizations/current                      -> updateCurrentOrganization(payload)
 * - GET    /api/v1/organizations/current/members              -> listMembers()
 * - POST   /api/v1/organizations/current/members              -> addMember(payload)
 * - PATCH  /api/v1/organizations/current/members/{member_id}  -> updateMemberRole(memberId, payload)
 * - DELETE /api/v1/organizations/current/members/{member_id}  -> removeMember(memberId)
 */

import { apiClient } from "./api.client";
import {
  MemberAddRequest,
  MemberListResponse,
  MemberRoleUpdate,
  OrganizationDetailRead,
  OrganizationMemberRead,
  OrganizationUpdate,
} from "@/types";

export const organizationsService = {
  /**
   * Fetches active tenant organization profile and member count.
   * Calls: GET /api/v1/organizations/current
   */
  async getCurrentOrganization(): Promise<OrganizationDetailRead> {
    return apiClient<OrganizationDetailRead>("/organizations/current");
  },

  /**
   * Updates active tenant organization name or slug.
   * Calls: PATCH /api/v1/organizations/current
   */
  async updateCurrentOrganization(
    payload: OrganizationUpdate
  ): Promise<OrganizationDetailRead> {
    return apiClient<OrganizationDetailRead>("/organizations/current", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Lists all members in the active tenant organization.
   * Calls: GET /api/v1/organizations/current/members
   */
  async listMembers(): Promise<MemberListResponse> {
    return apiClient<MemberListResponse>("/organizations/current/members");
  },

  /**
   * Adds an existing user or creates a new team member account.
   * Calls: POST /api/v1/organizations/current/members
   */
  async addMember(payload: MemberAddRequest): Promise<OrganizationMemberRead> {
    return apiClient<OrganizationMemberRead>("/organizations/current/members", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Updates an organization member's role.
   * Calls: PATCH /api/v1/organizations/current/members/{member_id}
   */
  async updateMemberRole(
    memberId: string,
    payload: MemberRoleUpdate
  ): Promise<OrganizationMemberRead> {
    return apiClient<OrganizationMemberRead>(
      `/organizations/current/members/${memberId}`,
      {
        method: "PATCH",
        body: JSON.stringify(payload),
      }
    );
  },

  /**
   * Removes a member from the active organization.
   * Calls: DELETE /api/v1/organizations/current/members/{member_id}
   */
  async removeMember(memberId: string): Promise<void> {
    await apiClient<void>(`/organizations/current/members/${memberId}`, {
      method: "DELETE",
    });
  },
};

