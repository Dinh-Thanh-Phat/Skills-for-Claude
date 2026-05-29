---
name: skip-vs-fail
description: When to use test.skip() vs test.fail() vs expect() in Playwright — prevent conditional skip from masking real bugs. Use when deciding whether to skip a test, when a test is flaky, or when adding test.skip() inside test body. Triggers on: "test.skip", "conditional skip", "mask bug", "false negative", "bỏ qua test", "skip test", "skip inside test body".
type: qa-practice
triggers:
  - "test.skip"
  - "conditional skip"
  - "mask bug"
  - "false negative"
  - "bỏ qua test"
  - "skip test"
  - "skip inside test body"
scope: playwright, e2e-testing
---

# Skip vs Fail — Avoid False Negatives

**Rule:** Never use conditional `test.skip()` inside test body to silently bypass failures. Skip masks bugs.

## The Antipattern (False Negative)

```typescript
// ❌ DANGEROUS — hides real failures
test('SE-017: bilingual template', async ({ page }) => {
  await page.goto('/send-email');
  const template = page.getByRole('option').filter({ hasText: /bilingual/i }).first();
  
  if (!await template.isVisible({ timeout: 3000 })) {
    test.skip(); // ← Bug: if template fails to load due to a real bug, test silently skips
    return;
  }
  // ... rest of test
});
```

If the template list fails to load (network error, API bug, regression) — this test silently skips instead of alerting you.

## Decision Tree

```
Feature exists in production?
├── YES → Does this specific scenario apply now?
│         ├── Always applies → Use expect(), NEVER skip
│         └── Conditionally applies (e.g., depends on test data) → Use beforeEach to setup data reliably
└── NO (feature not implemented) → test.skip() at TOP of test with clear reason
```

## Correct Patterns

### Pattern 1: Feature not implemented — skip at top
```typescript
test('EL-003: CSV import', async ({ page }) => {
  test.skip(true, 'CSV import feature not yet implemented in the application');
  // body never runs
});
```

### Pattern 2: Environment-dependent — skip at top
```typescript
test('US-001: admin feature', async ({ page }) => {
  test.skip(!process.env.ADMIN_ENABLED, 'Admin features disabled in this environment');
});
```

### Pattern 3: Feature exists — expect robustly, never skip
```typescript
// ✅ CORRECT: If the feature exists, the data must exist — set it up in beforeEach
test.beforeEach(async ({ page }) => {
  await setupBilingualTemplate(page); // ensure prerequisite exists
});

test('SE-017: bilingual template language selector', async ({ page }) => {
  await page.goto('/send-email');
  const template = page.getByRole('option', { name: /bilingual/i });
  await expect(template).toBeVisible({ timeout: 5000 }); // FAIL loudly if not found
  await template.click();
  // ... rest of test
});
```

### Pattern 4: `test.fail()` — expect known broken behavior
```typescript
// Use when you KNOW the test will fail (e.g., documenting a known bug)
test('known broken: reply-to field not saved', async ({ page }) => {
  test.fail(); // test is expected to fail — alerts if it unexpectedly passes
  // ...
});
```

## Summary Table

| Situation | Pattern |
|---|---|
| Feature not implemented | `test.skip(true, 'reason')` at top |
| Environment missing config | `test.skip(!env.FLAG, 'reason')` at top |
| Feature exists but brittle setup | Fix `beforeEach` to reliably set up data |
| Known bug (documenting) | `test.fail()` |
| Everything working | Plain `expect()` — no skip |
| ❌ Never | `if (!visible) { test.skip(); return; }` inside body |

## Why This Matters

A test suite where 80/80 pass but 10 silently skip broken features gives **false confidence**. A failed test alerts the team. A skipped test hides the bug until it reaches production.

**Sources:** Playwright Test Annotations docs, testautomationmastery.com

