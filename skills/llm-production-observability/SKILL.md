---
name: llm-production-observability
description: Three-pillar strategy for monitoring LLM/chatbot quality in production — offline golden-dataset evals, runtime input/output guardrails, and production tracing with drift alerts. Use when deploying an AI chatbot to production, setting up LLM monitoring, detecting hallucination drift, or building release gates for LLM features. Triggers on: "LLM monitoring", "chatbot drift", "golden dataset", "production tracing", "LLM observability", "hallucination rate", "drift detection", "LLM guardrails".
---

# LLM Production Observability — Three-Pillar Strategy

Running an LLM in production without observability means hallucinations, drift, and adversarial inputs go undetected until users complain. Implement all three pillars before launching.

## The Three Pillars

```
┌─────────────────────────────────────────────────────────┐
│  Pillar 1          Pillar 2           Pillar 3           │
│  Offline Evals     Runtime Guardrails Production Tracing │
│  (pre-deploy)      (every request)    (post-deploy)      │
└─────────────────────────────────────────────────────────┘
```

## Pillar 1 — Offline Evals on a Golden Dataset

A **golden dataset** is a curated set of (input, expected_output) pairs that represents your full coverage surface. Run it on every build before deploy.

### Build the Golden Dataset

```python
# golden_dataset.py structure
GOLDEN = [
    {
        "id": "refund-policy-001",
        "input": "What is the refund window?",
        "expected": "30 days from purchase date",
        "category": "policy",          # group for breakdown metrics
        "difficulty": "easy",
        "added_date": "2026-05-01",
        "source_doc": "refund_policy_v3.pdf"
    },
    # ... aim for 100-300 entries covering all intents and edge cases
]
```

### Run Evals as a Release Gate

```python
# eval_gate.py — fail CI if accuracy drops below threshold
import json, sys

THRESHOLD = 0.80   # 80% pass rate required to deploy

results = json.load(open("evaluations.json"))
pass_rate = sum(1 for r in results if r["pass"]) / len(results)

if pass_rate < THRESHOLD:
    print(f"❌ GATE BLOCKED: pass rate {pass_rate:.1%} < {THRESHOLD:.0%}")
    sys.exit(1)
print(f"✅ GATE PASSED: pass rate {pass_rate:.1%}")
```

### Keep the Dataset Alive

- Add every real production failure to the golden set immediately.
- Tag entries by intent category — track per-category regression, not just overall average.
- Track **embedding distribution** of the dataset over time: if live queries drift far from golden inputs, your coverage has a blind spot.

```python
# drift_coverage_check.py — detect when live traffic outpaces golden set
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def coverage_gap(golden_embeddings, live_embeddings, threshold=0.85):
    """Return live queries that have no golden counterpart within threshold."""
    gaps = []
    for live_emb in live_embeddings:
        sims = cosine_similarity([live_emb], golden_embeddings)[0]
        if sims.max() < threshold:
            gaps.append(live_emb)
    return gaps   # high count → update golden dataset
```

---

## Pillar 2 — Runtime Guardrails

Validate every input and output before the user sees it.

```python
# guardrails.py
import re

class InputGuardrail:
    INJECTION_PATTERNS = [
        r"ignore previous instructions",
        r"you are now",
        r"act as",
        r"jailbreak",
    ]

    def check(self, user_input: str) -> tuple[bool, str]:
        lower = user_input.lower()
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, lower):
                return False, f"Input blocked: possible prompt injection ({pattern})"
        if len(user_input) > 4000:
            return False, "Input too long — max 4000 characters"
        return True, ""


class OutputGuardrail:
    def check(self, response: str, expected_language: str = "en") -> tuple[bool, str]:
        # Block empty responses
        if not response or len(response.strip()) < 5:
            return False, "Response empty or too short"
        # Block obvious error strings leaking through
        error_phrases = ["sorry, i cannot", "as an ai", "i don't have access to"]
        lower = response.lower()
        for phrase in error_phrases:
            if phrase in lower:
                return False, f"Model refused or leaked system prompt language: '{phrase}'"
        return True, ""
```

---

## Pillar 3 — Production Tracing with Drift Alerts

**A trace captures the full chain**: user query → retrieved docs → prompt sent to model → model response. Without traces you cannot debug production failures.

### What a Trace Must Record

```python
# trace schema (store in your observability backend)
{
    "trace_id": "uuid",
    "session_id": "user session",
    "timestamp": "ISO-8601",
    "user_query": "...",
    "retrieved_docs": [
        {"doc_id": "...", "relevance_score": 0.92, "snippet": "..."}
    ],
    "prompt_sent": "...",    # full assembled prompt
    "model_response": "...",
    "latency_ms": 1230,
    "input_tokens": 850,
    "output_tokens": 210,
    "online_eval_score": 0.87,    # auto-eval score if running online evals
    "guardrail_triggered": false
}
```

### Recommended 2026 Tooling Stack

| Layer | Tool |
|-------|------|
| Tracing | [Langfuse](https://langfuse.com) or [LangSmith](https://smith.langchain.com) |
| APM-integrated | Datadog LLM Observability |
| Deep eval observability | Arize Phoenix or Arize AX |
| Online evals | Attach an eval function to your tracing layer |

### Drift Alert Pattern

```python
# drift_monitor.py — run nightly via cron or GitHub Actions
import statistics

def check_hallucination_drift(recent_scores: list[float], baseline: float, threshold: float = 0.05):
    """Alert if hallucination rate has risen more than threshold above baseline."""
    current_rate = 1 - statistics.mean(recent_scores)
    if current_rate - baseline > threshold:
        send_alert(
            f"⚠️ Hallucination drift detected: {current_rate:.1%} vs baseline {baseline:.1%}. "
            f"Possible causes: model update, knowledge base change, distribution shift."
        )
```

### Triggering Re-Eval

Run your golden-dataset eval again (Pillar 1) automatically when:
- Model version changes
- System prompt changes
- Knowledge base / documents updated
- Hallucination rate in production exceeds alert threshold

---

## When to Run Each Pillar

| Event | Pillar 1 (Offline Evals) | Pillar 2 (Guardrails) | Pillar 3 (Tracing) |
|-------|--------------------------|----------------------|---------------------|
| Pre-deploy | ✅ Run as CI gate | ✅ Validate config | — |
| Every request | — | ✅ Always on | ✅ Always on |
| Nightly | ✅ Optional regression | — | ✅ Drift check |
| System prompt change | ✅ Required | ✅ Re-validate | — |
| Model update | ✅ Required | ✅ Re-validate | ✅ Reset baseline |

## Sources

- [AI & LLM App Testing 2026 — Vervali](https://www.vervali.com/blog/ai-and-llm-application-testing-in-2026-the-definitive-guide/)
- [Building a Golden Dataset for AI Evaluation — Maxim](https://www.getmaxim.ai/articles/building-a-golden-dataset-for-ai-evaluation-a-step-by-step-guide/)
- [Evaluation-First AI Product Engineering (Jan 2026) — Medium](https://medium.com/@falvarezpinto/evaluation-first-ai-product-engineering-golden-sets-drift-monitoring-and-release-gates-for-llm-2c3bfb3f1e7b)
- [LLM Observability in Production — atal upadhyay (Mar 2026)](https://atalupadhyay.wordpress.com/2026/03/28/llm-observability-in-production-tracing-evals-cost-tracking-and-drift-detection/)
- [Chatbot Testing 2026 — Cekura](https://www.cekura.ai/blogs/complete-chatbot-testing-guide-ai-agents)
