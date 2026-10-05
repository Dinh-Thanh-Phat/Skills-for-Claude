---
name: dom-inspect-first
description: Always inspect the real DOM/accessibility tree before writing Playwright selectors — prevents selector mismatch bugs. Use when writing any Playwright locator, selector, getByRole, getByText, or when element is not found. Triggers on: "viết selector", "write locator", "find element", "getByRole", "element không thấy", "element not visible", "can't find element".
type: qa-practice
triggers:
  - "viết selector"
  - "write locator"
  - "find element"
  - "getByRole"
  - "element không thấy"
  - "element not visible"
  - "can't find element"
scope: playwright, e2e-testing
---

# DOM Inspect First

**Rule:** Never write a Playwright selector based on assumption. Always verify the real DOM first.

## Why

The #1 cause of broken selectors:
- Assumed text "English" → actual DOM has "EN"
- Assumed `<input>` → actual element is `<textarea>`
- Assumed role `button` → actual role is `combobox`

## Step-by-Step: Before Writing Any Selector

### Step 1: Use Playwright Inspector (fastest)
```bash
npx playwright test --ui
# Or open browser in headed mode with pause:
await page.pause(); // add to test, run it, inspect element in the UI
```

### Step 2: Snapshot the Accessibility Tree
```typescript
// Add to test temporarily to see actual roles + names
const snapshot = await page.locator('body').ariaSnapshot();
console.log(snapshot);
```

Output example:
```yaml
- combobox "Select language":
  - option "VI"
  - option "EN"       ← actual text, NOT "English"
```

### Step 3: Use Chrome DevTools Accessibility Panel
- Open DevTools → Accessibility tab
- Click on the element → see: Role, Name, Value

### Step 4: Check visible text directly
```typescript
// Before writing filter, print actual text:
console.log(await page.getByRole('option').allTextContents()); // no index loop / .nth() needed
```

## Locator Priority Order

| Priority | Method | Use when |
|---|---|---|
| 1 | `getByRole()` | Element has semantic role + accessible name |
| 2 | `getByLabel()` | Form fields with `<label>` |
| 3 | `getByPlaceholder()` | Inputs with placeholder |
| 4 | `getByText()` | Static visible text |
| 5 | `getByTestId()` | `data-testid` attributes |
| ❌ | CSS/XPath | Avoid — brittle, DOM-dependent |

## Checklist Before Committing a Selector

- [ ] I've inspected the accessibility tree or run `ariaSnapshot()`
- [ ] The text in `hasText` matches actual DOM text (not assumed)
- [ ] The role matches actual ARIA role (use DevTools Accessibility panel)
- [ ] I've verified element type (`input` vs `textarea` vs `div`)

## Quick Debug Snippet

```typescript
// Paste this anywhere in a test to debug selectors
test.only('debug: inspect element', async ({ page }) => {
  await page.goto('/your-page');
  await page.pause(); // Opens Playwright Inspector
});
```

**Sources:** Playwright Best Practices, ARIA Snapshots docs

