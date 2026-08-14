---
name: fail-loud
description: >-
  Enforce hard assertions and prevent error swallowing in Playwright tests. Use when writing or
  reviewing automation tests to ensure they fail loudly when features break. Triggers on: "write
  test", "review test", "viết test", "kiểm tra test", any test code generation task.
---

# Fail Loud Skill

You are a **Senior QA Engineer** enforcing strict assertion discipline.

## Core Law

> **A test that cannot fail is worse than no test.**
> It creates false confidence and hides real bugs.

---

## Rule 1: Hard Assertions Only

### NEVER — Soft assertion (always passes)
```typescript
try {
  await page.click('button');
} catch (e) {
  console.log('Error:', e); // swallowed
}
expect(true).toBeTruthy(); // meaningless
```

### ALWAYS — Hard assertion (fails loudly)
```typescript
await page.click('button');
await expect(page.locator('.success')).toBeVisible(); // fails if not visible
```

**Decision rule:** If you remove the assertion and the test still passes, the assertion is worthless. Delete it and write a real one.

---

## Rule 2: Never Swallow Errors in catch

### NEVER
```typescript
await someAction().catch(() => {}); // hides ALL failures
await page.goto(url).catch(e => console.log(e)); // silent failure
```

### ALLOWED — Re-throw after logging
```typescript
try {
  await someAction();
} catch (e) {
  await page.screenshot({ path: 'failure.png' }); // capture context
  throw e; // re-throw — let test fail
}
```

### ALLOWED — Specific retry for known flakiness
```typescript
// OK: retries but still asserts success — does NOT swallow
await expect(async () => {
  await page.goto(url);
}).toPass({ timeout: 30000 });
```

---

## Rule 3: Use Web-First Assertions (Auto-Retry)

Playwright assertions auto-retry until condition is met or timeout. Use them — don't fight the framework.

| ❌ Non-retrying (fragile) | ✅ Web-first (reliable) |
|---|---|
| `expect(await locator.isVisible()).toBe(true)` | `await expect(locator).toBeVisible()` |
| `expect(await locator.textContent()).toBe('x')` | `await expect(locator).toHaveText('x')` |
| `expect(await page.url()).toBe('/home')` | `await expect(page).toHaveURL('/home')` |
| `expect(await locator.count()).toBe(3)` | `await expect(locator).toHaveCount(3)` |

---

## Rule 4: Every Assertion Must Be Meaningful

Before writing any assertion, ask:

> **"If this assertion is removed, does the test still detect the bug?"**

- YES → The assertion is redundant or wrong. Rewrite it.
- NO → The assertion is meaningful. Keep it.

---

## Checklist — Before Submitting Any Test

- [ ] No `expect(true).toBeTruthy()` or `expect(false).toBeFalsy()`
- [ ] No `.catch(() => {})` (empty catch blocks)
- [ ] No catch block that logs but doesn't re-throw
- [ ] All assertions use `await expect(...)` form (web-first)
- [ ] Each assertion targets actual feature output (not intermediate state)
- [ ] Test fails when feature is broken — verified mentally

---

## Quick Diagnosis

If a test "always passes" — check for:
1. `expect(true)` / `expect(false)` → delete and rewrite
2. `.catch(() => {})` → re-throw the error
3. Non-awaited assertions → add `await`
4. Asserting on loading state instead of final state → wait for stable state

---

---

## Rule 5: AI Self-Healing ≠ Fail-Loud (2026 Caution)

AI tools (Healwright, TestMu, etc.) có thể tự fix broken selectors khi UI refactor — nhưng điều này KHÔNG thay thế hard assertions.

> **Note:** AI self-healing là tính năng của external tools, không phải Claude Code. Rule dưới đây áp dụng khi team dùng những tools đó.

**What AI self-healing solves:** Selector breaks when UI is refactored → test auto-updates `.submit-btn` to `[data-testid="submit"]`

**What AI self-healing does NOT solve:**
- A test that asserts the wrong thing (soft assertion that always passes)
- A test that swallows errors with `.catch(() => {})`
- A test where the assertion is removed or vacuously true

```typescript
// ❌ AI can heal the selector — but the test still always passes
const btn = await page.locator('.btn-submit'); // selector healed to data-testid
await btn.click();
// No assertion follows → test passes even if click fails silently
```

```typescript
// ✅ AI heals selector AND the assertion catches real failures
await page.getByRole('button', { name: 'Submit' }).click();
await expect(page.locator('[data-testid="success-toast"]')).toBeVisible();
// Now even if AI heals wrong → assertion catches it
```

**Rule:** Self-healing tools are a maintenance convenience, not a reliability substitute. Hard assertions are still mandatory.

---

## Sources (Research-backed)
- Playwright hard vs soft assertions: playwright.dev/docs/test-assertions
- Try-catch anti-patterns: "Used poorly, try-catch creates silent failures that destroy trust in test automation" — Medium
- Framework trust: "Most Playwright mistakes come down to fighting the framework instead of working with it" — TestDino
- AI self-healing selectors: aegisrunner.com/blog/brittle-selectors-killing-playwright-tests-self-healing-ai

---

## Cross-references (assertion quality)

Hai skills này cover cùng vấn đề "test luôn pass" từ 2 góc độ khác nhau — dùng cả hai:
- **this skill** — error swallowing với `.catch(() => {})` + hard assertions
- **`soft-assertion-ban`** — OR-assertions và length>N checks (always-pass patterns)

Checklist khi review test: `fail-loud` (check error handling) VÀ `soft-assertion-ban` (check logic assertions).
