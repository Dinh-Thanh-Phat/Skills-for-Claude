---
name: agent-eval-multi-trial
description: >-
  Run LLM agent and chatbot evals as repeated, isolated trials and report pass@k
  (at least one of k attempts succeeds) or pass^k (all k attempts succeed) instead of a
  single pass/fail snapshot. Also covers splitting capability evals from regression evals,
  treating a 0% task as a broken task, and spotting saturated suites. Use when an agent eval
  flips between runs, when choosing a release-gate metric for a non-deterministic agent, or
  when sizing a first agent eval suite. Triggers on: "pass@k", "pass^k", "pass hat k",
  "multiple trials", "eval flakiness", "non-deterministic agent eval", "capability vs
  regression eval", "eval saturation", "how many times to run an eval".
---

# Agent Eval: Multi-Trial Runs, pass@k and pass^k

An agent that passes a task once may fail the same task on the next run. A single run tells you
almost nothing about a non-deterministic agent. Run every task **n times in isolated trials**,
count successes `c`, and report the metric that matches the product's promise.

## Pick the metric from what the product promises

| Metric | Meaning | Behaviour as k grows | Use for |
|---|---|---|---|
| **pass@k** | P(**at least one** of k attempts succeeds) | Goes up | Tools where one good result is enough and a human or verifier picks it (code suggestions, draft generation, best-of-N with a checker) |
| **pass^k** | P(**all** k attempts succeed) | Goes down | Customer-facing agents and chatbots, where every user conversation must work (support bots, booking agents, anything that takes actions) |

Example: 70% per-trial success gives pass@3 ≈ 97% but pass^3 ≈ 34%. A chatbot release gate
built on pass@k hides exactly the inconsistency users will see. **Default to pass^k for
chatbot/agent release gates.**

## Unbiased estimators (n trials, c successes, k ≤ n)

```python
from math import comb

def pass_at_k(n: int, c: int, k: int) -> float:
    """P(at least one of k sampled trials passes). Chen et al. 2021."""
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)

def pass_hat_k(n: int, c: int, k: int) -> float:
    """P(all k sampled trials pass). tau-bench's pass^k."""
    return comb(c, k) / comb(n, k)

# Suite score = mean over tasks
def suite_score(results: dict[str, tuple[int, int]], k: int, fn=pass_hat_k) -> float:
    return sum(fn(n, c, k) for n, c in results.values()) / len(results)
```

Run `n` ≥ `k` (for example n=8 and report k=1,2,4). Reporting only `c/n` hides the consistency
gap.

## Trial hygiene (otherwise the numbers lie)

- **Isolate every trial.** Use a fresh environment, DB/session state, browser context, sandbox and
  conversation each time. Shared state or a shared rate-limited backend causes *correlated*
  failures and can inflate or deflate the score.
- **Log the full transcript of every trial**, including tool calls. Aggregates alone don't show
  whether a grader is wrong. Read a sample of transcripts from both passes and failures before
  trusting a number.
- **Grade outcomes, not exact paths.** Rigid step-order checks fail valid alternative solutions.
  Give partial credit for multi-part tasks. If the step order really matters for safety, enforce
  it with `llm-agent-trajectory-eval` subset/superset matching instead.
- **Model graders:** calibrate them against human verdicts, give them an explicit "Unknown"
  option, and use one judge per dimension. See `llm-judge-bias`.
- **Make graders hack-resistant.** A trial must pass only by solving the task, never by
  exploiting a loophole in the checker.

## Capability suite vs regression suite

| | Capability eval | Regression eval |
|---|---|---|
| Expected pass rate | Low at first: a hill to climb | ~100% |
| Purpose | Measure progress on hard or new behaviour | Catch breakage of what already works |
| CI role | Trend dashboard, non-blocking | **Blocking gate** (pass^k threshold) |
| Lifecycle | Tasks **graduate** into regression once reliably solved | Grows from graduated tasks + real production failures |

## Diagnosing the suite itself

- **0% across many trials** usually means a broken task (ambiguous spec, wrong reference, impossible
  environment), not an incapable agent. Ask whether a domain expert would independently reach the
  same verdict, and fix the task first.
- **Balanced sets:** include tasks where the behaviour *should not* happen (should refuse, should
  not call a tool, should escalate), not only where it should. Otherwise you optimize one way.
- **Saturation:** when nearly every solvable task passes, the score stops showing improvement.
  Add harder tasks, and don't read anything into a flat high score until transcripts are
  reviewed.
- **Start small:** 20–50 tasks taken from real failures and manual QA checks beat waiting for a
  perfect 500-task set. Treat the suite as a living artifact with an owner.

## Minimal CI gate (pytest)

```python
import pytest

N_TRIALS, K, GATE = 8, 4, 0.90

@pytest.mark.parametrize("task", REGRESSION_TASKS, ids=lambda t: t.id)
def test_regression_task_is_consistent(task):
    c = sum(grade(task, run_agent_in_fresh_env(task)) for _ in range(N_TRIALS))
    score = pass_hat_k(N_TRIALS, c, K)
    assert score >= GATE, f"{task.id}: {c}/{N_TRIALS} passed, pass^{K}={score:.2f}"
```

Cost scales with `n`. Run the full n on the regression gate nightly or pre-release, and use a
smaller n on PRs.

## Relationship to other skills

- `deepeval-llm-cicd`: wires metrics into CI. Use this skill to decide *how many runs and which
  aggregate* gate the build.
- `llm-agent-trajectory-eval` / `llm-agent-trace-eval`: what to grade in one trial (path or
  spans). This skill covers how to aggregate across trials.
- `llm-golden-dataset-construction`: where tasks come from.
- `test-rerun-discipline` / `flaky-test-prevention`: the deterministic-test counterpart. Do not
  "retry until green" on agent evals. Count the failures into pass^k instead.

## Sources
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents (Anthropic Engineering, "Demystifying evals for AI agents": pass@k vs pass^k, trial isolation, capability vs regression, saturation, grader calibration)
- https://arxiv.org/abs/2107.03374 (Chen et al. 2021, unbiased pass@k estimator)
- https://arxiv.org/abs/2406.12045 (τ-bench, pass^k consistency metric for tool-using agents)
- https://www.ibm.com/think/topics/ai-agent-testing (test for variance across runs rather than single snapshots)
