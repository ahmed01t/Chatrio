# Verification Guide: 007-ai-agent

## 1. Automated Unit & Integration Tests
Run the pytest suite:
```bash
cd backend
uv run pytest
```
Expected output:
- All existing 148 tests pass.
- New unit tests for guardrails, prompt injection detection, and input wrapping pass.
- New unit tests for deterministic multi-tenant tools pass.
- New unit tests for LangGraph state transitions and tool routing pass.
- New integration tests for messaging pipeline connection pass.

---

## 2. Code Quality & Conventions
```bash
cd backend
uv run ruff check .
uv run ruff format .
```
Expected output: Zero errors, zero warnings.

---

## 3. DeepEval Red-Teaming & Benchmark Evaluation
Run the DeepEval agent evaluation suite:
```bash
cd backend
uv run pytest tests/evals/test_agent_eval.py
```
Expected evaluation metrics:
1. **Prompt Injection Defense**: 100% rejection rate of adversarial jailbreaks (DAN, delimiter escape, prompt extraction).
2. **Hallucination Metric**: $< 0.1$ across all catalog Q&A benchmarks.
3. **Answer Relevancy Metric**: $\ge 0.85$ on standard customer ordering inquiries.
4. **Price Authority**: 0% occurrences of the LLM inventing custom prices or bypassing server pricing logic.

