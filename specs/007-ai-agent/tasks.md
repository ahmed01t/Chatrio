# Tasks: 007-ai-agent

Each task is atomic, independent, and verifiable.

- [x] **Task 1: AI Dependencies & Configuration Settings**
  - Files: `backend/pyproject.toml`, `backend/app/core/config.py`, `backend/.env.example`
  - Action: Add `langgraph`, `langchain-core`, `langchain-openai`, and `deepeval` dependencies. Add `OPENAI_API_KEY`, `AI_MODEL_NAME`, `AI_TEMPERATURE`, and `AI_MAX_TOKENS` configuration fields in `Settings`.
  - Verification: Unit tests in `test_config.py` verify new configuration fields and defaults.

- [x] **Task 2: Prompt Injection Defense & Input/Output Guardrails**
  - Files: `backend/app/modules/ai/guardrails.py`, `backend/app/modules/ai/prompts.py`, `backend/tests/unit/test_ai_guardrails.py`
  - Action: Implement `detect_prompt_injection`, `wrap_user_input`, `sanitize_output`, and the armored system prompt template.
  - Verification: Unit tests verifying detection of instruction resets, delimiter escapes, DAN roleplay exploits, and system prompt protection.

- [x] **Task 3: Deterministic & Multi-Tenant Scoped Tools**
  - Files: `backend/app/modules/ai/tools.py`, `backend/tests/unit/test_ai_tools.py`
  - Action: Implement server-side gated tools (`search_catalog`, `get_product_details`, `draft_order`, `request_human_agent`). Enforce strict `organization_id` tenancy and verified database pricing.
  - Verification: Unit tests verifying catalog search scoping, draft order price resolution from DB, stock validation, and human takeover triggers.

- [x] **Task 4: LangGraph Agent State Machine**
  - Files: `backend/app/modules/ai/state.py`, `backend/app/modules/ai/graph.py`, `backend/tests/unit/test_ai_graph.py`
  - Action: Build LangGraph workflow (`input_guardrail` -> `agent_reasoning` -> `tool_execution` -> `output_guardrail`). Handle tool loop limits and memory persistence.
  - Verification: Unit tests verifying state progression, tool dispatching, human handoff branching, and refusal paths.

- [x] **Task 5: End-to-End Messaging Pipeline Hook**
  - Files: `backend/app/modules/messaging/service.py`, `backend/tests/integration/test_ai_messaging_flow.py`
  - Action: Connect inbound debounced messages to LangGraph agent execution and automatically dispatch replies via `WhatsAppClient`.
  - Verification: Integration tests simulating customer message arrival triggering AI reasoning and delivering outbound response.

- [ ] **Task 6: DeepEval Automated Evaluation Suite**
  - Files: `backend/tests/evals/test_agent_eval.py`
  - Action: Implement automated DeepEval tests for Hallucination, Answer Relevancy, Prompt Injection Resistance, and Commerce Policy Compliance.
  - Verification: DeepEval test run executing assertions and generating evaluation metrics report.

