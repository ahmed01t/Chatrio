# Verification Guide: 009-frontend-dashboard

## 1. Build & TypeScript Verification
```bash
cd frontend
npm run build
```
Expected output:
- Next.js compiles all static and dynamic routes with zero TypeScript errors.
- Output generates optimized client bundles for `/`, `/login`, `/register`, `/inbox`, `/products`, `/orders`, `/settings`.

---

## 2. Linting & Formatting Check
```bash
cd frontend
npm run lint
```
Expected output: 0 errors, 0 warnings.

---

## 3. Visual & Functional Quality Verification
1. **Design System**: Obsidian dark palette (`#0B0D11`, `#131720`) matching the reference template.
2. **Auth Flow**: Login/signup validation and JWT token persistence.
3. **Live Inbox**: Split-view with customer conversations, AI takeover toggle, and human reply composer.
4. **Catalog**: Product listing with add/edit modals and category filtering.
5. **Orders**: Order table with status badges and detail slide-over drawer.

