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

```python
from deepeval.tracing import observe, RetrieverAttributes, LlmAttributes, ToolAttributes
import deepeval

@observe(type="retriever", attributes=RetrieverAttributes(
    embedding_model="text-embedding-3-small",
    top_k=5
))
def retrieve_docs(query: str) -> list[str]:
    return vector_store.search(query, k=5)

@observe(type="tool", attributes=ToolAttributes(name="search_web"))
def search_web(query: str) -> str:
    return web_api.search(query)

@observe(type="llm", attributes=LlmAttributes(
    model="claude-sonnet-4-6",
    cost_per_input_token=0.003 / 1000
))
def call_llm(prompt: str) -> str:
    return anthropic_client.messages.create(
        model="claude-sonnet-4-6",
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

```python
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, TaskCompletionMetric

with deepeval.collect_traces() as traces:
    final_answer = run_agent("What is our refund policy?")

test_case = LLMTestCase(
    input="What is our refund policy?",
    actual_output=final_answer,
    retrieval_context=["Refund window is 30 days from purchase date..."]
)

evaluate(
    test_cases=[test_case],
    metrics=[
        TaskCompletionMetric(threshold=0.7),
        AnswerRelevancyMetric(threshold=0.8),
        FaithfulnessMetric(threshold=0.8),
    ]
)
```

## Span-Level Evaluation (Per-Component)

```python
from deepeval.metrics import (
    ToolCorrectnessMetric,
    ArgumentCorrectnessMetric,
    ContextualRelevancyMetric,
)

with deepeval.collect_traces() as traces:
    run_agent("What is our refund policy?")

for trace in traces:
    for span in trace.spans:
        if span.type == "tool":
            span.add_metric(ToolCorrectnessMetric(threshold=0.8))
            span.add_metric(ArgumentCorrectnessMetric(threshold=0.8))
        elif span.type == "retriever":
            span.add_metric(ContextualRelevancyMetric(threshold=0.7))

evaluate(traces=traces)
```

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
import deepeval
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import TaskCompletionMetric, ToolCorrectnessMetric

@pytest.mark.parametrize("query,expected_tool", [
    ("Search for flights to Paris", "search_flights"),
    ("Book hotel in London", "book_hotel"),
])
def test_agent_tool_selection(query, expected_tool):
    with deepeval.collect_traces() as traces:
        run_agent(query)

    tool_spans = [s for t in traces for s in t.spans if s.type == "tool"]
    assert any(s.name == expected_tool for s in tool_spans), \
        f"Expected tool '{expected_tool}' not called for: {query}"

    assert_test(
        test_case=LLMTestCase(input=query, actual_output=traces[0].output),
        metrics=[TaskCompletionMetric(threshold=0.7)]
    )
```

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
