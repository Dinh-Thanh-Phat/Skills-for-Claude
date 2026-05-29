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

Wait for **STATE**, not **TIME**. `waitForSelector` > `waitForTimeout`.

## Root Causes

| Cause | Symptom | Fix |
|---|---|---|
| `networkidle` hangs | Timeout on goto | Use `domcontentloaded` + `waitForSelector` |
| Element in animation | Click hits wrong position | `waitForSelector` + check stable |
| Toast disappears before assertion | `toBeVisible` fails intermittently | Use `page.clock` or assert immediately |
| Parallel tests share state | Random failures | Isolated contexts per test |
| CI slower than local | Passes local, fails CI | Environment-aware timeouts |
| JS not hydrated yet | Input fills but value lost | Wait for interactive element state |

## Pattern 1: Replace networkidle

```typescript
// ❌ Hangs on WebSocket apps, Replit, polling
await page.goto(url, { waitUntil: 'networkidle' });

// ✅ Fast + explicit
await page.goto(url, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('[data-testid="main-content"]');
// or
await page.getByRole('main').waitFor({ state: 'visible' });
```

## Pattern 2: Wait for State, Not Time

```typescript
// ❌ Arbitrary delay — CI still fails
await page.waitForTimeout(2000);
await page.click('#submit');

// ✅ Wait for the enabling condition
await expect(page.locator('#submit')).toBeEnabled();
await page.click('#submit');

// ✅ Wait for specific state
await page.waitForSelector('#submit:not([disabled])');
```

## Pattern 3: Toast / Transient Notification

```typescript
// ❌ Toast may disappear before assertion reaches it
await page.click('[data-testid="save-btn"]');
await expect(page.locator('.toast')).toBeVisible();

// ✅ Sync with API response first, then assert toast
const [response] = await Promise.all([
  page.waitForResponse(r => r.url().includes('/api/save') && r.status() === 200),
  page.click('[data-testid="save-btn"]'),
]);
await expect(page.getByRole('status')).toBeVisible({ timeout: 3000 });
```

## Pattern 4: Stale Element References

```typescript
// ❌ Stale reference if DOM re-renders between locator + action
const btn = page.locator('#submit');
await page.click('#reload-section'); // DOM changes
await btn.click(); // Error: element detached

// ✅ Re-query after DOM change
await page.click('#reload-section');
await page.waitForLoadState();
await page.locator('#submit').click(); // fresh reference
```

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
  retries: process.env.CI ? 2 : 0, // retry in CI only
});

// For specific flaky section within a test
await expect(async () => {
  await page.click('[data-testid="refresh-btn"]');
  await expect(page.locator('[data-testid="data-loaded"]')).toBeVisible();
}).toPass({ timeout: 15000 }); // retry the whole block
```

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
- [ ] `networkidle` replaced with `domcontentloaded` + explicit selector wait
- [ ] Toast assertions: assert immediately after action, no delay
- [ ] `retries: 2` set for CI in `playwright.config.ts`
- [ ] Timeouts scale with environment (local < CI < Replit)
- [ ] Tests isolated: no shared page/context state across tests
- [ ] Stale elements: re-query locators after DOM-changing actions

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

