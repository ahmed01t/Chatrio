# Feature Spec: 010-organization-management

## 1. Objective
Provide full **Organization & Team Member Management** across the Chatrio backend API and Next.js merchant dashboard, building on the multi-tenant `Organization`, `OrganizationMember`, and `MemberRole` (`OWNER`, `ADMIN`, `AGENT`, `VIEWER`) data models defined in Spec 002.

---

## 2. Security & Multi-Tenancy Invariants

1. **Strict Tenant Isolation**:
   - Every organization query, member listing, role update, and member removal MUST be scoped strictly to `tenant_context.organization.id`.
   - Attempting to modify or delete a membership belonging to another organization MUST return `404 Not Found` (`MEMBER_NOT_FOUND`).
2. **Role-Based Access Control (RBAC)**:
   - Any authenticated tenant member (`OWNER`, `ADMIN`, `AGENT`, `VIEWER`) may view current organization details and list team members.
   - Only `OWNER` and `ADMIN` may update organization profile metadata, invite/add new members, change member roles, or remove members (`403 Forbidden` for `AGENT` and `VIEWER`).
   - Privilege Escalation Guard: An `ADMIN` cannot assign the `OWNER` role, modify an `OWNER`'s role, or remove an `OWNER`.
3. **Anti-Lockout Safeguards**:
   - A member cannot remove themselves via the team removal endpoint (`400 Bad Request`, `CANNOT_REMOVE_SELF`).
   - The sole remaining `OWNER` of an organization cannot be removed or demoted to a non-owner role (`400 Bad Request`, `CANNOT_DEMOTE_LAST_OWNER` / `CANNOT_REMOVE_LAST_OWNER`).

---

## 3. Backend API Specification (`/api/v1/organizations`)

### 3.1 `GET /api/v1/organizations/current`
- **Auth**: `CurrentTenant` (any role).
- **Response (`200 OK`)**: `OrganizationDetailRead` containing `id`, `name`, `slug`, `member_count`, `current_user_role`, `created_at`, `updated_at`.

### 3.2 `PATCH /api/v1/organizations/current`
- **Auth**: `OWNER` or `ADMIN`.
- **Payload (`OrganizationUpdate`)**: Optional `name` (1–255 chars), optional `slug` (2–100 chars, slugified).
- **Validation**: Rejects duplicate `slug` across organizations (`409 Conflict`, `SLUG_ALREADY_EXISTS`).
- **Response (`200 OK`)**: Updated `OrganizationDetailRead`.

### 3.3 `GET /api/v1/organizations/current/members`
- **Auth**: `CurrentTenant` (any role).
- **Response (`200 OK`)**: `MemberListResponse` with `items: list[OrganizationMemberRead]` (joining `OrganizationMember` and `User` fields: `id`, `organization_id`, `user_id`, `email`, `full_name`, `is_active`, `role`, `created_at`, `updated_at`) and `total`.

### 3.4 `POST /api/v1/organizations/current/members`
- **Auth**: `OWNER` or `ADMIN`.
- **Payload (`MemberAddRequest`)**: `email`, `role` (`ADMIN`, `AGENT`, `VIEWER`), optional `full_name`, optional `password` (min 8 chars).
- **Behavior**:
  - Rejects assigning `OWNER` role (`403 Forbidden`, `CANNOT_ASSIGN_OWNER`).
  - Only `OWNER` may assign the `ADMIN` role (`403 Forbidden`, `INSUFFICIENT_PERMISSIONS` if `ADMIN` attempts to add an `ADMIN`).
  - Normalizes `email` (lowercase, trimmed).
  - If `User` with `email` exists:
    - If already a member of this organization -> `409 Conflict` (`MEMBER_ALREADY_EXISTS`).
    - Otherwise links existing `User` via new `OrganizationMember`.
  - If `User` does not exist:
    - Requires `full_name` and `password` (`400 Bad Request`, `USER_DETAILS_REQUIRED` if missing).
    - Creates `User` with hashed password and creates `OrganizationMember` atomically.
- **Response (`201 Created`)**: `OrganizationMemberRead`.

### 3.5 `PATCH /api/v1/organizations/current/members/{member_id}`
- **Auth**: `OWNER` or `ADMIN`.
- **Payload (`MemberRoleUpdate`)**: `role: MemberRole`.
- **Behavior**:
  - Enforces tenant boundary (`404 Not Found` if missing or belongs to another org).
  - Rejects promoting to `OWNER` (`403 Forbidden`, `CANNOT_ASSIGN_OWNER`).
  - Prevents `ADMIN` from modifying an `OWNER` (`403 Forbidden`).
  - Prevents demoting the sole `OWNER` (`400 Bad Request`, `CANNOT_DEMOTE_LAST_OWNER`).
- **Response (`200 OK`)**: Updated `OrganizationMemberRead`.

### 3.6 `DELETE /api/v1/organizations/current/members/{member_id}`
- **Auth**: `OWNER` or `ADMIN`.
- **Behavior**:
  - Enforces tenant boundary (`404 Not Found`).
  - Prevents self-removal (`400 Bad Request`, `CANNOT_REMOVE_SELF`).
  - Prevents `ADMIN` from removing an `OWNER` (`403 Forbidden`).
  - Prevents removing the sole `OWNER` (`400 Bad Request`, `CANNOT_REMOVE_LAST_OWNER`).
- **Response (`204 No Content`)**.

---

## 4. Frontend Module (`/organization`)
- Accessible from the main Sidebar navigation (**Organization**).
- Displays Organization Profile editor (Name, Slug, Workspace ID) for `OWNER`/`ADMIN`, and read-only view for `AGENT`/`VIEWER`.
- Displays KPI summary cards (Total Members, Owners & Admins, Support Agents, Viewers).
- Displays searchable/filterable team members table with live role management, "Add Member" modal, and "Remove Member" confirmation modal.
