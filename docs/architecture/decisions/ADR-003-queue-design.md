# ADR-003: Redis 7 & BullMQ for Ingestion Debouncing and Asynchronous Jobs

## Status
Accepted

## Context
WhatsApp customers frequently send multiple short, fragmented messages within a 1–2 second window (e.g. "Hi", "I want 2 burgers", "Make them spicy"). If every message triggered an immediate LLM invocation, race conditions, duplicate responses, out-of-order executions, and excessive token expenses would occur.

Additionally, outbound Meta API requests and audio processing must run asynchronously outside the HTTP request lifecycle.

## Decision
We adopt **Redis 7 with BullMQ** (using the Python `bullmq` driver) with a **Store-First Write-Ahead & Delayed Debounce pattern**.

## Rationale
1. **Store-First Durability**: Webhooks immediately insert incoming messages into PostgreSQL (`status = 'RECEIVED'`) and return `200 OK` to Meta in < 50ms. If Redis crashes, zero messages are lost.
2. **Debounce Coalescing**: For each conversation, a delayed job (`delay = 2000ms`, keyed by conversation ID) is scheduled in BullMQ. When the timer fires, the worker queries all pending `RECEIVED` messages in chronological order, combines them, and feeds the unified turn to LangGraph.
3. **Native Deduplication**: BullMQ supports explicit `jobId` deduplication. If Meta delivers duplicate webhook payloads, the duplicate job is automatically discarded.
4. **Retry & Dead-Letter Queue (DLQ)**: Failed outbound WhatsApp deliveries or LLM provider errors are retried with exponential backoff and captured in DLQs.

## Consequences
- **Positive**: Eliminates burst race conditions, provides zero-data-loss durability, guarantees fast webhook response times.
- **Negative**: Adds a Redis infrastructure dependency and requires background worker processes.
