---
name: radix-ui-playwright
description: >-
  Cheatsheet for testing Radix UI components with Playwright — Select, Tabs, Dialog, Dropdown,
  handles portal rendering. Use when testing any Radix UI component, shadcn/ui, or any component
  library that renders to DOM portals. Triggers on: "radix ui", "combobox", "listbox",
  "tabpanel", "select option không thấy", "portal", "options not found", "shadcn".
type: qa-practice
triggers:
  - "radix ui"
  - "combobox"
  - "listbox"
  - "tabpanel"
  - "select option không thấy"
  - "portal"
  - "shadcn"
  - "options not found"
scope: playwright, radix-ui, e2e-testing
---

# Radix UI — Playwright Cheatsheet

Radix UI renders many components into DOM portals (outside the trigger element). Standard `.locator('select option')` won't work.

## Select / Combobox

```typescript
// ✅ Open the select
const trigger = page.getByRole('combobox').filter({ hasText: /Select a template/i });
await trigger.click();

// ✅ Options are rendered in a portal — use page scope, NOT trigger scope
const option = page.getByRole('option', { name: 'Bilingual Template' });
await option.click();

// ❌ WRONG — options not children of the combobox in DOM
const option = trigger.getByRole('option', { name: 'Bilingual Template' });
```

**If click causes instant open/close (known Radix bug):**
```typescript
// Use keyboard navigation instead of click
await trigger.focus();
await trigger.press('Enter');
await page.getByRole('option', { name: 'English' }).click();
```

## Tabs / TabPanel

```typescript
// ✅ Click a tab
await page.getByRole('tab', { name: 'English' }).click();

// ✅ Scope content queries to the active tabpanel
const panel = page.getByRole('tabpanel', { name: 'English' });
await panel.getByRole('textbox', { name: 'Subject' }).fill('My subject');

// ❌ WRONG — will match fields in ALL tabs (ambiguous)
await page.getByRole('textbox', { name: 'Subject' }).fill('My subject');
```

## Dialog / Modal

```typescript
// ✅ Trigger dialog
await page.getByRole('button', { name: 'Open Dialog' }).click();

// ✅ Scope all queries inside the dialog
const dialog = page.getByRole('dialog');
await dialog.getByRole('textbox', { name: 'Email' }).fill('test@example.com');
await dialog.getByRole('button', { name: 'Confirm' }).click();

// ✅ Wait for dialog to close
await expect(dialog).not.toBeVisible();
```

## Dropdown Menu

```typescript
// ✅ Open menu
await page.getByRole('button', { name: 'Actions' }).click();

// ✅ Menu items
await page.getByRole('menuitem', { name: 'Delete' }).click();

// ✅ If submenu
await page.getByRole('menuitem', { name: 'Export' }).hover();
await page.getByRole('menuitem', { name: 'Export as CSV' }).click();
```

## Short Codes vs Full Names

Radix Select options often use short codes. Always inspect first:

```typescript
// ❌ Assumed full name
page.getByRole('option').filter({ hasText: /english/i })

// ✅ Actual short code (verify with ariaSnapshot first!)
page.getByRole('option').filter({ hasText: /^EN$/ })
```

## Key Rules

1. **Options are in a portal** — always query from `page`, never from the trigger
2. **TabPanel scoping** — always wrap content queries in `getByRole('tabpanel', { name })`
3. **Dialog scoping** — always wrap content queries in `getByRole('dialog')`
4. **Short codes** — always inspect actual option text before writing `hasText`
5. **Keyboard fallback** — if `.click()` on combobox fails, try `.press('Enter')` instead

**Sources:** Radix UI docs, GitHub issue #2288, Playwright locators docs

