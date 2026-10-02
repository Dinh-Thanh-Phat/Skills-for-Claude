---
name: auth-session-testing
description: Playwright auth testing patterns — storageState setup project, role-based auth files, session expiry simulation, protected route redirects, OAuth/SSO flows. Use when writing tests that require login, testing auth itself, managing multiple user roles, or testing what happens when session expires. Triggers on: "auth test", "login test", "storageState", "session expiry", "protected route", "multiple roles", "OAuth", "SSO", "global setup auth", "reuse token", "storage state".
triggers:
  - "auth test"
  - "login test"
  - "storageState"
  - "session expiry"
  - "protected route"
  - "multiple roles"
  - "global setup auth"
  - "reuse token"
---

# Auth / Session Testing

## Core Decision

```
Is this a test ABOUT authentication itself?
  YES → re-authenticate fresh every time, never cache
  NO  → use storageState — login once in setup, reuse across tests
```

**Tests about auth** (`tests/auth/`) — login flow, logout, token expiry, wrong password, MFA
**Feature tests** (`tests/features/`) — consume stored session, never test login flow

---

## Pattern 1: Setup Project (Login Once, Reuse All Tests)

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'setup', testMatch: '**/auth.setup.ts' },
    {
      name: 'chromium',
      use: { storageState: '.auth/user.json' },
      dependencies: ['setup'],
    },
  ],
});
```

```typescript
// auth.setup.ts
import { test as setup } from '@playwright/test';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.TEST_EMAIL!);
  await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: 'Login' }).click();

  // ✅ CRITICAL: wait for FINAL redirect — cookies set server-side AFTER redirect
  await page.waitForURL('/dashboard');

  // Save AFTER final redirect, not before
  await page.context().storageState({ path: '.auth/user.json' });
});
```

## Pattern 2: Multiple Roles

```typescript
// playwright.config.ts
projects: [
  { name: 'setup:admin', testMatch: '**/auth.admin.setup.ts' },
  { name: 'setup:user', testMatch: '**/auth.user.setup.ts' },
  {
    name: 'admin-tests',
    use: { storageState: '.auth/admin.json' },
    dependencies: ['setup:admin'],
  },
  {
    name: 'user-tests',
    use: { storageState: '.auth/user.json' },
    dependencies: ['setup:user'],
  },
]
```

```typescript
// Multi-role fixture for same test file
const test = base.extend<{ adminPage: Page; userPage: Page }>({
  adminPage: async ({ browser }, use) => {
    const ctx = await browser.newContext({ storageState: '.auth/admin.json' });
    await use(await ctx.newPage());
    await ctx.close();
  },
  userPage: async ({ browser }, use) => {
    const ctx = await browser.newContext({ storageState: '.auth/user.json' });
    await use(await ctx.newPage());
    await ctx.close();
  },
});
```

## Pattern 3: Session Expiry Simulation

```typescript
// Simulate logout/session expiry: clear cookies then navigate to protected route
test('session expired → redirects to login', async ({ browser }) => {
  const ctx = await browser.newContext({ storageState: '.auth/user.json' });
  const page = await ctx.newPage();

  // Navigate first — the new page is on about:blank, where touching localStorage
  // from page.evaluate likely throws (opaque origin; UNVERIFIED on every browser)
  await page.goto('/dashboard');

  // Simulate expiry by clearing session
  await ctx.clearCookies();
  await page.evaluate(() => localStorage.clear());

  await page.reload();
  await expect(page).toHaveURL(/\/login/);
  await ctx.close();
});
```

## Pattern 4: Protected Route (Unauthenticated)

```typescript
test('unauthenticated → redirects to login', async ({ browser }) => {
  // Fresh context — NO storageState
  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/login/);
  await ctx.close();
});
```

## Pattern 5a: Token Refresh Mid-Test

```typescript
// Force a refresh by setting cookie expiry to past and triggering a request
await page.context().addCookies([{
  name: 'access_token', value: 'expired', domain: '.example.com', path: '/',
  expires: Math.floor(Date.now() / 1000) - 10,
}]);
const [refresh] = await Promise.all([
  page.waitForResponse(r => r.url().includes('/auth/refresh') && r.ok()),
  page.goto('/dashboard'),
]);
expect(refresh.status()).toBe(200);
await expect(page).toHaveURL(/dashboard/);  // refresh succeeded, no redirect to /login
```

## Pattern 5b: JWT Expiry via `page.clock`

> `page.clock` only fakes time INSIDE the browser. It works when expiry is enforced client-side
> (the SPA reads `exp` and redirects). If the server rejects the token, faking browser time
> does nothing — issue a genuinely short-lived token instead.

```typescript
// Issue a short-lived token, fast-forward, watch behavior
await page.clock.install();
await login(page);  // token expires in 5 minutes
await page.clock.fastForward('06:00');  // 6 minutes
await page.goto('/dashboard');
await expect(page).toHaveURL(/\/login/);  // expired → redirect
```

## Pattern 5c: Bearer Token (API) vs Cookie (Web)

```typescript
// API-only test — set Authorization header instead of using storageState
const apiCtx = await playwright.request.newContext({
  extraHTTPHeaders: { Authorization: `Bearer ${process.env.API_TOKEN}` },
});
const resp = await apiCtx.get('/api/me');
expect(resp.ok()).toBe(true);
```

## Pattern 5d: CSRF Token

```typescript
// Read CSRF from a tagged meta or cookie before form submit
const csrf = await page.locator('meta[name="csrf-token"]').getAttribute('content');
await page.request.post('/api/save', {
  data: { name: 'X' }, headers: { 'X-CSRF-Token': csrf! },
});
```

## Pattern 5e: Role-Boundary Negative Test

```typescript
// User in `user` role must NOT reach admin route.
// Pick the ONE behavior the spec defines — asserting "status ≥ 401 OR redirect" is a soft
// assertion (see `soft-assertion-ban`); as two separate expects, a redirect (200) fails the first.

// Variant A — spec says the server answers 403:
test('user blocked from admin (403)', async ({ browser }) => {
  const ctx = await browser.newContext({ storageState: '.auth/user.json' });
  const page = await ctx.newPage();
  const resp = await page.goto('/admin', { waitUntil: 'domcontentloaded' });
  expect(resp?.status()).toBe(403);
  await ctx.close();
});

// Variant B — spec says the app redirects to /forbidden:
test('user blocked from admin (redirect)', async ({ browser }) => {
  const ctx = await browser.newContext({ storageState: '.auth/user.json' });
  const page = await ctx.newPage();
  await page.goto('/admin');
  await expect(page).toHaveURL(/\/forbidden/);
  await expect(page.getByRole('heading', { name: /admin/i })).toHaveCount(0); // no admin UI leaked
  await ctx.close();
});
```

## Pattern 5f: Logout-All-Devices

```typescript
// Login on 2 contexts, logout from one, both must invalidate
const ctxA = await browser.newContext(); const pageA = await ctxA.newPage();
const ctxB = await browser.newContext(); const pageB = await ctxB.newPage();
await login(pageA); await login(pageB);  // both authenticated as same user
await pageA.goto('/account/security');
await pageA.getByRole('button', { name: 'Log out everywhere' }).click();
await pageB.goto('/dashboard');
await expect(pageB).toHaveURL(/\/login/);  // pageB also signed out
```

## Pattern 5g: Partitioned Cookies (CHIPS) for Cross-Site Embeds

Browsers now partition third-party cookies per top-level site (CHIPS). If your app is embedded as
a widget/iframe on customer domains and sets its own auth/session cookie, verify the cookie is
correctly scoped with `Partitioned` — a non-partitioned third-party cookie will silently fail to
persist across page loads in Chrome/Edge once third-party cookies are blocked.

```typescript
// Assert a cross-site embed's session cookie is set with the CHIPS partition key
const cookies = await page.context().cookies();
const sessionCookie = cookies.find(c => c.name === 'embed_session');
expect(sessionCookie?.partitionKey).toBeDefined(); // absent => cookie isn't partitioned, will be blocked

// Seed a partitioned cookie directly for a test that needs pre-authenticated embed state
await page.context().addCookies([{
  name: 'embed_session', value: 'abc123', domain: 'widget.example.com', path: '/',
  partitionKey: 'https://customer-site.com', // top-level site the widget is embedded under
}]);
```

Only relevant when testing embeddable/iframe auth (widgets, SSO popups on partner domains) — regular
first-party login flows are unaffected by CHIPS.

## Pattern 6: OAuth/SSO

```typescript
setup('OAuth authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByRole('button', { name: 'Sign in with Google' }).click();

  // Handle OAuth provider page
  await page.waitForURL('**/accounts.google.com/**');
  await page.getByLabel('Email').fill(process.env.OAUTH_EMAIL!);
  // ... fill password, handle MFA

  // Wait for FINAL app callback redirect (not the OAuth callback URL)
  await page.waitForURL('**/dashboard');

  // Save ONLY after landing on app — OAuth callback URL has no app session yet
  await page.context().storageState({ path: '.auth/oauth-user.json' });
});
```

## Security Rules

```gitignore
# .gitignore — MANDATORY
.auth/
*.token
*.session
```

```typescript
// ✅ Credentials from env vars only — never hardcoded
await page.fill('#email', process.env.TEST_EMAIL!);

// ❌ Never hardcode
await page.fill('#email', 'admin@example.com');
```

- sessionStorage is NOT captured by storageState (tab-scoped). Inject it after navigating to the
  origin — with the Web Storage API (1.61+) instead of `page.evaluate`:
  ```typescript
  await page.goto('/');
  await page.sessionStorage.setItem('key', 'value');   // also page.localStorage.getItem/items()
  ```
- Newer `BrowserContext.storageState` options: `credentials` persists virtual WebAuthn passkeys
  (1.62; virtual authenticator via `context.credentials`, 1.61) and `opfs` includes the origin
  private file system (1.63). Check the exact option shape in the BrowserContext.storageState docs
  before use (see `playwright-1.62-new-apis` / `playwright-1.63-new-apis`).

## Gotchas

| Gotcha | Fix |
|---|---|
| Saving storageState before final redirect | Wait for `page.waitForURL('/dashboard')` first |
| Parallel workers sharing same state file | Read-only shared file; tests that mutate the session need a per-worker account via a worker-scoped fixture (the docs call their example fixture `workerStorageState` — it's not built-in) keyed on `parallelIndex` |
| sessionStorage not in storageState | Inject via `page.sessionStorage.setItem()` (1.61+) after navigating |
| "Remember me" changes cookie expiry | Test explicitly: check `cookie.expires` value with/without |
| .auth/ committed to git | Add to .gitignore — contains live session tokens |

## Decision Table

| Scenario | Strategy |
|---|---|
| Feature test | Reuse storageState — no re-login |
| Test ABOUT login flow | Re-authenticate fresh — no cache |
| Test ABOUT logout | Re-authenticate after logout |
| Test token expiry | Re-authenticate with short-lived token |
| Parallel CI workers (same run) | Share same storageState file (read-only) |

## Sources
- Playwright `partitionKey` cookie property (CHIPS support) release notes: https://playwright.dev/docs/release-notes

