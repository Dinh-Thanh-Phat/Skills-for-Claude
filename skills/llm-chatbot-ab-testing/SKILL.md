---
name: llm-chatbot-ab-testing
description: >-
  Statistical A/B testing methodology for rolling out chatbot/LLM prompt, model, or config
  variants — minimum detectable effect, sample size, significance tests, guardrail metrics,
  rollout gate. Use when comparing two prompt versions, deciding whether a model swap actually
  improved quality, or gating a chatbot config change before 100% rollout. Triggers on: "A/B test
  chatbot", "prompt A/B test", "compare LLM variants", "statistical significance chatbot",
  "rollout gate LLM", "is this prompt better".
---

# LLM Chatbot A/B Testing

Offline evals (DeepEval, LLM-as-judge) tell you a variant *should* be better. A/B testing on live
traffic tells you it *actually is* — measuring against real user behavior, not a curated golden set.
Use this **after** a variant passes CI evals (see `deepeval-llm-cicd`, `llm-judge-bias`), as the final
gate before 100% rollout.

## When to A/B test vs when offline eval is enough

| Change type | Strategy |
|---|---|
| Prompt wording tweak, low risk | Offline eval (golden set) sufficient |
| New model swap (e.g. GPT-4o → Claude) | A/B test — behavior shift too broad for golden set to catch |
| System prompt rewrite affecting tone/policy | A/B test — user-perceived quality is subjective |
| RAG retrieval config change | A/B test — affects real query distribution offline set can't replicate |
| Bug fix / regression fix | Offline eval only — no need to re-litigate with live traffic |

## Step 1 — Define the metric and Minimum Detectable Effect (MDE)

Pick ONE primary metric before launching, plus 1–2 guardrails. Mixing many metrics without correction
inflates false positives.

- **Primary**: task completion rate, thumbs-up rate, escalation-to-human rate, or LLM-judge score (0–1) averaged per conversation.
- **Guardrails**: hallucination rate, refusal rate, latency (p95 TTFT) — a variant that wins on primary but blows a guardrail should NOT ship.
- **MDE**: smallest change worth caring about (e.g. "we only care if completion rate moves ≥2 points"). Smaller MDE requires exponentially more sample size — don't chase 0.5% effects on low-traffic bots.

## Step 2 — Sample size before you launch

Compute sample size from baseline rate, MDE, and desired power — do this before splitting traffic, not after peeking at results.

```python
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

baseline_rate = 0.72          # current completion rate
mde = 0.02                    # smallest effect worth detecting (2 points)
effect_size = proportion_effectsize(baseline_rate, baseline_rate + mde)

analysis = NormalIndPower()
n_per_arm = analysis.solve_power(
    effect_size=effect_size, alpha=0.05, power=0.8, ratio=1.0
)
print(f"Need ~{int(n_per_arm)} conversations per arm")
```

If your bot doesn't have that traffic volume in a reasonable window, either widen the MDE, extend the
test duration, or fall back to the offline simulation-flywheel approach (`llm-simulation-flywheel`)
instead of underpowering a live test.

## Step 3 — Split traffic and hold the line

- Randomize by **user/session ID**, not per-message — a user must see one variant for the whole conversation, or context contamination invalidates the comparison.
- Never peek-and-stop early on a favorable p-value ("optional stopping") — it inflates false-positive rate well above the nominal 5%. Pre-register the sample size or use a sequential-testing method (e.g. always-valid p-values) if you need early stopping.
- Log which variant served each conversation alongside the outcome metric for later analysis.

## Step 4 — Significance testing (pick by metric type)

| Metric type | Test | Notes |
|---|---|---|
| Binary (completed / not, thumbs up/down) | Two-proportion z-test or chi-square | Standard for conversion-style metrics |
| Ordinal (1–5 judge score) | Mann-Whitney U / Wilcoxon rank-sum | Don't assume normality on bounded Likert-style scores |
| Continuous (latency, token count) | Welch's t-test | Use Welch's (unequal variance), not Student's, by default |
| Multiple guardrail metrics checked together | Bonferroni correction | Divide alpha by number of metrics tested to control family-wise error rate |

```python
from scipy.stats import mannwhitneyu

control_scores = [...]    # per-conversation judge scores, variant A
treatment_scores = [...]  # per-conversation judge scores, variant B
stat, p_value = mannwhitneyu(control_scores, treatment_scores, alternative='two-sided')
significant = p_value < 0.05
```

## Step 5 — Rollout gate

```
p < 0.05 on primary metric AND treatment is better
  AND no guardrail metric regressed beyond its own threshold
  → ship treatment to 100%
p < 0.05 AND treatment is worse
  → kill treatment, keep control
p >= 0.05
  → inconclusive: extend test (if traffic allows) or treat as no-difference and pick on secondary grounds (cost, latency)
```

Document the decision (metric, p-value, sample size, guardrail status) in the release notes — this
becomes the audit trail for "why did we change the prompt."

## Distinct from other skills

- `deepeval-llm-cicd` — offline CI unit tests on a golden dataset, pre-merge. This skill is post-merge, live-traffic validation.
- `llm-judge-bias` — how to make a single LLM-as-judge scorer reliable. This skill uses that scorer's output as the A/B metric.
- `llm-simulation-flywheel` — synthetic conversation simulation when you don't have live traffic volume to A/B test with.
- `conversion-funnel-audit` — general web funnel A/B testing, not LLM-response-specific statistics.

## Sources
- A/B testing methodology, MDE, sample size for LLM chatbots: https://lotuslabs.medium.com/a-b-testing-for-llms-measuring-ai-impact-using-business-metrics-173b4c00cff0
- A/B testing AI chatbot responses best practices 2026: https://www.magicsuite.ai/blog-articles/ab-testing-ai-chatbot-responses-best-practices-2026
- Statistical significance testing for LLM comparison (Wilcoxon, chi-square, Bonferroni): https://medium.com/ai-simplified-in-plain-english/a-b-testing-openai-llms-a-methodology-for-performance-comparison-5a9fc9250306
