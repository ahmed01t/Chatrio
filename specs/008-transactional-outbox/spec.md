# Spec 008: Transactional Outbox Engine & Meta 24-Hour Policy Window

## 1. Overview & Problem Statement
In WhatsApp conversational commerce, direct synchronous network calls to external APIs (`POST graph.facebook.com/.../messages`) during request handling or database transactions cause severe failure modes:
1. **Dual Write Failure / Lost Messages**: If an order is saved in PostgreSQL but Meta's API times out, returns HTTP 429 (rate limit), or drops the socket, the customer never receives confirmation and the merchant loses visibility.
2. **Meta 24-Hour Policy Window Violations**: Meta strictly mandates that businesses can only send freeform text/interactive messages to customers within 24 hours of the customer's last inbound message. Freeform messages sent outside 24h cause Meta account strikes and delivery blocks unless converted to approved HSM templates.
3. **High Latency & Blocking Threads**: Direct API calls block worker processes and HTTP handlers waiting on external network I/O.

To achieve enterprise reliability, Spec 008 introduces the **Transactional Outbox Pattern** and **WhatsApp Policy Enforcement Engine**. Outbound messages are atomically recorded in PostgreSQL within the same ACID transaction as the business state changes, and asynchronously delivered by a dedicated queue worker with exponential backoff and 24h policy guards.

---

## 2. Architecture & Data Flow

```text
 ┌────────────────────────────────────────────────────────┐
 │            Application / Agent Business Turn           │
 │  - Save Order / Save Message / Human Agent Reply       │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼  Single ACID Transaction
 ┌────────────────────────────────────────────────────────┐
 │           PostgreSQL: outbox_messages Table            │
 │  - status: PENDING                                     │
 │  - organization_id (tenant scoped)                     │
 │  - conversation_id / customer phone                    │
 │  - payload (text, interactive, template)               │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼  Asynchronous Queue Job / Poller
 ┌────────────────────────────────────────────────────────┐
 │                  Outbox Policy Engine                  │
 │  - Check Conversation.last_customer_message_at         │
 │  - Within 24h? -> Allow TEXT / INTERACTIVE             │
 │  - Outside 24h? -> Allow TEMPLATE, Reject Freeform     │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼  Meta WhatsApp Cloud API
 ┌────────────────────────────────────────────────────────┐
 │                WhatsApp Delivery & Retry               │
 │  - 200 OK -> Mark Outbox status: SENT                  │
 │  - 429 / 5xx -> Increment retry_count, Backoff (2^n)   │
 │  - Exceeded Max Retries / Policy Rejection -> FAILED   │
 └────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema: `outbox_messages`

- `id`: UUID Primary Key.
- `organization_id`: UUID (Foreign Key `organizations.id`, indexed, non-nullable).
- `conversation_id`: UUID (Foreign Key `conversations.id`, nullable for system broadcasts).
- `recipient_phone`: String(32) (E.164 phone number, non-nullable).
- `message_type`: Enum (`TEXT`, `INTERACTIVE`, `TEMPLATE`).
- `payload`: JSONB (Text body, button descriptors, or template name/language/components).
- `status`: Enum (`PENDING`, `SENDING`, `SENT`, `FAILED`).
- `retry_count`: Integer (default 0).
- `max_retries`: Integer (default 5).
- `next_retry_at`: DateTime(timezone=True) (indexed with status for fast batch polling).
- `sent_at`: DateTime(timezone=True) (null until successful delivery).
- `last_error`: Text (stores error reason or HTTP status).
- `created_at`, `updated_at`: DateTime(timezone=True) (UTC timestamps).

---

## 4. Meta 24-Hour Customer Care Policy Engine

Meta Cloud API enforces:
- When a customer sends a message, a **24-hour customer care window** opens (`conversation.last_customer_message_at`).
- Inside window: Any message format (`TEXT`, `INTERACTIVE`, `IMAGE`, `TEMPLATE`) is permitted.
- Outside window: **Only pre-approved WhatsApp Templates (`TEMPLATE`)** can be sent. Freeform messages must be blocked before calling Meta to prevent policy strikes.

The Policy Engine implements:
```python
is_window_open = (
    conversation.last_customer_message_at is not None
    and (now - conversation.last_customer_message_at).total_seconds() <= 86400
)
```
If `is_window_open is False` and `message_type != TEMPLATE`:
- Block outbound transmission.
- Mark outbox message status as `FAILED` with `last_error = "POLICY_VIOLATION_24H_WINDOW_EXPIRED"`.
- Do not incur a Meta API call or risk tenant account suspension.

---

## 5. Delivery Worker & Exponential Backoff

- Worker processes pending outbox messages in batches (`SELECT ... FOR UPDATE SKIP LOCKED` or Redis BullMQ trigger).
- Backoff formula for temporary errors (network timeout, Meta HTTP 429 / 500 / 503):
  $$\text{Delay} = \min(300, 2^{\text{retry\_count}} \times 2)\text{ seconds}$$
- When `retry_count >= max_retries`, mark status `FAILED`.
- Upon successful Meta delivery (200 OK):
  - Mark outbox message `SENT` with `sent_at = now`.
  - Update `Message.status = SENT` and store `whatsapp_message_id`.

