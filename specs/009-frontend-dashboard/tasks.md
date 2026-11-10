# Tasks: 009-frontend-dashboard

Each task is atomic, independent, and verifiable.

- [x] **Task 1: Next.js 15 Foundation & Obsidian Design Tokens**
  - Files: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tailwind.config.ts`, `frontend/src/app/globals.css`
  - Action: Scaffold Next.js 15 App Router project with Tailwind CSS, Lucide icons, and the dark-mode obsidian palette (`#0B0D11`, `#131720`, `#1A202C`, `#10B981`).
  - Verification: `npm run build` succeeds without TypeScript or styling errors.

- [x] **Task 2: API Client, Type Definitions & Auth Context**
  - Files: `frontend/src/lib/api.ts`, `frontend/src/types/index.ts`, `frontend/src/context/AuthContext.tsx`
  - Action: Implement typed API client with automatic token attachment, full TypeScript schemas matching backend Pydantic models, and client-side AuthProvider.
  - Verification: Mock API client unit test or build verification.

- [x] **Task 3: Reusable Atomic UI Component Library**
  - Files: `frontend/src/components/ui/` (`Button.tsx`, `Card.tsx`, `Badge.tsx`, `Input.tsx`, `Modal.tsx`, `StatCard.tsx`, `Table.tsx`)
  - Action: Implement modern, accessible dark-mode UI components matching the reference design.
  - Verification: Component compilation and render check in page layout.

- [x] **Task 4: Application Shell, Sidebar & Navigation**
  - Files: `frontend/src/components/layout/Sidebar.tsx`, `frontend/src/components/layout/Navbar.tsx`, `frontend/src/app/layout.tsx`
  - Action: Create application frame with slim collapsible sidebar, top bar with organization switcher, search shortcut, and user profile.
  - Verification: Visual verification of layout rendering across all route slots.

- [x] **Task 5: Authentication Pages (Login & Register)**
  - Files: `frontend/src/app/(auth)/login/page.tsx`, `frontend/src/app/(auth)/register/page.tsx`
  - Action: Build modern login and merchant registration forms with validation, error states, and token storage.
  - Verification: Successful login and register form rendering and submission logic.

- [x] **Task 6: Dashboard Overview Page**
  - Files: `frontend/src/app/page.tsx`, `frontend/src/components/dashboard/ActivityFeed.tsx`
  - Action: Build main dashboard overview with KPI metric cards, recent customer activity, and quick actions.
  - Verification: Page builds cleanly and displays mock/fetched KPI data.

- [x] **Task 7: Live WhatsApp Shared Inbox**
  - Files: `frontend/src/app/inbox/page.tsx`, `frontend/src/components/inbox/ConversationList.tsx`, `frontend/src/components/inbox/ChatTranscript.tsx`, `frontend/src/components/inbox/MessageComposer.tsx`
  - Action: Build split-pane WhatsApp inbox with conversation list, message transcript, **AI Takeover Switch**, and human reply composer.
  - Verification: Split-view interaction, message sending, and takeover toggle functioning.

- [x] **Task 8: Product Catalog Management**
  - Files: `frontend/src/app/products/page.tsx`, `frontend/src/components/products/ProductModal.tsx`
  - Action: Build products table, category filtering, search, and "Add/Edit Product" modal dialog.
  - Verification: Product listing and modal dialog rendering and submission.

- [x] **Task 9: Orders & Commerce Board**
  - Files: `frontend/src/app/orders/page.tsx`, `frontend/src/components/orders/OrderDetailDrawer.tsx`
  - Action: Build orders list with status badges and slide-over order detail drawer.
  - Verification: Order listing and detail drawer rendering.

- [x] **Task 10: Store Settings & Public Release Build Verification**
  - Files: `frontend/src/app/settings/page.tsx`, `frontend/next.config.ts`
  - Action: Build settings page and perform full production build (`npm run build`).
  - Verification: Zero errors, zero warnings on `npm run build` and `npm run lint`.
