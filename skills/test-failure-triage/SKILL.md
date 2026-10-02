---
name: test-failure-triage
description: Batch triage all test failures at once — categorize into test bugs vs system bugs before fixing anything. Use when a test suite has multiple failures and you need to categorize them all before starting fixes. Triggers on: "multiple test fail", "test suite fail", "triage failures", "categorize test failures", "10 fail", "N tests failing".
---

# Test Failure Triage — Quick Decision Tree

When you see N failing tests, STOP and triage ALL of them before fixing anything.

## Triage Workflow (5 minutes per test)

### For Each Failing Test:

```
┌─ Look at error message
│
├─ Is it a TIMEOUT?
│  ├─ "locator.click: Timeout 15000ms"
│  │  └─> Check: Does element appear in screenshot?
│  │      YES + hidden = TEST BUG (wait issue)
│  │      NO = SYSTEM BUG (feature not rendered)
│  │
│  └─ "locator.waitFor: Timeout 10000ms"
│     └─> Element was waited for explicitly but never appeared
│         = SYSTEM BUG (feature not implemented)
│
├─ Is it an ASSERTION FAILURE?
│  ├─ "Expected false, Received true"
│  │  └─> Check: Does test logic look correct?
│  │      YES = SYSTEM BUG (feature works differently)
│  │      NO = TEST BUG (test logic wrong)
│  │
│  └─ "Expect text 'X' to be visible"
│     └─> Check screenshot: Is text there?
│         YES + hidden = TEST BUG (wait/visibility issue)
│         NO = SYSTEM BUG (feature not creating expected data)
│
├─ Is it ELEMENT NOT FOUND?
│  ├─ "element(s) not found"
│  │  └─> Check: Was element supposed to exist?
│  │      YES = SYSTEM BUG (feature not working)
│  │      NO = TEST BUG (selector wrong / setup failed)
│  │
│  └─> Look at screenshot/video
│      └─> Is it rendered in wrong place? TEST BUG (selector too generic)
│          Is it not rendered at all? SYSTEM BUG
│
└─ Look at TIMING PATTERN
   ├─ First run: 20s timeout, Retry: 4s pass
   │  └─> TEST BUG (race condition)
   │
   └─ First run: 10s timeout, Retry: 10s timeout
      └─> SYSTEM BUG (not timing-dependent)
```

## Quick Reference: Error → Category

| Error | Root Cause |
|-------|-----------|
| `TimeoutError: locator.click: Timeout 15000ms exceeded` | Element exists but not visible, or doesn't exist at all? Check screenshot. |
| `TimeoutError: locator.waitFor: Timeout 10000ms exceeded` | Element never appears → **SYSTEM BUG** |
| `expect(locator).toBeVisible() failed` | Element not in DOM or hidden → Check screenshot |
| `Error: element(s) not found` | Wrong selector or feature not implemented → Check screenshot |
| `AssertionError: expected false, received true` | Feature works opposite of test expectation → **SYSTEM BUG** |
| Flaky: First pass fails, second pass succeeds | Race condition → **TEST BUG** |
| Consistent failure across all retries | System bug or wrong selector → Check screenshot |

## Categorization Output

After triage, produce this summary before touching any code:

```
SYSTEM BUGS (test.fail-lock + report to user):
- CMT-002, CMT-003: Button never appears (feature not rendered)
- TC-005: Validation not enforced (expected feature behavior)
- TUG-002: Created item doesn't persist (backend issue)

TEST BUGS (fix with --last-failed):
- TC-001: Missing wait for modal visibility
- TC-003: Selector too generic, matches wrong element

TEST SUITE BUGS (fix with --last-failed):
- ADM-T012: State ripple from previous test not cleaned
- UPD-001: Setup not isolating between tests
```

→ System bugs: `test.fail(true, 'BUG-xxx: [reason]')` + report to user — keep the assertion on the EXPECTED behavior; the test stays green while the bug exists and turns red ("expected to fail but passed") the moment it's fixed → then remove the annotation. Never `test.skip` a known bug — that hides it. Canonical policy: `skip-vs-fail`.
→ Test bugs: fix, then `npx playwright test --last-failed`

## When in Doubt: Check Artifacts (In Order)

1. **Screenshot** — shows exactly what page looks like at failure
2. **Video** — see exact sequence of events
3. **Trace Viewer** — most thorough
   ```bash
   npx playwright show-trace test-results/[test]/trace.zip
   ```
4. **Test Code** — read fully, check selector logic and setup

## Group Failures Before Fixing

When you have >5 failures, group them — many "failures" are actually 1 root cause:

```
By module / spec:    auth.spec×3, dashboard.spec×8 → dashboard is the problem
By first error line: "locator … #submit not found" appearing in 6 tests → single bug
By timing:           all timeouts at exactly 30s → global config issue
By worker:           all from worker-2 → parallel/data-collision issue
By stage:            5 fail in beforeEach → setup is broken, not the tests
```

Fix the root cause first; the cluster of failures should disappear together.

## Infra Failures vs Test Bugs vs System Bugs

| Symptom | Category | Action |
|---|---|---|
| Browser crashed / OOM / "Target page closed" | INFRA | Retry with fewer workers; check memory |
| All tests fail at `beforeEach` (login) | INFRA / TEST | Run `login-verification` first |
| Single test times out, others pass | TEST BUG or SYSTEM | Triage by screenshot |
| Assertion fails on valid action | SYSTEM BUG | Skip + report, do not fix test |
| Test passes alone, fails in parallel | DATA RIPPLE | Add cleanup / isolate data |
| Flaky 1-in-20 with no screenshot | INVESTIGATE | Run `--repeat-each=10` to confirm |

## Critical Rules

🚫 NEVER assume flaky = race condition without checking screenshot first
🚫 NEVER add `waitFor()` before checking if element exists in screenshot
🚫 NEVER increase timeout without understanding what you're waiting for
✅ ALWAYS categorize ALL failures before fixing ANY of them
✅ ALWAYS look at screenshot/video before touching code

---

## Thứ tự invoke khi debug failures

```
N tests fail
     ↓
1. playwright-diagnosis-first  ← chạy TRƯỚC (single test, lấy screenshot/trace)
2. test-failure-triage (này)   ← batch categorize sau khi có data
3. ask-when-stuck              ← nếu sau 2 lần diagnose vẫn chưa rõ root cause
```

**Không** chạy triage trước khi có screenshot/trace — triage không có visual data sẽ chỉ đoán.
