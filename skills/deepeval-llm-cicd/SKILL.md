---
name: deepeval-llm-cicd
description: |
  Pytest-native LLM quality evaluation framework for CI/CD regression gating using DeepEval.
  Use when setting up automated LLM quality gates in CI, measuring answer relevancy /
  faithfulness / hallucination, or running LLM evals as unit tests in a pull-request pipeline.
  Triggers on: "deepeval", "LLM evaluation CI", "LLM quality gate", "pytest LLM eval",
  "answer relevancy metric", "faithfulness metric", "hallucination detection CI",
  "regression test LLM", "assert_test deepeval", "agent loop detection", "tool permission metric".
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

## Loop Detection & Tool Permission Metrics (v4.1.3, July 2026)

Two deterministic (no-LLM-judge) agent metrics shipped in DeepEval 4.1.3 — cheaper and more
reliable than judge-based metrics for the specific failure modes they target.

**`AgentLoopDetectionMetric`** catches infinite/cyclical agent loops directly from the trace,
without needing a judge model to notice the agent is stuck. Combines three independent
sub-signals into a weighted 0.0 (severe looping) – 1.0 (clean execution) score:
- tool-call repetition — identical `(name, args)` pairs; score degrades at `repetition_threshold`
  (default 3) and bottoms out at double that
- reasoning stagnation — bigram Jaccard + `SequenceMatcher` similarity across consecutive LLM
  outputs (`similarity_threshold` default 0.85); short outputs (<20 meaningful words) are skipped
  to avoid boilerplate false positives
- call-graph cycles — DFS over the trace's nested `children` tree for a repeated
  `type:name:input_hash` appearing twice on one root-to-leaf path

```python
from deepeval.metrics import AgentLoopDetectionMetric

loop_metric = AgentLoopDetectionMetric(
    threshold=0.5,
    repetition_threshold=3,
    similarity_threshold=0.85,
)
assert_test(agent_case, [loop_metric])
# loop_metric.score_breakdown exposes the three sub-signal scores individually
```

Needs trace data on `actual_output` (via `@observe`), same as `TaskCompletionMetric`.

**`ToolPermissionMetric`** is a deterministic (no judge model, no LLM cost) least-privilege
check: did the agent call only tools it was authorized to call? Distinct from
`ToolCorrectnessMetric` above, which compares against an *expected* tool sequence and cares
about task success — this only checks the permission boundary, independent of outcome.

```python
from deepeval.metrics import ToolPermissionMetric

permission_metric = ToolPermissionMetric(
    allowed_tools=["search_flights", "get_weather"],   # least-privilege allowlist
    # or: denied_tools=["delete_account", "issue_refund"],  # denylist; denial always wins
)
assert_test(agent_case, [permission_metric])  # score = fraction of calls that stayed in-policy
```

Requires at least one of `allowed_tools`/`denied_tools` (raises `ValueError` if neither is set);
only needs `tools_called` on the test case — cheap enough to run on every agent test, not just
release gates.

## Multi-Turn (Conversational) Evaluation

Use `ConversationalTestCase` when correctness depends on conversation history — chatbots,
support bots, onboarding wizards, or any system where later turns reference earlier context.
Single-turn `LLMTestCase` metrics cannot detect context loss or persona drift across turns.

```python
from deepeval.test_case import ConversationalTestCase, Turn
from deepeval.metrics.conversation import (
    KnowledgeRetentionMetric,
    RoleAdherenceMetric,
    ConversationCompletenessMetric,
)

def test_support_conversation():
    test_case = ConversationalTestCase(
        turns=[
            Turn(role="user",      content="My order #1234 is late."),
            Turn(role="assistant", content="I'm sorry. Let me check order #1234 for you."),
            Turn(role="user",      content="It was supposed to arrive yesterday."),
            Turn(role="assistant", content="You're right — order #1234 was due yesterday. I've escalated it."),
            Turn(role="user",      content="What was my order number again?"),
            Turn(role="assistant", content="Your order number is #1234."),  # tests retention
        ],
        scenario="Customer support agent helping with a delayed delivery",
    )
    assert_test(test_case, [
        KnowledgeRetentionMetric(threshold=0.8),       # retains facts across turns
        RoleAdherenceMetric(threshold=0.7),             # stays in support-agent persona
        ConversationCompletenessMetric(threshold=0.7),  # user's goal was resolved
    ])
```

Multi-turn simulation (auto-generate the user turns using an LLM):
```python
from deepeval.synthesizer import ConversationalSynthesizer

synth = ConversationalSynthesizer()
conversations = synth.simulate(
    scenario="User complains about missing shipment",
    agent_fn=my_chatbot.respond,
    num_turns=6,
    num_conversations=10,
)
# Returns list[ConversationalTestCase] ready for assert_test()
```

## Arena Evaluation (`ArenaGEval`) — Pairwise Prompt/Model Comparison

Standard metrics score one output in isolation. `ArenaGEval` instead picks a **winner** between
two or more candidate outputs for the same input — use it when regression-testing a prompt
rewrite, a model swap, or a fine-tune against the current production version, not just checking
whether the new version clears a fixed threshold.

```python
from deepeval.test_case import ArenaTestCase, LLMTestCase
from deepeval.metrics import ArenaGEval
from deepeval.test_case import LLMTestCaseParams

arena_case = ArenaTestCase(
    contestants={
        "prompt_v1_prod": LLMTestCase(
            input="How do I reset my password?",
            actual_output=prompt_v1("How do I reset my password?"),
        ),
        "prompt_v2_candidate": LLMTestCase(
            input="How do I reset my password?",
            actual_output=prompt_v2("How do I reset my password?"),
        ),
    },
)

arena_metric = ArenaGEval(
    name="Support Response Quality",
    criteria="The response is accurate, concise, and gives an actionable next step.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
)

arena_metric.measure(arena_case)
print(arena_metric.winner)  # e.g. "prompt_v2_candidate"
```

`ArenaGEval` first generates evaluation steps via chain-of-thought from `criteria` (same
mechanism as `GEval`), then applies them to each contestant with contestant identity masked
and position randomized — this blinding prevents both self-preference and position bias from
skewing the winner. Run across a batch of `ArenaTestCase`s and tally wins per contestant to
decide whether a prompt/model candidate is a net improvement before rolling it out. Distinct
from `llm-judge-bias` (single-output scoring calibration) and the threshold-based metrics above
(pass/fail against a fixed bar, not head-to-head comparison).

## Controlling the Judge Model (Cost vs Accuracy)

DeepEval defaults to whichever OpenAI model its current version ships as default (this has changed across DeepEval releases — check `deepeval --version` / the DeepEval docs rather than assuming a specific model name). Swap models to balance cost and accuracy:

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
- https://deepeval.com/docs/evaluation-multiturn-test-cases
- https://deepeval.com/guides/guides-multi-turn-evaluation-metrics
- https://www.confident-ai.com/blog/multi-turn-llm-evaluation-in-2026
- https://deepeval.com/docs/metrics-arena-g-eval
- https://deepeval.com/docs/getting-started-llm-arena
- https://github.com/confident-ai/deepeval/issues/2143
- https://github.com/confident-ai/deepeval
- https://github.com/confident-ai/deepeval/releases (v4.1.3, July 12 2026)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/metrics/agent_loop_detection/agent_loop_detection.py
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/metrics/tool_permission/tool_permission.py
