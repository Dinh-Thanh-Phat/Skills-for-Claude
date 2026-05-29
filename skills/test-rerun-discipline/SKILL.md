---
name: test-rerun-discipline
description: Prevent unnecessary full-suite re-runs when fixing failing tests. Use whenever fixing test failures, running automation during development, or debugging a test suite. Triggers on: "fix test", "re-run tests", "chạy lại test", "fix failing", "test suite bị fail", "sửa test".
---

# Test Rerun Discipline Skill

## Core Law

> **Never run the full test suite while actively fixing failures.**
> Every unnecessary full run = wasted DB writes + unnecessary cost.

---

## The Anti-Pattern (What Goes Wrong)

```
Test suite has 80 tests, 5 fail
→ Fix test #1 → run all 80 again (75 wasted)
→ Fix test #2 → run all 80 again (75 wasted)
→ Fix test #3 → run all 80 again (75 wasted)
...
Result: 240 unnecessary test executions, DB polluted, high cost
```

---

## The Complete Workflow

### Phase 1: Full run — once, to collect all failures
```bash
npx playwright test
```
Get the full failure list. This is the ONLY full run before fixes are complete.

---

### Phase 2: Batch triage — categorize ALL failures first

Run `test-failure-triage` on all failures at once. Do NOT start fixing until every failure is categorized.

Output two lists:
- **Test bugs** — wrong selector, assertion logic, data setup, etc.
- **System bugs** — feature is broken, API down, real product defect

**Why batch first:** Diagnosing one by one wastes time. Knowing all categories upfront lets you handle them in parallel.

---

### Phase 3: Handle each category

**Test bugs → fix inline:**
```bash
npx playwright test --last-failed   # run only failures, repeat until clean
```

**System bugs → skip + report:**
```typescript
// Mark as skipped immediately so --last-failed stops including them
test.skip(true, 'system bug: [short description]')
```
Then send `qa-quick-report` to user with all system bugs in one batch — not one by one.

---

### Phase 4: Fix loop — only remaining test bugs
```bash
npx playwright test --last-failed
```
System bugs are now skipped → `--last-failed` only shows real test bugs. Iterate until clean.

---

### Phase 5: Final verification — full run once
```bash
npx playwright test
```
Run full suite exactly once to catch regressions. Done.

---

## system bug → test.skip Pattern

After confirming a system bug, park it immediately:

```typescript
// ✅ Correct: skip with reason so future reader knows why
test.skip(true, 'system bug: order creation returns 500 on staging')

// When dev fixes → remove skip → verify
test('should create order', async ({ page }) => { ... })
```

**Rule:** A system bug test left failing (not skipped) keeps polluting `--last-failed` and makes it impossible to know when test bugs are truly resolved.

---

## When `--last-failed` Isn't Enough: Tag-Based Isolation

For long fix sessions (multi-day, many failures) or when fixing a specific module:

```typescript
test('should create order @orders', async ({ page }) => { ... })
test('should filter orders @orders @filter', async ({ page }) => { ... })
```

```bash
npx playwright test --grep "@orders"
npx playwright test --grep-invert "@stable"   # exclude known-passing tests
```

---

## Config Rule: No Retries on Local

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 1 : 0,  // retry only on CI, never local
});
```

Local retries hide flaky tests and double DB writes. Fail fast = find root cause fast.

---

## Decision Table

| Situation | Action |
|---|---|
| Starting a fix session | `npx playwright test` (once) |
| After full run — before fixing | Batch triage ALL failures first |
| System bug confirmed | `test.skip(true, 'reason')` + qa-quick-report |
| Mid-fix iteration (test bugs only) | `npx playwright test --last-failed` |
| Fixing one specific module | `npx playwright test --grep "@tag"` |
| All test bugs resolved | `npx playwright test` (final verify, once) |
| CI pipeline | `retries: 1` in config |

---

## `--last-failed` Limitations

- **Newly added tests** are not in the last run, so `--last-failed` does not include them.
  → Run them once with `--grep` before going back to `--last-failed`.
- **Skipped tests** (via `test.skip`) are not "failed", so they won't re-run.
- `--last-failed` reads from `test-results/.last-run.json` — deleting that file resets it.

## Faster Alternatives to Full Suite (Playwright 1.46+)

```bash
# Only tests whose spec file changed since main
npx playwright test --only-changed=main

# Combined: run only changed specs, then re-run their failures
npx playwright test --only-changed=main
npx playwright test --last-failed
```

## Checklist Before Each Run

- [ ] Did I triage ALL failures before starting to fix?
- [ ] Are system bugs skipped with `test.skip(true, reason)`?
- [ ] Am I mid-fix? → `--last-failed`, NOT full run
- [ ] Is `retries: 0` locally in `playwright.config.ts`?
- [ ] Is this the final check? → full run (once only)

---

## Real Cost Impact

| Approach | 80 tests, 5 failing, 5 fix iterations |
|---|---|
| Full run each iteration | 80 × 5 = **400 test executions** |
| `--last-failed` each iteration | 5 × 5 = **25 test executions** |
| **Savings** | **93.75% reduction** |

Each test execution that hits the DB = real writes. Use `--last-failed`.
