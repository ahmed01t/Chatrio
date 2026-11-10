# Spec 009: Next.js 15 Merchant Dashboard & Design System

## 1. Overview & Aesthetic Direction
Chatrio is a multi-tenant conversational commerce platform connecting WhatsApp with AI agents, products, and order management. This specification defines the production-ready Next.js 15 App Router merchant frontend.

### Design Language & Color Palette (Linear / Datadog Obsidian Theme)
Inspired by modern dark-mode AI operations dashboards (deep charcoal/slate with glowing status accents):
- **Primary Background**: Obsidian Deep Black (`#0B0D11`)
- **Card / Surface Background**: Dark Slate Charcoal (`#131720`)
- **Elevated Hover / Active Surface**: Slate Container (`#1A202C`)
- **Borders & Dividers**: Subtle Dark Stroke (`#222938`, `rgba(255,255,255,0.08)`)
- **Primary Brand Accent**: Electric Emerald / WhatsApp Green (`#10B981` / `#25D366`)
- **Secondary Cyber Accent**: Deep Sky Blue / Cyan (`#0EA5E9` / `#38BDF8`)
- **Warning Accent**: Warm Amber (`#F59E0B`)
- **Critical / Danger Accent**: Coral Red (`#EF4444`)
- **Typography**: Clean Sans-Serif (Geist / Inter) with tabular numeric displays.

---

## 2. Core Functional Modules

### 2.1 Authentication & Multi-Tenant Session (`/login`, `/register`)
- Merchant signup: Store Name, Owner Name, Email, Password, Store Currency.
- Merchant login: Email/password with JWT storage (HTTP cookies / local storage fallback).
- Auth state provider with route guards (`/login`, `/register` public; all other routes protected).

### 2.2 Dashboard Overview (`/`)
- KPI Stat Cards matching reference design:
  - Total Store Revenue (with currency and trend indicator).
  - Active WhatsApp Conversations today.
  - Pending Orders requiring fulfillment.
  - AI Automation Rate % (conversations resolved without human takeover).
- Recent Activity Feed (real-time orders and customer messages).
- Quick Action Pills (Add Product, View AI Escalations).

### 2.3 Live WhatsApp Shared Inbox (`/inbox`)
- Split-pane layout:
  - **Left Pane (Conversations List)**: Customer phone, name, last message snippet, timestamp, unread badge, and **AI Status Indicator** (`AI Active` vs `Human Needed` alert).
  - **Right Pane (Active Transcript)**:
    - Top bar: Customer info, session details, and **AI Takeover Switch** (`Toggle AI on/off`).
    - Message history: Inbound customer bubbles, Outbound AI Agent bubbles, Outbound Human Agent bubbles.
    - Bottom bar: Message composer with human send action (`POST /conversations/{id}/messages`), triggering the Transactional Outbox engine.

### 2.4 Product Catalog Management (`/products`)
- Grid and table view of all merchant products.
- Product cards with price, stock inventory badge, SKU, and category chips.
- "Add Product" & "Edit Product" modal dialogs interacting with `/api/v1/products`.
- In-line stock adjustment and deletion with confirmation dialogs.

### 2.5 Orders & Commerce Board (`/orders`)
- Orders table matching reference card style with Order Number, Customer Phone, Created Date, Line Item Count, Total Amount, and Payment/Order Status badges.
- Slide-over order detail drawer showing line items, pricing breakdown (subtotal, shipping, total), and customer delivery address.
- Order status state transitions (`CONFIRMED`, `SHIPPED`, `CANCELLED`).

### 2.6 Settings & Integrations (`/settings`)
- Organization Profile: Store Name, Slug, Currency.
- WhatsApp Cloud API configuration display: Phone Number ID, Webhook callback URL.
- AI Agent configuration: Assistant Persona, Store Welcome Message, Temperature.

---

## 3. Technology Stack & Directory Structure
- **Framework**: Next.js 15 (App Router, React 19).
- **Styling**: Tailwind CSS v3 / v4 with `clsx` and `tailwind-merge`.
- **Icons**: `lucide-react`.
- **Data Fetching & State**: TanStack React Query (or SWR) + Custom Fetch Client with automatic auth header injection.
- **Directory Structure**:
  - `frontend/src/app/` (Next.js App Router routes)
  - `frontend/src/components/ui/` (Reusable atomic UI elements: Button, Card, Badge, Modal, Input, etc.)
  - `frontend/src/components/layout/` (Sidebar, Navbar, Layout wrapper)
  - `frontend/src/components/inbox/` (Chat transcript, conversation list, takeover toggle)
  - `frontend/src/components/products/` (Product modal, table, card)
  - `frontend/src/components/orders/` (Order drawer, table, status chip)
  - `frontend/src/lib/` (API client, Auth context, utilities, formatting helpers)
  - `frontend/src/types/` (TypeScript interfaces mirroring backend Pydantic schemas)

