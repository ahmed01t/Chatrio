# Verification Criteria: 002-auth-and-tenancy

This document defines the strict gate criteria required to declare Feature 002 complete.

---

## 1. Automated Test Suite
Run the test suite from `backend/`:
```bash
.venv\Scripts\pytest -v
```

### Expected Test Results:
1. **Security & Cryptography (`tests/unit/test_security.py`)**:
   - `test_hash_password_generates_valid_bcrypt_hash` PASSED
   - `test_verify_password_returns_true_for_valid_password` PASSED
   - `test_verify_password_returns_false_for_invalid_password` PASSED
   - `test_jwt_encoding_decoding_roundtrip` PASSED
   - `test_jwt_token_expiration` PASSED

2. **Authentication Flow (`tests/integration/test_auth.py`)**:
   - `test_register_creates_organization_and_owner_user` PASSED (Status 201)
   - `test_register_fails_with_duplicate_email` PASSED (Status 409)
   - `test_login_succeeds_with_valid_credentials` PASSED (Status 200, returns JWT)
   - `test_login_fails_with_incorrect_password` PASSED (Status 401)
   - `test_get_me_returns_profile_with_valid_token` PASSED (Status 200)
   - `test_get_me_rejects_missing_or_invalid_token` PASSED (Status 401)

3. **Multi-Tenant Boundary Isolation (`tests/integration/test_tenant_isolation.py`)**:
   - `test_user_cannot_access_unauthorized_organization_context` PASSED (Status 403)
   - `test_jwt_tampered_org_id_is_rejected` PASSED (Status 403)

---

## 2. Code Quality & Linting
Run linter and formatting checks:
```bash
.venv\Scripts\ruff check .
.venv\Scripts\ruff format --check .
```
- Zero errors reported.
- All files strictly formatted.

---

## 3. Database Migration Verification
Run Alembic validation:
```bash
alembic check
```
- Database schema matches the SQLAlchemy declarative models with zero unapplied drifts.

---

## 4. Acceptance Criteria Checklist
- [ ] `docker-compose.yml` provides repeatable PostgreSQL (pgvector) and Redis service definitions.
- [ ] SQLAlchemy 2.0 Async engine operates cleanly with connection pooling.
- [ ] `organizations`, `users`, and `organization_members` tables are created with proper indexes, constraints, and foreign keys.
- [ ] Passwords are never saved in plain text.
- [ ] Registration atomically creates Organization + User + Member in one ACID transaction.
- [ ] `get_current_user` and `get_current_tenant` dependency guards reject unauthenticated or cross-tenant requests.
- [ ] All automated tests pass with 100% green status.
