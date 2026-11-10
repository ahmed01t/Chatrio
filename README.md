# Chatrio — Autonomous AI WhatsApp Conversational Commerce Platform

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16%20App%20Router-black?logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-336791?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Redis](https://img.shields.io/badge/Redis-7%20Cache%20%26%20Debounce-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Workflow-FF6F00?logo=langchain&logoColor=white)](https://langchain.com)
[![License](https://img.shields.io/badge/License-Proprietary-red)](#)

Chatrio is a multi-tenant B2B conversational commerce platform that turns **WhatsApp** into an autonomous, 24/7 sales and customer fulfillment channel. 

Powered by **LangGraph**, **FastAPI**, **PostgreSQL with pgvector**, and **Next.js**, Chatrio ingests messy, conversational WhatsApp voice and text messages, performs semantic catalog search, reserves inventory deterministically, and assembles orders directly in conversation—while giving human agents a shared live inbox with one-click AI takeover.

---

## Architecture Overview

```mermaid
flowchart TD
    subgraph WhatsApp["WhatsApp Ecosystem"]
        Customer["Customer on WhatsApp"]
        MetaCloud["Meta WhatsApp Cloud API"]
    end

    subgraph Ingestion["Ingestion & Queue Pipeline"]
        WebhookHandler["FastAPI Webhook Handler\n(HMAC-SHA256 Verified)"]
        RedisBuffer["Redis 7 Debounce Buffer\n(2.0s Coalescing Window)"]
        WorkerQueue["BullMQ Background Workers"]
    end

    subgraph Brain["Agentic Core (LangGraph)"]
        Agent["LangGraph Conversational Agent"]
        Guardrails["Server-side Invariant Guardrails"]
        Tools["Deterministic Business Tools\n(Stock, Orders, Outbox)"]
    end

    subgraph Storage["Storage & Infrastructure"]
        Postgres[("PostgreSQL 16 + pgvector\n(Multi-Tenant Scoped)")]
        OutboxTable[("Transactional Outbox Engine")]
    end

    subgraph MerchantApp["Merchant Dashboard (Next.js 16)"]
        Staff["Store Admin / Support Agent"]
        InboxUI["Shared Live Inbox & AI Takeover"]
        CatalogUI["Product & Stock Manager"]
        FulfillmentUI["Order Board & State Machine"]
    end

    Customer <-->|Text / Voice / Media| MetaCloud
    MetaCloud -->|Webhook POST < 50ms| WebhookHandler
    WebhookHandler -->|Buffer Rapid Bursts| RedisBuffer
    RedisBuffer --> WorkerQueue
    WorkerQueue --> Agent
    Agent <--> Tools
    Tools <--> Guardrails
    Guardrails <--> Postgres
    Tools --> OutboxTable
    OutboxTable -->|Reliable Dispatch| MetaCloud

    Staff <-->|Real-time Control| MerchantApp
    MerchantApp <-->|REST API v1| WebhookHandler
```

---

## Core Capabilities & Engineering Highlights

### 1. Deterministic Business Logic vs. AI Boundaries
- **Zero Raw Database Writing by LLM**: The AI model (LangGraph) functions as an intent classifier and tool invoker. It cannot directly update prices, inventory, or order records.
- **Server-Side Invariant Guardrails**: Every tool invocation undergoes server-side validation against session authorization, tenant isolation, and strict business rules.
- **Vector Semantic Search (`pgvector`)**: Customers can describe products conversationally (e.g., *"crisp red apples for baking"*), matching catalog SKUs via cosine vector distance.

### 2. WhatsApp Ingestion & Resiliency
- **HMAC-SHA256 Webhook Verification**: Every payload from Meta is verified against `X-Hub-Signature-256` before parsing.
- **2.0-Second Redis Debounce Buffer**: WhatsApp customers frequently send thoughts across multiple short messages (*"Hi"*, *"Do you have oranges?"*, *"And 2 apples"*). Redis buffers and merges rapid bursts into a single conversational turn.
- **Meta 24-Hour Customer Window Policy**: Enforces Meta's 24-hour service window, preventing unauthorized outbound charges and alerting agents when template messages are required.
- **Transactional Outbox Engine**: Outbound messages are committed inside database transactions before dispatch, guaranteeing zero lost messages during network drops.

### 3. High-Performance Merchant Dashboard (Next.js 16)
- **Obsidian Dark Aesthetic**: Built with `#0B0D11`, glowing emerald/cyan indicators, SVG trend sparklines, and responsive slide-over drawers.
- **Live Shared WhatsApp Inbox**: Real-time customer chat feed with message delivery receipts (`SENT`, `DELIVERED`, `READ`).
- **One-Click Human Takeover**: Operators can pause the AI instantly with `PATCH /api/v1/conversations/{id}/takeover` to handle delicate customer interactions manually.
- **Zero Mock Data Architecture**: 100% type-safe modular services mapping directly to FastAPI controllers.

---

## Repository Structure

```text
Chatrio/
├── backend/                        # FastAPI Asynchronous Backend
│   ├── app/
│   │   ├── api/                    # API v1 Router Aggregator
│   │   ├── core/                   # Config, Security, Database Engine, Exceptions
│   │   ├── modules/
│   │   │   ├── auth/               # Merchant Auth & Multi-Tenancy Router & Service
│   │   │   ├── products/           # Catalog, Categories & Stock Management
│   │   │   ├── customers/          # Customer Directory & Profile Store
│   │   │   ├── conversations/      # Chat History, Messages & Human Takeover
│   │   │   ├── orders/             # Order State Machine & Line Items
│   │   │   ├── outbox/             # Transactional Outbox Engine & Worker
│   │   │   └── webhooks/           # WhatsApp Webhook Verification & Processing
│   │   └── main.py                 # FastAPI Application Lifespan & Middleware
│   ├── migrations/                 # Alembic Database Version Control
│   ├── tests/                      # 207 Automated Pytest Unit & Integration Tests
│   ├── docker-compose.yml          # Local PostgreSQL 16 (pgvector) + Redis 7
│   └── pyproject.toml              # UV / Python Package Manifest
│
├── frontend/                       # Next.js 16 (App Router) Merchant UI
│   ├── src/
│   │   ├── app/                    # Next.js App Router Pages
│   │   │   ├── (auth)/             # Login & Merchant Registration Pages
│   │   │   ├── inbox/              # Shared Live Inbox & AI Takeover
│   │   │   ├── products/           # Product Catalog & Category Manager
│   │   │   ├── orders/             # Fulfillment Board & Detail Inspector
│   │   │   ├── customers/          # Customer Directory
│   │   │   ├── analytics/          # AI Ops Telemetry & Signal Monitoring
│   │   │   └── settings/           # Meta Credentials & Store Configuration
│   │   ├── components/             # Obsidian Dark UI Component Kit (Cards, Badges, Modals)
│   │   ├── services/               # Modular API Services (1:1 with Backend Routers)
│   │   └── types/                  # Strict TypeScript Interfaces Mirroring Pydantic DTOs
│   ├── tailwind.config.ts          # Custom Design Tokens & Glow Palette
│   └── package.json
└── specs/                          # Discrete Architecture & Product Specifications
```

---

## Getting Started

### Prerequisites
- **Python 3.12+** or **Python 3.14** with [`uv`](https://github.com/astral-sh/uv)
- **Node.js 18+** or **Node.js 20+**
- **Docker Desktop** (for PostgreSQL + Redis)

---

### Step 1: Start Infrastructure (Postgres with pgvector + Redis)

Chatrio runs on Docker Compose to provide PostgreSQL 16 with `pgvector` pre-installed alongside Redis 7:

```powershell
# In a new terminal
cd backend
docker compose up -d
```

> **Note on Ports**: The PostgreSQL container exposes host port `5433` (mapped internally to `5432`) to prevent conflicts with any local Windows PostgreSQL installations. Redis runs on `6379`.

---

### Step 2: Configure Environment Variables

#### Backend Configuration (`backend/.env`):
```env
APP_NAME="Chatrio API"
ENVIRONMENT="development"
DEBUG=true
API_V1_PREFIX="/api/v1"
ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# Database Connection (Docker container on port 5433)
DATABASE_URL="postgresql+asyncpg://postgres:Ahmed123@localhost:5433/chatrio_db"

# Redis Connection
REDIS_URL="redis://localhost:6379/0"

# Security
JWT_SECRET="dev-super-secret-jwt-key-change-this-in-production-min-32-chars-long"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

#### Frontend Configuration (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

### Step 3: Run Database Migrations

Apply Alembic migrations to construct all relational tables and vector indexes:

```powershell
cd backend
uv run alembic upgrade head
```

---

### Step 4: Run the Backend API Server

Start the FastAPI application with live reloading enabled:

```powershell
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

Once booted, explore:
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Step 5: Run the Frontend Dashboard

In a separate terminal, install dependencies and launch the Next.js dev server:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser:
- **Register Store**: Create your merchant organization and admin account.
- **Inbox**: Monitor live WhatsApp conversations and test human takeover.
- **Catalog**: Add store items with prices and stock quantities.
- **Fulfillment**: Track and advance order statuses (`Confirmed` → `Shipped` → `Delivered`).

---

## Verification & Testing Suite

Chatrio enforces rigorous test automation across domain isolation, security, and state machines.

```powershell
# Run backend test suite (207 tests)
cd backend
uv run pytest -v

# Run linting and formatting
uv run ruff check .
uv run ruff format .

# Build and verify frontend production build
cd ../frontend
npm run build
```

### Test Suite Summary
- **Total Tests**: `207 passed in ~58 seconds`
- **Domain Coverage**: Multi-tenant database isolation, Meta webhook HMAC authentication, 2-second Redis debounce buffering, Transactional Outbox workers, LangGraph conversational tools, and DeepEval evaluation harnesses.

---

## Technology Stack

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **API Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-speed asynchronous REST endpoints with Pydantic v2 validation |
| **Relational & Vector DB** | [PostgreSQL 16](https://postgresql.org) + [pgvector](https://github.com/pgvector/pgvector) | Multi-tenant relational storage and cosine semantic vector search |
| **Database ORM** | [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/) (`asyncpg`) | Fully asynchronous non-blocking connection pooling |
| **Schema Migrations** | [Alembic](https://alembic.sqlalchemy.org/) | Declarative schema version control |
| **Cache & Queue** | [Redis 7](https://redis.io) | Message burst debouncing and BullMQ job management |
| **AI Orchestration** | [LangGraph](https://langchain.com) | State machine conversational agent with typed deterministic tools |
| **Frontend Framework** | [Next.js 16](https://nextjs.org) (App Router) | React Server & Client Components with Turbopack |
| **Styling & Icons** | [Tailwind CSS](https://tailwindcss.com) + [Lucide React](https://lucide.dev) | Obsidian dark-mode design system with glowing accents |

---

## License

Copyright &copy; 2026 Chatrio. All rights reserved.
Proprietary software for enterprise conversational commerce.

