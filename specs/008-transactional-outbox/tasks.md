# Tasks: 008-transactional-outbox

Each task is atomic, independent, and verifiable.

- [x] **Task 1: Outbox Database Model & Migration**
  - Files: `backend/app/modules/messaging/models.py`, `backend/app/db/models.py`, `backend/migrations/versions/005_outbox_messages.py`
  - Action: Create `OutboxMessage` table model with `OutboxStatus`, `OutboxMessageType`, indexes, and Alembic migration.
  - Verification: Alembic model discovery and unit test for model instantiation.

- [x] **Task 2: Pydantic Schemas & Policy Validation**
  - Files: `backend/app/modules/messaging/outbox_schemas.py`, `backend/tests/unit/test_outbox_schemas.py`
  - Action: Define schemas for outbox creation, payload validation, and policy checks.
  - Verification: Unit tests verifying payload validation across `TEXT`, `INTERACTIVE`, and `TEMPLATE` types.

- [x] **Task 3: Outbox Service & 24-Hour Policy Window Engine**
  - Files: `backend/app/modules/messaging/outbox_service.py`, `backend/tests/unit/test_outbox_service.py`
  - Action: Implement transactional enqueuing, concurrency-safe batch retrieval (`FOR UPDATE SKIP LOCKED`), and the Meta 24-hour customer care policy window check.
  - Verification: Unit tests verifying enqueue, state transitions, and 24h window policy blocking.

- [x] **Task 4: Outbox Worker & Exponential Backoff Delivery**
  - Files: `backend/app/modules/messaging/outbox_worker.py`, `backend/tests/unit/test_outbox_worker.py`
  - Action: Implement the outbox worker loop, exponential backoff computation, error capturing, and Meta dispatch via `WhatsAppClient`.
  - Verification: Unit tests verifying successful dispatch, retry scheduling on 429/network errors, and permanent failure on policy violations.

- [x] **Task 5: End-to-End Pipeline Integration**
  - Files: `backend/app/modules/messaging/service.py`, `backend/tests/integration/test_outbox_integration.py`
  - Action: Connect `dispatch_ai_turn` and conversation messaging to atomically enqueue outbox messages instead of direct lossy network calls.
  - Verification: Integration test verifying end-to-end flow: inbound message -> AI turn -> transactional outbox insert -> worker dispatch.
