# Tasks: 001-backend-foundation

Each task is atomic, independent, and verifiable.

- [ ] **Task 1: Packaging & Tooling Configuration**
  - File: `backend/pyproject.toml`
  - Action: Define project metadata, production dependencies (`fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`), and dev dependencies (`pytest`, `pytest-asyncio`, `httpx`, `ruff`).
  - Verification: `uv pip check` or validation that pyproject is well-formed.

- [ ] **Task 2: Canonical Environment Specification**
  - File: `backend/.env.example`
  - Action: Populate documented environment variables for app name, environment, debug flag, and log level.
  - Verification: Inspect file content.

- [ ] **Task 3: Type-Safe Settings Model**
  - File: `backend/app/core/config.py`
  - Action: Implement `Settings` using `pydantic_settings.BaseSettings` with default values and cached getter.
  - Verification: Unit test verifying instantiation and attribute access.

- [ ] **Task 4: Application Factory & Health Endpoint**
  - File: `backend/app/main.py`
  - Action: Implement `create_app()` and `GET /health` endpoint returning JSON status.
  - Verification: Execute manual or automated HTTP request against `/health`.

- [ ] **Task 5: Test Suite Setup**
  - Files: `backend/tests/conftest.py`, `backend/tests/test_health.py`
  - Action: Create async-compatible test fixtures using `httpx.AsyncClient` or `starlette.testclient.TestClient`.
  - Verification: Run `pytest` and confirm tests execute and pass.

- [ ] **Task 6: Code Quality Verification**
  - Action: Run `ruff check backend` and `ruff format backend --check`.
  - Verification: Zero errors reported.
