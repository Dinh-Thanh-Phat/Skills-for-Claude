---
name: llm-golden-dataset-construction
description: >-
  Use when building, sizing, or maintaining the golden/eval dataset that other LLM testing
  techniques (DeepEval CI gates, hallucination detection, A/B rollout gates) run against —
  sourcing examples from production logs, schema design, avoiding few-shot/eval leakage,
  versioning, and a weekly upkeep routine. Triggers on: "golden dataset", "eval dataset", "gold
  set", "how many examples for LLM eval", "curate LLM test cases", "eval set data leakage",
  "few-shot leakage".
---

# LLM Golden Dataset Construction

Every other LLM testing skill in this repo (`deepeval-llm-cicd`, `llm-hallucination-detection`, `llm-chatbot-ab-testing`, `llm-agent-trace-eval`) assumes a "golden dataset" already exists and runs metrics against it. This skill covers building and maintaining that dataset itself — the reference collection of `(input, expected_output/rubric, context)` triples that all downstream evals compare against.

A golden dataset is different from `llm-simulation-flywheel`'s synthetic conversations: it's hand-checked and static (a trusted baseline for regression detection), not dynamically generated per run. Use both — the golden set catches known regressions cheaply; the simulation flywheel finds novel ones.

## Sizing — start small, grow with the product

| Stage | Size | Purpose |
|---|---|---|
| Early iteration (prompt/model tweaks) | 10–20 examples | Fast enough to eyeball every run |
| Product stabilizing | 100–200 diverse examples | Covers main intents + edge cases |
| Mature production system | 500–1000+ examples | Statistical signal across intents, personas, adversarial inputs |
| Specialized/regulated domain (medical, legal, finance) | 1000+, reviewed by domain experts | Compliance-grade coverage |

Don't wait for "enough" examples before starting — a 15-example set that runs on every PR beats a theoretical 500-example set that never gets built.

## Sourcing — production logs beat synthetic-only

Curating real production failures into the golden set measurably outperforms synthetic-only sets (one study found production-derived cases improved real-world task performance ~34% over synthetic-only). Sourcing priority:

1. **Production failure logs** — mine support escalations, thumbs-down feedback, and low-confidence-score conversations first. These are the regressions you already know matter.
2. **Persona/intent coverage** — deliberately fill gaps: one golden example per (intent × user persona × difficulty tier), not just whatever showed up in logs.
3. **Adversarial/edge cases** — ambiguous phrasing, contradictory context, out-of-scope requests (feed confirmed ones from `llm-red-teaming` / `ai-chaos-testing` runs back into the golden set as regression cases, not just one-off red-team findings).
4. **Synthetic fill-in** — only after 1–3 are covered, use an LLM to generate remaining coverage gaps (topics/languages/difficulty combinations you can enumerate but haven't seen naturally).

Raw production logs are not evaluation data until annotated: each mined example needs a human (or a calibrated LLM-judge per `llm-judge-bias`) to assign the expected output/label — don't skip straight from "interesting log line" to "golden example."

## Schema — minimum viable fields

```json
{
  "id": "refund-policy-ambiguous-001",
  "input": "Can I get a refund after 45 days if the item was defective?",
  "context": ["Return policy: 30 days for unused items, 90 days for defective items."],
  "expected_output": "Yes — defective items have a 90-day window, so this qualifies.",
  "rubric": "Must cite the 90-day defective-item exception, not the 30-day general policy.",
  "category": "policy-qa",
  "persona": "frustrated-returning-customer",
  "difficulty": "edge-case",
  "source": "production-escalation-2026-06-14",
  "added": "2026-06-20"
}
```

`rubric` matters more than `expected_output` for open-ended generation — an LLM-judge grades against the rubric, not exact string match. `category`/`persona`/`difficulty` let you slice pass rates (see `deepeval-llm-cicd`) instead of one aggregate score that hides which segment regressed.

## Avoiding leakage — the failure that invalidates your whole eval

**Few-shot leakage**: if an example (or a near-duplicate) sits in your prompt's few-shot block AND in the golden set, the model has literally seen the answer — the eval score is meaningless for that case. Keep few-shot examples and golden-set cases in strictly separate, non-overlapping pools; check new prompt few-shot additions against the golden set before merging.

**Training-data leakage**: for fine-tuned models, screen golden examples against the fine-tuning corpus for verbatim or near-verbatim overlap. Re-check whenever the fine-tuning or prompting setup changes, not just once at dataset creation.

## Versioning

Treat the golden dataset as versioned code, not a spreadsheet that mutates silently:
- Commit it (JSON/YAML/CSV) alongside the eval code, not in a separate untracked location.
- Tag/branch the dataset version alongside the prompt/model version being tested — a regression means "output changed," not "the eval set changed under you."
- Diff dataset changes in PR review like you'd review a test-code change — a case someone silently deleted is a coverage regression.

## Weekly upkeep routine

A golden dataset decays if untouched — prompts drift, policies change, product surface grows. Light recurring routine:

1. **Add** real failures from the past week's production logs (see sourcing above).
2. **Review** labels/rubrics for cases affected by any policy or product change that week.
3. **Prune** cases that test behavior you've intentionally removed — a stale case that now correctly fails is a false regression signal, not real coverage.
4. **Re-check leakage** whenever the prompting or fine-tuning setup changed that week.

## Where this plugs in

| Downstream skill | How it consumes the golden dataset |
|---|---|
| `deepeval-llm-cicd` | Parametrized pytest CI gate iterates the golden set on every PR |
| `llm-hallucination-detection` | Nightly `HallucinationMetric` suite runs against it |
| `llm-chatbot-ab-testing` | Pre-rollout offline gate before a variant reaches live traffic |
| `llm-judge-bias` | Human-calibration pass uses a golden-set sample to compute Cohen's Kappa |
| `llm-simulation-flywheel` | Complementary, not a replacement — simulation finds novel failures; golden set catches known ones cheaply |

## Sources
- https://www.getmaxim.ai/articles/building-a-golden-dataset-for-ai-evaluation-a-step-by-step-guide/
- https://qaskills.sh/blog/golden-dataset-llm-evaluation-guide
- https://arize.com/resource/golden-dataset/
- https://klu.ai/glossary/golden-dataset
- https://futureagi.com/glossary/llm-regression-testing/
- https://galileo.ai/blog/beyond-golden-datasets-static-evals-failures
