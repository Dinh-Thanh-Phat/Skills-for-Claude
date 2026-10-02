---
name: playwright-diagnosis-first
description: Systematic Playwright test failure diagnosis workflow — diagnose before fixing, avoid premature fixes. Use when any test fails or is flaky. Triggers on: "test fail", "test flaky", "debug test", "why test failing", "test timeout", any test failure scenario.
---

# Playwright Test Diagnosis-First Workflow

**Golden Rule**: Diagnosis BEFORE fixes. Understand root cause, not just symptoms.

> The moment you attribute a cause ("it fails **because** X"), switch to [[bug-repro-isolation]]:
> change one variable at a time and run the control before naming X. A symptom you observed is
> not yet a mechanism you confirmed.

## Phase 1: Gather Evidence (NO FIXES YET)

### Step 1.1: Collect Error Artifacts
```
✓ Full error message (exact timeout/assertion/selector)
✓ Test name + line number
✓ Pass/fail/flaky status + retry behavior
✓ Timing data (first run vs retry duration)
✓ Screenshot from test-results/
✓ Video from test-results/
✓ DOM state from trace viewer
```

**Why**: Screenshots + videos reveal what's ACTUALLY on page, not what code assumes.

### Step 1.2: Read Test Code (CRITICAL)
```typescript
// DO THIS FIRST
- Read the full test, not just failure point
- Understand setup (beforeEach, fixtures, data)
- Identify what test EXPECTS vs what assertion CHECKS
- Check if selector assumptions match actual HTML structure
```

### Step 1.3: Categorize Failure Type

| Error Type | Key Indicators | Likely Root Cause |
|-----------|---|---|
| **Race Condition** | First run timeout (20s+), retry passes (5s) | Missing/insufficient wait |
| **Missing Element** | `locator.waitFor: Timeout` after explicit wait | Feature not implemented — SYSTEM BUG |
| **Wrong Selector** | Element found sometimes, not others | Selector too generic or fragile |
| **Assertion Failed** | `expect(X).toBe(Y)` but received Z | Feature works differently — SYSTEM BUG |
| **Network Timeout** | Fails after API calls, not UI interactions | API/backend issue — SYSTEM BUG |
| **State Issue** | Passes alone, fails in sequence | Test isolation problem |

**Critical Distinction**:
- Race condition + retry passes = TEST BUG (fix with proper wait)
- Element never appears even with wait = SYSTEM BUG (leave as-is)
- Assertion fails on valid submission = SYSTEM BUG (leave as-is)

### Step 1.4: Look at Test Run Context
```
- Which test ran BEFORE the failure?
- Are there skipped tests that should run?
- Does failure occur only when tests run together?
- Does single test pass in isolation?
```

## Phase 2: Form Hypothesis

```
IF pattern matches:
  "first run timeout 20s, retry passes 4s"
  AND timing improves on retry
  THEN hypothesis = "race condition / missing wait"

IF pattern matches:
  "locator.waitFor: Timeout 10s exceeded"
  AND element still not found after explicit wait
  THEN hypothesis = "system bug - feature not rendered"

IF pattern matches:
  "assertion failed: expected false, received true"
  AND logic looks correct in test
  THEN hypothesis = "system bug - feature behavior differs from spec"
```

## Phase 3: Verify Hypothesis (Before Any Code Changes)

### Option A: Visual Inspection
```
1. Open test-results/[test-name]/test-failed-1.png
2. Does the element exist on the page?
   - YES + hidden = race condition (fix with wait)
   - NO = system bug (don't fix test)
```

### Option B: Trace Viewer (Most Reliable)
```bash
npx playwright show-trace test-results/[test-name]/trace.zip
```
- Scrub timeline to exact failure moment
- Inspect DOM at that instant
- See if element exists, is visible, has expected text

### Option C: Run Test in Isolation
```bash
npx playwright test --grep "^Test Name$"
```
- Does it pass alone? → state ripple issue (previous test left bad state)
- Does it fail alone? → inherent test bug

## Phase 4: Apply Fix ONLY if Test Bug Confirmed

✅ **Fix these** (TEST BUGS):
- Missing `waitFor({ state: 'visible' })`
- Insufficient timeout for legitimate async operation
- Selector too generic (add filter/context)
- State not cleaned up properly between tests

❌ **DON'T fix these** (SYSTEM BUGS):
- Element never appears even after explicit wait → feature not implemented
- Assertion fails on valid user action → validation not enforced
- Data not persisted after submit → API/DB issue

## Phase 5: Verify Fix

```
1. Run failing test alone → should pass
2. Run failing test + previous test → should pass
3. Run --last-failed → check no new failures
```

---

## Quick Checklist (For Each Failing Test)

- [ ] Read full error message + test code
- [ ] Categorize: race condition vs missing element vs assertion fail?
- [ ] Look at screenshot + video
- [ ] Open trace viewer and inspect DOM at failure point
- [ ] Form hypothesis: test bug or system bug?
- [ ] Verify hypothesis BEFORE coding
- [ ] Fix ONLY if test bug confirmed
- [ ] Re-run to validate fix

---

## Common Mistakes to Avoid

❌ Assume flaky = race condition without checking if element renders at all
❌ Apply waitFor blindly without knowing what you're waiting for
❌ Fix test code for system bugs that belong in backend
❌ Skip screenshot/video and just read error message
❌ Increase timeout instead of investigating why operation is slow
❌ Make code changes before gathering evidence

---

## Shared-helper failure: when MANY tests fail at the SAME line, fix the helper FIRST

If a whole suite (e.g. 7/7 wizard tests) fails, **do not debug each test**. Look at
the stack: if they all die inside the **same POM method / shared helper / fixture**,
that one helper is the single root cause — fix it once and the suite goes green.

Real example (June 2026): all 7 wizard tests timed out at 30s. Every stack ended in
`AgentWizardPage.continue()`. The bug was one broken locator in that helper
(`.filter({ has: page.locator('visible=true') })` has the wrong semantics — `visible=true` is a
valid engine, but inside `has:` it matches "any visible descendant", not "this element is visible";
use `.filter({ visible: true })` or `Locator.visible()` (v1.63) — and `getByText(/^Continue/)`
didn't match because the link text had leading whitespace/an icon → 0 matches →
`isDisabled()` hung for the full timeout). Fixing `continue()` once turned 7 reds green.

Triage step (do this before touching any test):
```
1. Read the failure stack of 2–3 failing tests.
2. Do they share a final frame (same helper/POM method/locator)?  → fix that helper.
3. Different frames?  → triage individually (see test-failure-triage).
```

Helper-bug smells: a locator that resolves to **0 elements** then an action/assertion
**hangs to timeout**; `^anchored` getByText against text that has whitespace/icons/CSS
`text-transform`; misused pseudo-locators (`visible=true` inside `filter({ has })`); a `.catch(()=>{})` swallowing
the real error. See also `dom-inspect-first` and `safe-locators`.
