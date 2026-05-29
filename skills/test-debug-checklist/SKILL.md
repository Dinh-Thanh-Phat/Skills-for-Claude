---
name: test-debug-checklist
description: Quick stop-and-diagnose checklist when a single test fails — prevent jumping to fixes without evidence. Use as a quick reference when debugging one specific failing test. Triggers on: "test fail", "debug test", "why test", "test not passing", single test failure scenarios.
---

# Test Debug Checklist — Stop & Diagnose

> **Cross-ref:** Pair with `playwright-diagnosis-first` (full workflow with hypothesis
> phase) and `test-failure-triage` (batch-categorize many failures). This file is the
> quick **single-test** checklist; the others are the full diagnosis flow + the batch
> triage flow. `test-diagnosis-before-code` covers diagnosis BEFORE writing tests.

**When a test fails, use this checklist BEFORE writing any code.**

## ⚠️ STOP — Don't code yet!

- [ ] Read the full error message (not just first line)
- [ ] Did I jump to "it's a race condition" without evidence? STOP
- [ ] Did I plan to add `waitFor()` without checking screenshot? STOP
- [ ] Did I plan to increase timeout without understanding why? STOP

## Phase 1: Gather Evidence (2 min)

- [ ] **Screenshot**: Open `test-results/[test-name]/test-failed-1.png`
  - Is the element visible on page? YES/NO
  - Is the element there but hidden? YES/NO
  - Is there an error message? YES/NO

- [ ] **Video**: If screenshot unclear, open video
  - When does failure happen? (start/middle/end?)
  - Does element appear then disappear? YES/NO
  - Does element never appear? YES/NO

- [ ] **Test code**: Read the full test
  - What does `beforeEach` do? (setup, navigation, data)
  - What element is being clicked/checked?
  - What does the assertion expect?

## Phase 2: Categorize (1 min)

```
Timeout error?
├─ locator.click: Timeout 15000ms
│  └─ Screenshot shows element hidden? → TEST BUG (add wait)
│  └─ Screenshot shows element missing? → SYSTEM BUG (don't fix)
│
└─ locator.waitFor: Timeout 10000ms
   └─ Element never appears → SYSTEM BUG (don't fix)

Assertion failed?
├─ expect(X).toBe(Y) but got Z
│  └─ Is test logic correct? → SYSTEM BUG (don't fix)
│  └─ Is test logic wrong? → TEST BUG (fix test)
│
└─ expect(element).toBeVisible()
   └─ Screenshot shows hidden? → TEST BUG (add wait/visibility)
   └─ Screenshot shows missing? → SYSTEM BUG (don't fix)

Element not found?
├─ Timeout finding element
│  └─ Wrong selector (matches something else)? → TEST BUG (fix selector)
│  └─ Element doesn't exist? → SYSTEM BUG (don't fix)
```

## Phase 3: Verify (if still unsure)

- [ ] Open trace viewer: `npx playwright show-trace test-results/[test]/trace.zip`
  - Scrub to exact failure moment
  - Inspect DOM: Does element exist?
  - Check console: Any errors?

- [ ] Run test in isolation: `npx playwright test --grep "^Test Name$"`
  - Passes alone? → State ripple issue (previous test left bad state)
  - Fails alone? → Inherent test bug

## Phase 4: Apply Fix (ONLY if TEST BUG confirmed)

✅ Fix these:
- [ ] Add `await btn.waitFor({ state: 'visible', timeout: 10_000 })`
- [ ] Improve selector (add filter, use context)
- [ ] Fix test logic (assertion or setup)

❌ Don't fix these:
- [ ] Element never appears → SYSTEM BUG
- [ ] Assertion fails on valid action → SYSTEM BUG
- [ ] Data not persisting → SYSTEM BUG

## Phase 5: Verify Fix

- [ ] Run failing test alone → ✅ passes?
- [ ] Run `npx playwright test --last-failed` → ✅ no regressions?

---

## Red Flags — Stop Immediately

🚫 "This is obviously a race condition" (without screenshot)
🚫 "I'll just increase timeout to 30s" (without measuring actual time)
🚫 "Let me add waitFor blindly" (without checking if element exists)
🚫 "The test code looks wrong" (without running full suite to check state)
