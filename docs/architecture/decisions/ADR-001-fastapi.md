# ADR-001: Adoption of Python FastAPI as Primary Backend Framework

## Status
Accepted

## Context
Chatrio requires an asynchronous, high-throughput backend to handle incoming WhatsApp webhooks (< 50ms acknowledgment SLA), manage real-time dashboards, and orchestrate complex LLM reasoning and agent tool execution.

Initially, a split stack (Node.js/Express for backend API + Python FastAPI for AI) was considered.

## Decision
We adopt **Python 3.12+ with FastAPI** as the single unified backend technology for both the core API and the AI agent orchestration.

## Rationale
1. **Elimination of Inter-Service Serialization Overhead**: Running the core backend and AI orchestration (LangGraph) in the same language eliminates network hops (`Node -> HTTP -> Python -> HTTP -> Node`), reducing turn latency by 150ms–300ms.
2. **First-Class AI/ML Ecosystem**: Native integration with LangGraph, LangChain, Pydantic v2, and vector libraries without language bridging.
3. **High Asynchronous Concurrency**: Built on Starlette and Uvicorn with native `asyncio` event loop, supporting thousands of concurrent I/O connections per instance.
4. **Strict Schema Validation**: Native Pydantic v2 integration guarantees typed data validation at runtime with minimal CPU overhead.

## Consequences
- **Positive**: Single codebase, shared data models and schemas between AI tools and backend services, simplified deployment.
- **Negative**: Synchronous or CPU-blocking code in route handlers can degrade event loop performance. This is mitigated by strictly enforcing async database drivers (`asyncpg`) and offloading heavy tasks to background workers.
