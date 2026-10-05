---
name: mutation-testing-stryker
description: >-
  Mutation testing for JavaScript/TypeScript with StrykerJS — validates that tests actually catch
  bugs (not just cover lines). Use when you want to measure test suite quality beyond code
  coverage, find tests that pass but never fail, set up incremental mutation CI for PRs, or use
  an AI agent to kill surviving mutants. Triggers on: "mutation testing", "Stryker", "mutation
  score", "surviving mutants", "test quality beyond coverage", "kill mutants", "StrykerJS".
---

# Mutation Testing with StrykerJS

Code coverage tells you which lines run during tests — it does not tell you whether tests would catch a bug. Mutation testing answers the real question: **if I break this code, will the tests fail?**

## How It Works

StrykerJS generates "mutants" — copies of your source with small deliberate changes (flipped conditions, swapped operators, removed statements). Each mutant is run against your test suite:

- **Killed** = tests caught the change ✅
- **Survived** = tests passed despite the broken code ❌ (your tests miss this case)
- **Mutation score** = killed / (killed + survived) × 100%

**Target:** ≥ 80% mutation score. 100% is impractical; 60% indicates major gaps.

---

## Setup

```bash
npm install --save-dev @stryker-mutator/core @stryker-mutator/vitest-runner
# or for Jest:
# npm install --save-dev @stryker-mutator/core @stryker-mutator/jest-runner
```

### ⚠️ Version compatibility (StrykerJS 10, Aug 2026)
- StrykerJS 10 requires **Node.js ≥ 22** (Node 20 dropped — the only breaking change in 10.0.0).
- **Do NOT pair `@stryker-mutator/vitest-runner@10.0.0` with Vitest 5.x.** Vitest 5 joins test names
  with `" > "`, the runner's per-test filter matches nothing, every covered mutant runs 0 tests and is
  reported **Survived** — scores collapse toward 0% (reported 92% → 0%). npm gives no warning (peer is
  `vitest >=2.0.0`). Pin `vitest@^4.1` for mutation runs until a fixed runner ships — track
  [#6210](https://github.com/stryker-mutator/stryker-js/issues/6210) / fix PR
  [#6214](https://github.com/stryker-mutator/stryker-js/pull/6214) (open as of 2026-10-02).
- Sanity check: a score that suddenly drops toward 0 with `testsCompleted: 0` in `mutation.json`
  = this bug, not bad tests. Don't "fix" tests against it.
- New in 10: partial incremental report saved if the run crashes; new empty-expression mutator
  (removes call statements like `foo();`); experimental TypeScript 7 in the typescript-checker; Mocha 12.

```json
// stryker.config.json
{
  "testRunner": "vitest",
  "coverageAnalysis": "perTest",
  "mutate": ["src/**/*.ts", "!src/**/*.spec.ts", "!src/**/*.test.ts"],
  "thresholds": {
    "high": 80,
    "low": 60,
    "break": 60
  },
  "reporters": ["html", "clear-text", "progress"],
  "htmlReporter": { "fileName": "reports/mutation/index.html" }
}
```

```bash
npx stryker run
```

---

## Incremental Mode — CI-Friendly

Running full mutation testing on every commit is too slow. Use incremental mode to only mutate **changed files**.

```json
// stryker.config.json — add:
{
  "incremental": true,
  "incrementalFile": "reports/stryker-incremental.json"
}
```

```bash
# PR pipeline: only mutates changed files
npx stryker run --incremental

# Nightly / weekly: full run to prevent drift
npx stryker run --force
```

**How it works:** Stryker diffs your files against `stryker-incremental.json` (the last saved result) and re-runs only the mutations that could be affected. Full report is still generated — you see the complete picture without paying the full cost.

**Commit `stryker-incremental.json` to source control** so each CI run builds on the previous.

### CI Example (GitHub Actions)

```yaml
- name: Run mutation tests (incremental)
  run: npx stryker run --incremental
  if: github.event_name == 'pull_request'

- name: Run full mutation tests (nightly)
  run: npx stryker run --force
  if: github.event_name == 'schedule'
```

---

## Reading the HTML Report

Open `reports/mutation/index.html` after a run. Key sections:

| Column | Meaning |
|--------|---------|
| **Killed** | Mutant caught — test is effective |
| **Survived** | Mutant not caught — test gap found here |
| **No coverage** | Mutant in uncovered code — dead code or missing tests |
| **Timeout** | Mutant caused infinite loop — usually a logic issue |

Click any survived mutant to see the exact code change that slipped through. That diff is your test-writing prompt.

---

## Killing Survivors — AI-Assisted Workflow

When Stryker reports surviving mutants, writing the missing tests is mechanical. Hand it to an AI agent:

```
Prompt to Claude Code:
"Stryker found 8 surviving mutants in src/utils/pricing.ts.
Here is the diff for each one: [paste Stryker HTML output or --json report].
Write a Vitest test for each surviving mutant that kills it.
Add the tests to src/utils/pricing.spec.ts."
```

**Why this works well for AI:** Each surviving mutant is a precise, isolated bug-shaped hole. The fix is always "add an assertion that breaks when [exact change] is applied." No ambiguity, no design decisions — exactly the mechanical work AI handles best.

### Export survivors as JSON for automation

```bash
npx stryker run --reporters json
# writes reports/mutation.json — parse survivors programmatically
```

```python
import json

report = json.load(open("reports/mutation.json"))
survivors = [
    m for m in report["files"].values()
    for mutant in m["mutants"]
    if mutant["status"] == "Survived"
]
for s in survivors[:10]:
    print(f"{s['location']['start']['line']}: {s['mutatorName']} — {s['replacement']}")
```

---

## Common Mutator Categories

| Mutator | Example change | What it tests |
|---------|---------------|---------------|
| `ArithmeticOperator` | `+` → `-` | Calculation correctness |
| `EqualityOperator` | `===` → `!==` | Boundary conditions |
| `LogicalOperator` | `&&` → `\|\|` | Condition logic |
| `ConditionalExpression` | `a > b` → `true` | Branch coverage |
| `StringLiteral` | `"active"` → `""` | String comparisons |
| `BlockStatement` | removes `{...}` body | Side-effect assertions |
| `OptionalChaining` | `a?.b` → `a.b` | Null-safety handling |

Focus first on survived `EqualityOperator` and `ConditionalExpression` mutants — these reveal missing boundary and branch tests.

---

## Thresholds in CI

```json
"thresholds": {
  "high": 80,   // green badge
  "low": 60,    // yellow badge — warning
  "break": 55   // CI fails if score drops below this
}
```

Start `break` at 55% and tighten by 5% each sprint. Don't jump straight to 80% break — you'll block CI before the team can catch up.

---

## Relationship to Coverage

| Metric | What it measures | Limitation |
|--------|-----------------|-----------|
| Line/branch coverage | Code was *executed* | Doesn't verify assertions |
| Mutation score | Tests actually *detect bugs* | Slower to run |

Use both: high coverage + low mutation score = tests run the code but don't assert anything meaningful.

## Sources

- [StrykerJS v10.0.0 release notes](https://github.com/stryker-mutator/stryker-js/releases/tag/v10.0.0)
- [vitest-runner + Vitest 5 issue #6210](https://github.com/stryker-mutator/stryker-js/issues/6210)
- [StrykerJS — GitHub](https://github.com/stryker-mutator/stryker-js)
- [Incremental Mode Docs — Stryker Mutator](https://stryker-mutator.io/docs/stryker-js/incremental/)
- [Announcing Incremental Mode — Stryker Blog](https://stryker-mutator.io/blog/announcing-incremental-mode/)
- [How to Configure Mutation Testing with Stryker — OneUptime (Jan 2026)](https://oneuptime.com/blog/post/2026-01-25-mutation-testing-with-stryker/view)
- [AI Test Generation and Code Quality Trends 2026 — LaraCopilot](https://laracopilot.com/blog/ai-test-generation-2026/)
