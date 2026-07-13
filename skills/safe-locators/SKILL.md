---
name: safe-locators
description: Rules for writing safe, unique Playwright locators — avoid .first()/.nth() silent failures, enforce strict uniqueness, and auto-normalize brittle CSS/XPath locators with locator.normalize(). Use when writing locators, dealing with "strict mode violation", ambiguous selectors, or multiple matching elements. Triggers on: "locator first()", "nth(0)", "ambiguous locator", "strict mode violation", "selector không unique", "multiple elements matched", "locator.normalize", "brittle CSS selector".
type: qa-practice
triggers:
  - "locator first()"
  - "nth(0)"
  - "ambiguous locator"
  - "strict mode violation"
  - "selector không unique"
  - "multiple elements matched"
  - "locator.normalize"
  - "brittle CSS selector"
scope: playwright, e2e-testing
---

# Safe Locators — No Silent Failures

**Rule:** Never use `.first()`, `.last()`, or `.nth()` to work around ambiguous locators.

## Why `.first()` Is Dangerous

```typescript
// ❌ DANGEROUS — if page structure changes, this matches a different element silently
const option = page.getByRole('option').filter({ hasText: /EN/ }).first();
await option.click();
// Test passes but may have clicked the wrong "EN" (e.g., "ENABLED" or another element)
```

Playwright's strict mode exists to catch this. `.first()` bypasses strict mode — silent wrong match.

## Fix: Make the Locator Unique

### Option 1: More precise text filter
```typescript
// ❌ Vague
page.getByRole('option').filter({ hasText: /EN/ })

// ✅ Exact match
page.getByRole('option').filter({ hasText: /^EN$/ })
// or
page.getByRole('option', { name: 'EN', exact: true })
```

### Option 2: Scope to container
```typescript
// ❌ Global — matches all options on page
page.getByRole('option', { name: 'Submit' })

// ✅ Scoped to specific dialog or section
page.getByRole('dialog').getByRole('option', { name: 'Submit' })
```

### Option 3: Use data-testid
```typescript
// ✅ When nothing else works, use stable test ID
page.getByTestId('language-option-en')
```

### Option 4: Combine role + accessible name + container
```typescript
// ✅ Most specific — 3-layer scoping
const form = page.locator('form[aria-label="Email Settings"]');
const select = form.getByRole('combobox', { name: 'Language' });
await select.getByRole('option', { name: 'EN', exact: true }).click();
```

## Auto-Normalize a Brittle Locator (`locator.normalize()`, v1.59+)

Instead of hand-rewriting a CSS/XPath locator inherited from Codegen or old code, ask Playwright to convert it for you:

```typescript
// Inherited from Codegen — implementation-detail CSS, breaks on any DOM reshuffle
const brittle = page.locator('div.container > ul li:nth-child(3) > button.submit-btn');

// Resolves the live element and returns an equivalent locator built from
// test ids / ARIA roles / other user-facing attributes instead of CSS structure
const safe = await brittle.normalize();
await safe.click();
```

`normalize()` inspects the actual matched element at call time — it needs the page in the state where that element exists (same rule as any other action: locate after the element is rendered). It doesn't replace scoping or uniqueness checks: still verify `toHaveCount(1)` before treating the normalized locator as safe to commit. Useful as a one-shot cleanup pass over old CSS-locator-heavy specs rather than a runtime pattern in new tests (write `getByRole`/`getByTestId` directly instead).

## When `.first()` Is Acceptable

Only use `.first()` when:
1. The list is genuinely unordered and any item works (e.g., "pick the first search result")
2. You've verified via `ariaSnapshot()` that only one element matches

```typescript
// ✅ OK: verifying count first
const matches = page.getByRole('option').filter({ hasText: /^EN$/ });
await expect(matches).toHaveCount(1); // assert unique BEFORE interacting
await matches.click();
```

## Strict Mode — Enabled by Default

Playwright strict mode is ON by default for action methods — `.click()`, `.fill()` throw on multiple matches. `.first()` bypasses this safety net silently.

## Verification Checklist

Before committing any locator:
- [ ] Does `await expect(locator).toHaveCount(1)` pass?
- [ ] No `.first()` unless count verified as 1 or "any item works" semantics
- [ ] Text filters use `exact: true` or `^...$` anchored regex
- [ ] Locator is scoped to nearest unique container (dialog, tabpanel, form)

## Sources
- https://playwright.dev/docs/locators
- https://playwright.dev/docs/best-practices
- https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/api/class-locator.md (`Locator.normalize()`, since v1.59)

