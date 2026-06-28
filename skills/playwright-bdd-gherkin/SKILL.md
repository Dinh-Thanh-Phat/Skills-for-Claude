---
name: playwright-bdd-gherkin
description: >-
  Set up BDD (Behavior-Driven Development) with Gherkin feature files on top of Playwright's native
  test runner using the `playwright-bdd` library — readable Given/When/Then scenarios that any
  stakeholder can review, backed by Playwright's full toolchain (Trace Viewer, HTML reporter,
  parallelism, retries). Use when the team wants stakeholder-readable test scenarios, when moving
  from Selenium+Cucumber to Playwright, when acceptance tests must be written in Gherkin, or when
  coordinating QA with product owners who define acceptance criteria in plain language. Triggers on:
  "BDD Playwright", "Gherkin Playwright", "Cucumber Playwright", "playwright-bdd", "Given When Then
  Playwright", "feature file Playwright", "acceptance tests Playwright", "BDD test design".
---

# BDD with Playwright: playwright-bdd Library

Behavior-Driven Development (BDD) combines human-readable Gherkin scenarios with Playwright's
automation power. The `playwright-bdd` library (by Vitalets) converts `.feature` files into
Playwright test files at build time — you get Gherkin's readability **and** Playwright's Trace
Viewer, parallelism, and web-first assertions, without a separate Cucumber process.

## playwright-bdd vs @cucumber/cucumber — when to choose

| | `playwright-bdd` | `@cucumber/cucumber` |
|---|---|---|
| Test runner | Playwright native (`npx playwright test`) | Cucumber native |
| Trace Viewer | ✅ Full support | ❌ Not available |
| HTML reporter | ✅ Playwright's built-in | Separate reporter install |
| Parallelism | ✅ Playwright workers | Custom setup required |
| `test.use()` / fixtures | ✅ Full Playwright fixture system | Limited to Cucumber hooks |
| Retries & `--last-failed` | ✅ | ❌ |
| Existing Cucumber plugin ecosystem | Limited | ✅ Rich |
| **Choose when** | **New project; Playwright-first team** | **Migrating existing Cucumber suite** |

---

## Setup

```bash
npm install -D @playwright/test playwright-bdd
npx playwright install chromium   # if not already installed
```

### playwright.config.ts

```typescript
import { defineConfig, devices } from '@playwright/test';
import { defineBddConfig } from 'playwright-bdd';

const testDir = defineBddConfig({
  paths: ['features/**/*.feature'],  // .feature files
  require: ['steps/**/*.ts'],         // step definitions
  // importTestFrom: 'fixtures.ts',  // uncomment if using custom fixtures
});

export default defineConfig({
  testDir,
  reporter: 'html',
  use: { baseURL: 'http://localhost:3000' },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

---

## Writing feature files

```gherkin
# features/login.feature
Feature: User Login

  Background:
    Given I am on the login page

  Scenario: Successful login with valid credentials
    When I enter email "user@example.com" and password "secret123"
    And I click the submit button
    Then I should be redirected to the dashboard
    And I should see a welcome message

  Scenario: Failed login with wrong password
    When I enter email "user@example.com" and password "wrong"
    And I click the submit button
    Then I should see an error message "Invalid credentials"

  Scenario Outline: Login with multiple locales
    Given the browser locale is set to "<locale>"
    When I enter email "user@example.com" and password "secret123"
    Then the dashboard title should be "<expected_title>"

    Examples:
      | locale  | expected_title |
      | en-US   | Dashboard      |
      | fr-FR   | Tableau de bord|
```

---

## Step definitions

```typescript
// steps/login.steps.ts
import { Given, When, Then } from 'playwright-bdd';
import { expect } from '@playwright/test';

// Direct page access — Playwright fixtures available in steps
Given('I am on the login page', async ({ page }) => {
  await page.goto('/login');
  await expect(page).toHaveTitle(/Login/);
});

When('I enter email {string} and password {string}', async ({ page }, email, password) => {
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
});

When('I click the submit button', async ({ page }) => {
  await page.getByRole('button', { name: 'Sign in' }).click();
});

Then('I should be redirected to the dashboard', async ({ page }) => {
  await expect(page).toHaveURL(/\/dashboard/);
});

Then('I should see a welcome message', async ({ page }) => {
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
});

Then('I should see an error message {string}', async ({ page }, message) => {
  await expect(page.getByRole('alert')).toHaveText(message);
});
```

### Gherkin parameter types (built-in)

| Token | Matches | TypeScript type |
|---|---|---|
| `{string}` | quoted string `"foo"` | `string` |
| `{int}` | integer | `number` |
| `{float}` | decimal number | `number` |
| `{word}` | single word (no spaces) | `string` |
| `/regex/` | custom regex | `string` |

---

## Integrating Page Object Model (POM)

Use Playwright fixtures to inject POM instances into step definitions:

```typescript
// fixtures.ts — extend playwright-bdd's test with POM fixtures
import { test as base } from 'playwright-bdd';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';

type Fixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
});
```

```typescript
// playwright.config.ts — point defineBddConfig to the fixture file
const testDir = defineBddConfig({
  paths: ['features/**/*.feature'],
  require: ['steps/**/*.ts'],
  importTestFrom: 'fixtures.ts',   // use custom test with POM fixtures
});
```

```typescript
// steps/login.steps.ts — use POM via fixture injection
import { Given, When, Then } from 'playwright-bdd';

Given('I am on the login page', async ({ loginPage }) => {
  await loginPage.navigate();
});

When('I enter email {string} and password {string}', async ({ loginPage }, email, password) => {
  await loginPage.fillCredentials(email, password);
});

Then('I should be redirected to the dashboard', async ({ dashboardPage }) => {
  await dashboardPage.assertIsLoaded();
});
```

---

## Hooks (before/after scenarios)

```typescript
// steps/hooks.ts
import { Before, After, BeforeAll, AfterAll } from 'playwright-bdd';

// Runs before each scenario — use for per-test setup
Before(async ({ page }) => {
  await page.goto('/');
});

// Scoped to a Gherkin tag — only runs for @auth scenarios
Before({ tags: '@auth' }, async ({ page, context }) => {
  // Restore saved auth state
  await context.addCookies([{ name: 'auth', value: 'token', domain: 'example.com', path: '/' }]);
});

After(async ({ page }, scenario) => {
  // Take screenshot on failure
  if (scenario.result?.status === 'FAILED') {
    await page.screenshot({ path: `screenshots/${scenario.pickle.name}.png` });
  }
});
```

---

## Tags — organize and filter scenarios

```gherkin
@smoke @auth
Scenario: Admin login
  ...

@regression @slow
Scenario: Full checkout flow
  ...
```

```bash
# Run only smoke tests
npx playwright test --grep @smoke

# Exclude slow tests
npx playwright test --grep-invert @slow

# Run multiple tags (AND logic)
npx playwright test --grep "@smoke.*@auth"
```

---

## Running tests

```bash
# Generate Playwright tests from .feature files, then run
npx playwright test

# UI mode with Gherkin scenarios visible
npx playwright test --ui

# Run a specific feature
npx playwright test --grep "User Login"

# See the generated test files (playwright-bdd caches them in .features-gen/)
cat .features-gen/features/login.feature.spec.js
```

---

## Project structure (recommended)

```
project/
├── features/
│   ├── login.feature
│   └── checkout.feature
├── steps/
│   ├── login.steps.ts
│   ├── checkout.steps.ts
│   └── hooks.ts
├── pages/               # Page Object Model
│   ├── LoginPage.ts
│   └── DashboardPage.ts
├── fixtures.ts          # Custom Playwright fixtures
└── playwright.config.ts
```

---

## Authoring guidelines (keep BDD sustainable)

- **Feature files are specifications, not scripts.** Write at the *business intent* level:
  `When I complete my purchase` not `When I click button "Buy Now" and wait 1 second`.
- **One scenario = one behavior.** Avoid multi-assertion monster scenarios.
- **Avoid implementation details in Gherkin.** No locators, no pixel coordinates, no UI IDs.
- **Use `Background:` for shared context**, not repeated `Given` steps in each scenario.
- **Prefer `Scenario Outline:` over copy-pasted scenarios** for data-driven cases.
- **Tag deliberately.** At minimum: `@smoke`, `@regression`, `@slow`.

---

## Anti-patterns to avoid

| Anti-pattern | Why it hurts | Better approach |
|---|---|---|
| `When I click button with id "btn-submit-123"` | Ties Gherkin to implementation | `When I submit the form` |
| 200-line step definition file | Hard to navigate | One file per feature area |
| `And I wait 3 seconds` in Gherkin | Timing dependency | Wait in step impl with Playwright auto-wait |
| Duplicating POM logic in steps | Two sources of truth | Inject POM via fixture; steps delegate to POM |
| Translating every unit test to Gherkin | BDD overhead without value | BDD for acceptance/integration scenarios only |

## Sources
- https://testdino.com/blog/playwright-bdd
- https://medium.com/@tito.irfanwibisono/behavior-driven-development-bdd-with-gherkin-cucumber-and-playwright-a-practical-guide-9c38396c4c11
- https://www.browserstack.com/guide/playwright-cucumber
- https://medium.com/@sreekanth.parikipandla/playwright-bdd-with-typescript-a-practical-guide-to-fast-readable-e2e-tests-6bd1dca6b3d1
- https://github.com/vitalets/playwright-bdd
