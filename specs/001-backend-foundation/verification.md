# Verification Criteria: 001-backend-foundation

This document defines the strict gate criteria required to declare Feature 001 complete.

---

## 1. Automated Test Verification
Run the following test command from the `backend/` directory:
```bash
pytest -v
```
**Expected Result**:
- `tests/test_health.py::test_health_check_returns_200` PASSED
- `tests/test_health.py::test_health_payload_schema` PASSED
- 0 failed, 0 errors.

---

## 2. Linter & Formatting Verification
Run the following commands:
```bash
ruff check backend/
ruff format backend/ --check
```
**Expected Result**:
- Zero lint errors.
- All files correctly formatted.

---

## 3. Manual Live Execution Verification
Start the development server:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Query the health check:
```bash
curl http://127.0.0.1:8000/health
```
**Expected Response**:
```json
{
  "status": "ok",
  "app_name": "Chatrio API",
  "version": "0.1.0",
  "environment": "development"
}
```
HTTP Status: `200 OK`, `Content-Type: application/json`.

---

## 4. Acceptance Criteria Checklist
- [ ] `pyproject.toml` defines correct dependencies and metadata.
- [ ] `.env.example` documents all required baseline environment variables.
- [ ] `app/core/config.py` loads settings safely with type validation.
- [ ] `app/main.py` provides working FastAPI instance and `/health` route.
- [ ] No database, authentication, Redis, AI, or WhatsApp dependencies are invoked.
- [ ] All tests pass without warnings or external server requirements.
