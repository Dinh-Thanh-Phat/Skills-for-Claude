---
name: soft-assertion-ban
description: Prevent OR-assertions and length>N checks that always pass in Playwright tests. Use when writing or reviewing any test code. Triggers on: "soft assertion", "expect(A || B)", "length > 0", "length > N", ".catch(() => false)", "assertion OR", any test code generation or review.
---

# Soft Assertion Ban Skill

You are a **Senior QA Engineer** who understands that a test that never fails is not a test — it's a lie.

## The Problem

"Soft" OR-assertions look like real tests but are almost impossible to fail:

```typescript
// ❌ This test ALWAYS PASSES — stayedOnPage is true 99% of the time
const hasError = await page.locator('.error').isVisible().catch(() => false);
const stayedOnPage = page.url().includes('/send');
expect(hasError || stayedOnPage).toBe(true);

// ❌ This "assertion" catches literally nothing meaningful
const text = await dialog.textContent();
expect(text?.trim().length).toBeGreaterThan(10);

// ❌ This asserts a boolean that is almost never false
expect(rows.length > 0 || emptyState.visible).toBe(true);
```

These are **fail-soft assertions** — they mask real bugs by accepting any of multiple outcomes.

---

## Root Cause

Soft assertions appear when:
1. You're unsure what the app ACTUALLY does in this case
2. The app behavior is inconsistent between environments
3. You're trying to "handle both cases" to avoid flaky tests
4. You added `.catch(() => false)` to stop a flaky failure without fixing the root cause

**The fix is not to widen the assertion — it's to understand and commit to ONE expected behavior.**

---

## Rules

### Rule 1: Never use `A || B` in `expect()`

```typescript
// ❌ BANNED
expect(hasError || stayedOnPage).toBe(true);
expect(toastVisible || errorVisible).toBe(true);
expect(navigated || isDisabled).toBe(true);

// ✅ Pick one behavior and assert it
await expect(page.locator('.error-toast')).toBeVisible({ timeout: 5000 });
// OR
await expect(page).toHaveURL(/\/send/);
// — not both with ||
```

### Rule 2: Never assert on `.length > N` where N is arbitrary

```typescript
// ❌ BANNED — "has some content" is not a real assertion
expect(dialogText?.trim().length).toBeGreaterThan(10);
expect(items.length).toBeGreaterThan(0);

// ✅ Assert the actual expected content
await expect(dialog.locator('.preview-subject')).toContainText('Xin chào Nguyễn');
await expect(page.locator('tbody tr')).toHaveCount(3);
```

### Rule 3: `.catch(() => false)` is only allowed at boundaries — never in assertions

```typescript
// ❌ BANNED — hiding a potential failure
const hasError = await locator.isVisible().catch(() => false);
expect(hasError).toBe(true); // This can NEVER fail on timeout — just returns false

// ✅ Let Playwright's built-in timeout handle it
await expect(locator).toBeVisible({ timeout: 5000 });
// — throws a real failure with a useful message if not visible
```

### Rule 4: If you don't know which behavior is correct — stop and ask

When you find yourself writing `A || B` it means one of:
- You don't know what the expected behavior is → **ask the dev/BA**
- The app is inconsistent → **file a bug, then assert the correct behavior**
- You're trying to handle two edge cases → **split into two separate tests**

---

## How to Fix Soft Assertions

### Pattern: "OR with URL stay"

```typescript
// ❌ Before
const hasError = await page.locator('...').isVisible().catch(() => false);
const stayedOnPage = page.url().includes('/send');
expect(hasError || stayedOnPage).toBe(true);

// ✅ After — commit to ONE assertion
await expect(page.locator('[class*="toast"]').filter({ hasText: /email|invalid/i }))
  .toBeVisible({ timeout: 5000 });
// OR
await expect(page).toHaveURL(/\/send/);
await expect(page.locator('.error, [aria-invalid]')).toBeVisible();
```

### Pattern: "Content length > N"

```typescript
// ❌ Before
const text = await dialog.textContent();
expect(text?.trim().length).toBeGreaterThan(10);

// ✅ After — assert what should ACTUALLY be in the dialog
await expect(dialog.locator('.preview-subject')).toContainText(subject);
await expect(dialog.locator('.preview-body')).not.toBeEmpty();
```

### Pattern: "Feature might or might not exist"

```typescript
// ❌ Before — always passes
if (await fileInput.isVisible()) {
  await fileInput.setInputFiles(path);
  expect(lines.length).toBeGreaterThan(0);
} else {
  const importBtn = page.getByRole('button', { name: /import/i });
  await expect(importBtn).toBeVisible(); // just checks button exists, not the feature
}

// ✅ After — be explicit
if (!await fileInput.isVisible({ timeout: 5000 }).catch(() => false)) {
  test.skip(); // feature not implemented — skip cleanly
  return;
}
await fileInput.setInputFiles(path);
await expect(page.locator('.email-textarea')).toContainText('@');
```

---

## Checklist — Before Committing Any Assertion

- [ ] Does my `expect()` call contain `||`? → **Rewrite. Pick one.**
- [ ] Does my assertion check `.length > 0` or `.length > N`? → **Assert the exact count or content.**
- [ ] Did I wrap `isVisible()` in `.catch(() => false)` and then assert on that? → **Use `toBeVisible()` with timeout instead.**
- [ ] Am I asserting "stayed on page" as a proxy for "validation fired"? → **Assert the actual error message.**
- [ ] Can this assertion fail in any realistic scenario? → If no: **it's not testing anything.**

---

## Legitimate Use of `expect.soft` (Playwright's Built-in)

Playwright's `expect.soft()` IS allowed — it collects multiple assertion failures in ONE test
run and reports all at the end, instead of bailing at the first. This is NOT a "soft assertion"
in the anti-pattern sense; it still fails the test.

```typescript
// ✅ OK — all 3 checks run; if any fail, test fails with full report
await expect.soft(page.getByRole('heading')).toHaveText('Dashboard');
await expect.soft(page.getByRole('navigation')).toBeVisible();
await expect.soft(page.locator('.error')).toBeHidden();
// Test still fails if any soft assertion failed
```

**Rule:** `expect.soft` ≠ `expect(A || B).toBe(true)`. Soft assertions still report failures
clearly; OR-assertions silently accept any of multiple states.

## Vacuous Negative Assertions

`not.toBeVisible()` passes if the element never existed at all. Make sure the element COULD
exist before asserting it shouldn't:
```typescript
// ❌ Passes vacuously if there's no .modal anywhere in DOM
await expect(page.locator('.modal')).not.toBeVisible();

// ✅ First confirm it COULD appear (e.g. open then verify close)
await page.click('button[name="Open Modal"]');
await expect(page.locator('.modal')).toBeVisible();
await page.click('button[name="Close"]');
await expect(page.locator('.modal')).toBeHidden();
```

## The Forcing Question

> "If I introduce a bug where the app accepts invalid data silently and navigates away — does my assertion catch it?"

If the answer is "no" or "maybe" → your assertion is soft. Rewrite it.

---

## Cross-references (assertion quality)

Hai skills này cover cùng vấn đề "test luôn pass" từ 2 góc độ khác nhau — dùng cả hai:
- **this skill** — OR-assertions và length>N checks (always-pass patterns)
- **`fail-loud`** — error swallowing với `.catch(() => {})` và hard assertions

Checklist khi review test: chạy cả `soft-assertion-ban` (check logic assertions) VÀ `fail-loud` (check error handling).
