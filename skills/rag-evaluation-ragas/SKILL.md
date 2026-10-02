---
name: rag-evaluation-ragas
description: |
  RAG pipeline evaluation using the 4-core RAGAS metrics: faithfulness, answer relevancy, context precision, context recall. Use when testing a RAG chatbot's retrieval quality, diagnosing retrieval vs generation failures, or adding automated RAG quality gates. Triggers on: "RAG evaluation", "RAGAS", "faithfulness metric", "context precision", "context recall", "retrieval quality", "RAG testing", "groundedness", "RAG pipeline quality".
---

# RAG Evaluation with RAGAS

RAG failures masquerade as each other: bad retrieval produces low faithfulness, bad generation produces low relevancy. The 4-core RAGAS metrics split retrieval from generation so you fix the right layer.

## The 4-Core Metrics

```
Retrieval layer  →  Context Precision + Context Recall
Generation layer →  Faithfulness + Answer Relevancy
```

| Metric | What it measures | Diagnoses |
|--------|-----------------|-----------|
| **Context Precision** | Relevant chunks / Total retrieved chunks | Retriever pulling noise |
| **Context Recall** | Retrieved info / All info needed to answer | Retriever missing docs |
| **Faithfulness** | Grounded claims / All claims in response | Generator hallucinating |
| **Answer Relevancy** | How well response addresses the query (0–1) | Generator going off-topic |

## Quick Failure Diagnosis

```
Faithfulness ✓, Answer Relevancy ✗  → irrelevant chunks; retrieval problem
Context Recall ✗, Faithfulness ✓    → retriever misses docs; generator honest with what it has
Faithfulness ✗, Context Precision ✓ → generator fabricates beyond context
All metrics ✗                        → chunking strategy broken; debug chunk boundaries first
```

## Setup

```bash
pip install ragas   # 0.4.x is current (0.4.3, 2026-01-13)
```

## Evaluate a RAG Pipeline (Ragas 0.4 collections API — preferred)

Ragas 0.4 moved metrics to `ragas.metrics.collections` (class-based, `await metric.ascore(...)` /
`.score(...)`, result in `.value`) and replaces `evaluate()` with the `@experiment()` decorator.
The legacy `from ragas.metrics import faithfulness` + `Dataset.from_dict({"question", "answer",
"contexts", "ground_truth"})` pattern below is the 0.1-era API — deprecated in 0.4 and slated for
removal in 1.0.

```python
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness, AnswerRelevancy

llm = llm_factory("gpt-4o-mini", client=AsyncOpenAI())   # judge LLM — pick a cross-family model

faith = await Faithfulness(llm=llm).ascore(
    user_input="What is the refund window?",
    response="You can return items within 30 days of purchase.",
    retrieved_contexts=["Our policy allows refunds within 30 days of purchase."],
)
rel = await AnswerRelevancy(llm=llm).ascore(
    user_input="What is the refund window?",
    response="You can return items within 30 days of purchase.",
)
result = {"faithfulness": faith.value, "answer_relevancy": rel.value}
# ContextPrecision / ContextRecall also live in ragas.metrics.collections
# (UNVERIFIED: their exact ascore() kwargs — check the metric's docs page before use).
```

For batch runs use `from ragas import experiment` + `@experiment(ResultModel)` per the official
v0.3→v0.4 migration guide.

### Legacy API (Ragas ≤0.3 — deprecated, kept for old pipelines)

```python
# eval_rag.py
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

# Build eval dataset — each row is one question/answer/context triple
data = {
    "question": [
        "What is the refund window?",
        "How do I reset my password?",
    ],
    "answer": [
        "You can return items within 30 days of purchase.",
        "Click 'Forgot Password' on the login screen to receive a reset email.",
    ],
    "contexts": [
        ["Our policy allows refunds within 30 days of purchase."],
        ["To reset your password, use the 'Forgot Password' link on the login page."],
    ],
    "ground_truth": [
        "30 days from purchase date",
        "Use Forgot Password link on login page",
    ],
}

result = evaluate(
    Dataset.from_dict(data),
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
)
print(result)
# {'faithfulness': 0.97, 'answer_relevancy': 0.91, 'context_precision': 0.85, 'context_recall': 0.79}
```

## CI Gate — Minimum Thresholds

```python
# gate.py — run post-eval; exit 1 if below thresholds
import sys

THRESHOLDS = {
    "faithfulness":       0.75,
    "answer_relevancy":   0.75,
    "context_precision":  0.65,
    "context_recall":     0.70,
}

def check_gate(result: dict) -> None:
    failures = [(k, result[k], v) for k, v in THRESHOLDS.items() if result[k] < v]
    if failures:
        for name, score, threshold in failures:
            print(f"❌ {name}: {score:.2f} < {threshold}")
        sys.exit(1)
    print("✅ All RAG metrics passed gates.")

check_gate(result)
```

## Production Confusion Matrix

Track retrieval outcomes over live traffic to prioritize where to improve:

```python
def rag_confusion_matrix(evals: list[dict]) -> dict:
    """
    evals: list of {"retrieved_relevant": bool, "answer_correct": bool}
    """
    tp = sum(1 for e in evals if     e["retrieved_relevant"] and     e["answer_correct"])
    fp = sum(1 for e in evals if     e["retrieved_relevant"] and not e["answer_correct"])
    fn = sum(1 for e in evals if not e["retrieved_relevant"] and     e["answer_correct"])
    tn = sum(1 for e in evals if not e["retrieved_relevant"] and not e["answer_correct"])
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall    = tp / (tp + fn) if (tp + fn) else 0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": precision, "recall": recall}
```

High FP (retrieved relevant but answer wrong) → generator not using context well.
High FN (retrieved irrelevant but answer correct) → retriever misses; generator guesses.

## Fixing Low Context Recall — Chunking Fixes

Context Recall drops when answer text is split across chunk boundaries:

```python
# ❌ Fixed-size chunks cut answers at wrong boundaries
chunks = [text[i:i+512] for i in range(0, len(text), 512)]

# ✓ Sentence-aware chunking preserves meaning
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=50, tokens_per_chunk=256)
chunks = splitter.split_text(text)

# ✓ Or increase overlap (quick fix for modest docs)
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=150)
```

## DeepEval Integration (pytest runner)

DeepEval ships its **own** implementations of the same four RAG metrics (not wrappers around
RAGAS — it only has a thin separate `deepeval/metrics/ragas.py` adapter) and runs them as pytest
gates. `ContextualPrecisionMetric` and `ContextualRecallMetric` **require `expected_output`**
(verified: `_required_params` = input, retrieval_context, expected_output in deepeval 4.2.7) —
omitting it raises a missing-params error:

```python
from deepeval.metrics import ContextualPrecisionMetric, ContextualRecallMetric, \
    FaithfulnessMetric, AnswerRelevancyMetric
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

def test_rag_quality():
    assert_test(
        LLMTestCase(
            input="What is the refund window?",
            actual_output="You can return items within 30 days.",
            expected_output="30 days from purchase date",
            retrieval_context=["Our policy allows refunds within 30 days of purchase."],
        ),
        [
            ContextualPrecisionMetric(threshold=0.70),
            ContextualRecallMetric(threshold=0.80),
            FaithfulnessMetric(threshold=0.80),
            AnswerRelevancyMetric(threshold=0.70),
        ]
    )
```

## Sources

- [RAG Evaluation 2026 — DataVLab](https://datavlab.ai/post/rag-evaluation-methods-metrics-2026-guide)
- [How to Evaluate RAG Pipelines with RAGAS — INVRA](https://www.invra.co/en/rag-evaluation-with-ragas-measuring-faithfulness-context-precision-and-recall-in-production/)
- [RAG Evaluation Metrics & Frameworks 2026 — blog.premai.io](https://blog.premai.io/rag-evaluation-metrics-frameworks-testing-2026/)
- [Chatbot Testing 2026 — Cekura](https://www.cekura.ai/blogs/complete-chatbot-testing-guide-ai-agents)
- [Best RAG Evaluation Tools 2026 — Braintrust](https://www.braintrust.dev/articles/best-rag-evaluation-tools)
- Ragas version (0.4.3): https://pypi.org/pypi/ragas/json
- Ragas Faithfulness (collections API, `ascore`, `.value`): https://raw.githubusercontent.com/explodinggradients/ragas/main/docs/concepts/metrics/available_metrics/faithfulness.md
- Ragas v0.3→v0.4 migration (`evaluate()` → `@experiment()`): https://raw.githubusercontent.com/explodinggradients/ragas/main/docs/howtos/migrations/migrate_from_v03_to_v04.md
- DeepEval 4.2.7 wheel (`metrics/contextual_precision`, `contextual_recall` required params): https://pypi.org/project/deepeval/
