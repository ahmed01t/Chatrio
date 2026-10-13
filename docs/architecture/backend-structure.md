# Chatrio — Backend Structure & Module Organization

This document details the backend codebase layout, directory roles, and responsibility boundaries.

---

## 1. Directory Blueprint

```text
backend/
├── pyproject.toml              # Dependencies, build tooling, ruff and pytest configurations
├── .env.example                # Canonical environment variable specification
├── alembic.ini                 # Database migrations configuration
├── Dockerfile                  # Production container definition
├── docker-compose.yml          # Local infrastructure (PostgreSQL 16 + pgvector, Redis 7)
│
├── app/
│   ├── main.py                 # FastAPI application factory, middleware registration, router mounts
│   │
│   ├── core/                   # Global cross-cutting infrastructure
│   │   ├── config.py           # Pydantic BaseSettings loading from .env
│   │   ├── security.py         # Password hashing & JWT token encoding/decoding
│   │   ├── logging.py          # Structured JSON logging
│   │   └── exceptions.py       # Custom exception classes and global error handlers
│   │
│   ├── db/                     # Database engine & base configuration
│   │   ├── session.py          # SQLAlchemy 2.0 async engine and sessionmaker
│   │   ├── base.py             # DeclarativeBase class
│   │   └── models.py           # Central registry importing all module models for Alembic
│   │
│   ├── api/                    # API gateway & dependencies
│   │   ├── router.py           # Master router aggregating /api/v1 endpoints
│   │   └── dependencies.py     # FastAPI dependencies (get_db, get_current_user, get_tenant)
│   │
│   ├── modules/                # Feature Modules (Domain-Driven Design)
│   │   ├── auth/               # User authentication, password management, tokens
│   │   ├── organizations/      # Multi-tenant workspace management and RBAC roles
│   │   ├── customers/          # Customer directory, phone identities, consent flags
│   │   ├── conversations/      # Live chat sessions, messages, human takeover
│   │   ├── products/           # Catalog items, categories, inventory stock
│   │   ├── orders/             # Carts, orders, state machine transitions
│   │   ├── support/            # Escalations, support tickets, agent assignment
│   │   ├── knowledge/          # Knowledge base documents, chunking, pgvector search
│   │   ├── whatsapp/           # Meta webhook ingestion, signature validation, policy rules
│   │   ├── ai/                 # LangGraph state machine, intent detection, restricted tools
│   │   ├── audit/              # Immutable audit logging for security-sensitive actions
│   │   └── analytics/          # Aggregated conversation, order, and AI performance metrics
│   │
│   ├── infrastructure/         # External service drivers and clients
│   │   ├── redis.py            # Redis client connection factory
│   │   ├── queues.py           # BullMQ queue instances and dispatch helpers
│   │   ├── storage.py          # S3-compatible object storage client
│   │   └── external/           # Third-party API integration clients
│   │       ├── whatsapp_client.py # Meta Cloud API caller
│   │       └── whisper_client.py  # Audio transcription client
│   │
│   └── workers/                # BullMQ asynchronous background workers
│       ├── debounce_worker.py  # Batches rapid WhatsApp messages before AI dispatch
│       ├── ai_worker.py        # LangGraph pipeline runner
│       ├── outbox_worker.py    # Dispatches queued outbound WhatsApp messages
│       └── media_worker.py     # Transcribes audio notes and processes image attachments
│
├── migrations/                 # Alembic migration revisions
│   ├── env.py
│   └── versions/
│
└── tests/                      # Automated test suite
    ├── conftest.py
    ├── unit/
    └── integration/
```

---

## 2. Responsibilities by Layer

1. **`app/core/`**: Shared utilities that have no awareness of specific business domains.
2. **`app/db/`**: Asynchronous database lifecycle and base model definition.
3. **`app/modules/<domain>/`**: Encapsulates all domain entities, validation schemas, business services, and HTTP routes for that feature.
4. **`app/infrastructure/`**: Thin wrappers around external resources (Redis, queues, S3, Meta API).
5. **`app/workers/`**: Background processes decoupled from web workers, scaling independently.
