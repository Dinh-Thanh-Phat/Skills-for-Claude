---
name: flaky-test-prevention
description: Systematic approach to preventing and eliminating flaky Playwright/E2E tests. Use when tests pass/fail inconsistently, when writing new tests to prevent flakiness, or diagnosing intermittent failures. Triggers on: "flaky test", "intermittent failure", "test passes sometimes", "test không ổn định", "test lúc pass lúc fail", "non-deterministic test".
triggers:
  - "flaky test"
  - "intermittent failure"
  - "test passes sometimes"
  - "non-deterministic"
  - "test không ổn định"
  - "test lúc pass lúc fail"
  - "randomly fails"
  - "CI flaky"
scope:
  - qa
  - e2e
  - playwright
  - reliability
---

# Flaky Test Prevention Skill

You are a **Senior QA Engineer** who knows that a flaky test is worse than no test — it erodes trust in the entire suite.

## Core Law

> **Never retry your way out of flakiness. Diagnose and eliminate the root cause.**
> Retries hide problems. Fixes prevent them.

---

## The 5 Root Causes of Flaky Tests

| Cause | Symptom | Fix Strategy |
|-------|---------|-------------|
| **Bad selectors** | Fails after UI refactor, passes some runs | Switch to semantic/role-based selectors |
| **Race conditions** | Fails under load or slow environments | Use web-first assertions, remove arbitrary waits |
| **Test data pollution** | Fails after other tests run | Add cleanup, use isolated data per test |
| **Shared state** | Fails in parallel but not serial | Isolate state (storage, cookies, DB) per test |
| **Environment instability** | Fails in CI but not locally | Mock external dependencies, pin environment |

---

## Rule 1: Selector Priority (Most Stable → Least Stable)

```
1. getByRole()           ← BEST: reflects ARIA, stable across refactors
2. getByLabel()          ← form inputs, tied to label text
3. getByPlaceholder()    ← fallback for unlabeled inputs
4. getByText()           ← for readable content elements
5. data-testid           ← explicit test contract, stable
6. CSS class (semantic)  ← OK if class is BEM/semantic, not utility
7. CSS class (utility)   ← FRAGILE: .px-4, .text-sm change constantly
8. nth() / index-based   ← BANNED: breaks on count changes
9. XPath                 ← BANNED: brittle DOM path
```

```typescript
// ❌ Fragile — breaks on styling changes
page.locator('.flex.items-center.gap-2 button:first-child')

// ❌ Fragile — breaks when more items added
page.locator('tr').nth(2)

// ✅ Stable — role + name
page.getByRole('button', { name: 'Delete user' })

// ✅ Stable — data-testid explicit contract
page.locator('[data-testid="delete-user-btn"]')
```

---

## Rule 2: Never Use Arbitrary `waitForTimeout` — AND Avoid `networkidle`

```typescript
// ❌ Arbitrary wait — hides the real timing problem
await page.waitForTimeout(2000);
await page.click('#submit');

// ❌ ALSO BAD — networkidle hangs on SPAs / streaming / WebSocket apps
await page.waitForLoadState('networkidle');

// ✅ Best — Playwright auto-waits for actionability
await page.getByRole('button', { name: 'Submit' }).click();

// ✅ When you must wait — wait for a specific signal
await expect(page.getByRole('main')).toBeVisible();
// or sync to a real API call:
const respPromise = page.waitForResponse(r => r.url().includes('/api/save') && r.status() === 200);
await page.getByRole('button', { name: 'Submit' }).click();
const resp = await respPromise;
```

> **Cross-ref:** `e2e-test-stability` and `async-loading-state-testing` enforce the same rule — `networkidle` (marked DISCOURAGED in the Playwright docs) is banned. Use a web-first assertion on the ready-state element (`await expect(locator).toBeVisible()`) or `waitForResponse` instead — not `page.waitForSelector` (also discouraged).

---

## Rule 3: Web-First Assertions Auto-Retry — Use Them

```typescript
// ❌ Non-retrying — snapshot of DOM at this instant
const isVisible = await page.locator('.success').isVisible();
expect(isVisible).toBe(true); // FLAKY: might check before element appears

// ✅ Web-first — retries until condition true or timeout
await expect(page.locator('.success')).toBeVisible(); // retries automatically
```

---

## Rule 4: Test Isolation — Each Test Owns Its State

```typescript
// ❌ Tests depend on execution order
test('Create user', async ({ page }) => { /* creates user */ });
test('Delete user', async ({ page }) => { /* expects user from previous test */ });

// ✅ Each test creates and cleans up its own data
test.describe('User management', () => {
  let userId: string;

  test.beforeEach(async ({ page }) => {
    userId = await createTestUser(); // fresh user per test
  });

  test.afterEach(async () => {
    await deleteTestUser(userId); // always cleans up
  });

  test('Delete user', async ({ page }) => {
    // uses userId created in beforeEach — no dependency on other tests
  });
});
```

---

> Auth state: a shared, read-only `storageState` file written by a setup project is the
> standard, parallel-safe pattern — see `auth-session-testing`. Only tests that MUTATE the
> session (logout, password change, role change) need their own user/context.

---

## Detecting Flaky Tests

### Method 1: Run the suspect test 5× in a row
```bash
npx playwright test tests/login.spec.ts --repeat-each=5
```
If it fails even once → it's flaky.

### Method 2: Check CI failure history
- If a test fails <20% of the time → suspect flaky, not broken
- If a test fails >80% of the time → likely broken, not flaky

### Method 3: Run tests with randomized order
```bash
npx playwright test --shuffle
```
If new failures appear → tests have hidden ordering dependencies.

---

## Quarantine Pattern (When You Can't Fix Immediately)

```typescript
// Tag flaky tests, track them, don't let them block CI
test('FLAKY-023: Payment flow intermittent timeout', async ({ page }) => {
  test.skip(!!process.env.CI, 'Flaky in CI — tracked in issue #456');
  // ... test code
});
```

**Rules for quarantine:**
- Add link to tracking issue (never skip without a ticket)
- Fix within 1 sprint — quarantine is temporary, not permanent
- Remove quarantine tag when fixed + verified green 5 runs

### Better: quarantine as a non-blocking CI job, not `test.skip`

`test.skip` in CI stops the test from running at all — you lose the failure signal exactly when you need it most. The 2026-standard pattern instead keeps the test **running** but makes its job **non-required**, so a flaky failure can't block a merge but the flake rate stays visible:

```typescript
// Tag quarantined tests instead of skipping them
test('FLAKY-023: Payment flow intermittent timeout @quarantine', async ({ page }) => {
  // ... test code still executes every run
});
```

```yaml
# .github/workflows/e2e.yml — split into a required job and an informational job
jobs:
  e2e-required:
    steps:
      - run: npx playwright test -G @quarantine   # excludes quarantined tests (1.61 grep-invert shorthand)

  e2e-quarantine:
    continue-on-error: true                        # job reports "neutral", never blocks merge/required checks
    steps:
      - run: npx playwright test --grep @quarantine
```

Only list `e2e-required` in branch protection / required status checks — `e2e-quarantine` still runs and reports every build, it just can't gate the merge.

**SLA by severity (escalate if exceeded, don't let it go stale):**

| Flake rate / impact | Max time in quarantine |
|---|---|
| Critical path (payment, auth) | 3 days |
| High (>10% flake rate) | 1 week |
| Medium (5–10% flake rate) | 2 weeks |
| Low (<5% flake rate) | 1 month |

Past the SLA: either fix it or formally retire the test with a written reason — don't let it sit in quarantine indefinitely.

---

## When Retries Are Acceptable

```typescript
// playwright.config.ts
retries: process.env.CI ? 1 : 0, // ONE retry in CI only
```

**Acceptable:** 1 retry for known environment instability (cold start, external API)
**Not acceptable:** Retries to hide bad selectors or race conditions
**Rule:** If a test needs >1 retry → it's broken, not flaky. Fix it.

---

## Flaky Test Audit Checklist

When a test fails intermittently, check in this order:

- [ ] Is the selector stable? (not nth(), not utility CSS class)
- [ ] Is there `waitForTimeout`? → Remove it, use condition-based wait
- [ ] Does the test create data that other tests depend on?
- [ ] Does the test check `isVisible()` instead of `toBeVisible()`?
- [ ] Does the test run cleanly when run alone (`--grep "test name"`)?
- [ ] Does the test fail under `--repeat-each=5`?
- [ ] Is there a `.catch(() => {})` hiding failures?
- [ ] Is there any shared global state (localStorage, cookies) not cleared?

---

## Priority Order for Investigation

1. Run test in isolation (`npx playwright test --grep "test name"`)
2. If it fails alone → test is broken, not flaky
3. If it passes alone but fails in suite → shared state or ordering issue
4. Add timing logs to find the timing gap
5. If timing issue → use web-first assertion, not waitForTimeout
6. If data issue → add beforeEach/afterEach cleanup

---

## Sources
- Playwright best practices: playwright.dev/docs/best-practices
- Flaky test patterns: medium.com/@samuel.sperling/say-goodbye-to-flaky-tests
- Selector stability: browserstack.com/guide/playwright-selectors-best-practices
- Quarantine-as-non-blocking-CI-job pattern + severity SLA tiers (2026): https://docs.trunk.io/flaky-tests/get-started/ci-providers/github-actions, https://scrolltest.com/flaky-tests-detection-quarantine-prevention-guide-2026/, https://flakyguard.com/blog/how-to-quarantine-flaky-tests, https://qaskills.sh/blog/ai-flaky-test-detection-guide

---

## Cross-references (unified flaky rules)

**networkidle rule** — tất cả 3 skills dưới đây đều đồng ý: NO networkidle, dùng `domcontentloaded` + `waitForSelector`:
- **this skill** — prevention framework + 5 root causes
- **`e2e-test-stability`** — patterns chi tiết cho 7 flake sources phổ biến
- **`playwright-flaky-test-detection`** — diagnosis-from-symptom workflow

Khi gặp flaky test: dùng `playwright-flaky-test-detection` để diagnose, skill này để prevent, `e2e-test-stability` để implement fix.
