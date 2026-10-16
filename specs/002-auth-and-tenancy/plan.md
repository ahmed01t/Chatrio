# Implementation Plan: 002-auth-and-tenancy

## 1. Summary
This plan details the technical steps to configure PostgreSQL (pgvector) and Redis via Docker Compose, implement the async SQLAlchemy database layer, build the multi-tenant data models, set up Alembic migrations, and expose secure authentication endpoints.

---

## 2. Technical Architecture & Database Design

### 2.1 Database Schema Definition

```text
       organizations
      ┌─────────────────────────┐
      │ id (UUID, PK)           │
      │ name (VARCHAR)          │
      │ slug (VARCHAR, UNIQUE)  │
      │ created_at (TIMESTAMPTZ)│
      │ updated_at (TIMESTAMPTZ)│
      └────────────┬────────────┘
                   │ 1
                   │
                   │ N
      ┌────────────▼────────────┐                   users
      │  organization_members   │             ┌─────────────────────────┐
      ├─────────────────────────┤             │ id (UUID, PK)           │
      │ id (UUID, PK)           │        N    │ email (VARCHAR, UNIQUE) │
      │ organization_id (FK)    │◄────────────┤ password_hash (VARCHAR) │
      │ user_id (FK)            │             │ full_name (VARCHAR)     │
      │ role (VARCHAR / ENUM)   │             │ is_active (BOOLEAN)     │
      │ created_at (TIMESTAMPTZ)│             │ created_at (TIMESTAMPTZ)│
      └─────────────────────────┘             │ updated_at (TIMESTAMPTZ)│
                                              └─────────────────────────┘
```

#### Roles Enum:
- `OWNER`: Full administrative control, billing, organization settings, team invites.
- `ADMIN`: Catalog, order management, AI settings, customer support.
- `AGENT`: Inbox chat response, order fulfillment, ticket management.
- `VIEWER`: Read-only reporting access.

---

### 2.2 Security & Authentication Strategy
- **Password Hashing**: `bcrypt` (via `passlib` or `pwdlib[bcrypt]`).
- **Token Format**: Standard JSON Web Tokens (JWT) signed with HMAC-SHA256 (`PyJWT` or `python-jose`).
- **Token Claims**:
  - `sub`: User UUID string
  - `org_id`: Active Organization UUID string
  - `role`: User's role within the organization
  - `exp`: Expiration timestamp (default: 60 minutes)
  - `type`: Token type (`access`)

---

### 2.3 Package Dependencies to Add
In `backend/pyproject.toml`:
- `sqlalchemy[asyncio]>=2.0.36`
- `asyncpg>=0.30.0`
- `alembic>=1.14.0`
- `pwdlib[bcrypt]>=0.2.0` (or `passlib[bcrypt]>=1.7.4`)
- `pyjwt>=2.10.0`

---

### 2.4 Directory & Module Layout for Feature 002

```text
backend/
├── docker-compose.yml           # Postgres 16 (pgvector) + Redis 7
├── alembic.ini                  # Alembic CLI config
├── migrations/
│   ├── env.py                   # Async Alembic runner
│   └── versions/                # Generated migration scripts
│
├── app/
│   ├── core/
│   │   ├── config.py            # Added DATABASE_URL, JWT_SECRET, JWT_ALGORITHM
│   │   └── security.py          # hash_password, verify_password, create_access_token
│   │
│   ├── db/
│   │   ├── base.py              # DeclarativeBase, UUID primary key & timestamp mixins
│   │   ├── session.py           # AsyncEngine & async_sessionmaker
│   │   └── models.py            # Re-exports all models for Alembic auto-discovery
│   │
│   ├── api/
│   │   ├── router.py            # Mounts auth router under /api/v1/auth
│   │   └── dependencies.py      # get_db, get_current_user, get_current_tenant
│   │
│   └── modules/
│       ├── auth/
│       │   ├── router.py        # POST /register, POST /login, GET /me
│       │   ├── schemas.py       # RegisterRequest, LoginRequest, AuthResponse, UserProfileResponse
│       │   └── service.py       # AuthService (authenticate, register_merchant)
│       │
│       └── organizations/
│           ├── models.py        # Organization, OrganizationMember ORM models
│           ├── schemas.py       # OrganizationRead, MemberRead
│           └── service.py       # OrganizationService
```

---

## 3. Risks & Mitigations
- **Database Connection Failure in Tests**: Use an in-memory SQLite async database (`aiosqlite`) or isolated PostgreSQL test database container during automated test execution.
- **Race Condition on Registration**: Enforce unique constraints at the database level (`unique=True` on `users.email` and `organizations.slug`). Wrap creation in an explicit `async with session.begin():` block.
