"""
LangGraph State Machine for Conversational Commerce Agent.

Assembles the cyclical execution graph:
1. `input_guardrail`: Scans for prompt injection / jailbreaks; encapsulates input in XML tags.
2. `agent_reasoning`: Injects armored system prompt and invokes model with bound tools.
3. `tool_execution`: Executes server-side tools with multi-tenant closure bindings.
4. `output_guardrail`: Validates and sanitizes model output before delivery to WhatsApp.
"""

from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.modules.ai.guardrails import SecurityGuardrails
from app.modules.ai.prompts import build_system_prompt
from app.modules.ai.state import AgentState

MAX_TOOL_LOOPS = 5


def build_agent_graph(
    model: BaseChatModel,
    tools: list[BaseTool],
) -> CompiledStateGraph:
    """
    Constructs and compiles the LangGraph State Machine for the AI shopping assistant.

    Args:
        model: Standard BaseChatModel instance (Groq, Grok, Gemini, OpenAI).
        tools: List of pre-bound tenant tools.

    Returns:
        CompiledStateGraph executable with `ainvoke({"messages": [...]})`.
    """
    tool_map = {t.name: t for t in tools}
    model_with_tools = model.bind_tools(tools) if tools else model

    # --------------------------------------------------------------------------
    # Node 1: Input Guardrail & Sanitization
    # --------------------------------------------------------------------------
    def input_guardrail_node(state: AgentState) -> dict[str, Any]:
        """
        Inspects the latest incoming customer message for prompt injection and jailbreaks.
        """
        messages = state.get("messages", [])
        if not messages:
            return {"is_injection_detected": False, "loop_count": 0}

        latest_msg = messages[-1]
        raw_text = str(latest_msg.content)

        # 1. Prompt Injection & Jailbreak Scanner
        is_attack, reason = SecurityGuardrails.detect_prompt_injection(raw_text)
        if is_attack:
            merchant = state.get("merchant_name", "our store")
            refusal_response = (
                f"I am the customer assistant for {merchant}. I am here to help you "
                "browse products, check stock, and place orders. How can I assist you today?"
            )
            return {
                "messages": [AIMessage(content=refusal_response)],
                "is_injection_detected": True,
                "injection_reason": reason,
                "loop_count": 0,
            }

        # 2. Input Boundary Encapsulation
        wrapped_text = SecurityGuardrails.wrap_user_input(raw_text)
        wrapped_msg = HumanMessage(
            content=wrapped_text,
            id=getattr(latest_msg, "id", None),
        )
        return {
            "messages": [wrapped_msg],
            "is_injection_detected": False,
            "loop_count": 0,
        }

    # --------------------------------------------------------------------------
    # Node 2: Agent Reasoning (LLM + Tools)
    # --------------------------------------------------------------------------
    async def agent_reasoning_node(state: AgentState) -> dict[str, Any]:
        """
        Constructs context, injects armored system prompt, and queries the LLM.
        """
        current_loops = state.get("loop_count", 0) + 1
        messages = list(state.get("messages", []))

        # Runaway loop circuit breaker
        if current_loops > MAX_TOOL_LOOPS:
            fallback = AIMessage(
                content="I've checked the details. Please let me know how you'd like to proceed!"
            )
            return {"messages": [fallback], "loop_count": current_loops}

        # Inject system prompt if not present at start
        merchant_name = state.get("merchant_name", "Our Store")
        currency = state.get("currency", "USD")
        system_content = build_system_prompt(merchant_name=merchant_name, currency=currency)

        call_messages: list[BaseMessage] = []
        if not messages or not isinstance(messages[0], SystemMessage):
            call_messages.append(SystemMessage(content=system_content))
        call_messages.extend(messages)

        # Invoke model
        response = await model_with_tools.ainvoke(call_messages)
        return {
            "messages": [response],
            "loop_count": current_loops,
        }

    # --------------------------------------------------------------------------
    # Node 3: Tool Execution Gate
    # --------------------------------------------------------------------------
    async def tool_execution_node(state: AgentState) -> dict[str, Any]:
        """
        Executes authorized backend tools and returns ToolMessage results.
        """
        messages = state.get("messages", [])
        if not messages:
            return {}

        last_msg = messages[-1]
        tool_calls = getattr(last_msg, "tool_calls", [])
        tool_results: list[ToolMessage] = []
        is_handoff = state.get("is_human_handoff", False)

        for tc in tool_calls:
            tname = tc["name"]
            targs = tc.get("args", {})
            t_instance = tool_map.get(tname)

            if t_instance is not None:
                try:
                    res = await t_instance.ainvoke(targs)
                    res_str = str(res)
                except Exception as err:
                    res_str = f'{{"error": "Tool execution error: {err}"}}'
            else:
                res_str = f'{{"error": "Unknown tool: {tname}"}}'

            if tname == "request_human_agent":
                is_handoff = True

            tool_results.append(
                ToolMessage(
                    content=res_str,
                    tool_call_id=tc["id"],
                    name=tname,
                )
            )

        return {
            "messages": tool_results,
            "is_human_handoff": is_handoff,
        }

    # --------------------------------------------------------------------------
    # Node 4: Output Guardrail & Delivery
    # --------------------------------------------------------------------------
    def output_guardrail_node(state: AgentState) -> dict[str, Any]:
        """
        Validates outbound model text and intercepts leaks or delimiter tags.
        """
        messages = state.get("messages", [])
        final_text = ""
        for m in reversed(messages):
            if isinstance(m, AIMessage):
                final_text = str(m.content)
                break

        clean_reply = SecurityGuardrails.sanitize_output(final_text)
        return {"final_response": clean_reply}

    # --------------------------------------------------------------------------
    # Conditional Routing Logic
    # --------------------------------------------------------------------------
    def route_after_input(state: AgentState) -> Literal["output_guardrail", "agent_reasoning"]:
        """If prompt injection is caught, skip model completely."""
        if state.get("is_injection_detected", False):
            return "output_guardrail"
        return "agent_reasoning"

    def route_after_reasoning(
        state: AgentState,
    ) -> Literal["tool_execution", "output_guardrail"]:
        """If tool calls requested and under loop limit, execute tools."""
        if state.get("loop_count", 0) > MAX_TOOL_LOOPS:
            return "output_guardrail"

        messages = state.get("messages", [])
        if not messages:
            return "output_guardrail"

        last_msg = messages[-1]
        tool_calls = getattr(last_msg, "tool_calls", [])
        if tool_calls:
            return "tool_execution"

        return "output_guardrail"

    # --------------------------------------------------------------------------
    # Graph Assembly
    # --------------------------------------------------------------------------
    workflow = StateGraph(AgentState)

    workflow.add_node("input_guardrail", input_guardrail_node)
    workflow.add_node("agent_reasoning", agent_reasoning_node)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("output_guardrail", output_guardrail_node)

    # Edges
    workflow.add_edge(START, "input_guardrail")
    workflow.add_conditional_edges(
        "input_guardrail",
        route_after_input,
        {"output_guardrail": "output_guardrail", "agent_reasoning": "agent_reasoning"},
    )
    workflow.add_conditional_edges(
        "agent_reasoning",
        route_after_reasoning,
        {"tool_execution": "tool_execution", "output_guardrail": "output_guardrail"},
    )
    workflow.add_edge("tool_execution", "agent_reasoning")
    workflow.add_edge("output_guardrail", END)

    return workflow.compile()

