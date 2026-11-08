# Verification Guide: 006-message-processing

## 1. Automated Test Execution
Run the full test suite with:
```bash
cd backend
uv run pytest
```

Expected output:
- All 114 existing tests pass.
- New unit tests for webhook security and HMAC verification pass.
- New unit tests for Meta payload parsing pass.
- New unit tests for the sliding window debounce buffer pass.
- New unit tests for the outbound WhatsApp Cloud API client pass.
- New integration tests for Meta webhook handshakes, burst ingestion, and deduplication pass.

---

## 2. Code Quality & Formatting
Run linter and formatter:
```bash
cd backend
uv run ruff check .
uv run ruff format .
```
Expected output: Zero errors, zero warnings.

---

## 3. Webhook Latency & Handshake Verification
1. **Verification Challenge (`GET /api/v1/webhooks/whatsapp`)**:
   - Querying with `hub.mode=subscribe` and matching `hub.verify_token` returns status `200` with the plaintext `hub.challenge`.
   - Querying with mismatched `hub.verify_token` returns status `403 Forbidden`.
2. **Ingestion Latency (`POST /api/v1/webhooks/whatsapp`)**:
   - Request completes in $< 50\text{ms}$ with status `200 OK`.
3. **HMAC Signature Check**:
   - Tampered body or missing `X-Hub-Signature-256` header returns status `401 Unauthorized`.

