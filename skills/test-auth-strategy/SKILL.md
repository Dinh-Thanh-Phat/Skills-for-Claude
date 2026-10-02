---
name: test-auth-strategy
description: Reusable test authentication strategy — login once, token caching, global setup, separation of auth vs feature tests, secure token handling. Use when setting up authentication for any test suite, managing multiple roles, or deciding when to reuse vs re-authenticate. Triggers on: "test authentication", "test login", "auth test", "login once", "token caching test", "global setup auth", "reuse token", "auth state", "storage state", "auth fixture".
triggers:
  - "test authentication"
  - "test login"
  - "auth test"
  - "login once"
  - "token caching test"
  - "global setup auth"
  - "reuse token"
  - "auth state"
  - "storage state"
  - "auth fixture"
---

# Test Authentication Strategy

> **Cross-ref:** Overlaps with `auth-session-testing`. **Use `auth-session-testing`** for
> Playwright project setup (setup project, multiple-role fixture, OAuth, session expiry).
> Use **this skill** for the higher-level decision logic + token caching policy + per-worker
> auth for parallel runs. Same content for the "login once, reuse" pattern — kept here so
> the decision tree is discoverable from the auth-strategy angle.

## Core Decision Tree

```
Is this a test ABOUT authentication itself?
  YES → re-authenticate fresh every time, no caching
  NO  →
    Is there a valid cached token for this role + env?
      YES → reuse it (verify exp first)
      NO  → authenticate once in global setup, cache result
            → all tests in this run share the cached state (read-only)
```

## Separation of Concerns

```
tests/
  auth/           ← tests ABOUT login, logout, refresh, token expiry, revocation
  features/       ← tests USING authentication (consume token, not test it)
```

**Auth tests** — Re-authenticate fresh on every run. Test failure cases: wrong password, expired token, logout invalidation.
**Feature tests** — Never test the login flow. Consume a pre-obtained token from global setup.

## Login Once, Reuse — Playwright Implementation

Use a **setup project** (Playwright's documented auth pattern), not a hand-launched browser in
`globalSetup`: a browser you `chromium.launch()` yourself does not get the config's `baseURL`,
so a relative `page.goto('/login')` there fails.

```typescript
// tests/auth.setup.ts
import { test as setup } from '@playwright/test';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');                       // baseURL applies here
  await page.getByTestId('email').fill(process.env.TEST_USER_EMAIL!);
  await page.getByTestId('password').fill(process.env.TEST_USER_PASSWORD!);
  await page.getByTestId('login-btn').click();
  await page.waitForURL('/dashboard'); // wait for FINAL redirect — cookies set AFTER this
  await page.context().storageState({ path: '.auth/user-state.json' });
});
```

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'setup', testMatch: /auth\.setup\.ts/ },
    {
      name: 'chromium',
      use: { storageState: '.auth/user-state.json' },
      dependencies: ['setup'],
    },
  ],
});
```
More variants (multi-role projects, OAuth, expiry): `auth-session-testing`.

## One State File Per Role

```
.auth/
  admin-state.json
  user-state.json
  viewer-state.json
```

```typescript
// Multi-role fixture
const test = base.extend<{ adminPage: Page; userPage: Page }>({
  adminPage: async ({ browser }, use) => {
    const ctx = await browser.newContext({ storageState: '.auth/admin-state.json' });
    const page = await ctx.newPage();
    await use(page);
    await ctx.close();
  },
  userPage: async ({ browser }, use) => {
    const ctx = await browser.newContext({ storageState: '.auth/user-state.json' });
    const page = await ctx.newPage();
    await use(page);
    await ctx.close();
  },
});
```

## Token Caching Strategy

```
Cache key: {role}:{environment}:{scope}
Examples: admin:staging:read-write, user:production:read-only
```

```python
BUFFER_SECONDS = 60  # refresh if expiring within 60s

def get_valid_token(cache, role, env):
    cached = cache.get(f"{role}:{env}")
    if cached and (cached.exp - time.now()) > BUFFER_SECONDS:
        return cached.token
    token = auth.login(credentials[role])
    cache.set(f"{role}:{env}", token)
    return token
```

On decode failure — invalidate once, then hard fail. No infinite retry loops.

## Secure Token Handling

```gitignore
# .gitignore — MANDATORY
.auth/
*.token
*.session
```

```typescript
// ✅ From env vars only
await page.fill('#email', process.env.TEST_USER_EMAIL!);

// ❌ Never hardcode credentials in test code
await page.fill('#email', 'admin@example.com');
```

- Never `console.log(token)` or log `Authorization` headers
- Never pass tokens via query string in test helpers

## Decision Table

| Scenario | Strategy | Reason |
|---|---|---|
| Feature test in same suite run | Reuse cached session | No value in repeated login |
| Test ABOUT login flow | Re-authenticate fresh | Must exercise real auth |
| Test ABOUT logout | Re-authenticate after logout | Session invalidated |
| Test for token expiry | Re-authenticate with short-lived token | Need controlled expiry |
| Performance test — throughput | Reuse token pool | Avoid overloading auth service |
| CI pipeline (each run independent) | Re-authenticate in global setup | No cross-run state |
| Parallel workers (same run) | Share same state file (read-only) | One login, many readers |

