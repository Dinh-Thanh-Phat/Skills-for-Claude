---
name: ai-agent-eval-platforms
description: Choosing and using commercial/OSS evaluation platforms for AI agents (multi-turn, tool-calling) in 2026 — Braintrust for pre-deployment experiments with sandboxed scorers, Latitude for agent-native causal tracing and multi-turn simulation, Langfuse for self-hosted open-source eval logging. Use when selecting an LLM eval platform, setting up continuous eval for an agentic system, or comparing eval platforms for a team. Triggers on: "Braintrust", "Latitude eval", "eval platform", "LLM eval SaaS", "agent evaluation platform", "multi-turn simulation testing", "GEPA", "production eval", "LLM experiment tracking".
---

# AI Agent Evaluation Platforms (2026)

## Why a Platform vs. Just a Framework?

`deepeval` / `RAGAS` (covered in companion skills) are **eval logic libraries** — they define metrics and run assertions. An **eval platform** adds dataset versioning, experiment tracking, PR merge blocking, team annotation workflows, and production-session scoring on top of those libraries. You need a platform once you have more than one person reviewing eval results or more than one model/prompt variant in flight.

---

## The 2026 Platform Landscape

Three clear tiers in early 2026:

| Tier | Tools | Best for |
|------|-------|---------|
| Agent-native SaaS | Latitude, Maxim AI | Multi-turn agents, tool-calling, causal traces |
| Experiment-first SaaS | Braintrust | Pre-deploy prompt experiments, dataset management |
| Open-source self-hosted | Langfuse | Full control, no vendor lock-in, budget teams |

---

## 1. Braintrust — Experiment-First Eval Platform

**When to use:** Pre-deployment — compare prompt variants, judge model changes, or RAG retrieval configurations against a versioned eval dataset. Blocks merges automatically when scores regress.

### Setup

```python
# pip install braintrust openai
import braintrust

# braintrust.init() RETURNS the Experiment (there is no project object with .init_experiment();
# braintrust.init_experiment(...) is a module-level alias). Python SDK 0.44.x verified.
experiment = braintrust.init(project="orders-chatbot", experiment="gpt-4o-mini-vs-gpt-4o")

for row in eval_dataset:
    output = call_llm(row["input"])
    experiment.log(
        input=row["input"],
        expected=row["expected"],
        output=output,
        scores={
            "relevance": score_relevance(output, row["expected"]),
            "faithfulness": score_faithfulness(output, row["context"]),
        }
    )

experiment.summarize()
```

### Sandboxed Custom Scorers

Braintrust can run custom scorer code server-side in an isolated environment — your scoring logic can call external APIs or run Python packages without your infra. (Not unique: Latitude V2 also runs custom JavaScript detector scripts as an evaluation method.)

```python
# Define a scorer in Braintrust UI (Python, runs in Braintrust cloud)
def score_json_validity(output, expected, input):
    try:
        import json
        json.loads(output)
        return {"name": "json_valid", "score": 1}
    except:
        return {"name": "json_valid", "score": 0}
```

### CI/CD Gate

```yaml
# GitHub Actions — block PR if scores regress
- name: Run Braintrust evals
  run: python run_evals.py
  env:
    BRAINTRUST_API_KEY: ${{ secrets.BRAINTRUST_API_KEY }}

- name: Run Braintrust Eval() files
  run: npx braintrust eval evals/ --terminate-on-failure
```

> There is **no** `--assert-no-regression` / `--experiment-name` flag on `braintrust eval`
> (real flags include `--filter`, `--list`, `--jsonl`, `--watch`, `--no-send-logs`,
> `--terminate-on-failure`, `--num-workers`). For PR comments showing per-score diffs vs. the base
> experiment use the official GitHub Action `braintrustdata/eval-action`, and enforce a hard gate
> in your own script by comparing the summary scores.

**Free tier:** UNVERIFIED (pricing changes often — check braintrust.dev/pricing).

---

## 2. Latitude — Agent-Native Causal Tracing

**When to use:** Production agents with multi-turn conversations and tool calls. Latitude models execution as a causal trace of dependent steps, not isolated LLM calls — essential for debugging where an agent went wrong in a 10+ turn session.

### Key Differentiators vs. Braintrust

| Capability | Latitude | Braintrust |
|-----------|---------|-----------|
| Multi-turn simulation testing | ✅ via datasets + your own runner (Scenario/promptfoo/Inspect), sessions tagged `simulation` | Via your own `Eval()` harness |
| Causal trace architecture | ✅ Agent-native (sessions/traces/spans) | Span model |
| Auto-cluster production failures | ✅ ("signals" from annotations/scores/evaluations) | UNVERIFIED |
| Pre-deploy experiment UX | ✅ Experiments (compare agent versions) | ✅ Strong |
| Custom scorer code | ✅ JavaScript custom-script detectors | ✅ Sandboxed scorers |
| License | **MIT open-source (V2), cloud or self-host** | SaaS |

> **Latitude V2 (2026) changed shape**: it is now an MIT-licensed open-source platform
> (Observe → Understand → Refine), self-hostable from one machine to Kubernetes. Simulations are
> **not** a hosted `lat.simulations.create/run` API — the old snippet here was not a real SDK call
> (`latitude-sdk` 9.x has no `simulations` client and `Latitude()` takes no `project_id`).

### Multi-Turn Simulation Testing (Latitude V2 pattern)

Per Latitude's "Simulate agents locally" doc: (1) curate a **dataset** from real traces/signals/CSV,
(2) pull rows with `latitude-sdk`, (3) run your agent against each row **in your own process**
(a for-loop for single-turn; a user-simulator runner such as LangWatch Scenario for multi-turn,
stopping on a judge verdict or turn limit), (4) send the sessions via Latitude telemetry tagged
`simulation` + an agent-version tag, (5) post the runner's verdict as a **score**, (6) compare
versions with **Experiments**. Put the multi-turn behavioral assertion in a dataset custom column
named `judgeCriteria` (e.g. "Issue the refund without asking for the order number twice").
Keep simulation traffic in a dedicated project, or exclude the `simulation` tag from production
evaluation triggers and monitors — otherwise CI scores cluster into signals and page the team.

### Failures → Regression Tests

Latitude turns annotations, scores, evaluations and flaggers into trackable **signals**; failing
traces can be added from a signal straight into a regression dataset, and signals can be
dispatched to Cursor/Linear agents to open fixes. (The earlier "GEPA = Generative Eval from
Production Annotations" description is UNVERIFIED — it does not appear in Latitude's docs index;
"GEPA" elsewhere refers to the Genetic-Pareto prompt optimizer.)

### Context Retention Degradation — Automatic Detection

Latitude surfaces when multi-turn agents degrade:

> "Context retention accuracy drops 15–30% in sessions exceeding 10 turns."

Latitude automatically surfaces these degradation patterns session-by-session rather than requiring you to manually investigate long conversation logs.

---

## 3. Langfuse — Open-Source, Self-Hosted

**When to use:** Teams that cannot send data to SaaS (data residency, privacy), or that want full control over storage and eval logic with no per-seat cost.

```python
# pip install langfuse   (v4.x; LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST env vars)
from langfuse import observe, get_client

langfuse = get_client()

@observe()
def run_agent(user_input: str) -> str:
    # Auto-traced: latency, token count, model name
    response = call_llm(user_input)
    langfuse.score_current_trace(
        name="relevance",
        value=score_relevance(response, user_input),
    )
    return response
```

> `langfuse.decorators` / `langfuse_context` were removed in the v3 rewrite and do not exist in
> v4 (`langfuse/decorators/` is gone from the repo) — the old import raises `ModuleNotFoundError`.

**What Langfuse provides:**
- Prompt versioning and A/B comparison
- Human annotation UI for labelling production traces
- Dataset management (good/bad example collection)
- Export to CSV/JSON for offline eval
- SDK experiments + batch evaluation (`langfuse.experiment`, `langfuse.batch_evaluation`, with a `RegressionError` for gating) in the v4 Python SDK

**What it lacks vs. Braintrust/Latitude:**
- No automatic issue clustering (must review traces manually)
- No built-in multi-turn user-simulation runner (bring your own, as with Latitude)
- Self-hosting needs Postgres + ClickHouse + Redis/Valkey (+ blob storage): Docker Compose for local/single-VM, Helm/Kubernetes or cloud templates for production

---

## Decision Matrix

```
Team size / budget?
├── Solo / OSS / < $500/mo budget
│   └── Langfuse (self-hosted, free)
├── Small team, pre-deploy focus, SaaS OK
│   └── Braintrust (pricing UNVERIFIED — check braintrust.dev/pricing)
└── Production agents, multi-turn, need simulation
    └── Latitude V2 (MIT OSS: cloud or self-host)

Primary concern?
├── "We want to compare prompts before shipping"
│   └── Braintrust experiments / Langfuse experiments / Latitude Experiments
├── "Our agent breaks in long sessions"
│   └── Latitude sessions + signals
├── "We need regression datasets built from production failures"
│   └── Latitude signals → dataset (or Langfuse annotation queues → dataset)
└── "We need custom Python scorers in the cloud"
    └── Braintrust sandboxed scorers
```

---

## Integration with DeepEval

These platforms complement `deepeval` (covered in `deepeval-llm-cicd`): use DeepEval metrics as the scorer logic, log results to a platform for experiment tracking and team review.

```python
# Use DeepEval metric, log result to Braintrust
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
import braintrust

metric = AnswerRelevancyMetric(threshold=0.7)
test_case = LLMTestCase(input=user_q, actual_output=response, retrieval_context=docs)
metric.measure(test_case)

experiment.log(
    input=user_q,
    output=response,
    scores={"answer_relevancy": metric.score},
)
```

## Sources

- [Best AI Agent Evaluation Platforms 2026 — Latitude](https://latitude.so/blog/best-ai-agent-evaluation-platforms-2026-comprehensive-comparison)
- [Agent-First vs LLM-Only Platforms 2026 — Latitude](https://latitude.so/blog/agent-first-comparison-guide-vs-braintrust)
- [AI Agent Eval Frameworks 2026: Testing Guide — Digital Applied](https://www.digitalapplied.com/blog/ai-agent-eval-frameworks-testing-guide-2026)
- [Langfuse vs Braintrust Alternatives 2026 — Langfuse](https://langfuse.com/faq/all/best-braintrustdata-alternatives)
- [Top 6 Agent Observability Platforms 2026 — Laminar](https://laminar.sh/article/2026-04-23-top-6-agent-observability-platforms)
