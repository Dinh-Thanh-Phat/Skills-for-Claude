---
name: llm-agent-trace-eval
description: Evaluate AI agents at the component level using DeepEval's trace/span architecture — score each tool call, retrieval step, LLM completion, and planning decision independently rather than only grading the final answer. Use when testing LLM agents with tool use, RAG pipelines, or multi-step reasoning where the final answer alone doesn't reveal what broke. Triggers on: "evaluate agent tool calls", "agent trace evaluation", "DeepEval agent", "span evaluation", "tool correctness metric", "component-level LLM eval", "agent step scoring", "trace-based evaluation".
---

# LLM Agent Trace Evaluation — DeepEval Component-Level Evals

Evaluating only the final output of an agent misses where failures originate. DeepEval's trace/span architecture scores each internal component — tool calls, retrievals, LLM completions — as independent test cases tied to a single trace.

## Core Concepts

```
Trace  = end-to-end LLMTestCase  → what the user asked, what the agent finally answered
Span   = component-level LLMTestCase → what happened inside one step (tool call, retriever, LLM call)
```

A single agent run produces one trace with N spans. Every span is independently scoreable.

## Setup

```bash
pip install deepeval
deepeval login   # or set CONFIDENT_AI_API_KEY env var
```

## Instrument Your Agent with @observe

> **API note (verified against deepeval 4.2.7 wheel, 2026-10-02):** `deepeval.tracing` exports
> `observe`, `update_current_span`, `update_current_trace`, `update_{llm,tool,retriever,agent}_span`,
> `evaluate_trace`, `evaluate_span`, `evaluate_thread`. There is **no** `RetrieverAttributes` /
> `LlmAttributes` / `ToolAttributes`, **no** `deepeval.collect_traces()`, and **no** `span.add_metric()` —
> older blog snippets using those will `ImportError`/`AttributeError`. Metrics attach to a span via
> `@observe(metrics=[...])`, and the span's test case is set with `update_current_span(...)`.

```python
from deepeval.tracing import observe, update_current_span
from deepeval.test_case import LLMTestCase
from deepeval.metrics import ContextualRelevancyMetric, ArgumentCorrectnessMetric

@observe(type="retriever", metrics=[ContextualRelevancyMetric(threshold=0.7)])
def retrieve_docs(query: str) -> list[str]:
    docs = vector_store.search(query, k=5)
    update_current_span(input=query, retrieval_context=docs)   # span-level test case
    return docs

@observe(type="tool", metrics=[ArgumentCorrectnessMetric(threshold=0.8)])
def search_web(query: str) -> str:
    result = web_api.search(query)
    update_current_span(input=query, output=result)
    return result

@observe(type="llm")
def call_llm(prompt: str) -> str:
    return anthropic_client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    ).content[0].text

@observe(type="agent")  # root — becomes the trace
def run_agent(user_query: str) -> str:
    docs = retrieve_docs(user_query)
    web_result = search_web(user_query)
    return call_llm(f"Context: {docs}\nWeb: {web_result}\nQ: {user_query}")
```

## Trace-Level Evaluation (End-to-End)

Iterate a dataset with `evals_iterator()`; metrics passed there score the whole trace, while the
`metrics=` on each `@observe` span (above) score the components in the same run.

```python
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.metrics import TaskCompletionMetric, StepEfficiencyMetric

dataset = EvaluationDataset(goldens=[Golden(input="What is our refund policy?")])

for golden in dataset.evals_iterator(
    metrics=[TaskCompletionMetric(threshold=0.7), StepEfficiencyMetric(threshold=0.7)]
):
    run_agent(golden.input)   # traced call — trace + span metrics evaluated automatically
```

## Span-Level Evaluation (Per-Component)

Span metrics are declared on the decorator (see instrumentation above). For tool *selection*,
give the tool span the called vs. expected tools so `ToolCorrectnessMetric` (requires `input`,
`tools_called`, `expected_tools`) can score it:

```python
from deepeval.test_case import ToolCall
from deepeval.metrics import ToolCorrectnessMetric

@observe(type="agent", metrics=[ToolCorrectnessMetric(threshold=0.8)])
def run_agent(user_query: str) -> str:
    ...
    update_current_span(
        input=user_query,
        output=answer,
        tools_called=[ToolCall(name="search_web")],
        expected_tools=[ToolCall(name="search_web")],   # from your golden
    )
    return answer
```

Offline (already-captured) traces/spans can be scored with `deepeval.tracing.evaluate_trace` /
`evaluate_span` instead of re-running the agent.

## Key Agent Metrics

| Metric | Scope | What it checks |
|--------|-------|----------------|
| `TaskCompletionMetric` | Trace | Did the agent complete the user's goal? |
| `ToolCorrectnessMetric` | Span (tool) | Was the right tool chosen for this step? |
| `ArgumentCorrectnessMetric` | Span (tool) | Were the tool arguments correct given the input? |
| `ContextualRelevancyMetric` | Span (retriever) | Did the retriever return relevant docs? |
| `AnswerRelevancyMetric` | Trace / Span (llm) | Is the output relevant to the input? |
| `FaithfulnessMetric` | Trace | Is the answer grounded in retrieved context? |
| `StepEfficiencyMetric` | Trace | Did the agent solve with minimal steps? |

## CI Integration (pytest)

```python
# test_agent_evals.py
import pytest
from deepeval import assert_test
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.metrics import TaskCompletionMetric

dataset = EvaluationDataset(goldens=[
    Golden(input="Search for flights to Paris"),
    Golden(input="Book hotel in London"),
])

# Run with: deepeval test run test_agent_evals.py
@pytest.mark.parametrize("golden", dataset.goldens)
def test_agent(golden: Golden):
    run_agent(golden.input)   # @observe'd — span metrics (tool/retriever) evaluated too
    assert_test(golden=golden, metrics=[TaskCompletionMetric(threshold=0.7)])
```

> UNVERIFIED: the exact `assert_test(golden=..., metrics=...)` signature for traced apps — confirm
> against https://deepeval.com/docs/evaluation-unit-testing-in-ci-cd before relying on it in CI.

## When to Use Trace vs Span Eval

- **Trace eval first** — if the final answer fails, drill into spans to locate the root cause.
- **Span eval for retrieval bugs** — `ContextualRelevancyMetric` on retriever spans reveals RAG ranking issues before they corrupt the final answer.
- **Span eval for tool bugs** — `ArgumentCorrectnessMetric` catches malformed tool inputs (wrong date format, missing required field) before they cause downstream API errors.
- **Don't instrument everything** — focus on the highest-risk spans: tool calls and retrieval are the most common agent failure points.

## Relationship to Other Skills

- Use `response-evaluator` for simple single-turn Q&A bots (no tool use, no retrieval chain).
- Use `deepeval-llm-cicd` for answer-level quality gates (relevancy / faithfulness / hallucination) on a single LLM output; use **this** skill for component/span-level scoring when the agent has tool calls or retrieval. Same library (DeepEval), different granularity.
- Use `llm-production-observability` for runtime monitoring and drift detection after deploy.
- Use this skill when the agent has tool calls, RAG, or multi-step reasoning and you need to know *which step* failed.

## Sources

- [LLM Agent Evaluation Metrics 2026 — Confident AI](https://www.confident-ai.com/blog/llm-agent-evaluation-complete-guide)
- [Component-Level LLM Evaluation — DeepEval](https://deepeval.com/docs/evaluation-component-level-llm-evals)
- [LLM Tracing — DeepEval](https://deepeval.com/docs/evaluation-llm-tracing)
- [AI Agent Evaluation Metrics — DeepEval](https://deepeval.com/guides/guides-ai-agent-evaluation-metrics)
- [Best LLM Evaluation Tools for AI Agents 2026 — Confident AI](https://www.confident-ai.com/knowledge-base/compare/best-llm-evaluation-tools-for-ai-agents)
- deepeval 4.2.7 wheel (PyPI, 2026-09-29) — `deepeval/tracing/__init__.py`, `tracing.py` (`observe(metrics=, type=)`), `context.py` (`update_current_span`), `dataset/dataset.py` (`evals_iterator`): https://pypi.org/project/deepeval/
