# ADR-002: PostgreSQL 16 + pgvector as Primary Relational & Vector Store

## Status
Accepted

## Context
Chatrio requires transactional integrity for orders, inventory balances, and customer conversations, alongside vector similarity search for merchant-specific RAG knowledge bases.

## Decision
We adopt **PostgreSQL 16+ with the `pgvector` extension** as the unified persistence engine, accessed via **SQLAlchemy 2.0 Async** (`asyncpg`) and managed via **Alembic**.

## Rationale
1. **ACID Guarantees & Pessimistic Locking**: Preventing inventory overselling requires row-level locking (`SELECT FOR UPDATE`), which relational databases handle deterministically.
2. **Unified Relational & Vector Storage**: `pgvector` allows storing unstructured knowledge embeddings in the same database as business data. This avoids synchronization drift between a separate vector database (e.g. Pinecone/Qdrant) and the primary database.
3. **Ironclad Multi-Tenancy**: Every relational table and vector chunk table contains `organization_id`. Queries strictly filter on `WHERE organization_id = :org_id`, with PostgreSQL Row-Level Security (RLS) available as a defense-in-depth layer.
4. **Mature Migration Tooling**: Alembic provides version-controlled schema evolution in Git.

## Consequences
- **Positive**: Single backup strategy, single database to monitor and scale, zero consistency lag between embeddings and merchant metadata.
- **Negative**: High-cardinality multi-tenant vector searches require HNSW indexes with iterative scans or composite indexing to avoid full-table scans.
