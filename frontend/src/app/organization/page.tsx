"use client";

/**
 * Chatrio Organization & Team Member Management Page.
 *
 * Connected directly to backend router:
 * - GET    /api/v1/organizations/current
 * - PATCH  /api/v1/organizations/current
 * - GET    /api/v1/organizations/current/members
 * - POST   /api/v1/organizations/current/members
 * - PATCH  /api/v1/organizations/current/members/{member_id}
 * - DELETE /api/v1/organizations/current/members/{member_id}
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Building2,
  CheckCircle2,
  Copy,
  Key,
  Mail,
  RefreshCw,
  Save,
  Search,
  Shield,
  ShieldCheck,
  Trash2,
  User,
  UserPlus,
  Users,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { StatCard } from "@/components/ui/StatCard";
import { useAuth } from "@/context/AuthContext";
import { organizationsService } from "@/services/organizations.service";
import {
  MemberRole,
  OrganizationDetailRead,
  OrganizationMemberRead,
} from "@/types";

const ROLE_BADGE_VARIANT: Record<
  MemberRole,
  "terracotta" | "active" | "success" | "neutral"
> = {
  OWNER: "terracotta",
  ADMIN: "active",
  AGENT: "success",
  VIEWER: "neutral",
};

const ROLE_DESCRIPTIONS: Record<MemberRole, string> = {
  OWNER: "Full workspace, team, billing & settings control",
  ADMIN: "Manage catalog, orders, AI agent & support staff",
  AGENT: "Handle WhatsApp inbox & order fulfillment",
  VIEWER: "Read-only access to store data",
};

export default function OrganizationPage() {
  const { user, updateOrganizationState } = useAuth();

  const [orgDetail, setOrgDetail] = useState<OrganizationDetailRead | null>(null);
  const [members, setMembers] = useState<OrganizationMemberRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // Organization Profile Edit state
  const [orgName, setOrgName] = useState("");
  const [orgSlug, setOrgSlug] = useState("");
  const [isSavingOrg, setIsSavingOrg] = useState(false);
  const [copiedId, setCopiedId] = useState(false);

  // Filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<"ALL" | MemberRole>("ALL");

  // Add Member Modal state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newFullName, setNewFullName] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState<MemberRole>("AGENT");
  const [isAddingMember, setIsAddingMember] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  // Role update & Remove confirmation state
  const [updatingMemberId, setUpdatingMemberId] = useState<string | null>(null);
  const [memberToRemove, setMemberToRemove] =
    useState<OrganizationMemberRead | null>(null);
  const [isRemoving, setIsRemoving] = useState(false);

  const loadOrganizationData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [detail, memberList] = await Promise.all([
        organizationsService.getCurrentOrganization(),
        organizationsService.listMembers(),
      ]);
      setOrgDetail(detail);
      setOrgName(detail.name);
      setOrgSlug(detail.slug);
      setMembers(memberList.items);
      updateOrganizationState({
        id: detail.id,
        name: detail.name,
        slug: detail.slug,
        created_at: detail.created_at,
        updated_at: detail.updated_at,
      });
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load organization details and team members."
      );
    } finally {
      setIsLoading(false);
    }
  }, [updateOrganizationState]);

  useEffect(() => {
    loadOrganizationData();
  }, [loadOrganizationData]);

  const currentRole = orgDetail?.current_user_role ?? "VIEWER";
  const canManage = currentRole === "OWNER" || currentRole === "ADMIN";
  const isOwner = currentRole === "OWNER";

  const ownerCount = useMemo(
    () => members.filter((m) => m.role === "OWNER").length,
    [members]
  );
  const adminAndOwnerCount = useMemo(
    () => members.filter((m) => m.role === "OWNER" || m.role === "ADMIN").length,
    [members]
  );
  const agentCount = useMemo(
    () => members.filter((m) => m.role === "AGENT").length,
    [members]
  );
  const viewerCount = useMemo(
    () => members.filter((m) => m.role === "VIEWER").length,
    [members]
  );

  const filteredMembers = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return members.filter((m) => {
      const matchesRole = roleFilter === "ALL" || m.role === roleFilter;
      const matchesQuery =
        !q ||
        m.full_name.toLowerCase().includes(q) ||
        m.email.toLowerCase().includes(q);
      return matchesRole && matchesQuery;
    });
  }, [members, roleFilter, searchQuery]);

  const showTemporaryNotice = (message: string) => {
    setNotice(message);
    setTimeout(() => {
      setNotice((prev) => (prev === message ? null : prev));
    }, 3500);
  };

  const handleSaveOrganization = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canManage) return;
    setIsSavingOrg(true);
    setError(null);
    try {
      const updated = await organizationsService.updateCurrentOrganization({
        name: orgName.trim(),
        slug: orgSlug.trim(),
      });
      setOrgDetail(updated);
      setOrgName(updated.name);
      setOrgSlug(updated.slug);
      updateOrganizationState({
        id: updated.id,
        name: updated.name,
        slug: updated.slug,
        created_at: updated.created_at,
        updated_at: updated.updated_at,
      });
      showTemporaryNotice("Organization profile updated successfully.");
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not update organization profile."
      );
    } finally {
      setIsSavingOrg(false);
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddError(null);
    setIsAddingMember(true);
    try {
      const created = await organizationsService.addMember({
        email: newEmail.trim(),
        role: newRole,
        full_name: newFullName.trim() || undefined,
        password: newPassword || undefined,
      });
      setMembers((prev) => [...prev, created]);
      if (orgDetail) {
        setOrgDetail({
          ...orgDetail,
          member_count: orgDetail.member_count + 1,
        });
      }
      setIsAddModalOpen(false);
      setNewEmail("");
      setNewFullName("");
      setNewPassword("");
      setNewRole("AGENT");
      showTemporaryNotice(`${created.full_name} added to the organization.`);
    } catch (err: unknown) {
      setAddError(
        err instanceof Error ? err.message : "Failed to add team member."
      );
    } finally {
      setIsAddingMember(false);
    }
  };

  const handleRoleChange = async (
    member: OrganizationMemberRead,
    targetRole: MemberRole
  ) => {
    if (member.role === targetRole) return;
    setUpdatingMemberId(member.id);
    setError(null);
    try {
      const updated = await organizationsService.updateMemberRole(member.id, {
        role: targetRole,
      });
      setMembers((prev) =>
        prev.map((m) => (m.id === updated.id ? updated : m))
      );
      showTemporaryNotice(`Updated ${updated.full_name}'s role to ${updated.role}.`);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to update member role."
      );
    } finally {
      setUpdatingMemberId(null);
    }
  };

  const handleConfirmRemove = async () => {
    if (!memberToRemove) return;
    setIsRemoving(true);
    setError(null);
    try {
      await organizationsService.removeMember(memberToRemove.id);
      setMembers((prev) => prev.filter((m) => m.id !== memberToRemove.id));
      if (orgDetail) {
        setOrgDetail({
          ...orgDetail,
          member_count: Math.max(0, orgDetail.member_count - 1),
        });
      }
      showTemporaryNotice(`${memberToRemove.full_name} removed from organization.`);
      setMemberToRemove(null);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to remove team member."
      );
      setMemberToRemove(null);
    } finally {
      setIsRemoving(false);
    }
  };

  const handleCopyWorkspaceId = () => {
    if (!orgDetail?.id) return;
    navigator.clipboard.writeText(orgDetail.id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  const canModifyMemberRole = (member: OrganizationMemberRead) => {
    if (!canManage) return false;
    if (member.role === "OWNER" && (!isOwner || ownerCount <= 1)) return false;
    if (!isOwner && member.role === "ADMIN") return false;
    return true;
  };

  const canRemoveMember = (member: OrganizationMemberRead) => {
    if (!canManage) return false;
    if (member.user_id === user?.id) return false;
    if (member.role === "OWNER" && (!isOwner || ownerCount <= 1)) return false;
    if (!isOwner && member.role === "ADMIN") return false;
    return true;
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-in fade-in duration-150">
      {/* ── Page Header ──────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-border">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-accent mb-1 font-mono">
            Workspace &amp; Access Control
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-ink-900">
            Organization &amp; Team
          </h1>
          <p className="text-xs sm:text-sm text-ink-500 mt-1">
            Manage your business profile, team members, and role-based permissions.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadOrganizationData}
            isLoading={isLoading}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </Button>
          {canManage && (
            <Button size="sm" onClick={() => setIsAddModalOpen(true)}>
              <UserPlus className="w-3.5 h-3.5" />
              <span>Add Member</span>
            </Button>
          )}
        </div>
      </div>

      {/* Status Banners */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {notice && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-700 flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-500" />
          <span>{notice}</span>
        </div>
      )}

      {/* ── 4 Aligned KPI StatCards ──────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Members"
          value={isLoading ? "—" : members.length}
          trend="Active seats"
          trendType="terracotta"
          subtitle="Organization team"
          icon={<Users className="w-4 h-4 text-accent" />}
        />
        <StatCard
          title="Owners & Admins"
          value={isLoading ? "—" : adminAndOwnerCount}
          trend={`${ownerCount} owner${ownerCount === 1 ? "" : "s"}`}
          trendType="success"
          subtitle="Admin privileges"
          icon={<ShieldCheck className="w-4 h-4 text-emerald-600" />}
        />
        <StatCard
          title="Support Agents"
          value={isLoading ? "—" : agentCount}
          trend="Inbox & orders"
          trendType="neutral"
          subtitle="Customer care"
          icon={<User className="w-4 h-4 text-ink-500" />}
        />
        <StatCard
          title="Viewers"
          value={isLoading ? "—" : viewerCount}
          trend="Read-only"
          trendType="neutral"
          subtitle="Reporting access"
          icon={<Shield className="w-4 h-4 text-ink-500" />}
        />
      </div>

      {/* ── Main 2-Column Split ──────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 4 Cols: Organization Profile & Role Guide */}
        <div className="lg:col-span-4 space-y-6">
          <div className="quiet-panel p-5 card-taste space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-ink-900 tracking-tight flex items-center gap-2">
                <Building2 className="w-4 h-4 text-accent" />
                <span>Organization Profile</span>
              </h2>
              <Badge variant={ROLE_BADGE_VARIANT[currentRole]} size="sm">
                {currentRole}
              </Badge>
            </div>

            <form onSubmit={handleSaveOrganization} className="space-y-3.5">
              <Input
                label="Organization Name"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                disabled={!canManage || isLoading}
                required
              />

              <Input
                label="Workspace Slug"
                value={orgSlug}
                onChange={(e) => setOrgSlug(e.target.value)}
                disabled={!canManage || isLoading}
                hint="Used as your unique store identifier"
                required
              />

              {orgDetail?.id && (
                <div className="space-y-1.5">
                  <label className="block text-[13px] font-medium text-ink-700">
                    Workspace ID
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      readOnly
                      value={orgDetail.id}
                      className="flex-1 bg-canvas-subtle border border-border rounded-[10px] px-3 py-2 text-[11px] font-mono text-ink-500 select-all"
                    />
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={handleCopyWorkspaceId}
                    >
                      <Copy className="w-3.5 h-3.5" />
                      <span>{copiedId ? "Copied" : "Copy"}</span>
                    </Button>
                  </div>
                </div>
              )}

              {canManage ? (
                <Button
                  type="submit"
                  size="sm"
                  className="w-full mt-1"
                  isLoading={isSavingOrg}
                  disabled={isLoading}
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>Save Organization</span>
                </Button>
              ) : (
                <p className="text-[12px] text-ink-500 pt-1">
                  Only Owners or Admins can edit organization profile details.
                </p>
              )}
            </form>
          </div>

          {/* Role Permissions Reference */}
          <div className="quiet-panel p-5 card-taste space-y-3">
            <h3 className="text-sm font-bold text-ink-900 tracking-tight flex items-center gap-2">
              <Shield className="w-4 h-4 text-accent" />
              <span>Role Permissions</span>
            </h3>
            <div className="space-y-2.5 text-xs">
              {(["OWNER", "ADMIN", "AGENT", "VIEWER"] as MemberRole[]).map(
                (r) => (
                  <div
                    key={r}
                    className="flex items-start justify-between gap-3 py-1.5 border-b border-border/60 last:border-b-0"
                  >
                    <Badge variant={ROLE_BADGE_VARIANT[r]} size="sm">
                      {r}
                    </Badge>
                    <span className="text-ink-500 text-right leading-snug">
                      {ROLE_DESCRIPTIONS[r]}
                    </span>
                  </div>
                )
              )}
            </div>
          </div>
        </div>

        {/* Right 8 Cols: Team Members Table */}
        <div className="lg:col-span-8">
          <div className="quiet-panel overflow-hidden card-taste">
            {/* Table Toolbar */}
            <div className="p-4 sm:p-5 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-ink-900 tracking-tight flex items-center gap-2">
                  <Users className="w-4 h-4 text-accent" />
                  <span>Team Members</span>
                </h2>
                <p className="text-xs text-ink-500 mt-0.5">
                  {members.length} member{members.length === 1 ? "" : "s"} in{" "}
                  {orgDetail?.name || "this workspace"}
                </p>
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                <div className="relative sm:w-52">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-ink-400 pointer-events-none" />
                  <input
                    type="text"
                    placeholder="Search name or email..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-canvas-subtle border border-border rounded-[10px] pl-8 pr-3 py-1.5 text-xs text-ink-900 placeholder:text-ink-400 focus:outline-none focus:border-accent"
                  />
                </div>

                <select
                  value={roleFilter}
                  onChange={(e) =>
                    setRoleFilter(e.target.value as "ALL" | MemberRole)
                  }
                  aria-label="Filter by role"
                  className="bg-canvas-subtle border border-border rounded-[10px] px-3 py-1.5 text-xs font-medium text-ink-800 focus:outline-none focus:border-accent"
                >
                  <option value="ALL">All roles</option>
                  <option value="OWNER">Owner</option>
                  <option value="ADMIN">Admin</option>
                  <option value="AGENT">Agent</option>
                  <option value="VIEWER">Viewer</option>
                </select>
              </div>
            </div>

            {/* Members Rows */}
            <div className="divide-y divide-border/60">
              {isLoading ? (
                <div className="p-10 text-center text-xs text-ink-500">
                  Loading team members…
                </div>
              ) : filteredMembers.length === 0 ? (
                <div className="p-10 text-center text-ink-500 space-y-2">
                  <Users className="w-8 h-8 text-ink-300 mx-auto" />
                  <p className="text-xs font-semibold text-ink-900">
                    No matching members found
                  </p>
                  <p className="text-xs text-ink-400">
                    Try adjusting your search or role filter.
                  </p>
                </div>
              ) : (
                filteredMembers.map((member) => {
                  const initials = member.full_name
                    ? member.full_name
                        .split(" ")
                        .map((part) => part[0])
                        .join("")
                        .slice(0, 2)
                        .toUpperCase()
                    : "U";
                  const isCurrentUser = member.user_id === user?.id;
                  const editableRole = canModifyMemberRole(member);
                  const removable = canRemoveMember(member);

                  return (
                    <div
                      key={member.id}
                      className="p-4 sm:px-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-accent-light/50 transition-colors"
                    >
                      {/* User identity */}
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-[10px] bg-accent/10 border border-accent/20 flex items-center justify-center text-xs font-semibold text-accent shrink-0">
                          {initials}
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-semibold text-ink-900 truncate">
                              {member.full_name}
                            </span>
                            {isCurrentUser && (
                              <Badge variant="neutral" size="sm">
                                You
                              </Badge>
                            )}
                            {!member.is_active && (
                              <Badge variant="critical" size="sm">
                                Disabled
                              </Badge>
                            )}
                          </div>
                          <p className="text-[11px] text-ink-500 truncate mt-0.5">
                            {member.email} · Joined{" "}
                            {new Date(member.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>

                      {/* Role & actions */}
                      <div className="flex items-center gap-2.5 self-end sm:self-center shrink-0">
                        {editableRole ? (
                          <select
                            value={member.role}
                            disabled={updatingMemberId === member.id}
                            aria-label={`Role for ${member.full_name}`}
                            onChange={(e) =>
                              handleRoleChange(
                                member,
                                e.target.value as MemberRole
                              )
                            }
                            className="bg-canvas-subtle border border-border rounded-[10px] px-2.5 py-1.5 text-xs font-semibold text-ink-900 focus:outline-none focus:border-accent disabled:opacity-50"
                          >
                            {member.role === "OWNER" && (
                              <option value="OWNER">OWNER</option>
                            )}
                            {isOwner && <option value="ADMIN">ADMIN</option>}
                            <option value="AGENT">AGENT</option>
                            <option value="VIEWER">VIEWER</option>
                          </select>
                        ) : (
                          <Badge
                            variant={ROLE_BADGE_VARIANT[member.role]}
                            size="sm"
                          >
                            {member.role}
                          </Badge>
                        )}

                        {removable && (
                          <button
                            type="button"
                            onClick={() => setMemberToRemove(member)}
                            title={`Remove ${member.full_name}`}
                            className="p-2 rounded-[10px] text-ink-400 hover:text-rose-600 hover:bg-rose-50 transition-colors focus-visible:ring-2 focus-visible:ring-rose-400"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Add Member Modal ─────────────────────────────────────── */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => {
          setIsAddModalOpen(false);
          setAddError(null);
        }}
        title="Add Team Member"
        description="Add an existing Chatrio user by email, or create a new staff account for your workspace."
      >
        <form onSubmit={handleAddMember} className="space-y-4">
          {addError && (
            <div className="p-3 rounded-[10px] bg-rose-50 border border-rose-200 text-xs text-rose-700">
              {addError}
            </div>
          )}

          <Input
            label="Work Email"
            type="email"
            placeholder="teammate@store.com"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            icon={<Mail className="w-4 h-4" />}
            required
          />

          <div className="space-y-1.5">
            <label className="block text-[13px] font-medium text-ink-700">
              Assigned Role
            </label>
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as MemberRole)}
              className="w-full h-10 bg-white border border-border rounded-[10px] px-3.5 text-[14px] text-ink-900 focus:outline-none focus:border-accent"
            >
              {isOwner && (
                <option value="ADMIN">ADMIN — Catalog, orders &amp; AI management</option>
              )}
              <option value="AGENT">AGENT — Inbox &amp; order fulfillment</option>
              <option value="VIEWER">VIEWER — Read-only reports access</option>
            </select>
          </div>

          <Input
            label="Full Name"
            placeholder="Required if creating a new account"
            value={newFullName}
            onChange={(e) => setNewFullName(e.target.value)}
            icon={<User className="w-4 h-4" />}
          />

          <Input
            label="Initial Password"
            type="password"
            placeholder="Min 8 characters (for new accounts)"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            icon={<Key className="w-4 h-4" />}
            hint="Leave Full Name and Password blank only if this email is already registered on Chatrio."
          />

          <div className="flex justify-end gap-2.5 pt-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setIsAddModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={isAddingMember}>
              <UserPlus className="w-3.5 h-3.5" />
              <span>Add to Organization</span>
            </Button>
          </div>
        </form>
      </Modal>

      {/* ── Remove Member Confirmation Modal ─────────────────────── */}
      <Modal
        isOpen={!!memberToRemove}
        onClose={() => setMemberToRemove(null)}
        title="Remove Team Member"
        description="This immediately revokes their access to this organization workspace."
      >
        {memberToRemove && (
          <div className="space-y-4">
            <div className="p-3.5 rounded-[10px] bg-canvas-subtle border border-border text-xs space-y-1">
              <p className="font-semibold text-ink-900">
                {memberToRemove.full_name}
              </p>
              <p className="text-ink-500">
                {memberToRemove.email} · Role: {memberToRemove.role}
              </p>
            </div>

            <div className="flex justify-end gap-2.5">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setMemberToRemove(null)}
              >
                Keep Member
              </Button>
              <Button
                type="button"
                variant="danger"
                size="sm"
                isLoading={isRemoving}
                onClick={handleConfirmRemove}
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Remove Member</span>
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

