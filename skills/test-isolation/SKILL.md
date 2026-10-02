---
name: test-isolation
description: Playwright test isolation patterns — prevent shared state, flaky tests from test order dependency, use timestamps for unique data. Use when writing E2E tests that might interfere with each other, when tests fail only in certain orders, or when adding beforeEach/afterEach. Triggers on: "test isolation", "shared state", "test order", "flaky test", "beforeEach", "test data cleanup", "parallel test fail".
type: qa-practice
triggers:
  - "test isolation"
  - "shared state"
  - "test order"
  - "flaky test"
  - "beforeEach"
  - "test data cleanup"
  - "parallel test fail"
scope: playwright, e2e-testing
---

# Test Isolation — No Shared State

**Rule:** Each test must be fully independent. A test must pass whether run alone, in any order, or in parallel.

## Why Tests Fail Due to Shared State

```
Test A: Creates email template "My Template"
Test B: Expects NO template named "My Template" to exist → FAILS because A ran first
```

Or the reverse:
```
Test A: Deletes all templates
Test B: Expects a template to exist → FAILS because A ran first
```

Both are **order-dependent failures** — flaky, hard to debug.

## Pattern 1: Unique Test Data (Timestamps)

```typescript
// ✅ Each test run creates unique, non-colliding data
const timestamp = Date.now();
const templateName = `Test Template ${timestamp}`;
const email = `test+${timestamp}@example.com`;

await page.fill('[name="template-name"]', templateName);
```

Never use hardcoded names like `"Test Template"` — multiple parallel runs collide.

## Pattern 2: beforeEach — Setup Known State

```typescript
test.describe('Email Templates', () => {
  let timestamp: number; // shared by beforeEach / test / afterEach of the SAME test

  test.beforeEach(async ({ page }) => {
    timestamp = Date.now();
    // Always start from a clean, known state
    await page.goto('/templates');
    await expect(page.getByRole('heading', { name: /templates/i })).toBeVisible();
    // If test needs a template: create it here, not in a previous test
  });

  test.afterEach(async ({ page }) => {
    // Clean up data this test created (only names containing this test's timestamp)
    await deleteTestTemplates(page, timestamp);
  });
});
```

## Pattern 3: Use Fixtures for Reusable Setup

```typescript
// tests/fixtures.ts
import { test as base } from '@playwright/test';

export const test = base.extend({
  loggedInPage: async ({ page }, use) => {
    await login(page, { email: process.env.TEST_EMAIL!, password: process.env.TEST_PASSWORD! });
    await use(page);
    // code after use() = teardown; put cleanup of data this fixture created here
    // (the page/context itself is closed by Playwright automatically)
  },
});
```

```typescript
// In test file
import { test } from '../fixtures';

test('create template', async ({ loggedInPage }) => {
  // page is already logged in, fresh every test
});
```

## Pattern 4: Browser Context Isolation (built-in)

Playwright automatically creates a fresh browser context per test:
- No shared cookies
- No shared localStorage
- No shared session state

This handles **auth isolation** automatically when using fixtures correctly.

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    storageState: '.auth/user.json', // written once by a setup project, loaded into each fresh context
  },
});
```
(The file must be produced by a `setup` project dependency — see `auth-session-testing`.)

## Pattern 5: API Setup Instead of UI Setup

For prerequisites (e.g., "test needs a campaign to exist"), use API calls in `beforeEach` instead of UI clicks — faster and more reliable:

```typescript
test.beforeEach(async ({ request }) => {
  // Create prerequisite data via API — no UI flakiness
  await request.post('/api/templates', {
    data: { name: `Template ${Date.now()}`, content: 'test' }
  });
});
```

## Checklist for Each Test

- [ ] Test uses unique data (timestamp-based IDs, emails, names)
- [ ] Test does NOT depend on another test having run first
- [ ] Test does NOT depend on another test NOT having run
- [ ] `beforeEach` sets up all preconditions this test needs
- [ ] `afterEach` (or API) cleans up data this test created
- [ ] Test passes when run in isolation: `npx playwright test --grep "TC-001"`

## Pattern 6: Isolation for Shared DB / File System / Global Mock

When tests share a real DB or file system, namespace EVERY write with the test:
```typescript
const testNs = `t${Date.now()}_${Math.random().toString(36).slice(2,6)}`;
await db.execute(`INSERT INTO records (key, value) VALUES (?, ?)`,
                 [`${testNs}:key1`, 'val']);

test.afterEach(async () => {
  await db.execute(`DELETE FROM records WHERE key LIKE ?`, [`${testNs}:%`]);
});
```

For global JS state in **unit tests** (Vitest mock state, module singletons — not Playwright):
```typescript
// vitest
afterEach(() => {
  vi.restoreAllMocks();   // reset mocks
  // reset any module-level state your code accumulates
});
```

## Running a Single Test to Verify Isolation

```bash
# Run just one test — it should pass without needing others to run first
npx playwright test tests/email-campaign/templates.spec.ts --grep "TMP-008"
```

**Sources:** Playwright Best Practices, Playwright Browser Contexts docs

---

## Cross-references (test data — 3 skills, 1 goal)

- **this skill** — broader isolation: state, cookies, auth, parallel (dùng khi test fail do shared state)
- **`test-data-lifecycle`** — rule "always clean up" + 3 strategies phổ biến (dùng khi viết test)
- **`test-data-lifecycle-strategy`** — "nên dùng strategy nào?" decision guide (dùng khi planning)

