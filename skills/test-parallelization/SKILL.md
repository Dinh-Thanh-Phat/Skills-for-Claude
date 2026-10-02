---
name: test-parallelization
description: Playwright parallel test execution — workers, sharding, isolation strategies. Use when configuring parallel tests, debugging parallel failures, setting up CI sharding, or ensuring test isolation for concurrent execution. Triggers on: "parallel tests", "test workers", "shard", "run tests in parallel", "chạy test song song", "test worker", "CI sharding".
triggers:
  - "parallel tests"
  - "test workers"
  - "shard"
  - "run tests in parallel"
  - "chạy test song song"
  - "fullyParallel"
  - "CI sharding"
  - "test isolation parallel"
scope:
  - qa
  - e2e
  - playwright
  - ci
---

# Test Parallelization Skill

You are a **Senior QA Engineer** configuring Playwright tests to run in parallel safely and efficiently.

## Core Law

> **Parallel tests must be completely independent.**
> Any shared mutable state (DB records, auth sessions, files) will cause intermittent failures.

---

## Parallelization Modes

### Mode 1: `fullyParallel: true` (recommended)
Each test file AND each test within a file runs in a separate worker.
```typescript
// playwright.config.ts
export default defineConfig({
  fullyParallel: true,
  workers: process.env.CI ? 4 : 2, // CI: more workers; local: fewer
});
```
**Best for:** Independent tests with good data isolation.

### Mode 2: File-level parallel (default)
Each FILE gets its own worker. Tests within a file run serially.
```typescript
export default defineConfig({
  fullyParallel: false, // default
  workers: 4,
});
```
**Best for:** Tests within a file that share setup (describe blocks with beforeAll).

### Mode 3: Serial within describe
```typescript
// `test.describe.serial` is DISCOURAGED in the API docs — use describe.configure instead
test.describe('Checkout flow', () => {
  test.describe.configure({ mode: 'serial' }); // run in order; if one fails, the rest are skipped
  test('Step 1: Add to cart', async ({ page }) => { ... });
  test('Step 2: Enter shipping', async ({ page }) => { ... });
  test('Step 3: Confirm order', async ({ page }) => { ... });
});
```
**Use sparingly** — serial describes block parallel speedup. Note: serial mode does NOT share
the `page` — each test still gets a fresh page/context. Only server-side state chains between
tests (prefer one test with `test.step()` for a real multi-step flow).

---

## Worker Count Guidelines

| Environment | Workers | Reason |
|-------------|---------|--------|
| Local dev (4-core) | 2 | Leaves cores for other work |
| Local dev (8-core) | 4 | Good balance |
| CI (GitHub Actions standard) | 4 | 2 vCPU × 2 |
| CI (GitHub Actions large runner) | 8 | 4 vCPU × 2 |
| CI with DB tests | 2-4 | DB connection pool limits |

```typescript
workers: process.env.CI ? 4 : 2,
```

---

## Authentication Strategy for Parallel Tests

### Problem: Multiple workers logging in simultaneously can cause session conflicts.

### Solution A: One shared read-only auth state (setup project)
```typescript
// tests/auth.setup.ts — runs ONCE before the dependent project
// (a setup project gets baseURL/fixtures; a hand-launched browser in globalSetup does NOT,
//  so a relative page.goto('/login') there fails)
import { test as setup, expect } from '@playwright/test';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.TEST_EMAIL!);
  await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('/dashboard');

  // Save auth state — workers will READ this, not modify it
  await page.context().storageState({ path: 'tests/.auth/user.json' });
});
```

```typescript
// playwright.config.ts
projects: [
  { name: 'setup', testMatch: /auth\.setup\.ts/ },
  {
    name: 'chromium',
    use: { storageState: 'tests/.auth/user.json' }, // all workers share this READ-ONLY
    dependencies: ['setup'],
  },
],
```
Full pattern (roles, OAuth, expiry): `auth-session-testing`.

### Solution B: Per-worker auth (for tests that modify auth state)
```typescript
// Each worker gets its own test user.
// Use parallelIndex (0..workers-1, REUSED when a worker restarts after a failure),
// NOT workerIndex (TEST_WORKER_INDEX) — that gets a NEW unique value after every restart,
// so you'd run out of pre-provisioned users.
const parallelIndex = test.info().parallelIndex; // or process.env.TEST_PARALLEL_INDEX
const testEmail = `test-worker-${parallelIndex}@test.example.com`;
```

---

## Data Isolation for Parallel Tests

### Problem: Two workers create a record with the same name → duplicate key error.

### Solution: Unique data per test, not per suite
```typescript
test('Create campaign', async ({ page }) => {
  // Include timestamp + random to ensure uniqueness across parallel runs
  const name = `AT-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
  await campaignPage.create(name);
  // ...
  await campaignPage.delete(name); // cleanup in same test
});
```

---

## Database Considerations in Parallel

```typescript
// ❌ Parallel risk — both workers delete "all records matching status=test"
test.afterEach(async () => {
  await db.query("DELETE FROM records WHERE name LIKE 'test%'");
});

// ✅ Safe — delete only THIS test's specific record
test.afterEach(async () => {
  if (createdRecordId) {
    await db.query('DELETE FROM records WHERE id = $1', [createdRecordId]);
  }
});
```

---

## CI Sharding — Split Tests Across Multiple Machines

Sharding runs a fraction of the test suite on each machine:

```bash
# Machine 1: runs 1/4 of tests
npx playwright test --shard=1/4

# Machine 2: runs 2/4 of tests
npx playwright test --shard=2/4

# Machine 3, 4: similar
```

### Step 1: Enable blob reporter in CI

The blob reporter emits a `.zip` per shard that can be merged after all shards finish. Without it, each shard only produces a standalone HTML report that can't be combined.

```typescript
// playwright.config.ts
export default defineConfig({
  reporter: process.env.CI ? 'blob' : 'html',  // blob in CI, human-readable HTML locally
  fullyParallel: true,
  workers: process.env.CI ? 4 : 2,
});
```

### Step 2: GitHub Actions sharding + merge

```yaml
jobs:
  test:
    strategy:
      matrix:
        shardIndex: [1, 2, 3, 4]
        shardTotal: [4]
    steps:
      - run: npx playwright test --shard=${{ matrix.shardIndex }}/${{ matrix.shardTotal }}
      - uses: actions/upload-artifact@v4
        with:
          name: blob-report-${{ matrix.shardIndex }}
          path: blob-report/

  merge-reports:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          path: all-blob-reports/
          pattern: blob-report-*
          merge-multiple: true
      - run: npx playwright merge-reports --reporter html ./all-blob-reports
      - uses: actions/upload-artifact@v4
        with:
          name: html-report
          path: playwright-report/
```

### Optimal shard count (2026 guidance)

The sweet spot for most teams is **4–6 shards × 2–4 workers each** — yields ~80% time reduction without runaway CI costs. Scale up shards (not workers) once a single machine can't finish in your time budget (~5–10 min threshold).

| Suite size | Recommended config | Wall time reduction |
|-----------|-------------------|-------------------|
| 50–200 tests | 4 shards × 2 workers | ~75% |
| 200–500 tests | 4 shards × 4 workers | ~80% |
| 500+ tests | 6 shards × 4 workers | ~85% |

---

## Debugging Parallel Failures

### Step 1: Does the test fail alone?
```bash
npx playwright test tests/my-test.spec.ts --grep "failing test name" --workers=1
```
- Fails alone → broken test, not parallel issue
- Passes alone → parallel/isolation issue

### Step 2: Does it fail with just 2 workers?
```bash
npx playwright test --workers=2
```
- Fails with 2 → likely data collision or shared state
- Passes with 2 → race condition specific to higher worker count

### Step 3: Does it fail with randomized order?
```bash
npx playwright test --shuffle
```
- New failures → hidden ordering dependency

---

## Common Parallel Failures and Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| "Duplicate key" DB error | Two workers create same unique record | Add unique suffix (timestamp) to test data |
| "Element not found" in second run | Test doesn't clean up, next test sees leftover | Add afterEach cleanup |
| "Session expired" or "Already logged in" | Workers share mutable auth state | Use read-only storageState or per-worker users |
| "Port already in use" | Two workers start test server on same port | Use dynamic port assignment |
| "File already exists" | Two workers write to same output file | Include worker index in file path |

---

## Port Conflicts (Local Dev Servers)

```typescript
// playwright.config.ts
webServer: {
  command: 'npm run dev',
  port: process.env.TEST_PORT ? parseInt(process.env.TEST_PORT) : 3000,
  reuseExistingServer: !process.env.CI,
},
```

---

## Performance Benchmark

| Configuration | 100 tests | 
|--------------|-----------|
| 1 worker (serial) | ~10 min |
| 4 workers (parallel) | ~3 min |
| 4 workers + 4-way sharding | ~45 sec per shard |

---

## Checklist — Parallel-Safe Test

- [ ] Test creates unique data (timestamp/random suffix, never fixed names)
- [ ] Test cleans up its own data in afterEach (not "all test data")
- [ ] Test does NOT depend on execution order (no beforeAll shared mutations)
- [ ] Authentication uses read-only shared state OR isolated per-worker users
- [ ] No file writes to shared paths without worker-index namespacing
- [ ] Test passes with `--workers=4 --repeat-each=3`

---

## Worker-Scoped Fixtures (Playwright)

Share heavy setup across tests in the same worker (DB connection, browser pool):
```typescript
import { test as base } from '@playwright/test';

export const test = base.extend<{}, { dbClient: DbClient }>({
  dbClient: [
    async ({}, use) => {
      const client = await DbClient.connect();
      await use(client);
      await client.close();
    },
    { scope: 'worker' },   // ← one per worker, not per test
  ],
});
```

## `test.describe.configure` — Mix Parallel + Serial

```typescript
test.describe.configure({ mode: 'serial' });
test('step 1', async ({ page }) => { ... });
test('step 2', async ({ page }) => { ... });   // runs in order, shares page
```

Use only when state intentionally chains across tests (rare — usually a smell).

## fullyParallel + Serial Mix

```typescript
// playwright.config.ts — most tests parallel, mark a few describes as serial
fullyParallel: true,
// In specs that need serial: test.describe.configure({ mode: 'serial' })
```

## Sources
- Playwright parallelism: playwright.dev/docs/test-parallel
- Playwright sharding: playwright.dev/docs/test-sharding
- CI integration: deviqa.com/blog/guide-to-playwright-end-to-end-testing
