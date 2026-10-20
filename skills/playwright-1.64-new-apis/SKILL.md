---
name: playwright-1.64-new-apis
description: Use Playwright 1.64 (October 2026) new APIs and breaking changes — page.webmcp / frame.webmcp for testing tools a page registers through WebMCP, APIRequestContext.addCookies()/cookies()/clearCookies() for API-test cookie control, testProject.default to keep a project configured but not run, --shuffle with a reproducible seed, describe-level test locks, video fps/CSS styling, Locator.within(), page.getByRef(). Use when testing a site's WebMCP tools (or page.webmcp.tools() unexpectedly returns []), injecting or clearing a session cookie in an API test without a storageState file, hunting order-dependent tests, upgrading from 1.63 and screenshots/media queries or snapshot CI runs changed. Triggers on: "playwright 1.64", "webmcp", "page.webmcp", "document.modelContext", "registerTool", "apiRequestContext addCookies", "request.cookies", "clearCookies request", "--shuffle", "shuffle seed", "project default false", "update-snapshots=missing", "Locator.within", "getByRef".
---

# Playwright 1.64 New APIs

1.64.0 released 2026-10-07, 1.64.1 on 2026-10-14 (latest stable as of 2026-10-20). Browsers: Chromium 156, Firefox 157, WebKit 27.2.
Everything marked **(measured)** was run against 1.64.1 + Chromium 156 on 2026-10-20, not copied from release notes.

## 1. WebMCP — test the tools a page exposes to AI agents

```typescript
import { test, expect, chromium } from '@playwright/test';

test('cart tool contract', async () => {
  const browser = await chromium.launch({ args: ['--enable-features=WebMCP'] }); // REQUIRED
  const page = await browser.newPage();
  await page.goto('https://staging.example.com/');           // real http(s) origin
  const tools = await page.webmcp.tools();                   // [{ name, description, inputSchema }]
  expect(tools.map(t => t.name)).toContain('add_to_cart');
  const res = await page.webmcp.callTool('add_to_cart', { sku: 'A1', qty: 2 });
  expect(res.content[0].text).toContain('added');
  await browser.close();
});
```

Page side, for writing fixtures: `document.modelContext.registerTool({ name, description, inputSchema, execute })`.

**Traps (measured):**

| Observation | Consequence for tests |
|---|---|
| In Chromium 156 the API lives on **`document.modelContext`**; `navigator.modelContext` is `undefined` | Fixture pages / feature-detection written for `navigator.modelContext` (as in many articles) register nothing |
| Flag missing → `tools()` throws `WebMCP is not enabled. Launch the browser with "--enable-features=WebMCP"` | Clear error — good |
| Flag present but page is `about:blank` / `setContent()` on a fresh page → `document.modelContext` is undefined and `tools()` returns **`[]` silently** | `expect(tools).toHaveLength(0)` passes for the wrong reason. Always assert a known tool EXISTS before asserting anything else |
| Browser does **not** validate `inputSchema`: calling `add` without required `b` ran the tool and returned `"NaN"` | Missing-field / wrong-type cases are the page's responsibility — write negative tests for every `required` field; they are real bugs, not "browser will reject it" |
| A tool that throws surfaces as `UnknownError: Tool was executed but the invocation failed…` — the original message is lost | Assert the call rejects, not the error text. To check the message, have the tool return an error result instead of throwing |
| A tool returning a plain string gives that string back (not wrapped in `content`) | Don't assume `res.content` exists — assert the shape the page promises |

Also: Playwright MCP exposes page tools to agents as `webmcp_<tool>` by default (`--no-webmcp` to opt out); `playwright-cli webmcp-list` / `webmcp-call <tool> --params '<json>'`. For testing a standalone MCP *server* (not a page), see `mcp-server-testing` instead.

## 2. APIRequestContext cookies — `addCookies()` / `cookies()` / `clearCookies()`

```typescript
test('expired session is rejected', async ({ request }) => {
  await request.addCookies([{ name: 'session-id', value: 'expired-123', url: BASE }]);
  expect((await request.get(`${BASE}/api/me`)).status()).toBe(401);
  await request.clearCookies({ name: 'session-id' });           // filter by name/domain/path
});
```

Measured behaviour:
- Added cookies are sent on the next request; `Set-Cookie` from responses lands in the same jar and shows up in `cookies(url)` and `storageState()`.
- `clearCookies({ name })` removes only that cookie; `clearCookies()` removes all.
- Each cookie needs `url` **or** `domain`+`path`, otherwise: `Cookie should have a url or a domain/path pair`.
- `page.request.addCookies()` writes into the **browser context** jar (visible to `context.cookies()` and `document.cookie`); `context.clearCookies()` empties `page.request.cookies()` too. The standalone `request` fixture stays isolated.

Replaces the old workarounds (hand-built `Cookie:` headers, or writing a `storageState` JSON just to seed one cookie). Good fit for auth negative tests: tampered/expired/foreign-user session cookies.

## 3. Test runner

- **`testProject.default: false`** — project stays in config but plain `npx playwright test` skips it; `--project=firefox` runs it, `--project="*"` runs all. (measured: 6 tests → 12 with `"*"`)
- **`--shuffle [seed]`** — random order, prints `shuffle seed N`; passing that seed reproduced the identical order on two runs (measured). Use in a nightly job to surface tests that depend on each other; when one fails, re-run with the printed seed before debugging.
- **`test.describe.configure({ lock: 'name' })`** — 1.63 test locks applied to a whole file/group.
- **`expect: { toHaveScreenshot: { type: 'webp' } }`** — store unnamed screenshots as WebP.

## 4. Breaking changes (check when upgrading from ≤1.63)

- **`--update-snapshots=missing` now PASSES** the test that only wrote a missing snapshot (measured: `1 passed`, file written). No flag (now called `'default'`) still writes it and FAILS. A CI job using `missing` will no longer go red on a forgotten baseline — review new snapshot files in the PR instead.
- **`screen` is forwarded from device descriptors** — with `...devices['Desktop Chrome']`, `window.screen` and media queries now see the emulated screen size. Opt out with `screen: undefined`. Expect visual / responsive diffs right after upgrade.
- Elements inside an invisible iframe (`visibility: hidden`) count as hidden for actions, `isVisible()` and `toBeVisible()`.
- JSX in test files follows `tsconfig.json` (`jsx`, `jsxImportSource`…), default automatic runtime `react/jsx-runtime`.
- Video `show.actions.fontSize` deprecated → `style: { point, highlight, title }` (CSS strings).

## 5. Other additions

- `locator.within(parent)` — "this button within that dialog"; `nth()`/`first()` resolve per parent, e.g. `page.getByRole('cell').nth(2).within(page.getByRole('row'))` = third cell of every row.
- `page.getByRef('e2')` — locate by aria ref from `page.ariaSnapshot({ mode: 'ai' })`.
- `page.content({ includeShadow: true })` serializes open shadow roots as declarative shadow DOM.
- WebAuthn: `credentials.create({ signCount })`; `signCount` returned by `create()`/`get()` and saved in storage state.
- `fullConfig.filteredProjects` — projects selected after `--project`, available in global setup and reporters.
- Video: `fps` option (Firefox/WebKit cap 25), VP9 encoding, cursor persists across navigations.
- 1.64.1 fixes: Chromium 155+ aborting a preflighted cross-origin redirect whenever any `page.route` is registered (`net::ERR_ABORTED`) — upgrade to 1.64.1 if API-mocking tests hit that; Electron first-window loss.

## Sources
- [Release v1.64.0 — microsoft/playwright](https://github.com/microsoft/playwright/releases/tag/v1.64.0)
- [Release v1.64.1 — microsoft/playwright](https://github.com/microsoft/playwright/releases/tag/v1.64.1)
- https://playwright.dev/docs/api/class-webmcp · https://playwright.dev/docs/api/class-apirequestcontext
