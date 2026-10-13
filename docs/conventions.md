# Chatrio — Engineering Conventions & Standards

This document specifies the exact code formatting, directory structures, naming conventions, and testing guidelines for the Chatrio platform.

---

## 1. Python & FastAPI Conventions

### 1.1 Python Style & Tooling
- **Python Version**: Target Python 3.12+ (compatible with Python 3.14).
- **Linter & Formatter**: `ruff` (`ruff check .`, `ruff format .`).
- **Line Length**: 100 characters max.
- **Type Checking**: Strict typing using standard annotations. Prefer `str | None` over `Optional[str]`.
- **Imports**: Grouped in order: standard library, third-party libraries, local application modules. Sorted by `ruff`.

### 1.2 Module Structure
Every feature module inside `backend/app/modules/<module_name>/` must follow the 4-layer structure:
- `router.py`: Handles HTTP routes, dependency injection, and HTTP status codes. No direct business calculations or raw database transactions.
- `schemas.py`: Pydantic models for request bodies, query params, and response DTOs.
- `service.py`: Encapsulates business logic, domain rules, state transitions, and database queries.
- `models.py`: SQLAlchemy declarative ORM models mapped to database tables.

### 1.3 Asynchronous Execution
- All database I/O, Redis interactions, and external HTTP calls must use `async`/`await`.
- Never block the event loop with synchronous calls (`time.sleep()`, synchronous `requests`, or CPU-bound loops).
- CPU-intensive tasks (e.g. document parsing, audio transcription) must run in worker processes via BullMQ.

---

## 2. Database & Data Modeling Conventions

1. **Table Naming**: Lowercase plural snake_case (e.g., `organizations`, `customers`, `conversations`, `messages`, `products`, `orders`).
2. **Primary Keys**: UUID v7 or v4 string representation (`id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)`).
3. **Multi-Tenancy Key**: Every tenant-owned table MUST include `organization_id` foreign key referencing `organizations.id` with `index=True, nullable=False`.
4. **Timestamps**: Every table must include `created_at` and `updated_at` (UTC timestamp with timezone).
5. **Soft Deletes**: Use `deleted_at: datetime | None = None` where soft-delete behavior is required.

---

## 3. API Design & Error Handling

1. **URL Prefix**: All API endpoints must be prefixed with `/api/v1/`.
2. **Response Envelope**: Successful responses return data directly conforming to their Pydantic response schema.
3. **Error Responses**: All client errors (4xx) and server errors (5xx) must follow a structured error format:
   ```json
   {
     "error": {
       "code": "RESOURCE_NOT_FOUND",
       "message": "The requested product was not found.",
       "details": {}
     }
   }
   ```
4. **Status Codes**:
   - `200 OK`: Successful read or standard mutation.
   - `201 Created`: Successful creation of a resource.
   - `204 No Content`: Successful deletion with no body.
   - `400 Bad Request`: Validation or malformed input.
   - `401 Unauthorized`: Missing or invalid authentication token.
   - `403 Forbidden`: Authenticated user lacks permission or crosses tenant boundary.
   - `404 Not Found`: Resource does not exist within the tenant.
   - `409 Conflict`: Unique constraint violation or state machine invalid transition.
   - `422 Unprocessable Entity`: Request body schema validation failure.
   - `500 Internal Server Error`: Unhandled server failure.

---

## 4. Git & Commit Guidelines

1. **Commit Messages**: Conventional commits (`feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `refactor: ...`, `chore: ...`).
2. **Branching**: `main` is protected. Features branch off `main` as `feature/<spec-number>-<name>`.
3. **Work-in-Progress**: Never commit half-broken states without passing local tests.
