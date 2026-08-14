---
name: playwright-shadow-dom
description: >-
  Testing web components and Shadow DOM elements with Playwright — auto-piercing behavior,
  locator patterns, closed root workarounds, and framework-specific strategies. Use when tests
  target Lit, Shoelace, SAP UI5, Salesforce Lightning, or any app using custom HTML elements with
  shadow roots. Triggers on: shadow DOM, web components, shadow root, custom elements, Shoelace,
  Lit, SAP UI5, pierce, closed shadow.
---

# Playwright Shadow DOM & Web Components Testing

## 1. How Playwright Handles Shadow DOM

Playwright **automatically pierces open shadow roots** for all CSS, text, and ARIA-based locators. You do not need special syntax in the common case.

```typescript
// All of these work even when the target is inside a shadow root:
await page.locator('custom-button button').click();
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByLabel('Email').fill('user@example.com');
await page.getByText('Confirm order').click();
```

**Key rule:** If the component uses `attachShadow({ mode: 'open' })` (the default for Lit, Shoelace, Google Material Web, Salesforce Lightning), Playwright locators pierce it automatically.

## 2. Locator Patterns

### Auto-piercing (preferred)

Chain locators normally — Playwright crosses shadow boundaries at each step:

```typescript
// Nested shadow roots: outer-component > inner-component > button
await page.locator('outer-component').locator('inner-component').locator('button[type="submit"]').click();

// Semantic locators pierce shadow DOM too
await page.locator('sl-dialog').getByRole('button', { name: 'Close' }).click();

// Test-id attributes inside shadow roots
await page.getByTestId('email-field').fill('user@example.com');
```

### CSS shadow-piercing combinator `>>>`

Use `>>>` when you need an explicit single-selector traversal across a shadow boundary:

```typescript
// Explicit pierce combinator
await page.locator('my-form >>> input[type="email"]').fill('user@example.com');

// Multiple levels: outer >>> inner >>> target
await page.locator('app-root >>> user-profile >>> sl-input >>> input').fill('Jane');
```

### Shoelace / Lit patterns

Shoelace components wrap native inputs inside their shadow roots:

```typescript
// sl-input exposes a shadow <input> — getByLabel works automatically
await page.getByLabel('Username').fill('admin');

// sl-button
await page.locator('sl-button[variant="primary"]').click();

// sl-select — open the dropdown, then pick option
await page.locator('sl-select[name="country"]').click();
await page.locator('sl-option[value="vn"]').click();
```

## 3. What Does NOT Pierce Shadow DOM

| Selector Type | Pierces? | Why |
|---|---|---|
| CSS locator (`locator('.class')`) | ✅ Yes | Playwright default behaviour |
| Text locator (`getByText`) | ✅ Yes | Playwright default behaviour |
| Role/ARIA (`getByRole`) | ✅ Yes | Playwright default behaviour |
| Label (`getByLabel`) | ✅ Yes | Playwright default behaviour |
| TestId (`getByTestId`) | ✅ Yes | Playwright default behaviour |
| XPath (`//tag[@attr]`) | ❌ No | XPath cannot cross shadow boundaries |
| `innerHTML()` assertion | ❌ No | Returns empty for shadow content |
| JS `querySelectorAll()` | ❌ No | Does not pierce by default |

```typescript
// WRONG: XPath never pierces
await page.locator('xpath=//my-element/button').click();   // fails

// RIGHT: rewrite to CSS or role
await page.locator('my-element button').click();           // works
await page.locator('my-element').getByRole('button').click(); // works
```

## 4. Closed Shadow Roots

`attachShadow({ mode: 'closed' })` makes `shadowRoot` null — even JavaScript cannot read it. This is rare in UI frameworks but common in browser-native elements (`<input type="date">` spinner UI, `<video>` controls).

**Playwright has no built-in way to pierce closed shadow roots.** Options:

```typescript
// Option 1: page.evaluate() escape hatch — only works if the component
// internally exposes a reference via a property or global
const value = await page.evaluate(() => {
  const el = document.querySelector('my-closed-component') as any;
  // Many frameworks leak a ref even in "closed" mode
  return el?._shadowRoot?.querySelector('.inner-value')?.textContent;
});

// Option 2: keyboard navigation (last resort)
// Click just before the target element, then Tab to it
await page.locator('my-form').click();
await page.keyboard.press('Tab');         // land on first focusable element inside
await page.keyboard.type('test value');

// Option 3: test the component API instead of the DOM
// Many web components expose JS properties you can assert without DOM access
const selected = await page.locator('my-select').evaluate((el: any) => el.value);
expect(selected).toBe('option-a');
```

## 5. Nested Shadow Roots (Deep Nesting)

Playwright handles arbitrary nesting depth. The locator engine descends recursively through shadow boundaries:

```typescript
// Three levels deep
const deepInput = page
  .locator('app-shell')          // light DOM
  .locator('settings-panel')    // first shadow root
  .locator('account-form')      // second shadow root
  .locator('sl-input')          // third shadow root (Shoelace)
  .locator('input');             // actual <input> inside Shoelace's shadow

await deepInput.fill('New name');
await expect(deepInput).toHaveValue('New name');
```

## 6. Framework-Specific Notes

### SAP UI5 / Fiori
UI5 uses a custom patched shadow DOM with internal control IDs. Use the `playwright-sap` wrapper:

```bash
npm install -D playwright-sap
```

```typescript
import { ui5 } from 'playwright-sap';

test('SAP UI5 input', async ({ page }) => {
  await page.goto('/fiori-app');
  await ui5(page).locator({ id: 'username' }).fill('admin');
  await ui5(page).locator({ controlType: 'sap.m.Button', text: 'Login' }).click();
});
```

### Lit Component Isolation Testing
For component-level (not E2E) testing of Lit elements, use `playwright-ct-web`:

```bash
npm install -D playwright-ct-web
```

```typescript
import { test, expect } from '@playwright/experimental-ct-web';
import './my-button.js';

test('renders slot content', async ({ mount }) => {
  const component = await mount(
    '<my-button>Submit</my-button>'
  );
  await expect(component).toContainText('Submit');
  await component.click();
  // assert side-effect
});
```

## 7. Decision Table

| Scenario | Approach |
|---|---|
| Element in open shadow root (Lit, Shoelace, Material Web) | Use normal locators — auto-piercing |
| Nested open shadow roots | Chain `locator().locator()` or `>>>` combinator |
| XPath needed (Selenium migration) | Rewrite to CSS/role — no alternative |
| Closed shadow root | `page.evaluate()` if component leaks ref; keyboard nav as fallback |
| SAP UI5 / Fiori app | `playwright-sap` library |
| Lit/web component isolation (not E2E) | `playwright-ct-web` mount fixture |
| `innerHTML()` content assertion fails | Use `textContent()` or `locator().textContent()` instead |

## 8. Common Pitfall: `innerHTML()` Is Empty

Asserting `innerHTML()` on a shadow host always returns the light-DOM slot content, not the shadow tree:

```typescript
// WRONG: innerHTML of shadow host is empty / just slot markup
const html = await page.locator('my-card').innerHTML();
expect(html).toContain('Card Title'); // fails — shadow not in innerHTML

// RIGHT: target the element inside the shadow root directly
await expect(page.locator('my-card').locator('h2')).toHaveText('Card Title');
```

## Sources

- https://playwright.dev/docs/locators
- https://playwright.dev/docs/other-locators
- https://www.desplega.ai/blog/2026-01-12-deep-dive-shadow-dom-testing
- https://www.testdock.io/articles/handling-shadow-dom-and-web-components-with-playwright
- https://github.com/sand4rt/playwright-ct-web
- https://playwright-sap.dev/intro
- https://webscraping.ai/faq/playwright/what-are-the-ways-to-handle-shadow-dom-elements-using-playwright
- https://medium.com/@erik.amaral/shadow-dom-testing-that-doesnt-flake-using-playwright-1c9313d086d3
