"""
Agent State Definition for LangGraph State Machine.

Maintains unified conversational and tenant context across reasoning steps:
1. Message history with append reducer (`add_messages`).
2. Multi-tenant identifiers (organization_id, customer_id, conversation_id).
3. Merchant metadata (merchant_name, currency).
4. Guardrail flags (is_injection_detected, injection_reason).
5. Human takeover state (is_human_handoff).
6. Loop limit counter to prevent runaway cycles.
7. Final sanitized response string.
"""

import uuid
from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """
    Unified state dictionary passed between nodes in the LangGraph agent graph.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    conversation_id: uuid.UUID
    merchant_name: str
    currency: str
    is_injection_detected: bool
    injection_reason: str | None
    is_human_handoff: bool
    loop_count: int
    final_response: str
