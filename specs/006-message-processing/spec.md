# Feature Spec: 006-message-processing

## 1. Objective
Establish the **Message Processing and Meta Webhooks** domain for Chatrio. This module connects Chatrio directly to the **Meta WhatsApp Cloud API (Graph API v21.0)**. It handles secure webhook ingestion, sub-50ms acknowledgement, HMAC-SHA256 signature verification, a Redis-backed sliding window debounce buffer to coalesce burst messages, customer/conversation record synchronisation, and outbound message dispatch.

---

## 2. In Scope
1. **Configuration & Credentials (`app/core/config.py`)**:
   - Meta Cloud API credentials: `meta_app_secret`, `meta_verify_token`, `meta_access_token`, `meta_phone_number_id`, `meta_api_version`.
   - Redis debounce settings: `whatsapp_debounce_seconds` (default 2.5s) and `whatsapp_debounce_max_wait_seconds` (default 8.0s).
2. **Webhook Verification & HMAC Security (`app/modules/messaging/security.py`)**:
   - `GET /api/v1/webhooks/whatsapp`: Challenge handshake responding to Meta registration queries (`hub.mode`, `hub.verify_token`, `hub.challenge`).
   - HMAC-SHA256 signature verification middleware/utility verifying `X-Hub-Signature-256` using timing-safe comparisons (`hmac.compare_digest`).
3. **Sub-50ms Webhook Ingestion (`app/modules/messaging/router.py`)**:
   - `POST /api/v1/webhooks/whatsapp`: Verifies signature, pushes raw payload to the ingestion buffer, and returns `200 OK` within $< 50\text{ms}$ to prevent Meta timeouts and duplicate webhook retries.
4. **Redis Sliding Window Debounce Buffer (`app/modules/messaging/debounce.py`)**:
   - Sliding inactivity timer: Resets on each new message received from the same sender phone number within 2.5 seconds.
   - Maximum buffer cap: Hard ceiling of 8.0 seconds to prevent indefinite delay.
   - Coalesces rapid customer bursts (e.g. typing 3 short messages in 5 seconds) into a single unified conversational turn.
5. **Inbound Webhook Payload Parsing & Service Integration (`app/modules/messaging/service.py`)**:
   - Extracts phone number, sender name, message timestamp, and message type (text, image, interactive button replies).
   - Resolves tenant organization via WhatsApp Business Phone Number ID.
   - Persists customer and messages via `CustomerService` and `MessageService` (Spec 004) with strict `whatsapp_message_id` idempotency.
6. **Outbound WhatsApp Cloud API Client (`app/infrastructure/whatsapp/client.py`)**:
   - Async HTTP client via `httpx.AsyncClient` supporting:
     - Sending standard text messages.
     - Sending interactive button messages (e.g., order confirmations, quick replies).
     - Error handling, timeouts, and structured logging.
7. **Automated Testing Suite**:
   - Unit tests for HMAC signature verification, challenge validation, payload parsing, and sliding debounce logic.
   - Integration tests simulating Meta webhook handshakes, multi-message bursts, and outbound message dispatch.

---

## 3. Out of Scope (Deferred to Later Specs)
- LangGraph LLM orchestration, prompt templates, and autonomous tool calling (Spec 007 - AI Agent).
- Human-agent real-time WebSocket notifications to the Next.js merchant inbox (Dashboard Spec).
- WhatsApp Media upload/hosting for custom merchant video/catalog files (Spec 008 - Media & Storage).

---

## 4. Requirements & Invariants

### 4.1 Functional Requirements
1. **Sub-50ms Meta SLA**:
   - `POST /api/v1/webhooks/whatsapp` must complete within 50ms by delegating heavy processing to asynchronous background tasks/Redis.
2. **Strict HMAC Authentication**:
   - All inbound POST webhook payloads must possess a valid `X-Hub-Signature-256` matching `HMAC-SHA256(meta_app_secret, raw_body)`. Unsigned or tampered requests are rejected with `401 Unauthorized`.
3. **Sliding Inactivity Debounce**:
   - A customer typing multiple messages within 2.5 seconds of each other must have their messages coalesced into a single unified turn, capped at an 8.0-second maximum wait window.
4. **Idempotent Ingestion**:
   - Duplicate webhook deliveries sharing the same `whatsapp_message_id` must be safely ignored without duplicate database entries or repeated AI actions.
5. **Multi-Tenant Routing**:
   - Incoming messages are bound to the correct merchant tenant by mapping Meta's `phone_number_id` to the tenant organization.

### 4.2 Non-Functional Invariants
1. **Zero Raw Secrets**:
   - `META_APP_SECRET` and `META_ACCESS_TOKEN` must never be logged or exposed in client responses.
2. **Type Safety & Pydantic Validation**:
   - 100% type annotations on all client methods, parser routines, and schemas.
3. **Zero Phantom Verifications**:
   - Every test must execute in the local test runner with verified output before advancing.

