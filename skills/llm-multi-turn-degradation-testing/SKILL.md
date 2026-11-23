---
name: llm-multi-turn-degradation-testing
description: >-
  Test whether an LLM chatbot or assistant gets worse when the user gives the task piece by piece
  over several turns instead of all at once. Take a fully specified task, split it into "shards",
  replay it as FULL (one turn), CONCAT (all shards in one turn) and SHARDED (one shard per turn),
  run each many times, and compare best-case score (aptitude) and best-to-worst spread
  (unreliability). Use when a bot passes single-turn evals but users report it "goes off the
  rails" mid-conversation, when gating a prompt or model change for a conversational product, or
  when choosing a recap/restart mitigation. Triggers on: "lost in conversation", "multi-turn
  degradation", "sharded instructions", "underspecified conversation", "chatbot gets worse over
  turns", "premature answer", "aptitude vs unreliability", "single-turn vs multi-turn eval".
---

# LLM Multi-Turn Degradation Testing (Sharded Instructions)

Most chatbot eval sets send one fully specified prompt and grade one answer. Real users rarely talk
that way: they reveal requirements a little at a time. Laban et al. (Microsoft Research and Salesforce,
ICLR 2026) simulated more than 200,000 conversations across 15 LLMs. When the same task was spread over
several turns, every model scored lower, by **39% on average** across six generation tasks. Most of that
loss was **unreliability**, not lost ability: best-case scores fell only slightly (about 15–16%), while the
gap between best and worst runs rose by about **112%**. The main cause: the model **guesses missing details
early, answers too soon, and then keeps building on its own wrong answer**. "When LLMs take a wrong turn,
they get lost and do not recover."

A single-turn eval suite **cannot** catch this. This skill adds the multi-turn counterpart.

## How it differs from neighbouring skills

| Skill | Question it answers |
|---|---|
| `llm-simulation-flywheel` | Does the bot handle realistic, scenario-driven conversations? (open-ended, judged) |
| `agent-eval-multi-trial` | How consistent is the agent across repeated runs? (pass@k / pass^k) |
| `metamorphic-testing` | Does output stay invariant under input transformations? |
| **this skill** | Given the **same information**, does spreading it over turns change the outcome? (controlled A/B with a fixed, gradeable answer) |

This skill is a metamorphic relation with a fixed answer key: FULL and SHARDED carry the same
information, so they should produce the same graded answer. Use `agent-eval-multi-trial` metrics to
report it.

## Step 1 — Build sharded test cases

Start from tasks that already have a **deterministic grader**, such as unit tests, a SQL result match,
an exact tool-call match, a numeric answer, or a checklist. Split each fully specified instruction into
shards:

- **Shard 1** states the high-level intent only, for example "I need a function that validates promo
  codes."
- **Shards 2..n** each add **one** requirement, constraint or data value.
- Together the shards contain **exactly** the information in the original. Nothing is added or dropped.
- No shard depends on the order of later shards. The simulated user may reveal them in any order after
  shard 1.

```json
{
  "task_id": "sharded-promo-007",
  "task": "code",
  "full_prompt": "Write validate_code(code) ... uppercase, 8 chars, ends in a digit, reject 'TEST' prefix",
  "shards": [
    {"shard_id": 1, "shard_text": "Can you write a promo-code validator in Python?"},
    {"shard_id": 2, "shard_text": "Codes are exactly 8 characters."},
    {"shard_id": 3, "shard_text": "They must be uppercase."},
    {"shard_id": 4, "shard_text": "The last character has to be a digit."},
    {"shard_id": 5, "shard_text": "Anything starting with TEST is invalid."}
  ],
  "grader": "pytest tests/test_promo_007.py"
}
```

This schema matches the released `sharded_instructions_600.json`. An LLM can draft the shards, but **a
human must check every case** for information parity. A shard that leaks or drops information
invalidates the comparison.

## Step 2 — Run three conversation types

| Type | What the bot sees | What it isolates |
|---|---|---|
| **FULL** | Original prompt, one turn | Baseline ability |
| **CONCAT** | All shards joined as bullets in one turn | Effect of rephrasing into shards (should be close to FULL) |
| **SHARDED** | Shard 1, then one shard per turn from a simulated user | The multi-turn effect |

If CONCAT ≈ FULL but SHARDED drops, the multi-turn delivery causes the loss, not the shard wording.
If CONCAT also drops, fix the shards before you draw conclusions.

**Simulated user rules (SHARDED):** reveal at most one shard per turn. Answer clarifying questions only
with information from the remaining shards. Never volunteer the full spec. Stop when every shard is
revealed and the bot has made a final answer attempt. **Do not tell the bot that the spec is arriving
incrementally**, because real users don't.

**Grade every assistant turn, not just the last one.** Have a small classifier label each turn as
`answer_attempt`, `clarification` or `other`. Extract and grade answer attempts. This exposes
**premature answers** that arrive before enough shards are known.

## Step 3 — Run each case many times and report two numbers

One run per case is meaningless here because the effect is mostly variance. Run **N ≥ 10** trials per
case per conversation type at your production temperature.

- **Aptitude:** best-case score per case. Use a high percentile such as P90 of the N trial scores so
  that one lucky run doesn't dominate. Average the result over cases.
- **Unreliability:** spread per case, for example P90 − P10 of the trial scores. Average the result
  over cases.

```python
import numpy as np

def aptitude_unreliability(scores_by_case):          # {case_id: [score_trial_1..N]} scores in 0..100
    apt = [np.percentile(s, 90) for s in scores_by_case.values()]
    unr = [np.percentile(s, 90) - np.percentile(s, 10) for s in scores_by_case.values()]
    return float(np.mean(apt)), float(np.mean(unr))

full_apt, full_unr = aptitude_unreliability(results["FULL"])
shard_apt, shard_unr = aptitude_unreliability(results["SHARDED"])
print(f"aptitude  {full_apt:.1f} -> {shard_apt:.1f}")
print(f"unreliab. {full_unr:.1f} -> {shard_unr:.1f}")
```

The percentile choice is an implementation choice for this skill. Keep it fixed across releases so the
numbers stay comparable.

### Release gate (example thresholds — tune per product)

```python
assert shard_apt >= 0.90 * full_apt, "multi-turn aptitude regression"
assert shard_unr <= baseline_shard_unr + 5, "multi-turn unreliability regression vs last release"
```

Gate on **change against the previous release's SHARDED numbers**, not on absolute parity with FULL.
Every model tested showed a gap, so requiring zero gap would block every release.

## Step 4 — Diagnose failing transcripts

Look for these failure behaviors in low-scoring SHARDED runs:

| Symptom in transcript | Meaning | What to try |
|---|---|---|
| Full answer at turn 1–2 with invented defaults | Premature answer attempt | System-prompt rule: ask before assuming when the spec is incomplete; add a clarify-first test |
| Final answer still contains an early wrong guess | Over-reliance on own earlier attempt | Recap or restart (below) |
| Middle-turn constraints missing, first and last present | Loss of middle turns | Recap; keep the conversation state summary in the system/context |
| Answers grow longer each turn and add unrequested assumptions | Answer bloat / verbosity | Length guidance; grade with a "no unrequested features" check |

## Step 5 — Test the mitigations as separate variants

The reference repo includes two agent-side variants. Run them as extra conversation types and keep any
that close the gap without hurting FULL:

- **RECAP:** after the last shard, add one more user turn: "Just to recapitulate, the entire task is:
  <all shards>. Now please complete the task correctly taking all the information into account."
- **SNOWBALL:** each user turn repeats all earlier shards, then adds the new one: "Just to reiterate,
  <shards so far>. Also, <new shard>."

If your product can do it, also test a **restart** variant: when the bot detects a long, revised spec,
it starts a fresh context from a consolidated summary. The paper's practical advice to users is the same
idea: if a conversation goes off track, start a new one with all the information combined.

## Anti-patterns

- **Grading only the last turn.** You miss premature answers, which are the main signal.
- **N = 1 per case.** The effect is variance, so one run gives you noise.
- **Open-ended tasks without a deterministic grader.** An LLM judge's own variance hides the
  unreliability you are trying to measure. Start with code, SQL, tool calls or math.
- **Shards that add hints** ("remember to also check..."). They break information parity and flatter
  SHARDED.
- **Using the research harness as-is in production gating.** Its README says it is a research tool. Port
  the method into your own eval runner and graders.

## Sources

- Laban, Hayashi, Zhou, Neville — "LLMs Get Lost In Multi-Turn Conversation" (ICLR 2026): https://arxiv.org/abs/2505.06120 · https://iclr.cc/virtual/2026/oral/10009147
- Microsoft Research project page: https://www.microsoft.com/en-us/research/?p=1139409
- Reference implementation, MIT license (`simulator_full.py`, `simulator_sharded.py`, `simulator_recap.py`, `simulator_snowball.py`, `data/sharded_instructions_600.json`): https://github.com/microsoft/lost_in_conversation
- Follow-up applying the method to RAG: "Lost in Conversation or Lost in Translation? Diagnosing Multi-Turn Degradation in RAG": https://arxiv.org/pdf/2609.36700
