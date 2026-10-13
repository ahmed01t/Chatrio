# Feature Spec: 001-backend-foundation

## 1. Objective
Establish the minimal, robust Python engineering baseline for the Chatrio backend. This includes project configuration via `pyproject.toml`, type-safe environment configuration loading, a runnable FastAPI application factory, a standardized health-check endpoint, and automated test/lint tooling.

## 2. In Scope
- Python project packaging specification using `pyproject.toml` (compatible with Python 3.12+ / 3.14, using modern build tooling such as `hatchling` or standard editable install with `uv`).
- Canonical `.env.example` defining runtime configuration variables.
- Type-safe application configuration via `app/core/config.py` using `pydantic-settings`.
- Minimal FastAPI application setup in `app/main.py`.
- Health-check endpoint: `GET /health` returning service metadata, status, and version.
- Development tooling configuration for linting/formatting (`ruff`) and testing (`pytest`).
- Initial unit test verifying that the application boots and `GET /health` returns `200 OK` with valid JSON.

## 3. Out of Scope (Explicitly Deferred)
- Database connections, SQLAlchemy models, and Alembic migrations (Deferred to Spec 002).
- Authentication, JWT, and multi-tenancy context (Deferred to Spec 002).
- Redis connections and BullMQ queues (Deferred to Spec 003).
- WhatsApp webhook ingestion and Meta API clients.
- LangGraph AI workflows, tools, and RAG.
- Frontend Next.js dashboard.

## 4. Requirements & Invariants

### 4.1 Functional Requirements
1. **Health Check Endpoint**:
   - Route: `GET /health`
   - Response Status: `200 OK`
   - Response Schema:
     ```json
     {
       "status": "ok",
       "app_name": "Chatrio API",
       "version": "0.1.0",
       "environment": "development"
     }
     ```
2. **Configuration Management**:
   - `Settings` class loads environment variables with sensible development defaults.
   - Missing required production variables in non-production environments must not crash application startup if valid defaults are provided.
   - Direct calls to `os.environ` in application logic are prohibited.

### 4.2 Non-Functional Invariants
1. **Zero External Runtime Blockers**: The application must boot locally without requiring live external network access, PostgreSQL, or Redis for this initial foundation phase.
2. **Speed & Cleanliness**: `ruff check .` and `pytest` must run cleanly with zero errors.
3. **Strict Typing**: All function definitions in `app/core/config.py` and `app/main.py` must have full type annotations.
