# Tasks: 001-backend-foundation

Each task is atomic, independent, and verifiable.

- [x] **Task 1: Packaging & Tooling Configuration**
  - File: `backend/pyproject.toml`
  - Action: Define project metadata, production dependencies (`fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`), and dev dependencies (`pytest`, `pytest-asyncio`, `httpx`, `ruff`).
  - Verification: `uv pip install -e ".[dev]"` executed with 0 errors.

- [x] **Task 2: Canonical Environment Specification**
  - File: `backend/.env.example`
  - Action: Populate documented environment variables for app name, environment, debug flag, and log level.
  - Verification: File verified and copied to local `.env`.

- [x] **Task 3: Type-Safe Settings Model**
  - File: `backend/app/core/config.py`
  - Action: Implement `Settings` using `pydantic_settings.BaseSettings` with default values and cached getter.
  - Verification: Unit tests in `tests/unit/test_config.py` passed.

- [x] **Task 4: Application Factory & Health Endpoint**
  - File: `backend/app/main.py`
  - Action: Implement `create_app()` and `GET /health` endpoint returning JSON status.
  - Verification: Integration tests in `tests/integration/test_health.py` passed.

- [x] **Task 5: Test Suite Setup**
  - Files: `backend/tests/conftest.py`, `backend/tests/test_health.py`
  - Action: Create async-compatible test fixtures and test suite.
  - Verification: Run `pytest` and confirmed 4/4 tests passed in 0.08s.

- [x] **Task 6: Code Quality Verification**
  - Action: Run `ruff check backend` and `ruff format backend --check`.
  - Verification: Zero errors reported across all files.
