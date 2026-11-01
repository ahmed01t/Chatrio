# Tasks: 002-auth-and-tenancy

Each task is atomic, independent, and verifiable.

- [x] **Task 1: Local Container Infrastructure & Dependencies**
  - Files: `backend/docker-compose.yml`, `backend/pyproject.toml`, `backend/.env.example`
  - Action: Configure PostgreSQL 16 (`pgvector/pgvector:pg16`) and Redis 7 in `docker-compose.yml`. Add `sqlalchemy`, `asyncpg`, `alembic`, `pwdlib[bcrypt]`, and `pyjwt` to `pyproject.toml`. Update `.env.example` with `DATABASE_URL` and `JWT_SECRET`.
  - Verification: `uv pip install -e ".[dev]"` installs new dependencies cleanly.

- [x] **Task 2: Database Engine & Base Models**
  - Files: `backend/app/db/base.py`, `backend/app/db/session.py`
  - Action: Implement `Base(DeclarativeBase)` with UUID PK and UTC timestamp mixins. Implement async engine and session factory with connection pooling.
  - Verification: Unit test verifying async session generation.

- [x] **Task 3: Organization & User ORM Models**
  - Files: `backend/app/modules/organizations/models.py`, `backend/app/modules/auth/models.py`, `backend/app/db/models.py`
  - Action: Define `Organization`, `User`, and `OrganizationMember` models with foreign keys, indexes, and unique constraints. Re-export in `app/db/models.py`.
  - Verification: Models import cleanly and SQLAlchemy metadata registers all 3 tables.

- [x] **Task 4: Alembic Migration Environment**
  - Files: `backend/alembic.ini`, `backend/migrations/env.py`
  - Action: Configure Alembic to use async SQLAlchemy engine and bind to `Base.metadata`. Generate initial migration (`001_initial_tenancy_and_auth`).
  - Verification: Migration file is generated with up/down revisions.

- [x] **Task 5: Cryptography & JWT Security Helpers**
  - File: `backend/app/core/security.py`
  - Action: Implement `hash_password(password: str) -> str`, `verify_password(plain: str, hashed: str) -> bool`, and `create_access_token(data: dict, expires_delta: timedelta | None) -> str`.
  - Verification: Unit tests verifying hash verification and JWT token encoding/decoding.

- [x] **Task 6: Authentication Schemas & Service Logic**
  - Files: `backend/app/modules/auth/schemas.py`, `backend/app/modules/auth/service.py`
  - Action: Define Pydantic request/response schemas. Implement `register_merchant` (atomic transaction creating Organization + User + Member) and `authenticate_user`.
  - Verification: Unit tests verifying registration and login logic with mock/test database.

- [x] **Task 7: FastAPI Authentication Routes & Dependencies**
  - Files: `backend/app/modules/auth/router.py`, `backend/app/api/dependencies.py`, `backend/app/api/router.py`, `backend/app/main.py`
  - Action: Implement `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, and `GET /api/v1/auth/me`. Implement `get_current_user` and `get_current_tenant` dependency guards. Mount router under `/api/v1`.
  - Verification: End-to-end integration tests covering registration, login, and `/me` authorization.

- [x] **Task 8: Tenant Boundary Isolation Verification**
  - Files: `backend/tests/integration/test_auth.py`, `backend/tests/integration/test_tenant_isolation.py`
  - Action: Test edge cases: duplicate email registration, invalid login passwords, expired JWT tokens, and attempting cross-tenant access.
  - Verification: All automated tests pass with 100% green status.
