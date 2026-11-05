# Tasks: 004-conversations

Each task is atomic, independent, and verifiable.

- [ ] **Task 1: Customer, Conversation & Message ORM Models**
  - Files: `backend/app/modules/customers/models.py`, `backend/app/modules/conversations/models.py`, `backend/app/db/models.py`
  - Action: Define `Customer`, `Conversation`, and `Message` models with foreign keys, indexes, unique constraints (`(organization_id, phone_number)`), and enums. Re-export in `app/db/models.py`.
  - Verification: Models import cleanly and SQLAlchemy metadata registers all 3 new tables.

- [ ] **Task 2: Alembic Database Migration for Conversations & Customers**
  - File: `backend/migrations/versions/003_conversations_and_customers.py`
  - Action: Create migration script creating `customers`, `conversations`, and `messages` tables with indexes and foreign keys.
  - Verification: Unit test verifies migration script structure and upgrade/downgrade callables.

- [ ] **Task 3: Customer & Conversation Pydantic Validation Schemas**
  - Files: `backend/app/modules/customers/schemas.py`, `backend/app/modules/conversations/schemas.py`
  - Action: Define schemas for creating, updating, and reading customers, conversations, messages, and takeover toggles.
  - Verification: Schema validation unit tests covering valid input, phone normalization formatting, and pagination limits.

- [ ] **Task 4: Customer & Conversation Business Service Logic**
  - Files: `backend/app/modules/customers/service.py`, `backend/app/modules/conversations/service.py`
  - Action: Implement `CustomerService` (get/create by phone, normalize E.164) and `ConversationService` + `MessageService` (session creation, message appending, idempotency check on `whatsapp_message_id`, human takeover toggle).
  - Verification: Unit tests verifying get-or-create, takeover state changes, and duplicate message prevention.

- [ ] **Task 5: FastAPI Customer & Conversation REST Endpoints**
  - Files: `backend/app/modules/customers/router.py`, `backend/app/modules/conversations/router.py`, `backend/app/api/router.py`
  - Action: Implement routes for `/api/v1/customers`, `/api/v1/conversations`, `/api/v1/conversations/{id}/messages`, and `/api/v1/conversations/{id}/takeover`. Mount under master API router.
  - Verification: Integration tests testing endpoint authentication, role restrictions, message history, and takeover toggling.

- [ ] **Task 6: Multi-Tenant Conversation & Customer Isolation Verification**
  - File: `backend/tests/integration/test_conversation_isolation.py`
  - Action: Verify Tenant A cannot view, query, or send messages to Tenant B's conversations or customers. Verify identical phone numbers across different tenants.
  - Verification: 100% green test suite across all unit and integration tests.

