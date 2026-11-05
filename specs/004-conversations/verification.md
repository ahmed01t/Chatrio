# Verification Guide: 004-conversations

## 1. Automated Test Execution
Run the complete test suite with:
```bash
cd backend
uv run pytest
```

Expected output:
- All 64 existing tests pass.
- New unit tests for Customer, Conversation, and Message models pass.
- New unit tests for phone normalization, get-or-create customer logic, and human takeover pass.
- New integration tests for customer/conversation REST endpoints and multi-tenant isolation pass.

## 2. Code Quality & Linting
Run linter and formatter:
```bash
cd backend
uv run ruff check .
uv run ruff format .
```
Expected output: Zero errors, zero warnings.

## 3. Database Schema Verification
Check that `Base.metadata` contains:
- `organizations`
- `users`
- `organization_members`
- `categories`
- `products`
- `product_categories`
- `inventory_logs`
- `customers`
- `conversations`
- `messages`

