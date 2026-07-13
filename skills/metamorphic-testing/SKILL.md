---
name: metamorphic-testing
description: Metamorphic testing — solve the "test oracle problem" (you can't assert an exact expected output) by defining Metamorphic Relations (MRs) between a source input/output and a transformed follow-up input/output, instead of hardcoding expected values. Use for search/ranking, recommendation, sorting/algorithmic, ML/LLM, and REST API systems where correctness is a *relationship*, not a fixed answer. Triggers on "test oracle problem", "no expected output to assert against", "metamorphic testing", "metamorphic relation", "MR", "testing non-deterministic output", "testing search ranking", "testing ML model output", "flaky because LLM output changes every run".
---

# Metamorphic Testing

Most test assertions compare actual output to a known expected value. Some systems have no such oracle:
search ranking, recommendation engines, sorting/graph algorithms with many valid outputs, ML models, and
LLM/chatbot responses (non-deterministic by design) can't be asserted against one "correct" string. This is
the **test oracle problem**.

Metamorphic testing sidesteps it: instead of asserting `output == expected`, define a **Metamorphic
Relation (MR)** — a known relationship between a **source** test case's input/output and a **follow-up**
test case's input/output, where the follow-up input is a controlled transformation of the source input.
You assert the *relation* holds, not any specific value.

```
source:    run(input)          → output1
follow-up: run(transform(input)) → output2
assert:    relation(output1, output2)   ← this is what you can actually check
```

## When to reach for this

| Symptom | Reach for |
|---|---|
| "I don't know what the exact output should be, only what's *reasonable*" | Metamorphic testing |
| Need combination coverage across independent input parameters | `pairwise-combinatorial-testing` |
| Need to partition one field's input space (EP/BVA) | `behavioral-coverage-matrix` |
| LLM output correctness via a scoring rubric against a fixed answer | `deepeval-llm-cicd` / `llm-judge-bias` |
| LLM output stability under paraphrased/adversarial input | this skill (see LLM section) — complements, doesn't replace, `llm-judge-bias` |

Not a replacement for oracle-based tests where you *do* know the exact expected value — use it specifically
where the oracle problem exists.

## Core relation types

| Relation | Meaning | Example |
|---|---|---|
| **Equivalence** | Semantically-equivalent input → same/equivalent output | `"houses in Vancouver"` and `"Vancouver houses"` return the same result set |
| **Monotonicity** | A "narrower" input → output that's a subset (or ≤ count) | If query B implies query A, `count(B) ≤ count(A)` |
| **Invariance under permutation** | Reordering input elements → same output (for order-independent ops) | Shuffle a list, then sort it → same sorted result as sorting the original |
| **Additive/scaling** | Scaling input by k → output scales predictably | Double every price in a cart → subtotal doubles |
| **Idempotence** | Applying the transform twice → same as applying once | Re-running a dedup pass twice yields the same result as running it once |

## Step 1 — Find MRs for your system

Don't invent MRs from nothing — look for operations where you can predict a *relationship* even without
knowing the exact output:

- **Search/query systems**: pagination consistency (`total_results` must not change when you only change
  `page_size`), narrower-query-implies-fewer-or-equal-results, synonym queries return overlapping result sets.
- **Sorting/graph algorithms**: shuffle-then-sort produces the same sorted output; reversing input to a
  min-finder should not change the minimum found.
- **REST APIs**: two requests with the same filter but different pagination sizes should report the same
  total count (this exact bug was found in Spotify's and YouTube's public Web APIs by researchers who
  catalogued 20 and 40 MRs respectively for those two APIs).
- **ML/recommendation models**: adding a small amount of noise to an image shouldn't flip a classification
  with high confidence margin; permuting the order of feature columns in a tabular model shouldn't change
  the prediction.

## Step 2 — Implement as a source/follow-up pair, not a fixed assertion

```python
# REST API example: pagination-size MR (catches an off-by-one/double-count bug)
def test_pagination_total_count_is_stable(api_client):
    source = api_client.search(query="jazz", page_size=20)
    follow_up = api_client.search(query="jazz", page_size=50)

    assert source["total_results"] == follow_up["total_results"], (
        f"total_results changed with page_size: {source['total_results']} vs {follow_up['total_results']}"
    )
```

```python
# Sorting algorithm example: permutation invariance
import random

def test_sort_is_permutation_invariant(sort_fn):
    source_input = [5, 3, 8, 1, 9, 2]
    source_output = sort_fn(source_input)

    follow_up_input = source_input.copy()
    random.shuffle(follow_up_input)
    follow_up_output = sort_fn(follow_up_input)

    assert follow_up_output == source_output
```

## LLM / chatbot metamorphic testing

LLM outputs are non-deterministic, so exact-string oracles don't work at all — this is the strongest fit
for metamorphic testing in this repo's domains. Define MRs over **paraphrase and structural invariance**
instead of exact text:

- **Paraphrase invariance**: semantically-equivalent rephrasing of a user question → same factual claims /
  same final decision (e.g. approve/deny) in the response, even though wording differs. Score with an
  LLM-judge for claim overlap rather than string match — this is where this skill hands off to
  `llm-judge-bias`'s calibrated judge.
- **Order invariance for multi-turn context**: presenting the same set of facts to the model in a different
  order within the prompt shouldn't flip the final answer for extractive/decision tasks.
- **Monotonic confidence**: adding more supporting evidence to a RAG context shouldn't decrease the model's
  stated confidence or reverse an affirmative answer to a negative one.
- **Fairness/robustness MRs**: swapping a demographic attribute (name, pronoun, nationality) that is
  irrelevant to the task should not change a decision outcome (loan approval, resume screen) — this is the
  standard technique researchers use to surface intersectional bias in LLMs; treat any relation violation
  as a defect, not noise.

MORTAR (Multi-turn Metamorphic Testing for LLM-based Dialogue Systems) is the current published approach
specifically for multi-turn chatbots: it infers candidate MRs from a dialogue schema, then generates
follow-up turns automatically and checks the relation holds across the conversation, rather than requiring
every MR to be hand-written.

```python
# LLM paraphrase-invariance MR (decision-task example: loan approval bot)
def test_paraphrase_invariance_loan_decision(chatbot, llm_judge):
    source_reply = chatbot.ask("Can I get approved for a $10,000 personal loan with a 680 credit score?")
    followup_reply = chatbot.ask("I have a 680 credit score — would a $10k personal loan get approved?")

    source_decision = llm_judge.extract_decision(source_reply)      # -> "approve" | "deny" | "unclear"
    followup_decision = llm_judge.extract_decision(followup_reply)

    assert source_decision == followup_decision, (
        f"paraphrased question flipped the decision: {source_decision} vs {followup_decision}"
    )
```

```python
# LLM fairness MR — swap an irrelevant demographic attribute, decision must not change
def test_fairness_name_swap_resume_screen(screening_bot, llm_judge):
    resume_a = build_resume(name="Emily Johnson")
    resume_b = build_resume(name="Lakisha Washington")   # identical resume, different name

    decision_a = llm_judge.extract_decision(screening_bot.screen(resume_a))
    decision_b = llm_judge.extract_decision(screening_bot.screen(resume_b))

    assert decision_a == decision_b, "screening decision changed with name only — bias signal"
```

## Anti-patterns

```
❌ Writing MRs for systems that already have a clean oracle — if you know the exact expected output, just
   assert it directly; metamorphic testing adds indirection without benefit there.
❌ Treating a single MR violation on LLM output as automatically a bug — non-determinism means you may need
   to run each side of the relation N times and compare distributions/majority vote, not one-shot compare.
❌ Picking transforms that aren't actually input-preserving for the relation you're asserting (e.g. a
   "paraphrase" that subtly changes the question's meaning) — verify the transform is semantically neutral
   before trusting a relation violation as a real defect.
❌ Only testing MRs in isolation — combine with `pairwise-combinatorial-testing` when the source input has
   multiple independent parameters, so you're not blind to interaction bugs the MR alone won't surface.
```

## Sources
- [Metamorphic Relation Patterns for Query-Based Systems (Spotify/YouTube MR catalogue)](https://personal.us.es/sergiosegura/files/papers/segura19-met.pdf)
- [Metamorphic Testing of RESTful Web APIs](https://javiertroyauma.github.io/publications/TSE2017_REST_prePrint.pdf)
- [Metamorphic Testing in a Nutshell](https://kenluck2001.github.io/blog_post/metamorphic_testing_in_a_nutshell.html)
- [Metamorphic Relation Generation: State of the Art and Research Directions (ACM TOSEM)](https://dl.acm.org/doi/10.1145/3708521)
- [Bidirectional Empowerment of Metamorphic Testing and Large Language Models: A Systematic Survey](https://arxiv.org/pdf/2605.13898)
- [MORTAR: Multi-turn Metamorphic Testing for LLM-based Dialogue Systems](https://arxiv.org/abs/2412.15557)
