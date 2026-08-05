---
name: playwright-1.62-new-apis
description: >-
  Use Playwright 1.62 (July 2026) new APIs including the "stories and galleries"
  component-testing model, AbortSignal cancellation on actions/assertions, WebP screenshots,
  Reporter.preprocess() custom test filtering, retryStrategy 'isolated', WebAuthn credentials in
  storageState, the scroll action option, APIResponse.timing(), Locator.waitForFunction(), and
  the bundled `npx playwright mcp` / `npx playwright cli`. Use when writing component tests with
  mount fixtures, needing to cancel a long-running action/assertion, storing screenshots as WebP,
  writing a custom reporter that skips/excludes tests before the run starts, isolating retries
  from a flaky suite, persisting passkeys across contexts, opting an action out of auto-scroll,
  timing an API response, or waiting on a custom condition via a Locator. Triggers on:
  "playwright 1.62", "stories and galleries", "Fixtures.mount", "playwright AbortSignal",
  "playwright cancel action", "toHaveScreenshot webp", "Reporter.preprocess", "retryStrategy
  isolated", "storageState credentials webauthn", "scroll auto none option",
  "APIResponse.timing", "Locator.waitForFunction", "npx playwright mcp", "npx playwright cli",
  "mergeFiles reporter option".
---

# Playwright 1.62 New APIs

Released July 2026. No breaking API changes; Debian 11 support dropped.

## 1. Component Testing: "Stories and Galleries"

[Component testing](https://playwright.dev/docs/test-components) moves off ad-hoc per-test mounting onto a **stories and galleries** model. A **story** wraps a component in one specific scenario (props, mock data, providers); a **gallery** page (served by your app) renders stories on demand. The new `Fixtures.mount` fixture navigates to the gallery, mounts a story by id, and returns a `Locator` scoped to the story's root element:

```typescript
test('click should expand', async ({ mount }) => {
  const component = await mount('components/Expandable/Stateful');
  await component.getByRole('button').click();
  await expect(component.getByTestId('expanded')).toHaveValue('true');
});
```

Pass a story type as a template argument to type-check its props, and call `update(props)` / `unmount()` on the returned locator to re-render or tear down mid-test without a fresh `mount()`.

## 2. Cancel Operations with `AbortSignal`

Most actions and web-first assertions now accept a `signal` option taking a standard `AbortSignal`:

```typescript
const controller = new AbortController();
setTimeout(() => controller.abort(), 1000);

await page.getByRole('button', { name: 'Submit' }).click({ signal: controller.signal });
await expect(page.getByText('Done')).toBeVisible({ signal: controller.signal });
```

A signal does **not** disable the default timeout — pass `timeout: 0` alongside it if you want the abort to be the only way the wait ends. Useful for tying a wait's lifetime to an outer test-level cancellation (e.g. a custom "stop testing this flow" trigger) instead of a fixed timeout.

## 3. WebP Screenshots

`toHaveScreenshot()` (page and locator assertions) and `page.screenshot()` / `locator.screenshot()` now support `.webp`:

```typescript
// Visual-regression golden stored as lossless WebP
await expect(page).toHaveScreenshot('homepage.webp');

// Standalone screenshot, trading quality for file size
await page.screenshot({ path: 'homepage.webp', quality: 50 });
```

Quality `100` (default) is lossless; lower values use lossy compression. Smaller golden-file storage for visual-regression suites with many baselines.

## 4. `Reporter.preprocess()` — Custom Test Filtering

New hook runs after config resolution but before `Reporter.onBegin()`, letting a reporter mark tests as skipped/excluded/fixed/failing via a `TestRun` object — before the run even starts:

```typescript
class MyReporter {
  async preprocess({ config, suite, testRun }) {
    for (const test of suite.allTests()) {
      if (shouldSkip(test)) testRun.skip(test);
    }
  }
}
```

**Use case**: dynamic skip logic driven by external state (feature-flag service, flaky-test quarantine list fetched from an API) that isn't expressible as a static `test.skip()` condition in the spec file itself.

## 5. Isolated Retries — `retryStrategy: 'isolated'`

```typescript
// playwright.config.ts
export default defineConfig({
  retries: 2,
  retryStrategy: 'isolated', // default is 'immediate'
});
```

`'immediate'` (default) retries a failed test as soon as a worker frees up, interleaved with other tests. `'isolated'` defers all retries to the end of the run and executes them one-by-one in a single worker — reduces cross-test interference (shared resources, rate limits, server load) when diagnosing whether a failure is a real regression or noise from parallel execution.

## 6. WebAuthn Credentials in `storageState`

`BrowserContext.storageState()` now has a `credentials` option that includes the context's virtual WebAuthn credentials (passkeys) in the saved state, so they persist and re-seed into later contexts the same way cookies/localStorage already do — no more separate serialize/`credentials.install()` dance introduced in 1.61 (see `playwright-1.61-new-apis`):

```typescript
const state = await context.storageState({ path: 'state.json', credentials: true });
// Later:
const context2 = await browser.newContext({ storageState: 'state.json' });
// Passkeys registered in the first context are already usable here.
```

## 7. `scroll` Action Option

New `scroll: 'auto' | 'none'` option on actions to opt out of Playwright's automatic scroll-into-view:

```typescript
await page.getByRole('button', { name: 'Submit' }).click({ scroll: 'none' });
```

**Use case**: testing sticky/fixed-position elements or custom scroll containers where Playwright's default scroll-into-view fights your app's own scroll logic.

## 8. `APIResponse.timing()`

```typescript
const resp = await request.get('https://api.example.com/data');
const timing = await resp.timing();
// Resource timing breakdown for the API response (DNS, connect, TTFB, etc.)
```

Brings the same timing introspection already available for page navigations to standalone `APIRequestContext` calls — useful for API-level performance assertions in a test suite that doesn't drive a full page.

## 9. `Locator.waitForFunction()`

```typescript
await page.locator('.chart').waitForFunction(el => el.dataset.rendered === 'true');
```

Waits until a function — called with the matching element — returns a truthy value. Complements the existing `page.waitForFunction()` when the condition is scoped to one element rather than the whole page. `page.evaluate()`/`addInitScript()` now also accept functions directly as arguments (previously required serializable values).

## 10. Bundled MCP + CLI: `npx playwright mcp` / `npx playwright cli`

Playwright now bundles the Playwright MCP server and `playwright-cli` directly — runnable via `npx playwright mcp` and `npx playwright cli` without installing the separate `@playwright/mcp` / `@playwright/cli` packages. The standalone packages (see `playwright-mcp-server` and `playwright-cli-agent` skills) still work and update independently; the bundled entry points are a lower-friction on-ramp when the project already has `@playwright/test` installed.

## 11. HTML Reporter `mergeFiles` Config Option

The HTML report's "Merge files" grouping — previously only a UI toggle in the report itself — is now configurable from `playwright.config.ts`:

```typescript
export default defineConfig({
  reporter: [['html', { mergeFiles: true }]],
});
```

## Browser Versions

Chromium 151.0.7922.34, Firefox 153.0, WebKit 26.5. Also tested against Chrome 151 and Edge 151 stable channels.

## Announcements

- Debian 11 is no longer supported.

## Sources
- https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/release-notes-js.md
