---
name: playwright-1.64-new-apis
description: >-
  Use Playwright 1.64 (October 2026) new APIs and breaking changes: WebMCP testing via
  `page.webmcp`, `Locator.within()`, `--shuffle` test order randomization, `TestProject.default`,
  `describe.configure({ lock })`, WebP `toHaveScreenshot`, video `fps` + CSS-styled action
  overlays, `page.getByRef()`, `APIRequestContext` cookie methods, `Credentials` signCount, plus
  breaking changes (device `screen` forwarding, JSX follows tsconfig, `--update-snapshots=missing`
  passes, hidden-iframe elements are hidden). Use when upgrading to 1.64, finding order-dependent
  tests, testing WebMCP tools a page exposes, or scoping a locator to a parent. Triggers on:
  "playwright 1.64", "page.webmcp", "WebMCP", "Locator.within", "playwright --shuffle",
  "project default false", "toHaveScreenshot webp", "getByRef", "APIRequestContext addCookies",
  "update-snapshots missing", "video fps".
---

# Playwright 1.64 New APIs

Released October 2026 (Chromium 156, Firefox 157, WebKit 27.2). Read the breaking changes first.

## Breaking changes — check before upgrading

- **Device `screen` forwarded**: `...devices['Desktop Chrome']` now sets `window.screen` and media
  queries. Opt out with `use: { ...devices['Desktop Chrome'], screen: undefined }`. Visual
  baselines or responsive tests may shift.
- **JSX follows `tsconfig.json`** (`jsx`, `jsxFactory`, `jsxFragmentFactory`, `jsxImportSource`);
  default is the automatic runtime from `react/jsx-runtime`.
- **`--update-snapshots=missing` now passes** when it only creates missing snapshots (CI can
  generate new + verify existing in one run). The unspecified default mode is now named
  `'default'` and behaves as before (writes missing snapshots but fails the test).
- **Elements in hidden iframes are hidden** for actions, `isVisible()` and `toBeVisible()`.

## WebMCP testing

Pages can register tools via the experimental WebMCP browser API; test them directly:

```ts
const browser = await chromium.launch({ args: ['--enable-features=WebMCP'] });
const page = await browser.newPage();
await page.goto('https://example.com');
for (const t of await page.webmcp.tools()) console.log(t.name, t.description);
const result = await page.webmcp.callTool('add', { a: 2, b: 40 });
expect(result.content[0].text).toBe('42');
```

Also on `Frame.webmcp`. Playwright MCP exposes page tools as `webmcp_<tool>` (disable with
`--no-webmcp`); CLI: `playwright-cli webmcp-list`, `webmcp-call <tool> --params '{...}'`.

## Test runner

- `npx playwright test --shuffle [seed]` — random order; prints the seed, rerun with it to
  reproduce. Run periodically to expose inter-test dependencies (see `flaky-test-prevention`).
- `TestProject.default: false` keeps a project defined but not run by default; a plain
  `npx playwright test` runs only default projects, `--project=firefox` runs one,
  `--project="*"` runs all (use on CI).
- `test.describe.configure({ lock: 'user-settings' })` — file/group-level named locks
  (see `playwright-1.63-new-apis`).
- `expect: { toHaveScreenshot: { type: 'webp' } }` stores unnamed screenshots as WebP (smaller).
- `FullConfig.filteredProjects` lists projects selected after `--project` filtering (global setup, reporters).

## Locator.within()

```ts
await page.getByRole('button', { name: 'Save' }).within(page.getByTestId('settings-dialog')).click();
// nth/first resolve inside EACH parent: third cell of every row
const col = page.getByRole('cell').nth(2).within(page.getByRole('row'));
await expect(col).toHaveText(['Apple', 'Banana', 'Cherry']);
```

## Video

`video: { mode: 'on', fps: 60, show: { actions: { style: { point, highlight, title } } } }` —
CSS-declaration strings style the click point, target highlight and title; replaces the deprecated
`fontSize`. VP9 encoding (smaller files); Firefox/WebKit cap at 25 fps. `fps` also on
`recordVideo` and `Screencast.start`.

## Other APIs

- `page.getByRef('e2')` — locate by aria ref from `page.ariaSnapshot({ mode: 'ai' })`.
- `page.content({ includeShadow: true })` — serialize open shadow roots as declarative shadow DOM.
- `request.addCookies() / cookies() / clearCookies()` on `APIRequestContext`.
- `Credentials.create({ signCount })`; `create/get` return `signCount`, saved in storage state (passkey tests).

## Sources
- https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/release-notes-js.md
- https://registry.npmjs.org/@playwright/test (latest = 1.64.0)
