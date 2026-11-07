# Verification Guide: 005-orders

## 1. Automated Test Execution
Run the complete test suite with:
```bash
cd backend
uv run pytest
```

Expected output:
- All 88 existing tests pass.
- New unit tests for Order and OrderItem models pass.
- New unit tests for order price calculation, state machine transitions, and inventory reservation pass.
- New integration tests for order placement, cancellation stock release, and multi-tenant order isolation pass.

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
- `orders`
- `order_items`

