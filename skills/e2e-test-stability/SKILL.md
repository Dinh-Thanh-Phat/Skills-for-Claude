---
name: e2e-test-stability
description: Fix and prevent flaky Playwright E2E tests — race conditions, stale element references, networkidle timeouts, CI vs local differences. Use when tests pass locally but fail in CI, when tests are intermittently failing, or when fixing timing-related test failures. Triggers on: "flaky test", "intermittent failure", "race condition", "networkidle timeout", "detached element", "passes locally fails CI", "CI failure", "element timing", "auto-wait".
origin: research
scope: testing, playwright, stability, flaky
triggers:
  - "flaky test"
  - "intermittent failure"
  - "race condition"
  - "networkidle timeout"
  - "passes locally fails CI"
  - "CI failure"
  - "element timing"
  - "detached element"
---

# E2E Test Stability

## Core Principle

Wait for **STATE**, not **TIME**. Web-first assertions (`await expect(locator).toBeVisible()`) > `waitForTimeout`.
(`page.waitForSelector` is *discouraged* in the Playwright API docs and `networkidle` is marked **DISCOURAGED** — use web-first assertions or `locator.waitFor()`.)

## Root Causes

| Cause | Symptom | Fix |
|---|---|---|
| `networkidle` hangs | Timeout on goto | `goto` (default `load`) + `await expect(locator).toBeVisible()` |
| Element in animation | Click hits wrong position | Locator actions already wait for "stable"; assert the target state with `expect` |
| Toast disappears before assertion | `toBeVisible` fails intermittently | Use `page.clock` or assert immediately |
| Parallel tests share state | Random failures | Isolated contexts per test |
| CI slower than local | Passes local, fails CI | Environment-aware timeouts |
| JS not hydrated yet | Input fills but value lost | Wait for interactive element state |

## Pattern 1: Replace networkidle

```typescript
// ❌ Hangs on WebSocket apps, Replit, polling
await page.goto(url, { waitUntil: 'networkidle' });

// ✅ Fast + explicit — wait for the element that proves the page is ready
await page.goto(url, { waitUntil: 'domcontentloaded' });
await expect(page.getByTestId('main-content')).toBeVisible();
// or, outside a test assertion context
await page.getByRole('main').waitFor({ state: 'visible' });
```

## Pattern 2: Wait for State, Not Time

```typescript
// ❌ Arbitrary delay — CI still fails
await page.waitForTimeout(2000);
await page.click('#submit');

// ✅ Wait for the enabling condition (web-first, auto-retrying)
const submit = page.getByRole('button', { name: 'Submit' });
await expect(submit).toBeEnabled();
await submit.click(); // locator.click() itself also waits for visible/enabled/stable
```

## Pattern 3: Toast / Transient Notification

```typescript
// ❌ Toast may disappear before assertion reaches it
await page.click('[data-testid="save-btn"]');
await expect(page.locator('.toast')).toBeVisible();

// ✅ Sync with API response first, then assert toast
const responsePromise = page.waitForResponse(r => r.url().includes('/api/save') && r.status() === 200);
await page.getByTestId('save-btn').click();
await responsePromise;
await expect(page.getByRole('status')).toBeVisible({ timeout: 3000 });
```

## Pattern 4: Stale References — Locators vs ElementHandles

A `Locator` is lazy: it re-resolves against the live DOM on **every** action/assertion, so
holding a locator across a re-render does NOT go stale.

```typescript
// ✅ Fine — the locator re-queries the DOM when click() runs
const btn = page.getByRole('button', { name: 'Submit' });
await page.getByRole('button', { name: 'Reload section' }).click(); // DOM re-renders
await btn.click();

// ❌ Stale — ElementHandles ($, $$, waitForSelector return values) pin ONE DOM node
const handle = await page.$('#submit');
await page.getByRole('button', { name: 'Reload section' }).click();
await handle!.click(); // Error: Element is not attached to the DOM
// Fix: don't use ElementHandles (docs: "inherently racy") — use locators.
```

"Element is detached" with a locator usually means the element was re-rendered *during* the
action (e.g. list re-sorting) — wait for the UI to settle with a web-first assertion on the
final state before acting.

## Pattern 5: Environment-Aware Timeouts

```typescript
// playwright.config.ts
const isCI = !!process.env.CI;
const isReplit = !!process.env.REPL_ID;

export default defineConfig({
  timeout: isCI ? 60000 : 30000,
  expect: { timeout: isCI ? 10000 : 5000 },
  use: {
    actionTimeout: isCI ? 15000 : 10000,
    navigationTimeout: isReplit ? 90000 : 15000,
  },
});
```

## Pattern 6: Retry Flaky Blocks

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 1 : 0,   // ONE retry in CI only, never local (suite-wide standard)
  retryStrategy: 'isolated',         // 1.62+: retries run at the end, one by one in a single worker
  failOnFlakyTests: !!process.env.CI // pass-on-retry still fails the run → flakes stay visible
});

// For specific flaky section within a test
await expect(async () => {
  await page.getByTestId('refresh-btn').click();
  await expect(page.getByTestId('data-loaded')).toBeVisible();
}).toPass({ timeout: 15000 }); // retry the whole block
```

A test that needs more than 1 retry is broken, not flaky — fix it (see `flaky-test-prevention`).

## Pattern 7: Test Isolation for Parallel Runs

```typescript
test.beforeEach(async ({ context }) => {
  await context.clearCookies();
  await context.clearPermissions();
});

// Never share mutable state between tests
// Each test gets fresh browser context via Playwright default isolation
```

## Stability Checklist

- [ ] No `waitForTimeout()` — replaced with state-based waits
- [ ] `networkidle` / `waitForSelector` replaced with web-first assertions (`await expect(locator)...`)
- [ ] Toast assertions: assert immediately after action, no delay
- [ ] `retries: process.env.CI ? 1 : 0` (+ `retryStrategy: 'isolated'`, `failOnFlakyTests` in CI)
- [ ] Timeouts scale with environment (local < CI < Replit)
- [ ] Tests isolated: no shared page/context state across tests
- [ ] No ElementHandles (`$`, `$$`) — locators only, so nothing goes stale

## Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| `waitForTimeout(1000)` anywhere | Replace with state/element wait |
| `networkidle` for any navigation | Use `domcontentloaded` + selector wait |
| Shared auth state between parallel tests | Per-test fresh context or read-only storageState |
| No `retries: 2` in CI | Infra noise causes false failures |
| Hardcoded `timeout: 5000` everywhere | Use config-level environment-aware timeouts |

---

## Cross-references (unified flaky rules)

**networkidle rule** — tất cả 3 skills dưới đây đều đồng ý: NO networkidle, dùng `domcontentloaded` + `waitForSelector`:
- **this skill** — patterns cho 7 flake sources phổ biến + CI vs local
- **`flaky-test-prevention`** — 5-cause framework + selector priority
- **`playwright-flaky-test-detection`** — diagnosis-from-symptom workflow

Khi gặp flaky test: `playwright-flaky-test-detection` để diagnose → `flaky-test-prevention` để prevent → skill này để implement patterns.

