# Chatrio — Engineering & Agent Operational Rules (AGENTS.md)

This document establishes the permanent operational, architectural, security, coding, and testing rules for all autonomous agents and engineers working in this repository.

---

## 1. Prime Directive & System Authority

1. **Deterministic Authority**: The backend application and PostgreSQL database are the single source of truth for business logic, catalog data, pricing, stock, customer state, and order workflows. The AI agent (LangGraph) is an assistant and tool-invoker, never an unrestricted database writer or policy authority.
2. **Strict Multi-Tenancy**: Every business is an isolated tenant. Every query, mutation, vector search, background job, and cache key must be bound to an explicit `organization_id`. Cross-tenant data access is a critical security violation.
3. **Spec-Driven Progression**: No application code shall be written without an approved specification in `specs/`. Implementation proceeds strictly in discrete, testable phases.
4. **Zero Silent Failures**: All exceptions must be explicitly handled or bubbled up into structured error responses. Never use empty `except:` blocks.

---

## 2. Technology Stack & Architectural Boundaries

- **API & Core Backend**: Python 3.12+ / 3.14 with **FastAPI** and **Pydantic v2**.
- **Asynchronous Execution**: Fully asynchronous I/O (`async`/`await`). No blocking synchronous calls (e.g. no `requests.get` or `time.sleep`) in the web process event loop.
- **Relational Storage & Vector Search**: PostgreSQL 16+ with `pgvector` extension via **SQLAlchemy 2.0 Async** (`asyncpg`) and **Alembic** migrations.
- **Async Queue & Cache**: **Redis 7** with **BullMQ** (via `bullmq` Python package).
  - Webhooks acknowledge Meta immediately (< 50ms) after persisting raw payloads.
  - A 2.0-second Redis debounce buffer coalesces rapid customer bursts into single conversational turns.
- **AI Orchestration**: **LangGraph** (Python) with strictly defined, typed tools. The LLM has zero raw SQL, shell, or filesystem permissions.
- **Frontend Dashboard**: Next.js 15 (App Router) + TypeScript + Tailwind CSS (in `frontend/`).

---

## 3. Code Quality & Conventions

1. **Type Safety**: 100% type annotations on all function signatures, parameters, and return types (`typing` / Python 3.10+ union syntax).
2. **Modular Architecture**: Code is partitioned into `app/modules/<module_name>/` containing `router.py`, `schemas.py`, `service.py`, and `models.py`. Infrastructure adapters reside in `app/infrastructure/`.
3. **Pydantic Validation**: All incoming requests and outgoing responses must be validated with explicit Pydantic v2 schemas.
4. **Environment Variables**: Loaded strictly through `app.core.config.Settings` inheriting from `pydantic_settings.BaseSettings`. Direct use of `os.environ.get()` inside domain modules is prohibited.
5. **Linting & Formatting**: Enforce `ruff` for linting and formatting. Run `ruff check .` and `ruff format .` prior to finalizing tasks.

---

## 4. Security Rules

1. **Input Untrustedness**: All customer WhatsApp messages, uploaded documents, external URLs, and webhook payloads are untrusted input.
2. **Webhook Verification**: Every incoming WhatsApp webhook must be verified via Meta HMAC-SHA256 signature (`X-Hub-Signature-256`) before parsing.
3. **Secrets Management**: Secrets, API keys, and database passwords must never be committed to git or logged. Use `.env` and environment variables.
4. **Prompt Injection Defense**: Tool invocations triggered by the AI must undergo server-side validation against session authorization and business invariants before executing database writes.

---

## 5. Testing & Verification Standards

1. **No Phantom Verifications**: Never declare a test or command as passed without actual execution and verified terminal output.
2. **Test Framework**: `pytest` with `pytest-asyncio` for async tests.
3. **Coverage Expectation**: Every new endpoint or service must have unit tests covering the happy path and at least two edge/failure cases.
4. **Regression Safety**: All tests must execute cleanly without warnings or unhandled exceptions before moving to the next spec.
