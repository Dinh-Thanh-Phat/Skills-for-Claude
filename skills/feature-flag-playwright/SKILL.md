---
name: feature-flag-playwright
description: >-
  Use when writing or reviewing Playwright tests for features that are gated behind feature flags
  (LaunchDarkly, Flagsmith, Unleash, PostHog, or env-var toggles). Triggers on: "feature flag
  test", "toggle-aware test", "LaunchDarkly playwright", "test flag on and off", "skip test when
  flag disabled", "flag fixture".
---

# Feature Flag Testing with Playwright

## Why flags make tests hard

A feature behind a flag creates **two valid application states** (enabled / disabled). Tests that ignore this either:
- Always fail when the flag is off in CI, or
- Only validate one path and miss regressions when the flag toggles.

---

## Three approaches (choose by flag provider)

### 1. Network mock — no flag service needed (fastest)

Intercept the SDK's bootstrap/evaluation endpoint and return a fixed payload.
Works in any environment; no credentials required.

```typescript
// fixtures/flagMock.ts
import { test as base, Page } from '@playwright/test';

export const test = base.extend<{ withFlag: (key: string, value: boolean) => Promise<void> }>({
  withFlag: async ({ page }, use) => {
    await use(async (key: string, value: boolean) => {
      // LaunchDarkly: intercept the streaming eval endpoint
      await page.route('**/sdk/evalx/**', route => {
        route.fulfill({ json: { [key]: { value, variation: value ? 0 : 1 } } });
      });
      // PostHog / GrowthBook: intercept /decide or /features endpoint similarly
    });
  },
});
```

### 2. REST API control — LaunchDarkly / Flagsmith / Unleash

Set the flag state before the test; restore it after. Requires a service-account API key.

```typescript
// lib/launchdarkly-util.ts
import axios from 'axios';

const LD_BASE = 'https://app.launchdarkly.com/api/v2';
const headers = { Authorization: process.env.LD_API_KEY! };

export async function setFlag(
  project: string, env: string, flagKey: string, enabled: boolean
): Promise<void> {
  await axios.patch(
    `${LD_BASE}/flags/${project}/${flagKey}`,
    [{ op: 'replace', path: `/environments/${env}/on`, value: enabled }],
    { headers: { ...headers, 'Content-Type': 'application/json' } }
  );
}
```

```typescript
// tests/new-checkout.spec.ts
import { test, expect } from '@playwright/test';
import { setFlag } from '../lib/launchdarkly-util';

const PROJECT = 'my-app';
const ENV     = 'test';
const FLAG    = 'new-checkout-flow';

test.describe('new checkout flow (flag=on)', () => {
  let originalState: boolean;

  test.beforeAll(async () => {
    // snapshot original state then enable
    // (fetch current state first if you need to restore exactly)
    originalState = false;
    await setFlag(PROJECT, ENV, FLAG, true);
  });

  test.afterAll(async () => {
    await setFlag(PROJECT, ENV, FLAG, originalState);
  });

  test('completes purchase with new UI', async ({ page }) => {
    await page.goto('/checkout');
    await expect(page.getByTestId('new-checkout-step1')).toBeVisible();
  });
});
```

### 3. Env-var driven — backend-rendered flags

When flags are server-rendered at request time via an env var:

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'flag-on',  use: { extraHTTPHeaders: { 'X-Feature-Flags': 'new_checkout=1' } } },
    { name: 'flag-off', use: { extraHTTPHeaders: { 'X-Feature-Flags': 'new_checkout=0' } } },
  ],
});
```

---

## Toggle-aware test — skip when flag is off

```typescript
test('premium dashboard widgets', async ({ page, request }) => {
  // Check flag state from a test-internal API or env
  const enabled = process.env.PREMIUM_WIDGETS_FLAG === 'true';
  test.skip(!enabled, 'Premium widgets flag is off in this environment');

  await page.goto('/dashboard');
  await expect(page.getByTestId('revenue-widget')).toBeVisible();
});
```

---

## Parameterized test — cover both paths in one spec

```typescript
for (const flagOn of [true, false]) {
  test(`checkout CTA — flag=${flagOn}`, async ({ page }) => {
    await page.route('**/sdk/evalx/**', route => {
      route.fulfill({ json: { 'new-cta': { value: flagOn } } });
    });
    await page.goto('/checkout');

    if (flagOn) {
      await expect(page.getByRole('button', { name: 'Buy now' })).toBeVisible();
    } else {
      await expect(page.getByRole('button', { name: 'Add to cart' })).toBeVisible();
    }
  });
}
```

---

## Decision table

| Situation | Approach |
|---|---|
| No flag service / local dev | Network mock (route interception) |
| Staging with LaunchDarkly / Flagsmith | REST API beforeAll/afterAll |
| Backend env-var flags | Playwright projects with extraHTTPHeaders |
| Need to test both on and off | Parameterized `for (const flagOn of [true, false])` |
| Skip when flag is off in env | `test.skip(!enabled, reason)` |
| Gradual rollout (% targeting) | Set context-specific targeting rule via API |

---

## Rules

- **One flag per test** — isolating tests to a single flag makes failures unambiguous.
- **Always restore** — use `afterAll`/`afterEach` to reset flags; a leaked state bleeds into other parallel tests.
- **Use the test environment** — never toggle flags in production or staging shared with users.
- **Don't hardcode API keys** — store LD_API_KEY in CI secrets; read via `process.env`.
- **Prefer mock > API** where flag complexity is low; API control is only needed when the backend reads the flag server-side.

## Sources
- https://www.scale-qa.com/post/feature-flag-testing-ultimate-guide
- https://medium.com/@mahtabnejad/harnessing-launchdarkly-in-playwright-building-a-robust-feature-flag-utility-b4272d16ed08
- https://launchdarkly.com/blog/testing-with-feature-flags/
- https://docs.launchdarkly.com/guides/flags/testing-code
- https://yrkan.com/blog/feature-flags-testing-strategy/
- https://www.thegreenreport.blog/articles/flipping-the-switch-automating-feature-flag-testing/flipping-the-switch-automating-feature-flag-testing.html
