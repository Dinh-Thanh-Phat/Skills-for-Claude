---
name: playwright-1.61-new-apis
description: >-
  Use Playwright 1.61 (June 2026) new APIs including WebAuthn passkey virtual authenticator, Web
  Storage read/write, expanded video retention modes, expect.soft.poll(), failOnFlakyTests,
  WebSocket recording in HAR/traces, connectOverCDP artifactsDir, screencast cursor decoration,
  the -G grep-invert shorthand, and FullConfig.argv/configFile reporter introspection. Use when
  testing passkey authentication flows, seeding localStorage/sessionStorage in tests, configuring
  video on retries, capturing WebSocket traffic in traces, attaching to an existing browser via
  CDP, annotating screencast recordings, or writing a custom reporter that needs the run's CLI
  args or resolved config path. Triggers on: "test passkeys playwright", "WebAuthn virtual
  authenticator", "playwright localStorage", "sessionStorage test", "video on retries
  playwright", "failOnFlakyTests", "soft poll assertion", "websocket trace playwright",
  "connectOverCDP artifactsDir", "screencast cursor", "grep-invert shorthand", "FullConfig.argv",
  "custom reporter config file".
---

# Playwright 1.61 New APIs

Released June 2026. No breaking changes.

## 1. WebAuthn Passkeys via `browserContext.credentials`

Virtual authenticator — no hardware security key needed. **Chromium-only** (does not work in WebKit/Firefox).

### Register a passkey in a setup test, reuse in spec tests:

```typescript
// global-setup.ts
import { chromium } from '@playwright/test';

export default async function setup() {
  const browser = await chromium.launch();
  const context = await browser.newContext({ ignoreHTTPSErrors: true });

  await context.credentials.enable();

  const page = await context.newPage();
  await page.goto('/register');
  await page.getByRole('button', { name: 'Register passkey' }).click();
  await expect(page.getByText('Passkey registered')).toBeVisible();

  // Serialize the registered credential for reuse across tests
  const creds = await context.credentials.get();
  require('fs').writeFileSync('passkey.json', JSON.stringify(creds));

  await browser.close();
}
```

```typescript
// passkey.fixture.ts
import { test as base, BrowserContext } from '@playwright/test';

const test = base.extend<{ authedContext: BrowserContext }>({
  authedContext: async ({ browser }, use) => {
    const context = await browser.newContext({ ignoreHTTPSErrors: true });
    await context.credentials.enable();

    const savedCreds = JSON.parse(require('fs').readFileSync('passkey.json', 'utf8'));
    await context.credentials.install(savedCreds);

    await use(context);
    await context.close();
  },
});

export { test };
```

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

> `credentials.enable()` → activates the virtual authenticator.  
> `credentials.install([...])` → seeds serialized passkeys into the context.  
> CDP-based: intercepts `navigator.credentials.create()` and `.get()` automatically.

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
// Returns: { authToken: 'test-jwt-abc123', userId: '42', ... }

// sessionStorage — same API, tab-scoped
await page.sessionStorage.setItem('step', '2');
```

**Use case**: Any feature that reads auth/session state from storage can skip UI login entirely — set the token, navigate, start testing the feature.

## 3. Video Retention Modes

| Mode | Records | Keeps video when... |
|------|---------|---------------------|
| `'off'` | Never | — |
| `'on'` | Always | Always |
| `'retain-on-failure'` | Yes | Test failed (any attempt) |
| `'retain-on-first-failure'` | Yes | **First** attempt fails only |
| `'on-all-retries'` | Yes | **Retries only** (skips initial pass) |
| `'retain-on-failure-and-retries'` | Yes | First failure + all retry attempts |

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

## 5. `failOnFlakyTests` Config

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

Adds a visual cursor decoration over recorded pointer actions, useful for demo/bug-repro recordings where a reviewer needs to see exactly where clicks landed:

```typescript
await page.screencast.showActions({ cursor: true });
```

## 10. `-G` Shorthand for `--grep-invert`

```bash
# Run everything except tests tagged @slow
npx playwright test -G @slow
```

Same behavior as `--grep-invert @slow`, just terser for frequent CLI use (e.g. excluding a smoke-only tag during full-suite local runs).

## 11. `FullConfig.argv` and `FullConfig.configFile` — Reporter Introspection

Two new fields on the `FullConfig` object passed to custom reporters:

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
- https://github.com/microsoft/playwright/releases/tag/v1.61.0
- https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/release-notes-js.md
- https://raw.githubusercontent.com/microsoft/playwright/v1.61.0/docs/src/release-notes-js.md
- https://www.corbado.com/blog/passkeys-e2e-playwright-testing-webauthn-virtual-authenticator
- https://changjoon-baek.medium.com/overcoming-passkey-verification-in-test-automation-fc7fc6748bd6
- https://dev.to/kochan/testing-webauthn-in-ci-e2e-automation-with-virtual-authenticators-and-mailpit-part-2-4j4i
