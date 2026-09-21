---
name: multimodal-chatbot-testing
description: Test AI chatbots/agents that accept image or video input (visual QA, document-image upload, chart/screenshot understanding) — distinct from the text-only chatbot-tester pipeline. Covers the MLLM-as-a-Judge scoring pattern (with its known scoring-consistency biases) and lmms-eval for benchmark-style regression testing of the underlying vision-language model. Use when testing a chatbot that takes image/video input, evaluating visual-QA or chart-reading accuracy, or regression-testing a VLM before/after a model swap. Triggers on: "test image chatbot", "multimodal LLM testing", "vision-language model evaluation", "MLLM-as-a-judge", "test chart reading AI", "lmms-eval", "VLM regression test".
---

# Multimodal Chatbot Testing

Testing a chatbot that accepts **image or video input** (not just text) needs two additional layers beyond the standard `chatbot-tester` pipeline: an image/video-aware judge for product-level QA, and a benchmark harness for the underlying vision-language model (VLM) itself.

## When to reach for this vs. existing skills

| Situation | Skill |
|---|---|
| Chatbot only reads/writes text | `chatbot-tester` → `response-evaluator` |
| Source docs are scanned PDFs/images you need to extract text from first | `ocr-processor` (feeds `chatbot-tester`) |
| Chatbot's *input* includes images/video and you're scoring its *understanding* of them | This skill |
| You need to benchmark a VLM's raw perception/reasoning ability (not a specific product) | This skill → `lmms-eval` |

## Layer 1 — MLLM-as-a-Judge (product-level scoring)

Use a current vision-capable model (an OpenAI, Gemini, or Claude model with image input) as the judge, scoring the chatbot's actual response against the source image plus an expected answer.

**Analyze-then-Judge prompting** (one-step CoT) scores measurably closer to human judgment than asking for a bare score:

```
You are a meticulous evaluator of Vision-Language AI responses.

Task: {task_description}                 # e.g. "chart data extraction", "receipt line-item QA"
Source image: {image}
Chatbot response: {response}
Expected answer: {expected_answer}

Step 1 — Analyze: describe what is actually visible in the image relevant to the task,
independent of the chatbot's response.
Step 2 — Judge: compare the chatbot's response to your own analysis and the expected
answer. Note any hallucinated details (facts not visible in the image) separately from
factual errors (details visible but misreported).

Output JSON: {"analysis": "...", "hallucination": bool, "factual_errors": [...], "score": 0-100}
```

**Known bias — do not trust absolute scores blindly.** Research (MLLM-as-a-Judge benchmark, arXiv 2402.04788) found MLLM judges align well with humans on **pairwise comparison** ("which response is better") but are inconsistent and hallucination-prone on **absolute scoring** and **batch ranking**. Practical implication:
- Prefer **pairwise comparison** (current chatbot response vs. last-release response vs. expected answer) over trusting a single 0–100 score in isolation.
- Track the score as a trend across the same fixed image set, not as a pass/fail absolute threshold on day one.
- Always separate "hallucinated" (invented content not in the image) from "misread" (real content, wrong reading) in the judge output — they need different fixes (grounding vs. OCR/resolution).

## Layer 2 — lmms-eval (VLM regression benchmarking)

When you need to know whether swapping the underlying vision model (e.g. a provider upgrade, a fine-tune, a cheaper model to cut cost) regresses visual understanding, run standard benchmarks rather than your own ad hoc image set:

```bash
pip install lmms-eval

python -m lmms_eval \
  --model qwen2_5_vl \
  --model_args pretrained=Qwen/Qwen2.5-VL-3B-Instruct \
  --tasks mme,mmbench,mathvista \
  --batch_size 1
```

Relevant task suites: `mmmu`, `mme`, `mmbench`, `mathvista` (image); `videomme`, `egoschema` (video). Pick tasks that match your product surface — e.g. `mathvista` for chart/diagram-heavy products, `videomme` if the chatbot ingests video.

**v0.6 (Feb 2026)** added an evaluation-as-a-service mode — a standalone HTTP eval server so evals run async out of the critical path of a CI pipeline or training loop, plus statistically grounded results (confidence intervals, paired t-tests) instead of a single point score:

```python
from lmms_eval.entrypoints import ServerArgs, launch_server

launch_server(ServerArgs(host="0.0.0.0", port=8000, max_completed_jobs=200))
# Clients submit async jobs via EvalClient and poll for results —
# use this to gate a model swap without blocking the deploy pipeline.
```

Gate a model-swap PR on: no statistically significant regression (paired t-test, not just "score went down") on the task suite matching your product's visual domain.

## CI Gate Pattern

```yaml
# Fail the PR if a VLM/prompt change regresses visual understanding on your fixed benchmark
- name: VLM regression check
  run: |
    python -m lmms_eval --model <provider> --tasks mathvista,mmbench --batch_size 1 \
      --output_path ./vlm-eval-results
    python check_regression.py ./vlm-eval-results --baseline ./vlm-eval-baseline --fail-on-regression
```

## Sources
- MLLM-as-a-Judge: Assessing Multimodal LLM-as-a-Judge with Vision-Language Benchmark (biases, Analyze-then-Judge prompting): https://arxiv.org/pdf/2402.04788
- MLLM-as-a-Judge project page: https://mllm-judge.github.io/
- LMMs-Eval (v0.6 evaluation-as-a-service, task list, CLI usage): https://github.com/evolvinglmms-lab/lmms-eval
- Multimodal LLM Evaluation developer guide: https://www.comet.com/site/blog/multimodal-llm-evaluation/
