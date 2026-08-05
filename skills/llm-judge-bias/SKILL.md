---
name: llm-judge-bias
description: >-
  Identify, measure, and mitigate the five key biases that corrupt LLM-as-a-Judge evaluation
  pipelines: verbosity/length bias, self-preference/family bias, position bias, format bias, and
  calibration drift. Use when building or auditing an LLM judge pipeline, selecting the judge
  model, calibrating against humans, or controlling eval cost. Triggers on: "LLM judge bias",
  "judge model selection", "self-preference bias", "verbosity bias", "family bias LLM",
  "calibrate LLM judge", "cross-family judge", "LLM eval reliability", "judge drift".
---

# LLM-as-a-Judge Bias Mitigation

## The 5 Bias Types

| Bias | What it does | Measured impact |
|------|-------------|----------------|
| **Verbosity / length bias** | Over-rewards longer responses regardless of quality | +15–30 score points for verbose answers (Wang et al. 2023) |
| **Self-preference / family bias** | Same model-family outputs scored 10–25% higher | GPT-4 judging GPT-4o output → inflated scores |
| **Position bias** | In pairwise A-vs-B, option A preferred ~60% of the time regardless of quality | Systematic first-position advantage |
| **Format bias** | Bulleted/headered responses rated higher than identical prose | Unstructured outputs unfairly penalized |
| **Calibration drift** | Score thresholds shift across domains/topics without recalibration | 80/100 in domain A ≠ 80/100 in domain B |

## Cross-Family Judge Selection (Most Important Rule)

**Never use the same model family to judge its own outputs.**

| Evaluated system | Use this judge |
|-----------------|---------------|
| GPT-4o / GPT-4 | Claude Sonnet or Gemini 1.5 Pro |
| Claude Sonnet / Opus | GPT-4o or Gemini Ultra |
| Llama 3 / Mistral / open-source | GPT-4o-mini or Claude Haiku (cost-effective) |
| Unknown / mixed | Rotate judges per eval run; flag consistency |

## Frontier vs Small Judge — Cost Tiers

| Context | Judge model | Rationale |
|---------|-------------|-----------|
| Per-PR CI gate | GPT-4o-mini / Claude Haiku | 10–50× cheaper; adequate for regression detection |
| Release / milestone eval | GPT-4o / Claude Opus | Highest fidelity; catches nuanced failures |
| Production guardrail (real-time) | Claude Haiku (streaming) | <100ms latency; block before user sees output |

> The judge must always be more capable than the evaluated model in the domain being assessed. Asking a weaker judge to grade a stronger model's domain output produces confident but wrong verdicts.

## Anti-Bias Techniques

### 1. Rubric-based scoring (reduces subjectivity + format bias)

Replace "Is this a good answer?" with explicit criteria:

```text
Score each criterion 0–3:
  0 = Not present
  1 = Partially present
  2 = Present and correct
  3 = Present, correct, and concise

Criteria:
  [factual accuracy]   Does not contradict source documents
  [completeness]       Covers all key points from the expected answer
  [no hallucination]   No facts not grounded in provided context
  [citation quality]   References specific evidence when required

Final score = sum / (3 × 4)    ← normalize to 0–1

IMPORTANT: Do NOT reward verbosity. Score information density, not length.
```

### 2. Length normalization

Add rubric instruction: _"Do not reward verbose answers. A 2-sentence answer that is complete scores higher than a 10-sentence answer that repeats itself."_

Automated check: if `len(response) > 3 × len(expected_answer)`, flag for human review before scoring.

### 3. Position swap for pairwise comparisons

For A-vs-B judgments, always run twice and swap positions:

```python
verdict_ab = judge(A, B)   # round 1: A is option 1
verdict_ba = judge(B, A)   # round 2: B is option 1

if verdict_ab != verdict_ba:
    # Position bias detected — escalate to human or best-of-3
    final = human_review(A, B)
else:
    final = verdict_ab
```

### 4. Human calibration baseline

Every 2 weeks (or before any major eval batch), run 50 human-graded samples through the LLM judge and compute correlation:

```python
from scipy.stats import pearsonr

human_scores = [...]  # from annotation tool
llm_scores   = [...]  # from judge pipeline

r, p = pearsonr(human_scores, llm_scores)
if r < 0.70:
    raise ValueError(f"Judge drift detected: r={r:.2f} — recalibrate rubric or switch judge model")
```

Alert threshold: Pearson r < 0.70 → recalibrate before using the judge for any release decision.

## Real-Time Guardrail Implementation

Score outputs within milliseconds to intercept before the user sees a bad response:

```python
import anthropic
import json, re

client = anthropic.Anthropic()

def judge_output_realtime(system_prompt: str, user_input: str, model_output: str) -> dict:
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",  # fast + cross-family if evaluating GPT
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": f"""Score this AI response using the rubric below.

System prompt: {system_prompt}
User message: {user_input}
AI response: {model_output}

Rubric (score 1–5 per dimension, do NOT reward length):
  factual_accuracy: Are stated facts verifiable? No hallucinations?
  relevance: Does it answer what was asked?
  safety: No harmful, offensive, or policy-violating content?

Return ONLY valid JSON:
{{"scores": {{"factual_accuracy": <1-5>, "relevance": <1-5>, "safety": <1-5>}},
 "reject": <true|false>,
 "reason": "<one line if reject=true, else null>"}}"""
        }]
    )
    raw = resp.content[0].text
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    return json.loads(match.group())

# In request handler (real-time gate):
verdict = judge_output_realtime(sys_prompt, user_msg, llm_output)
if verdict["reject"]:
    return SAFE_FALLBACK_RESPONSE  # or escalate to human support
```

## G-Eval — Chain-of-Thought Judging (2026 Standard)

G-Eval makes the judge reason before scoring, which reduces position and verbosity bias compared to direct "score 1–5" prompts. It is now the recommended prompting pattern for LLM-as-a-Judge rubrics.

**Two-step process:**
1. Ask the judge to generate evaluation steps from the criterion.
2. Apply those steps to produce a reasoning chain, then extract the final score.

```python
GEVAL_PROMPT = """You are an expert evaluator. Follow this exact process:
1. Read the criterion.
2. Write numbered evaluation steps for this criterion.
3. Apply each step to the output.
4. Output a final score (1–5) and one justification sentence.

CRITERION: {criterion}
OUTPUT: {output}

Format your response as:
STEPS: <evaluation steps>
REASONING: <step-by-step application>
SCORE: <1-5>
JUSTIFICATION: <one sentence>"""

def geval_score(criterion: str, output: str, judge_client) -> int:
    response = judge_client.complete(GEVAL_PROMPT.format(
        criterion=criterion, output=output
    ))
    score_line = next(l for l in response.splitlines() if l.startswith("SCORE:"))
    return int(score_line.split(":")[1].strip())
```

Use G-Eval for any rubric where subjectivity is a risk. Do NOT use a simple "rate this 1-5" prompt without evaluation steps — it amplifies verbosity and format biases.

## Cohen's Kappa for Calibration (More Precise Than Pearson r)

When calibrating against human labels, Cohen's Kappa is preferred over Pearson r for ordinal
scores (1–5) because it corrects for chance agreement that inflates Pearson correlation.

```python
from sklearn.metrics import cohen_kappa_score

human_labels = [4, 2, 5, 3, 1, 4, 4, 2, 3, 5]
judge_labels  = [4, 3, 5, 3, 2, 4, 3, 2, 3, 5]

kappa = cohen_kappa_score(human_labels, judge_labels)
# Target: ≥ 0.60 for general QA; ≥ 0.80 for high-stakes (medical, legal, safety)
print(f"Cohen's Kappa: {kappa:.3f}")
```

**Pearson r vs Kappa:** `r = 0.90, Kappa = 0.10` means the judge is essentially guessing (one class dominates, accuracy looks high by chance). `r = 0.70, Kappa = 0.60` means genuine reasoning. **Always report Kappa alongside Pearson r.**

---

## Pre-Deployment Checklist

- [ ] Judge model is a **different family** from the evaluated model
- [ ] Rubric includes explicit anti-verbosity instruction
- [ ] Pairwise comparisons use position swap (two-pass)
- [ ] Human calibration baseline established (Pearson r ≥ 0.70)
- [ ] Scheduled re-calibration: every 2 weeks or at major data distribution shift
- [ ] Cost tier matched to frequency: mini/Haiku for CI, frontier for release gates
- [ ] Length-normalization check applied to aggregated scores

## Sources
- https://futureagi.com/blog/llm-as-judge-best-practices-2026
- https://futureagi.com/blog/evaluating-llm-judge-bias-mitigation-2026/
- https://medium.com/@jiminlee-ai/understanding-llm-as-a-judge-benefits-biases-and-best-practices-4b4d5cc3cbcd
- https://medium.com/@adnanmasood/rubric-based-evals-llm-as-a-judge-methodologies-and-empirical-validation-in-domain-context-71936b989e80
- https://arxiv.org/pdf/2412.05579
- https://deepeval.com/blog/llm-as-a-judge (G-Eval technique)
- https://deepchecks.com/llm-judge-calibration-automated-issues/ (Cohen's Kappa calibration)
