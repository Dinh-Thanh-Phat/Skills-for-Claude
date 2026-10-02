---
name: expensive-irreversible-ops
description: "⚠️ P0 — Before automating any action that costs money (AI credits/API quota), publishes externally (real social post/email/SMS), or creates data with no known delete path, STOP and de-risk first. Use BEFORE running tests that trigger AI generation, real publishing, paid APIs, or create accounts/agents/records. Triggers on: AI generation test, RUN_GEN, create agent, publish post, real posting, costs credit, generate image, send email/SMS, paid API, irreversible."
priority: P0
type: qa-practice
triggers:
  - "AI generation test"
  - "tạo bài thật"
  - "đăng thật"
  - "tốn credit"
  - "costs credit"
  - "publish post"
  - "real posting"
  - "RUN_GEN"
  - "create agent"
  - "generate image"
  - "paid API"
  - "irreversible"
---

# Expensive / Irreversible Operations — P0

## Why this exists (a real, costly mistake)

In one session I ran an AI-generation test ~4 times to "validate" it. Generation
time was wildly variable (one run 30s, later runs hung >4 min). Most runs failed,
**burning the user's AI credits for nothing**, and each run **created a test agent
I could not delete** (its delete control was un-automatable). Result: wasted money +
piled-up orphan data the user had to clean by hand.

The mistakes: (1) treated an expensive, side-effecting op like a cheap test I could
retry; (2) created data before confirming I could delete it; (3) kept retrying after
the first failure instead of stopping.

## The Three Laws

### 1. Verify the teardown BEFORE creating the data
Before any test creates an entity (agent, account, record, real post), **prove the
cleanup path works first** — delete one manually-created instance via the same code
the teardown will use. If you cannot delete it programmatically, **do not create it
in an automated loop**. Data you can't delete is a leak, not a test.

```
NEVER: write create-test → run repeatedly → "I'll figure out cleanup later"
ALWAYS: confirm delete works → then create → assert → delete in afterAll/globalTeardown
```

### 2. One validated run — never a retry loop
For credit/quota/real-publish/irreversible ops:
- Set `retries: 0` for that test (e.g. `test.describe.configure({ retries: 0 })` in its describe,
  overriding the CI default of 1). A failed expensive op must NOT auto-retry.
- Run it **once**. If it fails, **diagnose from artifacts** (screenshot/trace/log) —
  do **not** "just run it again". Each re-run spends real money and may leave debris.
- If the failure is environmental (slow AI, quota exhausted), STOP and report —
  see `warn-environment-factors`. Do not keep paying to discover the same thing.

### 3. Gate it and warn+consent every time
- Keep these tests behind an env flag (`test.skip(!process.env.RUN_GEN, ...)`).
- Before the first run, state plainly: **what it costs, what it publishes, and that
  it is irreversible** — get explicit consent (this combines with
  `warn-environment-factors`). Consent for one run is not consent for a retry loop.

## Decision gate (run this before executing)

```
Does this action cost money / publish externally / create undeletable data?
   NO  → normal test, proceed.
   YES → 1. Is the teardown proven to work?           no → STOP, solve cleanup first
         2. retries == 0 for this test?               no → set it
         3. Did I warn + get consent for THIS run?    no → ask first
         4. Run ONCE. Failed? → diagnose, don't rerun. Environmental? → stop & report.
```

## Red-flag thoughts (you are about to waste money)

| Thought | Reality |
|---|---|
| "Let me just run it again to see" | Each run costs real credit. Diagnose the artifact instead. |
| "I'll clean up the test agents later" | If you can't delete them now, you won't be able to later. Solve cleanup first. |
| "The timeout was too short, rerun" | Maybe — but verify generation actually completes manually before re-spending. |
| "It worked once, the retry will too" | Variable backends: 30s once, >4 min next. One green run ≠ reliable. |

## Related
- `warn-environment-factors` (P0) — warn before env/cost-affected runs.
- `test-data-lifecycle` / `test-data-lifecycle-strategy` — cleanup strategies.
- `ask-when-stuck` (P0) — stop after 1–2 failures; don't loop.
- `synthetic-click-limits` — when the delete control itself can't be automated.
