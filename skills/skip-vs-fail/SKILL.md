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
  const template = page.getByRole('option', { name: /bilingual/i });
  
  if (!await template.isVisible({ timeout: 3000 })) { // (timeout is ignored — isVisible never waits)
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

### Pattern 4: `test.fail()` — known system bug (CANONICAL known-bug policy)
```typescript
// Use when you KNOW the test will fail because of a filed product bug
test('reply-to field is saved', async ({ page }) => {
  test.fail(true, 'BUG-123: reply-to field not saved'); // always include the ticket ID
  // ... assertions on the EXPECTED (correct) behavior — never weaken them to match the bug
});
```

**This is the single policy every other skill links to** (`test-failure-triage`,
`test-rerun-discipline`, `test-diagnosis-before-code`, `ui-error-classification`,
`soft-assertion-ban`):
1. Bug confirmed → file it → `test.fail(true, 'BUG-xxx: …')` at the top of the test.
2. The test keeps RUNNING; while the bug exists it counts as passed (expected failure), so it
   doesn't pollute `--last-failed` or turn CI red.
3. When the bug is fixed, Playwright reports "expected to fail, but passed" → **remove the
   `test.fail` line** and verify the test is green.
4. Never `test.skip` a known bug — a skipped test can't tell you it was fixed, or that it got worse.

## Summary Table

| Situation | Pattern |
|---|---|
| Feature not implemented | `test.skip(true, 'reason')` at top |
| Environment missing config | `test.skip(!env.FLAG, 'reason')` at top |
| Feature exists but brittle setup | Fix `beforeEach` to reliably set up data |
| Known bug (filed) | `test.fail(true, 'BUG-xxx: …')` — remove when fixed |
| Everything working | Plain `expect()` — no skip |
| ❌ Never | `if (!visible) { test.skip(); return; }` inside body |

## Why This Matters

A test suite where 80/80 pass but 10 silently skip broken features gives **false confidence**. A failed test alerts the team. A skipped test hides the bug until it reaches production.

**Sources:** Playwright Test Annotations docs, testautomationmastery.com

