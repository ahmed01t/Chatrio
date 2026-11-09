# Implementation Plan: 008-transactional-outbox

## User Review Required
No breaking database changes to existing tables. Adding a new `outbox_messages` table and an asynchronous outbox worker.

---

## Proposed Changes

### 1. Database Model & Migration
- Create `backend/app/modules/messaging/models.py` with `OutboxMessage`, `OutboxStatus`, `OutboxMessageType`.
- Register `OutboxMessage` in `backend/app/db/models.py`.
- Create Alembic migration script `backend/migrations/versions/005_outbox_messages.py`.

### 2. Pydantic Schemas & Service Layer
- Create `backend/app/modules/messaging/outbox_schemas.py` with validation for `TEXT`, `INTERACTIVE`, and `TEMPLATE` payloads.
- Create `backend/app/modules/messaging/outbox_service.py`:
  - `enqueue_outbox(...)`: Atomic transactional insertion.
  - `fetch_pending_batch(...)`: Concurrency-safe batch retrieval (`SKIP LOCKED`).
  - `process_outbox_message(...)`: Meta 24-hour policy verification and dispatch via `WhatsAppClient`.
  - `mark_as_sent(...)`, `mark_as_failed(...)`, `schedule_retry(...)`.

### 3. Outbox Processing Worker
- Create `backend/app/modules/messaging/outbox_worker.py`:
  - Asynchronous worker loop processing batches of pending outbox messages.
  - Exponential backoff calculation and error handling.

### 4. Integration into Messaging & AI Pipeline
- Update `backend/app/modules/messaging/service.py`:
  - Modify `dispatch_ai_turn` to enqueue outbox messages transactionally rather than calling `WhatsAppClient` synchronously.
  - Ensure zero message loss if Meta is unreachable.

### 5. Automated Verification & Testing
- Unit tests for schema validation, outbox status transitions, and backoff calculations.
- Unit tests for Meta 24-hour policy window enforcement (blocking freeform, allowing templates).
- Integration tests for end-to-end transactional enqueue -> worker dispatch -> status update.

