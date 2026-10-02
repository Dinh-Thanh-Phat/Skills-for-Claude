---
name: playwright-test-anti-patterns
description: Detect and fix Playwright test anti-patterns - soft assertions, nth locators, silent catches, assertions inside expect(). Triggers on: "review test", "check test quality", "anti-pattern", "test always pass", "viết test review".
type: skill
triggers:
  - "review test"
  - "check test quality"
  - "anti-pattern"
  - "test always pass"
  - "soft assertion"
  - "silent catch"
  - "nth locator"
---

# Playwright Test Anti-Patterns Detection & Fix

## Problem
Tests pass but don't actually test anything due to anti-patterns. Fails silently or with flaky results.

## Anti-Patterns & Fixes

### 1. Soft Assertions (expect(bool) instead of expect(element))

**❌ WRONG:**
```ts
const hasHeaders = /port|name|location|berth/i.test(header);
expect(hasHeaders).toBe(true);  // Soft assertion - doesn't wait, can fail silently
```

**✅ CORRECT:**
```ts
// Match directly on the content
expect(header).toMatch(/port|name|location|berth/i);

// Or for visibility:
const headerElement = page.locator('th').first();
await expect(headerElement).toContainText(/port|location/i);
```

**Why:** `expect(bool)` bypasses Playwright's retry/wait mechanism. Assertions should be on locators/elements, not extracted variables.

---

### 2. Nth Locators (fragile, order-dependent)

**❌ WRONG:**
```ts
const option = page.locator('.ant-select-item-option').first();  // Breaks if order changes
const element = page.locator('input').nth(1);  // Breaks if UI adds input
```

**✅ CORRECT:**
```ts
// Use role-based locators
const submitBtn = page.getByRole('button', { name: 'Submit' });

// Use filter for specific content
const portOption = page.locator('.ant-select-item-option')
  .filter({ hasText: /CMIT|Port Name/ })
  .first();

// Use data-testid attributes
const element = page.locator('[data-testid="form-email"]');
```

**Why:** nth() locators break when UI structure changes. Use semantic selectors or filters instead. See: [Playwright Locators Best Practices](https://www.techlistic.com/2026/02/playwright-locators-explained-best.html)

---

### 3. Silent .catch() (hides real errors)

**❌ WRONG:**
```ts
const isVisible = await element.isVisible().catch(() => false);
if (!isVisible) { test.skip(); }  // Don't know WHY it failed
```

**✅ CORRECT:**
```ts
// Option 1 (default): let the web-first assertion fail loudly — message names locator + timeout
await expect(element, 'Element should render after page load').toBeVisible({ timeout: 2_000 });

// Option 2: precondition genuinely unavailable in this env → skip with an explicit, logged reason
// (isVisible() never waits; its `timeout` option is deprecated and IGNORED — class-locator.md)
const featurePresent = await element.isVisible();
test.skip(!featurePresent, 'Feature X not deployed in this env — see skip-vs-fail');
```

Never swallow the error with `.catch(() => …)` — not even to call `test.skip`. If the
condition is a real bug, it must FAIL (see `fail-loud`, `skip-vs-fail`).

**Why:** `.catch(() => false)` masks whether error is timeout, selector mismatch, or app bug. See: [Avoid Flaky Tests](https://betterstack.com/community/guides/testing/avoid-flaky-playwright-tests/)

---

### 4. Assertions Inside expect()

**❌ WRONG:**
```ts
await expect(async () => {
  const text = await page.locator('h1').textContent();
  return text === 'Login';
}).resolves.toBeTruthy();
```

**✅ CORRECT:**
```ts
await expect(page.locator('h1')).toHaveText('Login');
```

**Why:** Assertions should wrap the action, not contain await. Playwright's web-first assertions handle waiting automatically.

---

### 5. Multiple Expectations on Extracted Variables

**❌ WRONG:**
```ts
const count = await page.locator('.item').count();
expect(count).toBeGreaterThan(0);
expect(count).toBeLessThan(100);
```

**✅ CORRECT:**
```ts
const items = page.locator('.item');
await expect(items).toHaveCount(5);  // If expecting exactly 5

// Or for range assertions — wrap in expect(...).toPass() so the count is re-read until it fits:
await expect(async () => {
  const count = await items.count();
  expect(count).toBeGreaterThan(0);
  expect(count).toBeLessThan(100);
}).toPass({ timeout: 5_000 });
```

**Why:** Web-first assertions on locators retry; extracted variables don't.

---

## Detection Checklist

- [ ] All assertions are on **locators or elements**, not extracted variables/booleans
- [ ] No `.catch()` that silently fails — use explicit error handling
- [ ] No `.nth()` locators without fallback to semantic selectors
- [ ] No `expect(async () => …).resolves.toBeTruthy()` — use a web-first matcher, or `expect(async () => { …expect… }).toPass()` for multi-value retries
- [ ] Timeout values are data-driven (measure actual duration × 1.5)
- [ ] Error messages in `test.fixme()` explain WHY test can't run

## Auto-Fix Script (cross-platform — use ripgrep)

```bash
# rg works on Windows + Linux + macOS — grep with **/*.spec.ts is bash-only
rg -n "expect\([^)]+\)\.toBe\(true\)"  tests/
rg -n "\.catch\(\s*\(\)\s*=>\s*false\s*\)" tests/
rg -n "\.nth\(" tests/
rg -n "waitForTimeout\(" tests/
rg -n "waitForLoadState\(['\"]networkidle" tests/
```

PowerShell fallback:
```powershell
Get-ChildItem -Recurse -Filter *.spec.ts | Select-String -Pattern 'expect\(.*\)\.toBe\(true\)'
```

> **Cross-ref:** This skill overlaps with `fail-loud` + `soft-assertion-ban` + `safe-locators` —
> use those for the full rules; use this file as the quick-scan / lint reference.

## References

- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Locators Guide](https://playwright.dev/docs/locators)
- [Anti-patterns Article](https://testdino.com/blog/playwright-best-practices/)
- [Assertion Best Practices](https://www.checklyhq.com/docs/learn/playwright/assertions/)
