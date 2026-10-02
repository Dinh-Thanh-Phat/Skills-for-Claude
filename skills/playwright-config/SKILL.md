---
name: playwright-config
description: Correct playwright.config.ts structure — where to place baseURL, timeouts, use options, projects, and global setup. Use when creating or editing playwright.config.ts, seeing TypeScript errors in config, or when baseURL is not being applied. Triggers on: "playwright.config.ts", "baseURL not working", "No overload matches this call", "TypeScript error config", "playwright config", "createConfig", "defineConfig".
type: skill
scope: playwright, e2e, automation
triggers:
  - "playwright.config.ts"
  - "baseURL not working"
  - "No overload matches this call"
  - "TypeScript error config"
  - "playwright config"
  - "defineConfig"
---

# Playwright Config

## Critical Rule: baseURL MUST be inside `use: {}`

```typescript
// ❌ WRONG — TypeScript error (exact message text UNVERIFIED, e.g. "No overload matches this call")
export default defineConfig({
  baseURL: 'https://example.com',  // wrong location
  use: { headless: true },
});

// ✅ CORRECT
export default defineConfig({
  use: {
    baseURL: 'https://example.com',  // inside use
    headless: true,
  },
});
```

## Property Placement Reference

**Inside `use: {}`** (browser/page options):
- `baseURL`, `headless`, `viewport`, `screenshot`, `video`, `trace`
- `storageState`, `locale`, `timezoneId`, `geolocation`
- `extraHTTPHeaders`, `ignoreHTTPSErrors`
- `actionTimeout`, `navigationTimeout`
- `hasTouch`, `isMobile`, `deviceScaleFactor`

**Top level of `defineConfig()`** (NOT in `use`):
- `testDir`, `timeout`, `retries`, `workers`, `reporter`
- `outputDir`, `projects`, `globalSetup`, `globalTeardown`
- `expect: { timeout }`, `fullyParallel`

## Canonical Config Template

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 120000,                          // 2 min per test
  retries: process.env.CI ? 1 : 0,
  workers: 1,                               // stateful tests: sequential
  fullyParallel: false,
  reporter: [
    ['html', { outputFolder: '../TestReport/html', open: 'never' }],
    ['json', { outputFile: '../TestReport/results.json' }],
    ['line'],
  ],
  use: {
    baseURL: process.env.BASE_URL ?? 'https://your-app.com',
    headless: true,
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    viewport: { width: 1280, height: 800 },
  },
  outputDir: '../TestReport/artifacts',     // outside testDir
});
```

## Projects with Dependencies (Smoke Gating + Auth)

```typescript
export default defineConfig({
  projects: [
    // Auth setup runs first
    { name: 'setup', testMatch: '**/auth.setup.ts' },
    // Smoke gates full suite
    {
      name: 'smoke',
      testMatch: '**/*.smoke.ts',
      dependencies: ['setup'],
    },
    // Full suite depends on smoke
    {
      name: 'full-suite',
      testMatch: '**/*.spec.ts',
      dependencies: ['smoke'],
      use: { storageState: '.auth/user.json' },
    },
  ],
});
```

## Environment-Aware Timeouts

```typescript
const isCI = !!process.env.CI;
const isReplit = !!process.env.REPL_ID;

export default defineConfig({
  timeout: isReplit ? 120000 : isCI ? 60000 : 30000,
  use: {
    navigationTimeout: isReplit ? 90000 : isCI ? 30000 : 15000,
    actionTimeout: isCI ? 15000 : 10000,
  },
});
```

## Test Locks & Retry Isolation (1.62/1.63)

`workers: 1` serializes the **whole** suite just because a few tests share state. Since 1.63, declare a named **lock** on only those tests — tests sharing a lock name never run concurrently (across files, workers and projects); everything else stays parallel:

```typescript
// one test
test('update user settings', { lock: 'user-settings' }, async ({ page }) => { /* ... */ });

// a group (a test can hold several locks: lock: ['user-settings', 'billing'])
test.describe('billing admin', { lock: 'billing' }, () => { /* ... */ });

// all tests in the current scope
test.describe.configure({ lock: 'user-settings' });
```

Use for: one shared staging account, a global account setting, a rate-limited 3rd-party sandbox, a singleton seed. Still prefer per-test data isolation (`test-isolation`) when possible — a lock removes the race, not the coupling.

Since 1.62, `retryStrategy` controls **when** retries run:

```typescript
export default defineConfig({
  retries: process.env.CI ? 2 : 0,
  retryStrategy: 'isolated',   // default 'immediate'
  // failOnFlakyTests: true,   // (1.52+) exit non-zero if any test only passed on retry
});
```

- `'immediate'` (default) — retry as soon as a worker is free, interleaved with other tests.
- `'isolated'` — all retries run **at the end, one by one in a single worker** → separates "real regression" from "noise caused by parallel load".

Sources: https://github.com/microsoft/playwright/blob/main/docs/src/test-parallel-js.md#test-locks, test-api/class-test.md (`lock`), release-notes-js.md 1.62 (`retryStrategy`) / 1.63 (locks).

## Anti-Patterns

| Anti-Pattern | Error / Problem | Fix |
|---|---|---|
| `baseURL` at top level | TypeScript: "No overload matches" | Move inside `use: {}` |
| `import path from 'path'` unused | TypeScript lint error | Remove unused imports |
| `timeout: 30000` on Replit | First test always times out | Set 120000 for cold-start envs |
| `workers: 4` with stateful tests | Race conditions corrupt state | 1.63+: `{ lock: '<resource>' }` on the conflicting tests; older versions: `workers: 1` |
| `retries: 0` in CI | Infra noise = failed pipelines | `retries: process.env.CI ? 1 : 0` |
| `outputDir: './tests/results'` | Artifacts mixed with test files | Put outputDir outside testDir |

## TypeScript Validation

```bash
# Run before committing config changes — catches placement errors
npx tsc --noEmit
```

