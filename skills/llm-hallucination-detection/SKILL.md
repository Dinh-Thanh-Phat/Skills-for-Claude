---
name: llm-hallucination-detection
description: Use when adding hallucination detection to an LLM application, choosing between NLI, consistency sampling, or LLM-as-judge methods, or setting CI gates on hallucination rates. Triggers on: "hallucination detection", "groundedness check", "faithfulness check", "SelfCheckGPT", "consistency sampling", "NLI entailment", "LLM makes up facts", "reduce hallucinations in production".
---

# LLM Hallucination Detection

## Four failure modes (detect each differently)

| Failure mode | Description | Detection method |
|---|---|---|
| **Ungrounded claim** | Statement not supported by retrieved context (RAG) | Faithfulness / groundedness scorer |
| **Factual error** | Incorrect real-world fact (no context to check against) | Consistency sampling (SelfCheckGPT) or factuality scorer |
| **Self-contradiction** | Response contradicts itself within one turn | NLI entailment (premise vs hypothesis from same response) |
| **Context contradiction** | Response contradicts what user stated earlier | NLI check against prior user turns |

---

## Detection methods

### 1. NLI-based (fastest, cheapest — ~2ms/claim)

A trained DeBERTa NLI model checks whether each claim is **entailed** by the source document.
Catches ungrounded claims and factual contradictions without LLM API calls.

```python
# pip install deepeval[nli]   or   pip install sentence-transformers
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

test_case = LLMTestCase(
    input="What did the document say about returns?",
    actual_output="Customers have 60 days to return items.",
    retrieval_context=["Our return policy allows 30 days for all purchases."]
)
metric = FaithfulnessMetric(threshold=0.8, model="gpt-4o-mini", include_reason=True)
# Or use NLI backend: FaithfulnessMetric(threshold=0.8, use_nli=True)
metric.measure(test_case)
print(metric.score, metric.reason)  # 0.0 — claim contradicts context
```

### 2. Consistency sampling / SelfCheckGPT (no reference needed)

Generate N independent responses for the same prompt. Factual statements converge when the model knows the answer; hallucinations produce high variance. Use when there is no retrieved document to check against.

```python
import anthropic, re
from statistics import mean

client = anthropic.Anthropic()

def consistency_score(prompt: str, n: int = 5) -> float:
    """Lower score = higher hallucination risk. Returns 0–1."""
    responses = [
        client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        ).content[0].text
        for _ in range(n)
    ]
    # Simple word-overlap consistency; replace with NLI for higher accuracy
    ref = set(responses[0].lower().split())
    scores = [len(ref & set(r.lower().split())) / max(len(ref), 1) for r in responses[1:]]
    return mean(scores)

score = consistency_score("What year was the Eiffel Tower built?")
if score < 0.6:
    print("Low consistency — likely hallucination")
```

For production: use `SelfCheckGPT` with NLI backend (requires `selfcheckgpt` package and a fine-tuned NLI model) for sentence-level scoring.

### 3. LLM-as-judge (flexible, higher cost)

Best for complex claims where NLI lacks the world-knowledge needed to evaluate them.

```python
from anthropic import Anthropic

client = Anthropic()

def judge_groundedness(claim: str, context: str) -> dict:
    prompt = f"""You are a factual accuracy judge.

Context: {context}

Claim: {claim}

Is this claim FULLY SUPPORTED by the context? Answer JSON only:
{{"supported": true/false, "reason": "<one sentence>"}}"""
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",   # fast tier for inline judging
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    return json.loads(response.content[0].text)
```

### 4. Semantic entropy (most robust, batch only)

Measures uncertainty via semantic diversity across N responses. High semantic entropy = high hallucination risk. Use offline/nightly; not suitable for real-time serving.

Requires embedding model to cluster semantically equivalent responses, then compute entropy of cluster distribution. See `SEReDeEP` (arxiv 2505.07528) for RAG-specific implementation.

---

## Decision table — which method to use

| Situation | Method |
|---|---|
| RAG: have retrieved context | Faithfulness / NLI-based scorer (for the full retrieval-vs-generation metric suite, see `rag-evaluation-ragas`) |
| Open-domain: no context | Consistency sampling (SelfCheckGPT) |
| Multi-turn: prior conversation | NLI check claim vs user-stated facts |
| CI regression suite | DeepEval `HallucinationMetric` in pytest |
| Production inline guard (real-time) | Fast NLI or Haiku-based judge |
| Offline analysis / research | Semantic entropy |
| High-stakes (medical, legal) | Multi-layer: NLI → LLM-judge → human review |

---

## Multi-layer production strategy

```
Request ──► [Fast NLI check] ──► PASS ──► Serve response
                │
              FAIL / borderline
                │
                ▼
        [LLM-as-judge (Haiku)]
                │
              PASS ──► Serve with confidence caveat
                │
              FAIL ──► Block + fallback ("I'm not certain…")
                │
                ▼
        [Log to evaluation dataset for nightly semantic entropy run]
```

~80% of checks terminate at the NLI layer (fast + free). LLM-judge only fires for the tail.

---

## CI gate with DeepEval

```python
# tests/eval_hallucination.py
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import HallucinationMetric, FaithfulnessMetric

@pytest.mark.parametrize("case", GOLDEN_DATASET)
def test_no_hallucination(case):
    test_case = LLMTestCase(
        input=case["input"],
        actual_output=run_bot(case["input"]),
        context=case["retrieved_docs"]
    )
    assert_test(test_case, [
        HallucinationMetric(threshold=0.1),   # < 10% hallucination rate
        FaithfulnessMetric(threshold=0.8),    # ≥ 80% claims grounded
    ])
```

Recommended thresholds:
- **General chatbot**: Hallucination < 10%, Faithfulness > 0.80
- **High-stakes (medical, legal)**: Hallucination < 5%, Faithfulness > 0.95
- **Internal tooling / low-risk**: Hallucination < 20%

---

## 2026 framing

The industry has moved from "chase zero hallucinations" to **"measure and manage uncertainty predictably."** Production systems combine:
1. A faithfulness scorer for RAG outputs (automated gate)
2. Consistency sampling for open-domain responses (spot-check on low-confidence queries)
3. A nightly CI suite against a golden dataset with HallucinationMetric
4. Drift alerts when hallucination rate increases week-over-week (see `llm-production-observability`)

## Sources
- https://www.braintrust.dev/articles/ai-hallucination-evaluations-metrics-methods-2026
- https://www.braintrust.dev/articles/best-hallucination-detection-tools-2026
- https://www.getmaxim.ai/articles/how-to-detect-hallucinations-in-your-llm-applications/
- https://deepeval.com/docs/metrics-hallucination
- https://arxiv.org/pdf/2505.07528
- https://www.bugraptors.com/blog/llm-output-evaluation-hallucination-detection
