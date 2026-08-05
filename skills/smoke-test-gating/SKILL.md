---
name: smoke-test-gating
description: >-
  Run a smoke test project before the full suite — gate the full run on basic health checks
  passing. Use when setting up any Playwright test suite in CI, configuring playwright.config.ts
  projects, or when environment issues are causing mass test failures. Triggers on: "smoke test",
  "test gating", "playwright projects", "CI pipeline tests", "all tests failing environment",
  "gate full suite", "dependencies between projects".
type: skill
scope: playwright, e2e, automation, ci-cd
triggers:
  - "smoke test"
  - "test gating"
  - "playwright projects"
  - "CI pipeline tests"
  - "all tests failing environment"
  - "gate full suite"
---

# Smoke Test Gating

## Purpose

Prevent wasting time running 33+ tests when the environment is broken, login is invalid, or the app is down. Smoke test runs first — if it fails, full suite never starts.

## Config: Gate Full Suite on Smoke

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    {
      name: 'smoke',
      testMatch: '**/*.smoke.ts',
      retries: 0,                      // No retries — must pass first try
    },
    {
      name: 'full-suite',
      testMatch: '**/*.spec.ts',
      dependencies: ['smoke'],         // Full suite ONLY runs if smoke passes
    },
  ],
});
```

## Smoke Test File (Minimal — max 5 assertions)

```typescript
// tests/smoke.ts
import { test, expect } from '@playwright/test';

test('env: app is reachable', async ({ page }) => {
  await page.goto('/');
  await expect(page).not.toHaveURL(/error|5\d\d/);
  await expect(page).toHaveTitle(/.+/); // any title = app responded
});

test('env: login works', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.TEST_EMAIL!);
  await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page).not.toHaveURL(/login/, { timeout: 60000 });
});

test('env: dashboard loads after login', async ({ page }) => {
  // This test uses storageState from auth setup
  await page.goto('/dashboard');
  await expect(page.getByRole('main')).toBeVisible({ timeout: 10000 });
});
```

## Cold-Start Environments (Replit, etc.)

```typescript
test('env: warm up Replit instance', async ({ page }) => {
  // First request wakes instance — may take 30-60s
  await page.goto('/', { timeout: 90000, waitUntil: 'domcontentloaded' });
  await expect(page).not.toHaveURL(/error/);
});
```

## CI Commands

```bash
# CI — gate is enforced by project dependencies (smoke must pass first)
npx playwright test

# Local — run smoke alone before starting full session
npx playwright test --project=smoke

# If smoke passes, run full suite
npx playwright test --project=smoke && npx playwright test --project=full-suite
```

## Smoke Fail → Stop, Diagnose Environment

When smoke fails, do NOT debug feature tests. Diagnose environment:
1. Is the app running? `curl -I https://your-app.com`
2. Did credentials change? Test login manually in browser
3. Is staging environment asleep? (Replit cold start)
4. Is CI environment configured correctly?

## Rules

- **Smoke: zero retries** — if smoke fails once, environment is broken. Retrying masks it.
- **Smoke: max 5 assertions** — it's a gate, not a regression suite.
- **Full suite: `dependencies: ['smoke']`** — enforced in config, not just documentation.
- **Any new suite added must reference the smoke file** — PR rule.

## Anti-Patterns

| Anti-Pattern | Problem |
|---|---|
| No smoke gate — running 33 tests cold | 33 failures for 1 env issue — wastes 10 min |
| `retries: 1` in smoke | Hides broken environment — fails slow instead of fast |
| Smoke test with 20+ assertions | Smoke is a gate, not regression |
| No `dependencies` in config | Full suite runs even when smoke fails |
| Skipping smoke in CI to save time | 30s saved → 10 min of debugging env failures |

