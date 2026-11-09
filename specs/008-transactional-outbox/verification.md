# Verification Guide: 008-transactional-outbox

## 1. Automated Unit & Integration Tests
Run the pytest suite:
```bash
cd backend
uv run pytest tests/unit/test_outbox_*.py tests/integration/test_outbox_integration.py -v
```

Expected output:
- All new outbox model, schema, service, worker, and policy tests pass.
- Zero regressions across existing 189 tests (`uv run pytest`).

---

## 2. Code Quality & Conventions
```bash
cd backend
uv run ruff check .
uv run ruff format --check .
```

Expected output: Zero errors, zero warnings.

---

## 3. Policy & Invariant Verification
1. **Atomicity**: Outbox message is written inside the same SQL transaction as conversation messages/orders.
2. **Meta 24h Policy**: Freeform messages to a conversation inactive for $> 24\text{ hours}$ are safely rejected without calling Meta.
3. **Template Exemption**: Pre-approved templates pass through even outside the 24h window.
4. **Retry Resilience**: Temporary HTTP errors trigger exponential backoff up to `max_retries`.

