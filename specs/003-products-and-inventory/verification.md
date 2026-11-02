# Verification Guide: 003-products-and-inventory

## 1. Automated Test Execution
Run the complete test suite with:
```bash
cd backend
uv run pytest
```

Expected output:
- All 41 existing tests pass.
- New unit tests for Product, Category, and Inventory models pass.
- New integration tests for product endpoints and tenant isolation pass.

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

