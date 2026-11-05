# Feature Spec: 004-conversations

## 1. Objective
Establish the **Customers** and **Conversations** domain for Chatrio. This module manages customer phone identities, conversation sessions, message history, and the human-in-the-loop takeover mechanism. It serves as the conversational foundation that connects WhatsApp webhooks (Spec 006) and the AI Agent (Spec 007) with the product catalog (Spec 003) and orders (Spec 005).

---

## 2. In Scope
1. **Core Data Models & Enums**:
   - `Customer` (`app/modules/customers/models.py`): Multi-tenant customer profile linked to an organization, keyed by normalized E.164 phone number, with optional name, email, metadata, and blocklist flags.
   - `Conversation` (`app/modules/conversations/models.py`): Active or closed chat session between a customer and a merchant store, tracking channel (`WHATSAPP`), status (`ACTIVE`, `CLOSED`, `ARCHIVED`), human takeover state (`is_ai_active: bool`), and assigned staff agent.
   - `Message` (`app/modules/conversations/models.py`): Individual messages exchanged in a conversation, tracking sender type (`CUSTOMER`, `AI_AGENT`, `HUMAN_AGENT`, `SYSTEM`), direction (`INBOUND`, `OUTBOUND`), delivery status (`RECEIVED`, `SENT`, `DELIVERED`, `READ`, `FAILED`), content type (`TEXT`, `IMAGE`, `INTERACTIVE`), and raw payload audit.
2. **Database Migration (`migrations/versions/003_conversations_and_customers.py`)**:
   - Create tables `customers`, `conversations`, and `messages` with foreign keys, cascading rules, and multi-tenant indexes.
   - Enforce composite uniqueness on `(organization_id, phone_number)` for customers and index on `whatsapp_message_id` for idempotency.
3. **Pydantic Validation Schemas**:
   - `CustomerCreate`, `CustomerUpdate`, `CustomerRead`, `CustomerListResponse`.
   - `ConversationCreate`, `ConversationRead`, `ConversationListResponse`, `ConversationTakeoverUpdate`.
   - `MessageCreate`, `MessageRead`, `MessageListResponse`.
4. **Service Business Logic**:
   - `CustomerService` (`app/modules/customers/service.py`): Get or create customer by phone, phone normalization, profile updates.
   - `ConversationService` (`app/modules/conversations/service.py`): Get active conversation or start new session, human takeover toggle, list customer messages with cursor/pagination.
   - `MessageService` (`app/modules/conversations/service.py`): Append incoming/outgoing messages, deduplicate by `whatsapp_message_id`, update delivery status.
5. **FastAPI REST Endpoints**:
   - `/api/v1/customers`: List and manage customer records.
   - `/api/v1/conversations`: List active/closed conversations for the merchant inbox.
   - `/api/v1/conversations/{id}/messages`: View message history and send manual human replies.
   - `/api/v1/conversations/{id}/takeover`: Toggle AI automation on/off for human agent intervention.

---

## 3. Out of Scope (Deferred to Later Specs)
- Live Meta WhatsApp API HTTP calls (Spec 006 - Message Processing).
- 2.0-second Redis debounce queue worker (Spec 006 - Message Processing).
- LangGraph automated responses and tool execution (Spec 007 - AI Agent).
- Real-time WebSocket/SSE notifications for the frontend inbox (Dashboard Spec).

---

## 4. Requirements & Invariants

### 4.1 Functional Requirements
1. **Strict Multi-Tenancy**:
   - Customers, conversations, and messages MUST belong to an explicit `organization_id`.
   - A customer phone number (e.g., `+14155552671`) can exist under multiple distinct tenants without cross-talk or data leakage.
2. **Phone Number Normalization**:
   - All customer phone numbers must be sanitized and stored in standard E.164 format (e.g., `+1234567890`).
3. **Idempotency & Message Deduplication**:
   - Messages with the same `(organization_id, whatsapp_message_id)` must be deduplicated to prevent duplicate processing on Meta webhook retries.
4. **Human Takeover Mechanism**:
   - When a merchant takes over a conversation (`is_ai_active = False`), the conversation is flagged for human control and the AI agent will not post automated replies until AI control is resumed (`is_ai_active = True`).

### 4.2 Non-Functional Invariants
1. **Type Safety**: 100% type-annotated function signatures, Pydantic v2 schemas, and SQLAlchemy 2.0 mapped columns.
2. **Zero Unhandled Exceptions**: Return standard application error responses (`404 NOT_FOUND`, `409 CONFLICT`, `422 UNPROCESSABLE_ENTITY`).
3. **Automated Testing**: Complete unit and integration test suite covering happy paths, tenant boundaries, and concurrent message appending.

