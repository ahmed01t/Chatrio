# Tasks: 006-message-processing

Each task is atomic, independent, and verifiable.

- [x] **Task 1: Dependencies & Meta Configuration Settings**
  - Files: `backend/pyproject.toml`, `backend/app/core/config.py`, `backend/.env.example`
  - Action: Add `redis>=5.2.0` dependency. Update `Settings` class with Meta WhatsApp Cloud API credentials (`meta_app_secret`, `meta_verify_token`, `meta_access_token`, `meta_phone_number_id`, `meta_api_version`) and sliding debounce parameters (`whatsapp_debounce_seconds=2.5`, `whatsapp_debounce_max_wait_seconds=8.0`). Update `.env.example`.
  - Verification: Unit tests in `test_config.py` verify new configuration fields and defaults.

- [x] **Task 2: Webhook Security & HMAC-SHA256 Signature Verification**
  - Files: `backend/app/modules/messaging/security.py`, `backend/tests/unit/test_webhook_security.py`
  - Action: Implement timing-attack-safe HMAC-SHA256 signature verification (`verify_meta_signature`) comparing `X-Hub-Signature-256` against `HMAC(meta_app_secret, raw_body)`.
  - Verification: Unit tests verifying valid signatures, invalid signatures, malformed headers, and body tampering.

- [x] **Task 3: Meta Webhook Schemas & Handshake Endpoint**
  - Files: `backend/app/modules/messaging/schemas.py`, `backend/app/modules/messaging/router.py`, `backend/app/api/router.py`
  - Action: Define Pydantic models for incoming Meta webhook payloads (contacts, messages, interactive replies). Implement `GET /api/v1/webhooks/whatsapp` verifying `hub.mode == 'subscribe'` and returning `hub.challenge`. Mount router in `app/api/router.py`.
  - Verification: Integration tests testing successful challenge validation and rejection of invalid verification tokens.

- [x] **Task 4: Redis Sliding Window Debounce Buffer**
  - Files: `backend/app/modules/messaging/debounce.py`, `backend/tests/unit/test_debounce.py`
  - Action: Implement `SlidingDebounceBuffer` using Redis (with in-memory fallback for local testing). Resets on message arrivals within 2.5s; flushes immediately when 8.0s max wait cap is reached or when 2.5s of silence occurs.
  - Verification: Unit tests simulating burst arrivals, timer resets, and hard ceiling execution.

- [ ] **Task 5: Fast Webhook Ingestion & Inbound Payload Processing**
  - Files: `backend/app/modules/messaging/service.py`, `backend/app/modules/messaging/router.py`, `backend/tests/unit/test_messaging_service.py`
  - Action: Implement `POST /api/v1/webhooks/whatsapp` to verify HMAC, buffer payloads, and return `200 OK` in $< 50\text{ms}$. Implement `MessagingService.process_incoming_payload` to parse text/button messages and persist records via `CustomerService` and `MessageService` with WhatsApp ID deduplication.
  - Verification: Unit tests verifying webhook ingestion, message parsing, and conversation/customer linking.

- [ ] **Task 6: Outbound WhatsApp Cloud API Client**
  - Files: `backend/app/infrastructure/whatsapp/client.py`, `backend/tests/unit/test_whatsapp_client.py`
  - Action: Implement asynchronous `WhatsAppClient` via `httpx.AsyncClient` supporting `send_text_message` and `send_interactive_buttons` against Meta Graph API endpoints.
  - Verification: Unit tests with mocked HTTP transport validating outbound payload structures, auth headers, and error handling.

- [ ] **Task 7: End-to-End Integration Tests**
  - File: `backend/tests/integration/test_webhooks.py`
  - Action: End-to-end integration test simulating the entire webhook lifecycle: Meta registration challenge -> HMAC verified burst message ingestion -> debounce coalescing -> customer/message persistence -> outbound confirmation.
  - Verification: 100% green test suite across all unit and integration tests.

