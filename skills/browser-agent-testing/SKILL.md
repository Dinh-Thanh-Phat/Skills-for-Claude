---
name: browser-agent-testing
description: >-
  Test browser-use / computer-use AI agents (Browser Use, Claude Computer Use, OpenAI
  Operator/CUA, and similar autonomous GUI-driving agents) as the system under test — distinct
  from using Playwright/Maestro AI agents as a testing tool. Covers the six-failure-mode taxonomy
  (DOM selector drift, screenshot ambiguity, login state, modal interruptions, rate-limit cliffs,
  irreversibility), the "silent wrong-success" anti-pattern and evidence-based assertion fix, a
  staging-mirror pattern for gating irreversible actions, and why public benchmarks (WebVoyager,
  WebArena) overstate production reliability. Use when QA-testing an autonomous agent that
  clicks/types/navigates a real browser or OS UI on its own, evaluating whether such an agent is
  production-ready, or designing a regression harness for one. Triggers on: "browser-use agent
  testing", "computer-use agent evaluation", "test AI browser agent", "operator agent QA", "GUI
  agent reliability", "agent silent wrong success", "irreversible action agent testing".
---

# Browser-Use / Computer-Use Agent Testing

QA-testing an autonomous agent that **is** the browser operator (Browser Use, Claude Computer Use, OpenAI Operator/CUA, and similar) — not using an AI agent to *write or heal* your Playwright tests. If you're doing the latter, see `playwright-test-agents` or `playwright-mcp-server` instead.

## Why this is a different problem than normal E2E testing

In normal Playwright/Maestro E2E testing, the test script is deterministic and the assertion is the source of truth. Here, the **agent itself decides what to click and when to stop** — so the system under test can fail in ways a scripted test never can: it can complete the wrong task, misjudge success, or take an action nothing can undo. Public agent benchmarks measure happy-path task completion; they do not measure recovery rate per failure mode, which is what determines whether an agent is safe in production. One reported case: a browser agent scored 78% on WebArena but only completed 22% of real production checkouts — the gap between a frozen benchmark and a live page with real rate limits, real modals, and real irreversible buttons.

Also treat WebVoyager-style leaderboard numbers with caution: once several agents cluster above ~90%, the benchmark has saturated and stops discriminating — a high score means "competent," not "best," and definitely not "safe to point at your production checkout."

## The core anti-pattern: silent wrong-success

The single worst failure mode is the agent **believing it succeeded while it validated the wrong thing** — it clicked through to *a* confirmation-looking screen, or completed *a* task, and self-reports success. If your eval trusts the agent's own "I completed the task" claim, you cannot tell this apart from a real success.

**Fix — assert on concrete evidence, never on self-assessment:**
- Exact string match on the confirmation page (order number format, not "contains 'success'")
- The resulting URL (`/orders/{id}/confirmed`, not just "not the cart page anymore")
- A downloaded file's actual content/hash
- A database/API-level state check on the backend the agent doesn't see

Judge the **trace** (the full sequence of tool calls / clicks / DOM snapshots the agent made), not just its final text summary — a healed-looking final screenshot can hide the wrong path taken to get there. Use an LLM-judge panel scoring the trace against expected evidence, rather than letting the agent grade its own run.

## The six failure modes to test for explicitly

| Failure mode | What breaks | How to test it |
|---|---|---|
| **DOM selector drift** | A class rename / aria-label change between runs breaks the agent's element targeting; the rerun looks like a regression when the app didn't actually break | Re-run the same task after a cosmetic-only DOM change (rename a class, don't change behavior) and confirm the agent still completes it — distinguishes "agent is brittle" from "app regressed" |
| **Screenshot ambiguity** | Visually similar elements (two "Confirm" buttons, a disabled vs. enabled state that looks identical in a screenshot) get confused | Include near-duplicate-looking UI states in your task set; assert the agent picked the *enabled*/*correct* one, not just *a* plausible-looking one |
| **Login state** | Agent loses or never establishes an authenticated session mid-task and silently proceeds as a guest, or gets stuck on a login wall it can't solve | Seed an expired/soon-to-expire session in one task variant; confirm the agent detects it and re-authenticates or escalates rather than continuing unauthenticated |
| **Modal interruptions** | Cookie banners, promo pop-ups, or app-update modals block the intended element; agent may fail to notice or fail to close them | Inject an unexpected modal mid-flow in a staging run; score whether the agent detects and dismisses it before continuing |
| **Rate-limit cliffs** | Agent hits a 429 and either retries the identical call into a hard ban, or keeps clicking through the rate-limit interstitial | Stub a `429` on a staging endpoint that fires after N requests. Score 1.0 if the agent detects the 429, backs off with exponential delay or switches to a fallback path, or escalates cleanly to a human; score 0.0 if it hammers the same call or clicks through the interstitial |
| **Irreversibility** | Actions like Submit Order / Confirm Transfer / Send Email / Delete Account have no undo — a wrong click here isn't a test failure, it's a production incident | See dedicated section below — this one needs a structural gate, not just a test case |

## Irreversibility: gate it structurally, don't just hope the eval catches it

An agent that treats "Confirm Delete" with the same confidence threshold as "Next" has no second-order sense of *action reversibility* — this is a distinct failure from the other five because a single miss in a live run is unrecoverable, so testing has to prevent it structurally rather than just score it after the fact:

1. **Staging mirror**: replace every irreversible endpoint (payment capture, delete, send, transfer) with a sandbox/stub in your test environment — never let an agent under test reach the real endpoint.
2. **Rubric-layer gate**: classify each action in your task taxonomy by reversibility up front. For high-risk actions, the passing rubric requires the agent to have **surfaced an explicit confirmation step** to the (simulated) human before executing — not just "task completed," but "task completed *and* asked for confirmation first."
3. **In production**, enforce the guardrail in code at the browser/tool layer (e.g., the automation harness itself refuses to click a selector matching your irreversible-action allowlist without a separate confirm token), not by trusting the agent's prompt instructions alone — prompts are not a safety boundary.

## Minimal test harness shape

```
for each task in task_set:
    run agent against staging (irreversible endpoints stubbed)
    capture: full action trace, final DOM/URL/downloaded-artifact state
    score:
      - completion: does the captured evidence match the expected end-state? (not agent's self-report)
      - trace-cleanliness: any irreversible-classified action taken without a confirmation step? → fail
      - recovery: for tasks with an injected failure mode (429 stub, injected modal, expired session,
        cosmetic DOM change) — did the agent recover, or did it silently fail / silently succeed wrong?
    judge with an LLM-judge panel scoring the trace + evidence, never the agent's own summary alone
report: completion rate AND per-failure-mode recovery rate, separately — a single aggregate
        completion number hides which failure mode is actually unsafe
```

## When to reach for this vs. other skills

| Situation | Skill |
|---|---|
| Testing an autonomous agent that drives a browser/OS UI as the product | This skill |
| Using an AI agent to *generate or heal* your own Playwright test suite | `playwright-test-agents` |
| AI navigating your app ad-hoc via MCP for exploration, not autonomous task completion | `playwright-mcp-server` |
| Scoring an LLM agent's ordered tool-call sequence (not specifically a browser/GUI agent) | `llm-agent-trajectory-eval` |
| Single-agent tool-call/span-level scoring via DeepEval `@observe` | `llm-agent-trace-eval` |
| Supervisor→sub-agent dispatch correctness in a multi-agent system | `llm-agent-handoff-testing` |
| An action in your *own* test automation is expensive/irreversible (not the system-under-test's action) | `expensive-irreversible-ops` |

## Verification note

The primary source (futureagi.com's "Six Failure Modes" article) and several corroborating blogs (qaskills.sh, testmuai.com, browser-use.com's own eval-infrastructure post, asteroid.ai) returned HTTP 403 to the fetcher — consistent with this domain's recurring fetch-blocking pattern noted in prior runs of this log. This skill is sourced from cross-corroborated WebSearch summaries citing those pages plus the peer-reviewed BrowserArena and WebArena benchmark literature, flagged here per the "verify before writing" guardrail rather than a single first-party fetch.

## Sources
- https://futureagi.com/blog/evaluating-browser-use-agents-2026/ (WebSearch summary — direct fetch 403'd)
- https://qaskills.sh/blog/browser-use-ai-agent-testing-guide (WebSearch summary — direct fetch 403'd)
- https://browser-use.com/posts/our-browser-agent-evaluation-system (WebSearch summary — direct fetch 403'd)
- https://asteroid.ai/blog/building-reliable-browser-automation/ (WebSearch summary — direct fetch 403'd)
- https://www.testmuai.com/blog/state-of-ai-browser-agents-2026/ (WebSearch summary — direct fetch 403'd)
- https://arxiv.org/pdf/2510.02418 (BrowserArena: Evaluating LLM Agents on Real-World Web Navigation Tasks)
