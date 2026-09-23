---
name: deepeval-llm-cicd
description: |
  Pytest-native LLM quality evaluation framework for CI/CD regression gating using DeepEval.
  Use when setting up automated LLM quality gates in CI, measuring answer relevancy /
  faithfulness / hallucination, or running LLM evals as unit tests in a pull-request pipeline.
  Triggers on: "deepeval", "LLM evaluation CI", "LLM quality gate", "pytest LLM eval",
  "answer relevancy metric", "faithfulness metric", "hallucination detection CI",
  "regression test LLM", "assert_test deepeval", "agent loop detection", "tool permission metric",
  "flaky metric deepeval", "deepeval flaky test case", "deepeval typescript", "deepeval npm",
  "deepeval-ts", "deepeval vitest", "toPass matcher", "MCPUseMetric", "MCPTaskCompletionMetric",
  "MultiTurnMCPUseMetric", "deepeval mcp evaluation", "test agent mcp tool use",
  "ToolCallType", "tool type mismatch deepeval", "ToolCorrectnessMetric mcp vs function",
  "deepeval voice metrics", "VoiceNaturalnessMetric", "SpeechIntelligibilityMetric",
  "VoiceConsistencyMetric", "TurnTakingNaturalnessMetric", "AgentResponsivenessMetric",
  "AudioIntegrityMetric", "VoiceReliabilityMetric", "test voice agent CI deepeval",
  "deepeval score direction flip", "BiasMetric threshold", "ToxicityMetric threshold",
  "HallucinationMetric threshold", "MisuseMetric threshold", "warn_score_direction_flipped",
  "deepeval 4.2.0", "ToolUseMetric", "GoalAccuracyMetric", "TopicAdherenceMetric",
  "tool selection metric deepeval", "goal accuracy conversational", "topic adherence metric",
  "VoiceConfig ConversationSimulator", "VapiConnector", "PipecatConnector deepeval",
  "deepeval voice connector", "live voice agent simulation deepeval", "WebRTCConnector",
  "deepeval webrtc voice testing", "aiortc voice agent test", "deepeval Jev", "TypeSafe AI",
  "System One model", "deepeval set-typesafe", "TypeSafeModel", "Jev judge model",
  "deepeval Classifiers", "categorical LLM-as-judge".
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
| Hallucination (deepeval ≥ 4.2.0) | ≥ 0.8 (higher = better) | ≥ 0.9 |
| Hallucination (deepeval < 4.2.0) | ≤ 0.2 (lower = better) | ≤ 0.1 |
| ContextualRecall | ≥ 0.65 | ≥ 0.80 |

Tighten after baseline runs; never set thresholds before collecting data on your system. The
Hallucination row's direction depends on your installed version — see the score-direction flip
below before picking a threshold for Hallucination/Bias/Toxicity/Misuse.

## Safety Metric Score-Direction Flip: Bias/Toxicity/Hallucination/Misuse (v4.2.0, August 2026)

DeepEval 4.2.0 flipped the scoring direction of four metrics — `BiasMetric`, `ToxicityMetric`,
`HallucinationMetric`, `MisuseMetric` — to match every other metric in the library. This is a
**silent breaking change for any threshold you already have configured**, not an opt-in migration:

- **Before 4.2.0**: score was the *proportion of violations found* (0 = clean, 1 = fully biased/
  toxic/hallucinated/misused). `threshold` acted as a *maximum* — `is_successful()` passed when
  `score <= threshold`. `strict_mode` set the effective threshold to `0`.
- **From 4.2.0**: score is now *1 minus that proportion* (1 = clean, 0 = fully bad), consistent
  with `AnswerRelevancyMetric`/`FaithfulnessMetric`/every other metric. `threshold` is now a
  *minimum* — the base class's default `score >= threshold` applies (each metric's own
  `is_successful()` override was deleted). `strict_mode` now sets the effective threshold to `1`.

A `threshold=0.2` that used to mean "pass if at most 20% of statements are biased" now means
"pass only if the bias score is at least 0.2" — i.e. it passes almost everything, the opposite of
the old intent. DeepEval emits a one-time-per-metric-name `DeprecationWarning` (via
`warn_score_direction_flipped`, shown in pytest's warnings summary) the first time each of these
four metrics is instantiated, but it does **not** fail the run or rewrite your threshold — CI keeps
going green on the old, now-inverted, config unless you fix it by hand:

```python
# Before 4.2.0
BiasMetric(threshold=0.2)        # pass if <=20% biased

# From 4.2.0 — same intent, flipped number
BiasMetric(threshold=0.8)        # pass if >=80% unbiased
```

Action when upgrading across 4.2.0: grep your suite for `BiasMetric(`, `ToxicityMetric(`,
`HallucinationMetric(`, `MisuseMetric(` and invert every explicit `threshold=` (`new = 1 - old`);
re-baseline rather than guess, since the underlying judge behavior is unchanged, only the number
reported is inverted. **Not affected**: `PIILeakageMetric`, `RoleViolationMetric`,
`NonAdviceMetric`, and every other metric already scored "higher is better" and did not change.
Verified via a direct diff of the official PyPI sdists for `deepeval` 4.1.10 vs 4.2.0 (`bias.py`,
`toxicity.py`, `hallucination.py`, `misuse.py`, `metrics/utils.py` — the only metric files that
changed in that release; no other new files or metrics shipped in 4.2.0).

## Marking a Metric or Test Case Flaky (v4.1.4, July 2026)

Some checks are flaky for reasons outside your system's control (a judge model's own
inconsistency, an unstable third-party dependency in the test fixture) but you still want the
result tracked, not silently deleted. DeepEval 4.1.4 added a `flaky` boolean on both `Metric` and
`LLMTestCase`, but **only the test-case-level flag changes `assert_test()`'s pass/fail behavior**
— re-verified directly against source (`evaluate/utils.py`'s `_is_metric_successful()` and
`assert_test()`'s own raise/warn branch in `evaluate/evaluate.py`) after an earlier version of
this section overstated the metric-level flag's effect:

```python
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

# Metric-level flaky: recorded into MetricData (visible in reports / the Confident AI dashboard)
# for your own filtering, but it does NOT stop this metric's failure from failing the test case —
# _is_metric_successful() only checks metric_data.error / metric_data.success, never .flaky.
flaky_metric = FaithfulnessMetric(threshold=0.85, flaky=True)

# Test-case-level flaky is what actually gates CI: any failing metric on this test case makes
# assert_test() emit warnings.warn(...) (shows up in pytest's warnings summary) instead of
# raising AssertionError — so a flaky *test case* can't block CI, but a flaky *metric* alone can.
test_case = LLMTestCase(
    input="...", actual_output="...", retrieval_context=[...],
    flaky=True,
)
```

Set `flaky=True` on the **test case**, not just the metric, if the goal is to stop a known-unstable
eval from blocking CI — the metric-level flag alone won't do it. Prefer this over deleting or
skipping a known-unstable eval outright either way — the run still shows up in `deepeval test run`
output and the Confident AI dashboard (if connected), so you can watch its trend and un-flake it
later instead of losing visibility into it.

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

### Tool-Type-Aware Scoring in `ToolCorrectnessMetric` (v4.1.9, August 2026)

`ToolCall` gained a `type: ToolCallType` field back in v4.1.8 (`ToolCallType.FUNCTION` default,
`ToolCallType.MCP` for MCP-classified calls — see the `MCPUseMetric` v4.1.8 section below), but
until 4.1.9 that field was informational only for `ToolCorrectnessMetric`. As of 4.1.9,
`ToolCorrectnessMetric` requires `type` equality alongside `name` as a match precondition in
**all three** scoring modes — exact match (`should_exact_match=True`), the ordering-aware
weighted-LCS mode (`should_consider_ordering=True`), and the default order-independent mode. A
`tools_called` entry with the right `name` but the wrong `type` no longer counts as a match; it's
scored the same as if the wrong tool had been called outright, and `.reason` now names the
mismatch explicitly (`"{name} (expected {expected_type}, called {called_type})"`, appended as
`"Tool type mismatches: [...]"` for exact match or `"tool type mismatches [...]"` for the other
two modes).

Practical gotcha this creates: `type` only gets auto-classified on both `expected_tools` *and*
`tools_called` when tests run through `evaluate(mcp_servers=...)` (`process_mcp_servers()`
classifies both sides consistently). `assert_test()` still has no `mcp_servers` param, so if you
hand-set `expected_tools=[ToolCall(name="get_weather", type=ToolCallType.MCP)]` but assert via
`assert_test()` against an untyped `tools_called` (which defaults to `ToolCallType.FUNCTION`),
`ToolCorrectnessMetric` now fails that pair on type alone even though the name matched — a
regression trap for suites upgrading from pre-4.1.9 where `type` was ignored. Either classify both
sides the same way (both through `mcp_servers=` auto-classification, or both manually set to the
same `ToolCallType`), or route MCP-aware `ToolCorrectnessMetric` runs through `evaluate()` instead
of `assert_test()`. Verified against `deepeval/test_case/llm_test_case.py` (`ToolCallType`,
`ToolCall.type`) and `deepeval/metrics/tool_correctness/tool_correctness.py`
(`_get_type_mismatches`, `_calculate_exact_match_score`, `_calculate_non_exact_match_score`,
`_compute_weighted_lcs`), tag `python-v4.1.9`.

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

Three more conversational metrics (present since at least 4.1.10, undocumented here until now)
cover ground `KnowledgeRetentionMetric`/`RoleAdherenceMetric`/`ConversationCompletenessMetric`
don't:

- **`ToolUseMetric`** — requires `available_tools: List[ToolCall]` at construction. Groups the
  conversation into "unit interactions" (one user request through its resolution) and scores two
  things per interaction where a tool was used — was the *right* tool selected, and were its
  *arguments* correct — then combines both into one score with a two-part reason string. Distinct
  from the trace-level `ToolCorrectnessMetric`/`ArgumentCorrectnessMetric` in
  `llm-agent-trace-eval`: those score one isolated span; this scores tool use *as it plays out
  across a conversation*.
- **`GoalAccuracyMetric`** — no extra constructor args. Extracts `(user_goal, steps_taken)` per
  unit interaction and scores both whether the goal was achieved and whether the steps taken were
  a sound plan for it, combining into one score. Use for task-oriented bots (booking, support
  resolution) where "did the conversation actually get the user what they wanted" matters more
  than any single turn's wording.
- **`TopicAdherenceMetric`** — requires `relevant_topics: List[str]` at construction. Builds a
  TP/TN/FP/FN confusion matrix over the conversation's question/response pairs (did the bot answer
  in-scope questions and correctly refuse/deflect out-of-scope ones) and scores accuracy from that
  matrix. Use to catch scope creep — a support bot that starts giving medical or legal advice, or
  a narrow-domain bot that a user has walked off-topic.

```python
from deepeval.metrics import ToolUseMetric, GoalAccuracyMetric, TopicAdherenceMetric
from deepeval.test_case import ToolCall

assert_test(test_case, [
    ToolUseMetric(available_tools=[ToolCall(name="check_order_status"), ToolCall(name="escalate_to_human")], threshold=0.7),
    GoalAccuracyMetric(threshold=0.7),
    TopicAdherenceMetric(relevant_topics=["order status", "shipping", "returns"], threshold=0.8),
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

## MCP-Aware Agent Evaluation (v4.1.6/4.1.7, August 2026)

If your agent talks to Model Context Protocol servers, `LLMTestCase` and `ConversationalTestCase`
now carry dedicated MCP fields — `mcp_servers` (`MCPServer`: `server_name`, `transport`,
`available_tools`/`available_resources`/`available_prompts`), `mcp_tools_called`
(`MCPToolCall`: `name`, `args`, `result`), `mcp_resources_called` (`MCPResourceCall`: `uri`,
`result`), and `mcp_prompts_called` (`MCPPromptCall`: `name`, `result`) — plus three metrics
that judge MCP usage directly, instead of treating MCP calls as generic `tools_called` and
losing the resource/prompt-primitive distinction:

- **`MCPUseMetric`** (single-turn, `LLMTestCase`) — scores `min(primitive_selection_score,
  argument_correctness_score)`: did the agent pick the right MCP tool/resource/prompt for the
  input, and were the arguments passed to it correct? Distinct from `ToolCorrectnessMetric`,
  which only compares against an expected call sequence and doesn't know about MCP's
  tool/resource/prompt primitive split.
- **`MultiTurnMCPUseMetric`** (conversational) — the same selection/argument scoring, averaged
  per-task across a multi-turn conversation's "unit interactions" instead of one isolated call.
- **`MCPTaskCompletionMetric`** (conversational) — extracts individual tasks from the
  conversation, scores whether each was completed (accounting for the MCP tool calls/results
  used to complete it), and averages the per-task scores.

All three take the same common kwargs as other metrics (`threshold`, `model`, `include_reason`,
`strict_mode`, `flaky`, `async_mode`) and need the relevant `mcp_*` fields actually populated to
have anything to judge — instrument your agent's MCP client to record calls into these fields
rather than reusing `tools_called`.

```python
from deepeval.test_case import LLMTestCase, MCPServer, MCPToolCall
from deepeval.metrics import MCPUseMetric

mcp_case = LLMTestCase(
    input="What's the weather in Hanoi?",
    actual_output=agent.run("What's the weather in Hanoi?"),
    mcp_servers=[MCPServer(server_name="weather-mcp", transport="stdio")],
    mcp_tools_called=[MCPToolCall(name="get_weather", args={"city": "Hanoi"}, result="28C, clear")],
)

assert_test(mcp_case, [MCPUseMetric(threshold=0.7)])
```

Use this instead of (or alongside) `skills/mcp-server-testing` — that skill tests an MCP
*server* itself as the system under test (protocol/contract/security); these metrics evaluate an
*agent's* use of MCP servers as part of its response quality, the same CI-gate pattern as every
other metric in this skill.

**v4.1.8 (August 2026): auto-classification from `evaluate(mcp_servers=...)`.** The manual
`mcp_tools_called`/`MCPToolCall` instrumentation above still works, but `evaluate()` (not
`assert_test()`) now takes a top-level `mcp_servers` param that removes it for the common case:

```python
from deepeval import evaluate
from deepeval.test_case import LLMTestCase, ToolCall

test_case = LLMTestCase(
    input="What's the weather in Hanoi?",
    actual_output=agent.run("What's the weather in Hanoi?"),
    tools_called=[ToolCall(name="get_weather", input_parameters={"city": "Hanoi"})],
)

evaluate(
    test_cases=[test_case],
    metrics=[MCPUseMetric(threshold=0.7)],
    mcp_servers=[my_official_mcp_server],  # a real mcp.server.MCPServer instance works directly
)
```

Passing the **real MCP SDK server object** (not DeepEval's `MCPServer` dataclass) is now
supported directly — `evaluate()` calls the live server's `list_tools()`/`list_resources()`/
`list_prompts()` to build the tool inventory itself. It then walks every test case's plain
`tools_called`/`expected_tools` (ordinary `ToolCall`, not `mcp_tools_called`) and flips
`ToolCall.type` from its new default `ToolCallType.FUNCTION` to `ToolCallType.MCP` for any call
whose `name` matches one of the server's tools — so `MCPUseMetric` can score MCP usage from
tool-call instrumentation you likely already have, without a separate `mcp_tools_called`
recording path. This only fires through `evaluate()`'s `mcp_servers` kwarg or a `mcp_servers`
already set directly on the test case; `assert_test()` still has no `mcp_servers` parameter, so
route MCP-classified runs through `evaluate()`. Verified against `deepeval/test_case/mcp.py`
(`normalize_mcp_servers`, `_from_official_mcp_server`), `deepeval/test_case/utils.py`
(`classify_tool_call_types`, `process_mcp_servers`), and the `evaluate()`/`assert_test()`
signatures in `deepeval/evaluate/evaluate.py`.

## Voice Metrics (v4.1.10, August 2026)

DeepEval 4.1.10 adds seven audio-channel metrics for testing voice agents (IVR bots, phone-call
assistants, TTS/voice-connector pipelines) directly in a pytest CI gate — the same
`assert_test()`/threshold pattern as every other metric here, applied to `ConversationalTestCase`
turns that carry audio. Unlike the judge-based metrics above, all seven are **dependency-free
acoustic analysis** (PCM decoding, RMS/pitch/zero-crossing math) — no LLM call, no judge cost, and
deterministic given the same WAV bytes:

```python
from deepeval.metrics import (
    VoiceNaturalnessMetric,      # clipping, dropouts, pacing, pitch variation → does it sound robotic?
    SpeechIntelligibilityMetric, # SNR, volume, clipping, dropouts → can a listener understand it?
    VoiceConsistencyMetric,      # pitch/loudness/timbre stability across turns → same voice throughout?
    TurnTakingNaturalnessMetric, # gap/overlap timing between speaker turns → natural back-and-forth?
    AgentResponsivenessMetric,   # did every user turn that needed a reply get one, with audio?
    AudioIntegrityMetric,        # missing/undecodable audio, abrupt cutoffs, loops
    VoiceReliabilityMetric,      # composite: 0.5 * responsiveness + 0.5 * audio integrity
)
```

Audio lives on `Turn.audio` (a `deepeval.test_case.Audio`), built from a file/URL or in-memory
bytes — e.g. straight from a TTS or voice-connector call:

```python
from deepeval.test_case import ConversationalTestCase, Turn, Audio

test_case = ConversationalTestCase(
    turns=[
        Turn(role="user", content="What's my account balance?",
             audio=Audio(url="fixtures/user_turn1.wav", start_time=0.0)),
        Turn(role="assistant", content="Your balance is $1,240.",
             audio=Audio.from_bytes(tts_output_bytes, mimeType="audio/wav", start_time=2.1)),
    ],
)

assert_test(test_case, [
    VoiceNaturalnessMetric(threshold=0.7),
    AudioIntegrityMetric(threshold=0.9),
])
```

Gotchas verified directly against source (`deepeval/metrics/voice/`, tag `python-v4.1.10`):
- Audio must be **16-bit PCM WAV**; anything else raises inside `analyze_audio()` and that turn is
  skipped (or, for `AudioIntegrityMetric`/`VoiceReliabilityMetric`, counted as a critical failure)
  rather than silently scored — check `.score_breakdown["turns"]` for per-turn `"error"` entries
  before trusting a suspiciously high score on a run with encoding problems.
- `TurnTakingNaturalnessMetric` needs `start_time` set on **every** audio turn's `Audio` object
  (it's a field on `Audio`, not `Turn`) — the metric derives gaps/overlaps from real timestamps
  and returns `None` rather than guessing sequential timing if any is missing.
- `VoiceConsistencyMetric` needs at least 2 decodable assistant-audio turns; single-turn test
  cases return `None`, not a score.
- All seven return `None` (not 0.0) when there isn't enough eligible audio to evaluate —
  distinguish "nothing to measure" from "measured and failed" when reading results in CI.
- Metric-level `flaky` does *not* stop a bad score from failing the test case (see the corrected
  v4.1.4 section above) — for real (not synthesized) recordings where acoustic noise is expected
  to vary run-to-run, set `flaky=True` on the **test case** wrapping
  `VoiceConsistencyMetric`/`TurnTakingNaturalnessMetric` if you don't want that variance blocking CI.

Complements — not a replacement for — `skills/voice-ai-agent-testing`'s WER/latency/barge-in
methodology: these metrics score the *audio artifact itself* (clarity, naturalness, integrity)
from recorded turns, they don't measure transcription accuracy or wall-clock response latency.
Run both: `voice-ai-agent-testing`'s replay-corpus + synthetic-noise-injection harness to generate
the audio, these metrics as the pytest-native CI gate on top of it.

Sources: https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/metrics/voice/base_metric.py,
https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/metrics/voice/naturalness.py,
https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/metrics/voice/intelligibility.py,
https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/metrics/voice/consistency.py,
https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/metrics/voice/turn_taking.py,
https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/metrics/voice/reliability.py,
https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/metrics/voice/integrity.py,
https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/metrics/voice/responsiveness.py,
https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/metrics/voice/_analysis.py,
https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/metrics/__init__.py,
https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/voice/timeline.py,
https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.10/deepeval/test_case/llm_test_case.py (`Audio` class),
https://pypi.org/pypi/deepeval/json (confirmed v4.1.10 latest, Aug 21 2026)

### Automated Live Voice-Agent Simulation via Connectors (v4.2.1–4.2.2, Sep 2026)

The Voice Metrics above score a `ConversationalTestCase` you already built by hand (recorded/TTS
audio dropped onto `Turn.audio`). `ConversationSimulator` can now generate those test cases itself
by driving a **live** voice agent through a `VoiceConfig`, instead of you wiring up TTS/STT and
turn objects manually:

```python
from deepeval.simulator import ConversationSimulator
from deepeval.voice import VoiceConfig
from deepeval.voice.connectors import VapiConnector  # also: ElevenLabsConnector, LiveKitConnector, PipecatConnector

simulator = ConversationSimulator(
    voice_config=VoiceConfig(
        connector=VapiConnector(assistant_id="...", api_key="..."),
        # tts_model / stt_model default to OpenAI via env vars (DEEPEVAL_TTS_MODEL/DEEPEVAL_STT_MODEL)
    ),
    async_mode=True,  # required for voice mode
)

test_cases = simulator.simulate(conversational_goldens=goldens, max_user_simulations=10)
assert_test(test_cases[0], [VoiceNaturalnessMetric(threshold=0.7)])
```

The simulator speaks each simulated user turn (TTS), sends it to the agent over the connector,
transcribes the agent's spoken reply (STT), and assembles the resulting `ConversationalTestCase`
with real `Turn.audio` already attached — ready for the Voice Metrics above with no manual audio
plumbing. `PipecatConnector` and `VapiConnector` are new in 4.2.1/4.2.2; `ElevenLabsConnector` and
`LiveKitConnector` existed earlier and were restructured onto the same connector interface. A
`ConversationSimulator` takes exactly one of `model_callback` (text agents, the existing pattern)
or `voice_config` (voice agents) — passing both or neither raises `TypeError`.

Caveats verified directly against source, not docs (`deepeval.com` is blocked to this session's
fetcher entirely): each provider's own connector module ships a contributor-facing `README.md`
listing exactly which of that vendor's protocol features are/aren't wired up yet (e.g. Vapi's
notes it doesn't yet surface the agent-side ASR transcript of *your* synthesized audio, only the
agent's spoken reply) — read the connector's own README before assuming full parity with driving
that platform's SDK directly.

Sources: https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/voice/connectors/providers/__init__.py,
https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/voice/connectors/providers/vapi/connector.py,
https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/voice/connectors/providers/vapi/README.md,
https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/voice/config.py,
https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/simulator/conversation_simulator.py,
https://pypi.org/pypi/deepeval/4.2.0/json, https://pypi.org/pypi/deepeval/4.2.2/json (wheel diff confirming Pipecat/Vapi are new between these two releases)

### Protocol-Agnostic `WebRTCConnector` (v4.2.3, Sep 2026)

The connectors above are each wired to one vendor's SDK/API. `WebRTCConnector` instead speaks
plain WebRTC, so it works against **any** voice agent that exposes a raw WebRTC signaling
endpoint — a self-hosted agent, or a vendor with no dedicated connector yet — without waiting for
a provider-specific integration:

```python
from deepeval.voice import VoiceConfig
from deepeval.voice.connectors import WebRTCConnector  # requires: pip install aiortc av

connector = WebRTCConnector(
    signaling_url="https://agent.example.com/webrtc/offer",  # http(s):// POSTs the SDP offer, gets an SDP answer back
    # or ws(s):// — exchanges {"type": "offer"/"answer"/"candidate", ...} JSON messages instead
    data_channel="text",       # optional: agent transcripts arrive over this WebRTC data channel
    ice_servers=["stun:stun.l.google.com:19302"],
    turn_detection="balanced", # same turn-detection knob as the other connectors
)
simulator = ConversationSimulator(voice_config=VoiceConfig(connector=connector), async_mode=True)
```

Needs the optional `aiortc`/`av` dependencies (not installed with base `deepeval`). Two signaling
modes only: an `http(s)://` URL is POSTed the SDP offer and must answer with the SDP (raw or
`{"sdp": "..."}` JSON); a `ws(s)://` URL exchanges `offer`/`answer`/`candidate` JSON messages over
the socket for full ICE trickle support. Use this connector, not a vendor-specific one, for a
homegrown or self-hosted voice agent — anything speaking standard WebRTC rather than a supported
platform's proprietary transport.

Sources: https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/voice/connectors/transports/webrtc.py,
https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/voice/connectors/transports/__init__.py,
https://pypi.org/pypi/deepeval/json (raw PyPI JSON confirms 4.2.3 uploaded 2026-09-14, one day after 4.2.2 — cross-checked against a WebFetch summary of the same endpoint that hallucinated "December 2024" upload dates for these same version numbers, discarded per this log's standing practice; wheel diff of 4.2.2 vs 4.2.3 confirms `transports/webrtc.py` and the `WebRTCConnector` export are new in 4.2.3)

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

## TypeScript SDK

DeepEval ships a TypeScript package (`npm install deepeval`, published from the `typescript/`
directory of the same monorepo as the Python package). It runs metrics **locally** — you do not
need a Python step, and you do not need a Confident AI account.

> ⚠️ Do not scope this package from its `typescript/README.md`. That file is stale — it still
> says *"Status: Initial version shipping June 5th"* and *"LLM-as-a-judge metrics… remain in the
> Python package"*, which the shipped source contradicts. Check `typescript/src/` directly.

What's actually in the package:

- **~40 metrics**, mirroring the Python names — `AnswerRelevancyMetric`, `FaithfulnessMetric`,
  `GEval`, `ContextualPrecision/Recall/Relevancy`, `HallucinationMetric`, `BiasMetric`,
  `ToxicityMetric`, `ToolCorrectnessMetric`, `TaskCompletionMetric`, `PIILeakageMetric`,
  `SummarizationMetric`, the `Turn*` conversational set, and the agent metrics.
- **Local judge models** — `OpenAIModel`, `AzureOpenAIModel`, `AnthropicModel`, `GeminiModel`,
  `AmazonBedrockModel`, `DeepSeekModel`, `GrokModel`, `KimiModel`, `OllamaModel`, `LocalModel`,
  `AISDKModel`, plus `OpenRouterModel`/`PortkeyModel` gateways and
  `DeepEvalOpenAICompatibleModel` for any OpenAI-compatible endpoint.
- **`evaluate()` / `compare()`**, dataset push/pull, prompts, tracing, and integrations for
  Vitest, LangChain/LangGraph, Mastra, OpenAI Agents, and AI SDK.

The CI quality gate — the TypeScript analogue of pytest's `assert_test()` — is the **Vitest**
integration, which registers a `toPass` matcher:

```typescript
import "deepeval/integrations/vitest";      // registers expect().toPass()
import { LLMTestCase, AnswerRelevancyMetric } from "deepeval";
import { test, expect } from "vitest";

test("answer stays relevant", async () => {
  const testCase = new LLMTestCase({
    input: "What is our refund window?",
    actualOutput: await myApp.ask("What is our refund window?"),
  });
  // Fails the Vitest run when the metric falls under threshold — same gate semantics
  // as assert_test() under pytest.
  await expect(testCase).toPass([new AnswerRelevancyMetric({ threshold: 0.8 })]);
});
```

Dataset sync works the same as Python, with `CONFIDENT_API_KEY` authenticating in place of the
`deepeval login` flow:

```typescript
import { EvaluationDataset } from "deepeval";

const dataset = new EvaluationDataset();
await dataset.pull({ alias: "production-goldens", autoConvertGoldensToTestCases: true });
// ...run the app under test against dataset.testCases...
await dataset.push({ alias: "production-goldens", finalized: true });
```

**Choosing Python vs TypeScript:** default to Python — it's still the more complete
implementation and where new capabilities land first. Two concrete gaps to plan around: the
`flaky` flag documented above is **Python-only** (no `flaky` field on the TypeScript
`BaseMetric` or `LLMTestCase`), and there is no TypeScript equivalent of DeepTeam red-teaming.
Pick TypeScript when keeping evals in the same language and test runner as the app under test is
worth more than those features. The package is still pre-1.0 (`0.1.x`), so pin the version and
re-check the exported surface on upgrade rather than assuming API stability.

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

### Jev / System One Decision Model (v4.2.4, September 2026 — opt-in, experimental)

`python-v4.2.4` added support for routing metrics' *decision* step to **Jev**, TypeSafe AI's
"System One" model. Jev is not an LLM — it takes a typed question (yes/no verdict, a DAG node's
binary judgement, a G-Eval rubric level, a classifier label) and returns a calibrated probability
instead of generated text, so it can't hallucinate a verdict format or go off-rubric. The LLM you
already configured still does every *language* step (extracting claims/statements, writing G-Eval
evaluation steps, generating the human-readable reason) — only the final decision hands off to Jev.
This is a separate axis from the GPT-model swap above: it changes *which kind of model* renders the
verdict, not which LLM does the reasoning.

Where it plugs in (per the DeepEval source, `deepeval/models/system_one/`): QAG-based metrics'
claim verification (e.g. `FaithfulnessMetric`), `GEval`'s per-step verdict, `DAGMetric`'s binary
node decisions, and the new **Classifiers** feature (categorical LLM-as-judge against a closed
label set, instead of a 0–1 score).

Opt in globally — metrics auto-detect it once configured, there's no per-metric constructor param:

```bash
# Enable (reads/writes local DeepEval settings)
deepeval set-typesafe --model=jev

# Disable, fall back to pure-LLM verdicts
deepeval unset-typesafe
```

Or via environment variables (same settings the CLI writes): `TYPESAFE_API_KEY`,
`TYPESAFE_MODEL_NAME` (defaults to the latest Jev model), `TYPESAFE_COST_PER_INPUT_TOKEN` (override
if you're on a custom pricing tier — DeepEval validates it's `>= 0`).

Tradeoffs before enabling for a release gate: TypeSafe's own numbers put Jev at ~100ms per query
(batched for independent questions) and $0.042/M input tokens with no output-token charge — cheap
and fast relative to a frontier-model judge call. But it's marked experimental in the release notes
and existing behavior is unchanged unless you opt in, so pilot it on a non-blocking metric run
before swapping a release-gate threshold onto it, and don't expect a reasoning trace back from the
decision step itself (the LLM-authored `reason` field is unaffected, but a Jev verdict itself is a
bare probability, not an explanation).

## Sources

- https://deepeval.com/docs/evaluation-unit-testing-in-ci-cd
- https://deepeval.com/guides/guides-regression-testing-in-cicd
- https://deepeval.com/docs/metrics-introduction
- https://deepeval.com/docs/evaluation-multiturn-test-cases
- https://deepeval.com/guides/guides-multi-turn-evaluation-metrics
- https://www.confident-ai.com/blog/multi-turn-llm-evaluation-in-2026
- https://deepeval.com/docs/metrics-arena-g-eval
- https://raw.githubusercontent.com/confident-ai/deepeval/main/typescript/package.json (npm package name; version `0.9.10` at time of writing, up from `0.1.32`)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/typescript/src/index.ts (exported API surface — exports `metrics` and `evaluate`)
- https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.2.0/deepeval/metrics/tool_use/tool_use.py
- https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.2.0/deepeval/metrics/goal_accuracy/goal_accuracy.py
- https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.2.0/deepeval/metrics/topic_adherence/topic_adherence.py
- https://raw.githubusercontent.com/confident-ai/deepeval/main/typescript/src/metrics/index.ts and the ~40 metric dirs under `typescript/src/metrics/` — local judge metrics DO exist in TypeScript
- https://raw.githubusercontent.com/confident-ai/deepeval/main/typescript/src/metrics/answer-relevancy/answer-relevancy.ts (imports `DeepEvalBaseLLM`/`initializeModel`/`generateWithSchema` — proof of local judge execution)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/typescript/src/models/index.ts (13 judge providers + OpenRouter/Portkey gateways)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/typescript/src/integrations/vitest/index.mts and `matchers.mts` (`expect().toPass()` — the `assert_test()` analogue)
- https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.9/deepeval/test_case/llm_test_case.py (`ToolCallType` enum, `ToolCall.type` field, v4.1.9)
- https://github.com/confident-ai/deepeval/releases/tag/python-v4.2.4 (Jev/System One release notes, September 22 2026)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/models/system_one/typesafe_model.py (`TypeSafeModel` constructor, env vars)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/metrics/g_eval/g_eval.py (`initialize_system_one_model()`, `_experimental_system_one_spec`)
- https://github.com/confident-ai/deepeval/pull/3340 (`deepeval set-typesafe`/`unset-typesafe` CLI opt-in)
- https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.9/deepeval/metrics/tool_correctness/tool_correctness.py (`_get_type_mismatches`, type-aware exact/non-exact/ordering scoring, v4.1.9)
- https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.1.9/deepeval/test_case/utils.py (`classify_tool_call_types`, `process_mcp_servers` classifying both `tools_called` and `expected_tools`)
- https://github.com/confident-ai/deepeval/pull/3062 (PR introducing tool-call type distinction, merged into v4.1.9)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/typescript/src/dataset/dataset.ts (push/pull/queue method signatures)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/typescript/README.md — ⚠️ STALE, do not scope the package from it: claims local metrics are Python-only, which `typescript/src/metrics/` contradicts
- https://pypi.org/pypi/deepeval/json (release history — confirms 4.2.0 published 2026-08-24, one release after 4.1.10)
- https://raw.githubusercontent.com/confident-ai/deepeval/python-v4.2.0/deepeval/metrics/bias/bias.py, .../toxicity/toxicity.py, .../hallucination/hallucination.py, .../misuse/misuse.py, .../metrics/utils.py (`warn_score_direction_flipped`), .../metrics/base_metric.py (default `is_successful()` now `score >= threshold`) — v4.2.0 score-direction flip, verified by diffing the official PyPI sdists for 4.1.10 vs 4.2.0
- https://deepeval.com/docs/getting-started-llm-arena
- https://github.com/confident-ai/deepeval/issues/2143
- https://github.com/confident-ai/deepeval
- https://github.com/confident-ai/deepeval/releases (v4.1.3, July 12 2026)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/metrics/agent_loop_detection/agent_loop_detection.py
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/metrics/tool_permission/tool_permission.py
- https://github.com/confident-ai/deepeval/releases/tag/python-v4.1.4 (July 29 2026, PR #2951)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/test_case/llm_test_case.py
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/metrics/base_metric.py
- https://github.com/confident-ai/deepeval/tags (python-v4.1.6 and python-v4.1.7, both Aug 9 2026 — MCP evaluation support)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/metrics/mcp_use_metric/mcp_use_metric.py (`MCPUseMetric`)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/metrics/mcp/multi_turn_mcp_use_metric.py (`MultiTurnMCPUseMetric`)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/metrics/mcp/mcp_task_completion.py (`MCPTaskCompletionMetric`)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/test_case/mcp.py (`MCPServer`/`MCPToolCall`/`MCPResourceCall`/`MCPPromptCall` field definitions; also `normalize_mcp_servers`/`_from_official_mcp_server`/`get_available_mcp_tool_names`, v4.1.8)
- https://pypi.org/pypi/deepeval/json (confirmed v4.1.8 latest, Aug 12 2026)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/_version.py
- https://github.com/confident-ai/deepeval/compare/v4.1.7...v4.1.8.diff
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/test_case/utils.py (`classify_tool_call_types`/`process_mcp_servers`)
- https://raw.githubusercontent.com/confident-ai/deepeval/main/deepeval/evaluate/evaluate.py (`evaluate()`/`assert_test()` signatures — `mcp_servers` param on `evaluate()` only)
- https://github.com/confident-ai/deepeval/compare/python-v4.1.9...python-v4.1.10.diff (voice metrics package introduced, 32 commits)
