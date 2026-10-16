# Feature Spec: 002-auth-and-tenancy

## 1. Objective
Establish the multi-tenant database foundation, data modeling, role-based access control (RBAC), and authentication system for Chatrio. This ensures that every business (tenant) is strictly isolated, users can register and log in securely, and every protected API route can deterministically identify the authenticated user and their active organization.

---

## 2. In Scope
1. **Containerized Local Infrastructure**:
   - `backend/docker-compose.yml` provisioning PostgreSQL 16 with the `pgvector` extension and Redis 7.
2. **Database Engine & Lifecycle**:
   - Asynchronous SQLAlchemy 2.0 session factory using `asyncpg`.
   - Central base model (`DeclarativeBase`) providing common timestamp fields (`created_at`, `updated_at`) and UUID primary keys.
   - Alembic migration environment configured for async database migrations.
3. **Core Multi-Tenant Data Models**:
   - `organizations`: Represents a business tenant (id, name, slug, created_at, updated_at).
   - `users`: Represents an individual user (id, email, password_hash, full_name, is_active, created_at, updated_at).
   - `organization_members`: Junction table binding a user to an organization with a specific role (`OWNER`, `ADMIN`, `AGENT`, `VIEWER`).
4. **Security & Cryptography**:
   - Password hashing and verification using modern algorithms (`bcrypt` or `argon2`).
   - JSON Web Token (JWT) encoding and decoding with expiration time and signature verification.
5. **Authentication API Endpoints (`/api/v1/auth/`)**:
   - `POST /api/v1/auth/register`: Creates an organization, an owner user, and their membership in a single atomic database transaction.
   - `POST /api/v1/auth/login`: Authenticates credentials and returns a JWT access token.
   - `GET /api/v1/auth/me`: Protected route returning the current user profile, active organization, and role.
6. **FastAPI Dependency Injection**:
   - `get_db`: Asynchronous database session lifecycle manager.
   - `get_current_user`: Decodes JWT and retrieves the active user from PostgreSQL.
   - `get_current_tenant`: Resolves the active organization context and verifies user membership and role.

---

## 3. Out of Scope (Deferred to Future Specs)
- WhatsApp webhook handling, phone number connections, and Meta APIs (Deferred to Spec 003).
- Message debouncing and BullMQ workers (Deferred to Spec 003).
- Product catalog and inventory tables (Deferred to Spec 004).
- Shopping carts and orders (Deferred to Spec 005).
- AI agent and LangGraph workflows (Deferred to Spec 006).
- Frontend Next.js UI integration.

---

## 4. Requirements & Invariants

### 4.1 Functional Requirements
1. **Atomic Merchant Registration**:
   - When a user registers via `POST /api/v1/auth/register`, the organization and the user account must be created within the same database transaction. If either fails, all changes must roll back.
   - The registering user is automatically assigned the `OWNER` role.
2. **Authentication Flow**:
   - Emails must be normalized (lowercased) and unique across the `users` table.
   - Passwords must be hashed before writing to PostgreSQL. Plain-text passwords must never be stored, logged, or returned in responses.
   - Login with invalid email or incorrect password must return `401 Unauthorized` with a generic error message (preventing email enumeration).
3. **Tenant Boundary Enforcement**:
   - A user who belongs only to Organization A must receive a `403 Forbidden` if attempting to access Organization B resources.
   - The JWT token payload must encode the `sub` (User ID) and the `org_id` (Active Organization ID).

### 4.2 Non-Functional Invariants
1. **Asynchronous Execution**: All database operations must strictly use `await session.execute(...)` with `asyncpg`. No synchronous blocking database drivers.
2. **Structured Error Handling**: Invalid requests, unique constraint conflicts (e.g. duplicate email), or missing credentials must return standardized JSON errors matching the format specified in `docs/conventions.md`.
3. **Database Migration Safety**: All database schema changes must be generated and applied through version-controlled Alembic migrations.
