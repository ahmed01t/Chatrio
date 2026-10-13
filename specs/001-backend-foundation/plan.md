# Implementation Plan: 001-backend-foundation

## 1. Summary
This plan outlines the exact technical implementation steps to stand up the minimal Python backend runtime and test harness.

## 2. Technical Approach

### 2.1 Dependency Management (`backend/pyproject.toml`)
- Declare standard PEP 621 metadata.
- Core dependencies:
  - `fastapi>=0.115.0`
  - `uvicorn[standard]>=0.32.0`
  - `pydantic>=2.10.0`
  - `pydantic-settings>=2.7.0`
- Development / Test dependencies:
  - `pytest>=8.3.0`
  - `pytest-asyncio>=0.24.0`
  - `httpx>=0.28.0` (required for FastAPI TestClient / AsyncClient)
  - `ruff>=0.8.0`
- Configure `tool.ruff` (line-length = 100, target-version = "py312").
- Configure `tool.pytest.ini_options` (asyncio_mode = "auto", testpaths = ["tests"]).

### 2.2 Environment Configuration (`backend/app/core/config.py` & `.env.example`)
- Create `Settings` class inheriting from `pydantic_settings.BaseSettings`.
- Properties:
  - `APP_NAME: str = "Chatrio API"`
  - `VERSION: str = "0.1.0"`
  - `ENVIRONMENT: str = "development"`
  - `DEBUG: bool = True`
  - `API_V1_PREFIX: str = "/api/v1"`
- Use `lru_cache` on `get_settings()` function to prevent re-parsing environment on every injection.

### 2.3 Application Factory (`backend/app/main.py`)
- Define `create_app() -> FastAPI` factory pattern.
- Attach CORS middleware allowing development origins.
- Mount `GET /health` route directly or via core router.

### 2.4 Test Suite Setup (`backend/tests/`)
- `tests/conftest.py`: Fixtures for `TestClient(app)` and settings overrides.
- `tests/unit/test_config.py`: Verifies `Settings` loading and defaults.
- `tests/integration/test_health.py`: Verifies `GET /health` returns status `200` with expected JSON payload.

## 3. Risks & Fallbacks
- **Python 3.14 Compatibility**: Python 3.14 was recently released. If any binary dependency has compilation issues under Python 3.14, pure-python packages and modern wheels in `uv` provide seamless fallbacks.
