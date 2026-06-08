---
name: deepeval-llm-cicd
description: |
  Pytest-native LLM quality evaluation framework for CI/CD regression gating using DeepEval.
  Use when setting up automated LLM quality gates in CI, measuring answer relevancy /
  faithfulness / hallucination, or running LLM evals as unit tests in a pull-request pipeline.
  Triggers on: "deepeval", "LLM evaluation CI", "LLM quality gate", "pytest LLM eval",
  "answer relevancy metric", "faithfulness metric", "hallucination detection CI",
  "regression test LLM", "assert_test deepeval".
---

# DeepEval — LLM Quality CI/CD Regression Testing

DeepEval (by Confident AI) turns LLM evaluations into pytest-style unit tests.
Each quality metric produces a pass/fail that can block a PR like any other test failure.

Distinct from:
- `llm-red-teaming` — adversarial security/prompt-injection testing
- `llm-production-observability` — runtime monitoring & drift detection
- `chatbot-tester` — end-to-end functional pipeline testing

## Install

```bash
pip install deepeval
deepeval login   # optional: connects to Confident AI dashboard for trend tracking
```

## Core Concepts

| Term | Meaning |
|---|---|
| `LLMTestCase` | One input → actual_output (+ optional expected_output, context) |
| `Metric` | Scorer that evaluates the test case (0–1, pass/fail threshold) |
| `EvaluationDataset` | Collection of test cases (loaded from CSV, JSON, or Confident AI) |
| `assert_test()` | pytest-compatible assertion — fails the test if any metric fails |

## Key Metrics

```python
from deepeval.metrics import (
    AnswerRelevancyMetric,   # Is output on-topic for the input?
    FaithfulnessMetric,      # Is output grounded in the provided context?
    HallucinationMetric,     # Does output contain facts not in context?
    ContextualRecallMetric,  # Did retrieval surface the right chunks?
    GEval,                   # Custom rubric-based metric (any criterion)
)
```

All metrics use an LLM-as-a-Judge internally (configurable model).

## Minimal Example

```python
# tests/test_llm_quality.py
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

@pytest.mark.parametrize("test_case", [
    LLMTestCase(
        input="What is the refund policy?",
        actual_output=my_llm("What is the refund policy?"),
        retrieval_context=["Refunds are processed within 5–7 business days."],
    ),
])
def test_rag_quality(test_case):
    assert_test(test_case, [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.8),
    ])
```

```bash
deepeval test run tests/test_llm_quality.py        # run serially
deepeval test run tests/test_llm_quality.py -n 4   # 4 parallel eval workers
```

## Loading Goldens (Dataset)

```python
from deepeval.dataset import EvaluationDataset

# From JSON file
dataset = EvaluationDataset()
dataset.add_test_cases_from_json_file(
    file_path="goldens.json",
    input_key_name="input",
    actual_output_key_name="actual_output",
    expected_output_key_name="expected_output",
    context_key_name="context",
)

# From Confident AI dashboard (enables trend tracking across runs)
dataset = EvaluationDataset()
dataset.pull(alias="production-goldens")
```

## GitHub Actions Integration

```yaml
# .github/workflows/llm-quality.yml
name: LLM Quality Gate

on: [pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install deepeval pytest

      - name: Run LLM evals
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}   # judge model
          CONFIDENT_API_KEY: ${{ secrets.CONFIDENT_API_KEY }}  # optional dashboard
        run: deepeval test run tests/test_llm_quality.py -n 4

      - name: Upload junit results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: llm-eval-results
          path: "**/.deepeval-cache/**"
```

## Custom Rubric Metric (GEval)

When no built-in metric fits, define a natural-language rubric:

```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams

tone_metric = GEval(
    name="Professional Tone",
    criteria="The response is professional, concise, and does not use slang.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    threshold=0.7,
)
```

## RAG Pipeline Evaluation

```python
from deepeval.metrics import (
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
)

rag_case = LLMTestCase(
    input="What are the return window deadlines?",
    actual_output=rag_pipeline.query("What are the return window deadlines?"),
    expected_output="Items must be returned within 30 days of purchase.",
    retrieval_context=rag_pipeline.get_retrieved_chunks("What are the return window deadlines?"),
)

assert_test(rag_case, [
    ContextualPrecisionMetric(threshold=0.7),   # retrieved chunks relevant?
    ContextualRecallMetric(threshold=0.8),      # expected answer in chunks?
    FaithfulnessMetric(threshold=0.85),         # output grounded in chunks?
])
```

## Recommended Thresholds (Starting Points)

| Metric | Development | Release gate |
|---|---|---|
| AnswerRelevancy | ≥ 0.6 | ≥ 0.75 |
| Faithfulness (RAG) | ≥ 0.7 | ≥ 0.85 |
| Hallucination | ≤ 0.2 (lower = better) | ≤ 0.1 |
| ContextualRecall | ≥ 0.65 | ≥ 0.80 |

Tighten after baseline runs; never set thresholds before collecting data on your system.

## Agent Evaluation Metrics

When testing AI agents (tool use, multi-step reasoning), use agent-specific metrics:

```python
from deepeval.metrics import TaskCompletionMetric, ToolCorrectnessMetric

agent_case = LLMTestCase(
    input="Book a flight from Hanoi to HCMC for next Monday",
    actual_output=agent.run("Book a flight from Hanoi to HCMC for next Monday"),
    # tools_called is populated from your agent's trace
)

assert_test(agent_case, [
    TaskCompletionMetric(threshold=0.8),     # did the agent achieve the user's goal?
    ToolCorrectnessMetric(threshold=0.9),    # were the right tools called in the right order?
])
```

## Controlling the Judge Model (Cost vs Accuracy)

DeepEval defaults to GPT-4o as judge. Swap models to balance cost and accuracy:

```python
from deepeval.models import GPTModel

# Per-PR (fast & cheap): smaller judge model
fast_metric = FaithfulnessMetric(
    threshold=0.8,
    model=GPTModel(model="gpt-4o-mini"),
)

# Release gate (accurate): best available judge
release_metric = FaithfulnessMetric(
    threshold=0.85,
    model=GPTModel(model="gpt-4o"),
)
```

Strategy: use a lightweight judge for per-PR speed checks; use the strongest judge for release-gate evals where accuracy matters most.

## Sources

- https://deepeval.com/docs/evaluation-unit-testing-in-ci-cd
- https://deepeval.com/guides/guides-regression-testing-in-cicd
- https://deepeval.com/docs/metrics-introduction
- https://github.com/confident-ai/deepeval
