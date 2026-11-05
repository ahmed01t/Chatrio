# Implementation Plan: 004-conversations

## 1. Architecture & Entity Relationship

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ CUSTOMERS : "owns"
    ORGANIZATIONS ||--o{ CONVERSATIONS : "owns"
    ORGANIZATIONS ||--o{ MESSAGES : "owns"
    CUSTOMERS ||--o{ CONVERSATIONS : "participates_in"
    CONVERSATIONS ||--o{ MESSAGES : "contains"
    USERS ||--o{ CONVERSATIONS : "assigned_to"

    CUSTOMERS {
        uuid id PK
        uuid organization_id FK
        string phone_number "E.164 unique per org"
        string name "WhatsApp Profile Name"
        string email "Optional"
        jsonb metadata
        boolean is_blocked
        timestamp created_at
        timestamp updated_at
    }

    CONVERSATIONS {
        uuid id PK
        uuid organization_id FK
        uuid customer_id FK
        uuid assigned_agent_id FK "Optional User ID"
        enum channel "WHATSAPP"
        enum status "ACTIVE, CLOSED, ARCHIVED"
        boolean is_ai_active "True: AI handles; False: Human agent"
        timestamp last_message_at
        timestamp created_at
        timestamp updated_at
    }

    MESSAGES {
        uuid id PK
        uuid organization_id FK
        uuid conversation_id FK
        enum sender_type "CUSTOMER, AI_AGENT, HUMAN_AGENT, SYSTEM"
        enum direction "INBOUND, OUTBOUND"
        enum content_type "TEXT, IMAGE, DOCUMENT, LOCATION, INTERACTIVE, TEMPLATE"
        text text_body
        string media_url
        enum status "RECEIVED, PROCESSING, SENT, DELIVERED, READ, FAILED"
        string whatsapp_message_id "Meta external ID"
        jsonb raw_payload
        timestamp created_at
    }
```

---

## 2. Human Takeover State Machine

```mermaid
stateDiagram-v2
    [*] --> AI_Handling : Customer sends message
    AI_Handling --> AI_Handling : AI answers customer
    AI_Handling --> Human_Takeover : Merchant toggles takeover (is_ai_active=False)
    Human_Takeover --> Human_Takeover : Human agent sends replies
    Human_Takeover --> AI_Handling : Merchant releases back to AI (is_ai_active=True)
    AI_Handling --> Closed : Conversation resolved
    Human_Takeover --> Closed : Conversation resolved
```

---

## 3. Implementation Phases

1. **Phase 1: Domain Models & Database Central Registry**:
   - Define `Customer` in `app/modules/customers/models.py`.
   - Define `Conversation` and `Message` in `app/modules/conversations/models.py`.
   - Re-export all models in `app/db/models.py`.
2. **Phase 2: Database Migration**:
   - Generate Alembic revision `003_conversations_and_customers.py`.
   - Add unit tests verifying schema creation, foreign key constraints, and downgrade cleanup.
3. **Phase 3: Validation Schemas**:
   - Define Pydantic v2 schemas for customers, conversations, messages, and human takeover requests.
4. **Phase 4: Business Services**:
   - `CustomerService`: Phone number normalization, customer upsert.
   - `ConversationService`: Get-or-create active conversation, list conversations, takeover toggle.
   - `MessageService`: Message creation, deduplication by `whatsapp_message_id`, pagination.
5. **Phase 5: REST API Endpoints**:
   - Customers router under `/api/v1/customers`.
   - Conversations router under `/api/v1/conversations`.
   - Mount under master `api_v1_router`.
6. **Phase 6: Multi-Tenant Isolation & Integration Verification**:
   - Verify that Merchant A cannot access, read, or send messages into Merchant B's conversations.
   - Verify phone number reuse across different merchants without conflict.

