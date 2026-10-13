# Chatrio — Product Vision & Strategy

## 1. Product Overview
**Chatrio** is a multi-tenant B2B SaaS platform that enables businesses to connect their official WhatsApp Business account and deploy an intelligent, autonomous AI agent that handles conversational e-commerce, order creation, order tracking, FAQ answering, and customer support handoff.

## 2. Core Value Proposition
- **Turn WhatsApp into an Automated Storefront**: Customers discover products, ask questions, assemble carts, and place orders directly in WhatsApp without needing an app download.
- **Enterprise Multi-Tenancy**: Complete data and operational isolation for each merchant organization.
- **Deterministic Business Rules**: Prices, stock levels, delivery rules, and order states are strictly enforced by the backend database. The AI cannot hallucinate prices or invent invalid orders.
- **Seamless Human Co-Pilot**: Integrated shared inbox in the Owner Dashboard allowing human agents to intervene, pause AI automation, or return control to the agent at any moment.

## 3. Target Audience & Personas
1. **Retail & E-commerce Merchants**: Direct-to-consumer brands and restaurants looking to automate high-volume order intake and customer inquiries.
2. **Support & Operations Teams**: Business owners and support staff who manage orders, monitor agent escalations, and review analytics.
3. **End Consumers**: WhatsApp users expecting immediate, human-like answers and effortless mobile ordering.

## 4. Key Differentiators
- **Store-First Debounce Architecture**: Collects rapid-fire messages into coherent conversational turns before invoking AI.
- **Meta Policy Compliance by Design**: Hard enforcement of Meta's 24-hour service window and message templates at the backend layer.
- **Transactional Outbox Engine**: Outbound messages are tied transactionally to database changes, preventing lost notifications.
- **Isolated Multi-Tenant RAG**: Vector searches are strictly bounded to the merchant's uploaded documentation.
