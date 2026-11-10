# Implementation Plan: 009-frontend-dashboard

## User Review Required
The frontend will be built directly inside `frontend/` using modern Next.js 15, TypeScript, and Tailwind CSS with the obsidian dark-mode aesthetic requested by the user.

---

## Proposed Phases & Milestones

### 1. Project Initialization & Architecture Setup
- Initialize Next.js 15 with TypeScript, Tailwind CSS, and `lucide-react`.
- Configure custom design system tokens in `tailwind.config.ts` (obsidian `#0B0D11`, slate card `#131720`, emerald `#10B981`, cyber cyan `#0EA5E9`).
- Set up typed API client (`src/lib/api.ts`) with automatic JWT injection, base URL handling (`http://localhost:8000/api/v1`), and error toasts.
- Set up `AuthContext` with persistent login state, token refresh, and route protection.

### 2. Design System & Layout Components
- Build atomic UI library: `Button`, `Input`, `Card`, `Badge`, `Modal`, `Table`, `Tabs`, `StatCard`, `Avatar`.
- Build application shell: Collapsible Sidebar, Top Navbar with search (`Cmd+K`), Organization switcher, and User Menu.

### 3. Authentication & Onboarding
- Build `/login`: Email & password login with demo/auto-fill helpers and validation.
- Build `/register`: Multi-tenant organization registration with store name, currency, and credentials.

### 4. Dashboard Overview Page (`/`)
- KPI stat cards with trend badges (Revenue, Active Chats, Pending Orders, AI Resolution %).
- Real-time customer activity stream.
- Quick navigation shortcuts.

### 5. Live WhatsApp Shared Inbox (`/inbox`)
- Split-screen layout:
  - Conversation list with search, unread count, and AI vs Human takeover badges.
  - Active chat window with message transcript bubbles (Customer, AI, Human).
  - Prominent **AI Takeover Switch** (Pause/Resume AI).
  - Human reply composer connected to `/api/v1/conversations/{id}/messages` (Transactional Outbox).

### 6. Products & Catalog Management (`/products`)
- Product catalog table & card view with search and category filters.
- "Add Product" and "Edit Product" dialogs with stock validation.
- Delete and stock quick-adjustment actions.

### 7. Orders & Commerce Board (`/orders`)
- Orders table with filtering by status (`PENDING`, `CONFIRMED`, `SHIPPED`, `CANCELLED`).
- Slide-over order detail drawer showing customer details, line items, and delivery address.
- Status update action buttons.

### 8. Settings & Store Profile (`/settings`)
- Organization metadata editor.
- WhatsApp Cloud API configuration display.
- AI Agent prompt/welcome message configuration.

