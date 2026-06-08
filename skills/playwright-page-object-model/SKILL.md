---
name: playwright-page-object-model
description: Playwright Page Object Model patterns — organizing locators, actions, and assertions into reusable classes. Use when structuring any Playwright test suite, creating new test files, or when the same UI interactions appear in 3+ tests. Triggers on: "page object model", "POM", "page object", "locator encapsulation", "reusable page", "test organization", "action method", "page class", "component object".
origin: research
scope: testing, playwright, pom, code-organization
triggers:
  - "page object model"
  - "POM"
  - "page object"
  - "locator encapsulation"
  - "reusable page"
  - "test organization"
  - "action method"
  - "page class"
  - "component object"
---

# Playwright Page Object Model

## Core Principle

Tests describe **WHAT** the user does. Page Objects describe **HOW** to do it.

```typescript
// Test (WHAT)
await templatePage.create(templateName);
await templatePage.expectCreatedSuccessfully(templateName);

// Not this in tests
await page.getByRole('button', { name: 'Create Template' }).click();
await page.getByLabel('Template Name').fill(templateName);
await page.getByRole('button', { name: 'Save' }).click();
```

## Structure

```
tests/
  pages/              ← Page Objects
    login.page.ts
    dashboard.page.ts
    template.page.ts
  components/         ← Reusable UI components
    toast.component.ts
    modal.component.ts
  fixtures/
    auth.fixture.ts
  specs/              ← Tests (thin, readable)
    templates.spec.ts
```

## Page Object Pattern

```typescript
// pages/template.page.ts
import { Page, Locator, expect } from '@playwright/test';

export class TemplatePage {
  readonly page: Page;

  // ✅ Locators as GETTERS — always fresh, no stale references
  get createBtn()    { return this.page.getByRole('button', { name: 'Create Template' }); }
  get nameInput()    { return this.page.getByLabel('Template Name'); }
  get saveBtn()      { return this.page.getByRole('button', { name: 'Save' }); }
  get templateList() { return this.page.locator('[data-testid="template-list"]'); }

  constructor(page: Page) { this.page = page; }

  async goto() {
    await this.page.goto('/templates');
    await this.templateList.waitFor({ state: 'visible' });
  }

  // ACTION methods — perform operations, no assertions inside
  async create(name: string) {
    await this.createBtn.click();
    await this.nameInput.fill(name);
    await this.saveBtn.click();
  }

  async delete(name: string) {
    await this.getRow(name).getByRole('button', { name: 'Delete' }).click();
    await this.page.getByRole('button', { name: 'Confirm' }).click();
  }

  async deleteIfExists(name: string) {
    const rows = this.page.locator('tr').filter({ hasText: name });
    const count = await rows.count();
    for (let i = 0; i < count; i++) {
      await rows.first().getByRole('button', { name: 'Delete' }).click();
      await this.page.getByRole('button', { name: 'Confirm' }).click();
    }
  }

  // QUERY methods — return locators for test assertions
  getRow(name: string): Locator {
    return this.page.locator('tr').filter({ hasText: name });
  }

  // ASSERTION methods — only for complex/reused assertions
  async expectCreatedSuccessfully(name: string) {
    await expect(this.page.getByRole('status')).toContainText(/success/i);
    await expect(this.getRow(name)).toBeVisible();
  }
}
```

## Component Objects (Reusable UI Elements)

```typescript
// components/modal.component.ts
export class ModalComponent {
  constructor(private page: Page) {}

  get dialog()     { return this.page.getByRole('dialog'); }
  get confirmBtn() { return this.dialog.getByRole('button', { name: /confirm|yes|ok/i }); }

  async confirm() {
    await this.dialog.waitFor({ state: 'visible' });
    await this.confirmBtn.click();
    await this.dialog.waitFor({ state: 'hidden' });
  }
}
```

## Composition (Not Inheritance)

```typescript
// ✅ Compose components into page objects
class TemplatePage {
  readonly modal: ModalComponent;
  readonly toast: ToastComponent;

  constructor(private page: Page) {
    this.modal = new ModalComponent(page);
    this.toast = new ToastComponent(page);
  }

  async delete(name: string) {
    await this.getRow(name).getByRole('button', { name: 'Delete' }).click();
    await this.modal.confirm();       // reuse modal component
    await this.toast.expectSuccess(); // reuse toast component
  }
}

// ❌ Avoid deep inheritance chains
class AdminPage extends BasePage extends AuthenticatedPage { ... }
```

## Test Using POM

```typescript
test.describe('Template management', () => {
  let templatePage: TemplatePage;
  let templateName: string;

  test.beforeEach(async ({ page }) => {
    templatePage = new TemplatePage(page);
    templateName = `AT-TMP ${Date.now()}`;
    await templatePage.goto();
    await templatePage.deleteIfExists(templateName);
  });

  test.afterEach(async () => {
    await templatePage.deleteIfExists(templateName).catch(() => {});
  });

  test('create template', async () => {
    await templatePage.create(templateName);
    await templatePage.expectCreatedSuccessfully(templateName);
  });
});
```

## When NOT to Use POM

- One-off tests that won't be reused
- Smoke tests (keep flat and readable)
- Tests with fewer than 3 locators
- Exploration/discovery tests

## Composable Fixtures as an Alternative (2026)

For small-to-medium suites (< 200 specs), Playwright's `test.extend()` fixtures give the same isolation and reusability with less boilerplate than class hierarchies. In 2026, this is the community-preferred pattern for new suites.

```typescript
// fixtures/app.fixture.ts
import { test as base } from '@playwright/test';
import { TemplatePage } from '../pages/template.page';

type AppFixtures = {
  templatePage: TemplatePage;
};

export const test = base.extend<AppFixtures>({
  // Fixture: depends on built-in `page`; Playwright composes them automatically
  templatePage: async ({ page }, use) => {
    const templatePage = new TemplatePage(page);
    await templatePage.goto();
    await use(templatePage);   // test runs here
    // teardown (e.g. cleanup) goes after use() if needed
  },
});

export { expect } from '@playwright/test';
```

```typescript
// specs/templates.spec.ts — no beforeEach, no manual instantiation
import { test, expect } from '../fixtures/app.fixture';

test('create template', async ({ templatePage }) => {
  await templatePage.create('My Template');
  await templatePage.expectCreatedSuccessfully('My Template');
});
```

**Prefer fixtures over POM when:**
- New suite, small-to-medium size (< 200 specs) — less class hierarchy ceremony
- Setup is stateful (auth sessions, seeded data) — explicit setup/teardown in one place
- Tests need different combinations of setup — fixtures compose without inheritance

**Keep POM when:**
- 200+ specs across many engineers — shared Page class vocabulary aids coordination
- Migrating from Selenium — POM is already the team's mental model
- UI structure is very stable — the abstraction cost pays back over time

The two are not mutually exclusive: use fixtures for the setup/teardown lifecycle, and POM classes for interaction methods inside those fixtures.

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| `readonly btn = this.page.locator(...)` as property | Stale reference if DOM changes | Use getter: `get btn() { return ... }` |
| Assertions inside action methods | Test can't control assertion behavior | Move to `expectX()` methods |
| One giant 300-line Page Object | Hard to maintain | Split by feature section |
| POM for every single test | Over-engineering | Only when 3+ tests reuse the flow |

