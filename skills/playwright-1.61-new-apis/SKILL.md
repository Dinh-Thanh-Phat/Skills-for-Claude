---
name: playwright-1.61-new-apis
description: Use Playwright 1.61 (June 2026) new APIs including the cross-browser WebAuthn passkey virtual authenticator (credentials.create/install/get), Web Storage read/write, expanded video retention modes, expect.soft.poll(), FullConfig.failOnFlakyTests, WebSocket recording in HAR/traces, connectOverCDP artifactsDir, screencast cursor decoration, the -G grep-invert shorthand, and FullConfig.argv reporter introspection. Use when testing passkey authentication flows, seeding localStorage/sessionStorage in tests, configuring video on retries, capturing WebSocket traffic in traces, attaching to an existing browser via CDP, annotating screencast recordings, or writing a custom reporter that needs the run's CLI args or resolved config path. Triggers on: "test passkeys playwright", "WebAuthn virtual authenticator", "playwright localStorage", "sessionStorage test", "video on retries playwright", "failOnFlakyTests", "soft poll assertion", "websocket trace playwright", "connectOverCDP artifactsDir", "screencast cursor", "grep-invert shorthand", "FullConfig.argv", "custom reporter config file".
---

# Playwright 1.61 New APIs

Released June 2026. No breaking changes.

## 1. WebAuthn Passkeys via `browserContext.credentials`

Virtual authenticator — no hardware security key needed. Works in **all browsers** (Chromium, Firefox, WebKit) — Playwright overrides `navigator.credentials` in the page rather than using a CDP-only authenticator.

API: `context.credentials.create(rpId, { id?, userHandle?, privateKey?, publicKey? })` seeds a passkey · `context.credentials.install()` (no args) turns interception on · `context.credentials.get({ rpId?, id? })` returns `[{ id, rpId, userHandle, privateKey, publicKey, signCount }]` · `context.credentials.delete(id)`. There is **no** `enable()`.

> `install()` is **required** and must run **before the page first touches `navigator.credentials`**. Credentials seeded with `create()` but never installed are invisible to the page.

### Register a passkey in a setup test, reuse in spec tests:

```typescript
// passkey.setup.ts (setup project)
import { test as setup, expect } from '@playwright/test';
import fs from 'fs';

setup('register passkey', async ({ context, page }) => {
  await context.credentials.install();          // intercept before the page uses WebAuthn

  await page.goto('/register');
  await page.getByRole('button', { name: 'Register passkey' }).click();
  await expect(page.getByText('Passkey registered')).toBeVisible();

  // Read back what the app registered (includes private key + signCount)
  const creds = await context.credentials.get({ rpId: 'example.com' });
  fs.writeFileSync('passkey.json', JSON.stringify(creds));
});
```

```typescript
// passkey.fixture.ts
import { test as base, BrowserContext } from '@playwright/test';
import fs from 'fs';

const test = base.extend<{ authedContext: BrowserContext }>({
  authedContext: async ({ browser }, use) => {
    const context = await browser.newContext();
    const saved = JSON.parse(fs.readFileSync('passkey.json', 'utf8'));
    for (const c of saved)
      await context.credentials.create(c.rpId, c);   // re-seed each credential
    await context.credentials.install();

    await use(context);
    await context.close();
  },
});

export { test };
```

> Simpler since 1.62: `context.storageState({ path, credentials: true })` saves passkeys; restoring that storage state auto-installs the authenticator (see `playwright-1.62-new-apis` §6).

```typescript
// login.spec.ts
import { test } from './passkey.fixture';
import { expect } from '@playwright/test';

test('passkey login works', async ({ authedContext }) => {
  const page = await authedContext.newPage();
  await page.goto('/login');
  await page.getByRole('button', { name: 'Sign in with passkey' }).click();
  await expect(page).toHaveURL('/dashboard');
});
```

> `credentials.create(rpId, cred)` → seeds a passkey (fresh keys are ECDSA P-256; seeded credentials are discoverable/resident).  
> `credentials.install()` → overrides `navigator.credentials.create()` / `.get()` in all current and future pages of the context; real authenticators stop working in that context.

## 2. Web Storage API

`page.localStorage` and `page.sessionStorage` directly read/write the page's storage without `page.evaluate()`:

```typescript
// Seed before navigation — faster than UI login when app reads token from localStorage
await page.goto('/');
await page.localStorage.setItem('authToken', 'test-jwt-abc123');
await page.localStorage.setItem('userId', '42');
await page.reload();

// Read what the app wrote
const cartJson = await page.localStorage.getItem('cart');

// Inspect all entries
const all = await page.localStorage.items();
// Returns an ARRAY of name/value pairs:
// [{ name: 'authToken', value: 'test-jwt-abc123' }, { name: 'userId', value: '42' }, ...]

await page.localStorage.removeItem('userId');
await page.localStorage.clear();

// sessionStorage — same API, tab-scoped
await page.sessionStorage.setItem('step', '2');
```

**Use case**: Any feature that reads auth/session state from storage can skip UI login entirely — set the token, navigate, start testing the feature.

## 3. Video Retention Modes

1.61 makes `video` support the same modes as `trace` (new: `'on-all-retries'`, `'retain-on-first-failure'`, `'retain-on-failure-and-retries'`). Official table:

| Mode | Records a video on | Keeps the video when |
|------|--------------------|----------------------|
| `'off'` | never | — |
| `'on'` | every run | always |
| `'retain-on-failure'` | every run | that run failed |
| `'retain-on-first-failure'` | first run only | the first run failed |
| `'retain-on-failure-and-retries'` | every run | that run failed, or it is a retry |
| `'on-first-retry'` | first retry only | always |
| `'on-all-retries'` | every retry | always |

```typescript
// playwright.config.ts
use: {
  video: 'retain-on-failure-and-retries',  // diagnose flakiness across all retry attempts
}
```

`'on-all-retries'` cuts storage costs: no video for healthy runs, full coverage for any test that needed a retry.

## 4. `expect.soft.poll()`

Polling + soft assertions combined: retries the assertion until it passes or times out, but does not abort the test if it never passes:

```typescript
// Poll every 500ms for up to 5s; test continues even on timeout
await expect.soft.poll(
  () => page.locator('.sync-status').textContent(),
  { timeout: 5000, intervals: [500] }
).toBe('Synced');

// Soft failures accumulate — all reported at test end
await page.getByRole('button', { name: 'Download' }).click();
await expect.soft(page.locator('.toast')).toBeVisible();
```

**When to use**: Async background operations (real-time sync, polling UIs) where you want to observe all failures instead of stopping at the first one.

## 5. `FullConfig.failOnFlakyTests` (reporter-visible)

The `failOnFlakyTests` **config option** itself dates from 1.52; what 1.61 adds is `FullConfig.failOnFlakyTests`, mirroring it so reporters can explain why a flaky run failed.

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 2 : 0,
  failOnFlakyTests: true,  // non-zero exit if any test needed a retry to pass
});
```

A test that passes after 1 retry is counted as flaky and fails CI. Forces investigation of tests that only pass on retry, preventing masked flakiness from shipping.

## 6. Network: `apiResponse.securityDetails()` and `apiResponse.serverAddr()`

Mirror the browser-side response methods on `APIResponse` objects:

```typescript
const resp = await request.get('https://api.example.com/data');

const security = await resp.securityDetails();
// { issuer: 'Let's Encrypt', protocol: 'TLS 1.3', subjectName: 'api.example.com', ... }

const server = await resp.serverAddr();
// { ipAddress: '93.184.216.34', port: 443 }
```

Useful for security-focused tests that need to verify TLS certificate properties.

## 7. HAR + Trace Include WebSocket Frames

WebSocket messages now appear in both HAR recordings and Playwright Trace archives:

```typescript
// Record trace (WebSocket frames included automatically)
await context.tracing.start({ screenshots: true, snapshots: true });
// ... use WebSocket-driven features (live chat, real-time dashboard) ...
await context.tracing.stop({ path: 'trace.zip' });
// Trace Viewer → Network tab → WebSocket section shows all frames
```

For HAR recording via `tracing.startHar()` (added in 1.60), WebSocket frames are also captured — useful for replaying WS-heavy interaction sequences.

## 8. `browserType.connectOverCDP()` — `artifactsDir` Option

Controls where traces and downloads land when attaching Playwright to an already-running browser over CDP (e.g. a browser launched by another tool, or a persistent debugging session):

```typescript
const browser = await chromium.connectOverCDP('http://localhost:9222', {
  artifactsDir: './cdp-artifacts',  // traces/downloads from this session land here
});
const context = browser.contexts()[0];
await context.tracing.start({ screenshots: true, snapshots: true });
// ... drive the already-open browser ...
await context.tracing.stop({ path: './cdp-artifacts/session.zip' });
```

**Use case**: CDP-attach workflows (debugging extensions, reusing a logged-in browser instance, AI-agent browser control) previously had no first-class place to put artifacts — they'd default to a temp dir or be lost.

## 9. `screencast.showActions()` — `cursor` Option

Controls the cursor decoration rendered for pointer actions, useful for demo/bug-repro recordings where a reviewer needs to see exactly where clicks landed. Values: `'pointer'` (default — a mouse pointer animating from the previous action point to the next) or `'none'`:

```typescript
await page.screencast.showActions({ position: 'top-right', cursor: 'pointer' });
await page.screencast.showActions({ cursor: 'none' });   // annotations without cursor
```

Also in 1.61: the `screencast.start({ onFrame })` callback's frame object gains a `timestamp` (ms since epoch, when the browser presented the frame).

## 10. `-G` Shorthand for `--grep-invert`

```bash
# Run everything except tests tagged @slow
npx playwright test -G @slow
```

Same behavior as `--grep-invert @slow`, just terser for frequent CLI use (e.g. excluding a smoke-only tag during full-suite local runs).

## 11. `FullConfig.argv` — Reporter Introspection

`FullConfig.argv` is new in 1.61. (`FullConfig.configFile` is a much older field, shown here only because the two pair well.)

```typescript
// custom-reporter.ts
import type { Reporter, FullConfig } from '@playwright/test/reporter';

class CustomReporter implements Reporter {
  onBegin(config: FullConfig) {
    // Snapshot of process.argv from the runner process — read custom args
    // passed after the `--` separator without re-parsing process.argv yourself.
    console.log('Runner argv:', config.argv);

    // Path to the config file actually loaded, if any — useful when a
    // reporter needs to resolve paths relative to the config, or log which
    // of several config files (e.g. staging vs prod) a run used.
    console.log('Config file:', config.configFile);
  }
}
```

**Use case**: custom reporters that need to know exactly how the run was invoked (e.g. `npx playwright test -- --env=staging`) or which config file was resolved, without duplicating CLI-argument parsing logic.

## Sources
- https://github.com/microsoft/playwright/blob/main/docs/src/api/class-credentials.md, class-webstorage.md, class-screencast.md, test-use-options-js.md#video-modes (corrected 2026-10-02)
- https://github.com/microsoft/playwright/releases/tag/v1.61.0
- https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/release-notes-js.md
- https://raw.githubusercontent.com/microsoft/playwright/v1.61.0/docs/src/release-notes-js.md
- https://www.corbado.com/blog/passkeys-e2e-playwright-testing-webauthn-virtual-authenticator
- https://changjoon-baek.medium.com/overcoming-passkey-verification-in-test-automation-fc7fc6748bd6
- https://dev.to/kochan/testing-webauthn-in-ci-e2e-automation-with-virtual-authenticators-and-mailpit-part-2-4j4i
