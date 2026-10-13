# Chatrio — System Architecture Document

## 1. System Topology

```text
                        CUSTOMER
                            │
                            ▼
                    WHATSAPP CLOUD API
                            │
                     Webhook Event
                            │
                            ▼
                ┌────────────────────────┐
                │ FastAPI Webhook Router │
                │  - Signature Verify    │
                │  - Payload Validation  │
                └───────────┬────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │   Store-First DB Save  │
                │  - Persist Message     │
                │  - Status: RECEIVED    │
                └───────────┬────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │ BullMQ Debounce Queue  │
                │  - 2.0s Timer / Buffer │
                └───────────┬────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │  AI Processing Worker  │
                │  - Aggregate Messages  │
                │  - LangGraph Pipeline  │
                │  - RAG Retrieval       │
                │  - Controlled Tools    │
                └───────────┬────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │ Business State Machine │
                │  - Inventory Lock      │
                │  - Orders Table Write  │
                │  - Outbox Message Save │
                └───────────┬────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │  Outbox Queue Worker   │
                │  - Policy Verification │
                │  - Meta Send API       │
                └───────────┬────────────┘
                            │
                            ▼
                        CUSTOMER
```

## 2. Core Architectural Layers

### 2.1 Webhook & Ingestion Layer
- Receives inbound Meta webhook payloads.
- Verifies `X-Hub-Signature-256` HMAC-SHA256 signature against the app secret.
- Idempotently stores incoming messages into PostgreSQL (`messages` table with status `RECEIVED`).
- Schedules a delayed BullMQ job (2000ms delay) keyed by conversation to aggregate burst messages.
- Returns `HTTP 200 OK` in < 50ms to satisfy Meta SLA.

### 2.2 Async Debounce & Processing Layer
- When the 2.0-second debounce job fires, worker collects all pending `RECEIVED` messages for that conversation.
- Assembles them into a single chronological message batch and marks them `PROCESSING`.
- Hands batch to the LangGraph AI workflow.

### 2.3 AI Agent & Tool Execution Layer
- Implements a LangGraph StateGraph.
- Evaluates customer intent (`ORDER`, `PRODUCT_QUERY`, `ORDER_STATUS`, `SUPPORT`, `HUMAN_REQUEST`).
- Tool calls interact strictly through internal service boundaries with tenant context validation (`organization_id`).
- Tools never execute raw SQL or bypass business logic.

### 2.4 Transactional Outbox & WhatsApp Policy Engine
- Responses and order notifications write to an `outbox_messages` table within the same ACID transaction as the business state changes.
- The Outbox Worker inspects the 24-hour customer service window:
  - If within 24h: Sends standard text / interactive message via Meta Cloud API.
  - If outside 24h: Requires pre-approved WhatsApp message template.

### 2.5 Real-Time Owner Dashboard Layer
- Next.js 15 App Router providing the merchant control center.
- Communicates with FastAPI over authenticated REST endpoints and WebSocket/SSE streams for real-time inbox updates.
