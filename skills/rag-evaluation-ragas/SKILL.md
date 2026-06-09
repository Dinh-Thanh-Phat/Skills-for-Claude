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
pip install ragas datasets
```

## Evaluate a RAG Pipeline

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

RAGAS provides the metrics; DeepEval wraps them in pytest:

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
