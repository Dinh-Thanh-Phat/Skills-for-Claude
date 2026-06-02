---
name: playwright-deprecated-selectors
description: Identifies and migrates away from removed Playwright selector engines — _react, _vue, and the :light suffix. Use when a test throws "Unknown engine" errors, when upgrading Playwright, or when reviewing tests that use component-based selectors. Triggers on: "_react selector", "_vue selector", ":light selector", "Unknown engine", "selector engine removed", "migrate Playwright selectors".
---

# Playwright Deprecated Selectors — Migration Guide

## What Was Removed

Playwright has removed three selector engines across all language bindings (JS/TS, Python, Java, .NET):

| Removed | Replacement |
|---------|-------------|
| `_react=ComponentName[prop=value]` | `getByTestId()`, `getByRole()`, or `getByText()` |
| `_vue=component-name[prop=value]` | `getByTestId()`, `getByRole()`, or `getByText()` |
| `:light` CSS suffix | Standard CSS selectors (`:light` was for non-Shadow-DOM piercing) |

## Migration Patterns

### _react / _vue selectors → role or testId

```typescript
// ❌ REMOVED — will throw "Unknown engine: _react"
await page.locator('_react=SubmitButton[disabled=false]').click();
await page.locator('_vue=submit-button[loading=false]').click();

// ✅ Option 1: accessible role (preferred — mirrors user perception)
await page.getByRole('button', { name: 'Submit' }).click();

// ✅ Option 2: data-testid (when no stable role/label exists)
await page.getByTestId('submit-button').click();

// ✅ Option 3: visible text
await page.getByText('Submit').click();
```

### :light suffix → standard CSS

```typescript
// ❌ REMOVED — :light was used to stop CSS from piercing Shadow DOM
await page.locator('div.card:light .title').click();

// ✅ Replacement: use standard CSS; Playwright now handles Shadow DOM
// piercing via its own engine. If you need to scope, use locator chaining:
await page.locator('div.card').locator('.title').click();

// ✅ Or use getByRole scoped to the host:
await page.locator('div.card').getByRole('heading').click();
```

## Audit Script — Find All Usages

```bash
# Find _react / _vue / :light in test files
rg -n "_react=|_vue=|:light" tests/ --type ts
rg -n "_react=|_vue=|:light" tests/ --type py
```

## Why These Were Removed

The `_react` and `_vue` engines required Playwright to inspect component internals (fiber tree / Vue instance data), which:
- Broke with every major React/Vue version boundary
- Coupled tests to implementation, not user-visible behavior
- Violated Playwright's principle that tests should mirror what users see

The modern locator API (`getByRole`, `getByLabel`, `getByTestId`) is stable across framework versions.

## Priority Migration Order

1. `getByRole()` — best; aligns with ARIA, catches accessibility regressions
2. `getByLabel()` — for form fields with labels
3. `getByText()` — for unique visible text
4. `getByTestId()` — when nothing above is stable; requires `data-testid` in markup
5. CSS/XPath — last resort only

## Sources

- [Playwright Release Notes](https://playwright.dev/docs/release-notes) — "Removed _react and _vue selectors. See locators guide for alternatives."
- [Playwright Locators Guide](https://playwright.dev/docs/locators)
- [BrowserStack: Playwright Selector Best Practices 2026](https://www.browserstack.com/guide/playwright-selectors-best-practices)
- [What's new with Playwright in 2026](https://getdecipher.com/blog/whats-new-with-playwright-in-2026)
