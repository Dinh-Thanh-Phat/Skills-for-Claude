---
name: playwright-1.63-new-apis
description: >-
  Use Playwright 1.63 (September 2026) new APIs including named test locks for shared-resource
  serialization, frame-agnostic `frameLocator()`, `Locator.visible()`, structured step
  params/subtitles, aria+screen snapshots in traces, storageState `opfs`, `dialogClosed` events,
  `ariaSnapshotJSON()`, typed `APIRequestContext` responses, standalone `reducedMotion`/
  `forcedColors`/`contrast` test options, `--add-reporter`, `omitTags`, and the built-in
  `perfetto` reporter. Use when tests fight over a shared external resource/account, need to
  locate an element inside an unknown/nested iframe, must match only visible elements, want
  richer step metadata in reports, want an aria snapshot next to the screenshot in a trace, need
  typed API responses, or want to add a reporter without overriding the configured ones. Triggers
  on: "playwright 1.63", "playwright test lock", "lock option describe", "frameLocator no
  selector", "Locator.visible", "test.step subtitle params", "trace aria screenshot",
  "Display Aria trace viewer", "storageState opfs", "dialogClosed event", "ariaSnapshotJSON",
  "APIRequestContext typed response", "reducedMotion forcedColors contrast test options",
  "--add-reporter", "omitTags reporter option", "perfetto reporter playwright", "playwright
  install --no-remove", "codegen --http-credentials".
---

# Playwright 1.63 New APIs

Released September 2026. No breaking API changes; Ubuntu 20.04 support dropped; the experimental
`@playwright/experimental-ct-react`/`-react17`/`-vue` packages are frozen (migrate to the 1.62
stories model, see `playwright-1.62-new-apis`).

## 1. Test Locks — Serialize Access to a Shared Resource

A test (or a whole `describe` group) can declare a named `lock`. Tests sharing a lock name never
run concurrently — across files, workers, and projects — while every other test keeps running in
parallel:

```typescript
test('update user settings', { lock: 'user-settings' }, async ({ page }) => {
  // never runs at the same time as any other test holding 'user-settings'
});

test.describe('billing', { lock: 'billing-account' }, () => {
  // every test in this group serializes against the 'billing-account' lock
});
```

A test can hold multiple locks. This replaces ad-hoc `test.describe.serial()` + manual sharding
tricks for the specific case of "these tests are safe to parallelize except they all hit one
external service / one shared seeded account" — keep `serial()` for ordering-dependent tests,
reach for `lock` when the constraint is contention, not order.

## 2. Locate Across Frames Without Finding the Iframe First

`page.frameLocator()` / `frame.frameLocator()` called with **no selector** search any frame in the
subtree:

```typescript
// Old: had to locate the iframe first
await page.frameLocator('#payment-iframe').getByRole('button', { name: 'Pay' }).click();

// New: works regardless of which frame (or how deeply nested) the button is in
await page.frameLocator().getByRole('button', { name: 'Pay' }).click();
```

The rest of the locator chain still resolves inside a single frame like a normal locator, and
Playwright throws if the selector matches elements in more than one frame — so this is safe for
"I don't know/care which iframe" cases, not a way to match across multiple frames at once.
Useful for third-party embeds (payment widgets, chat widgets) whose iframe id/name churns.

## 3. `Locator.visible()` — Visible-Only Matching

```typescript
await page.locator('button').visible().click();
```

Recommended replacement for the `:visible` CSS pseudo-class — filters a locator down to elements
Playwright considers visible, composable with the rest of the locator API (`.first()`, `.filter()`,
assertions) in a way the CSS pseudo-class wasn't.

## 4. Structured Step Data: `subtitle` and `params`

`test.step()` now accepts `subtitle` and `params`, surfaced by reporters (trace viewer, HTML
report) next to the step title:

```typescript
await test.step('Login', async () => {
  await page.getByLabel('Username').fill('admin');
  await page.getByRole('button', { name: 'Sign in' }).click();
}, { subtitle: 'as admin', params: { user: 'admin' } });
```

Playwright's own API steps (`click`, `fill`, navigations, …) now report this automatically — a
`click` step's subtitle is the locator, a navigation step's subtitle is the URL — so traces are
readable without expanding every step to see what it acted on.

## 5. Aria + Screen Snapshots in Traces

`Tracing.start()` / the `trace` fixture option's `snapshots` sub-option now takes an object
selecting exactly what to capture on every action, instead of an implicit DOM-only snapshot:

```typescript title="playwright.config.ts"
export default defineConfig({
  use: {
    trace: {
      mode: 'on',
      snapshots: { dom: true, aria: true, screen: true },
    },
  },
});
```

With `aria` and `screen` both recorded, the trace viewer's new **Display Aria** mode shows the
action's screenshot side by side with its aria snapshot, and hovering an aria node highlights the
matching region on the screenshot — useful for debugging a locator that resolved to the "wrong"
element without re-running the test with `--debug`.

## 6. Other New APIs

- `Browser.newContext({ httpCredentials })` accepts an **array** of credentials; the first entry
  matching the request origin is used, entries without an origin match any request — useful when a
  test drives multiple origins each behind their own basic-auth.
- `BrowserContext.storageState({ opfs: true })` includes the [origin private file
  system](https://developer.mozilla.org/en-US/docs/Web/API/File_System_API/Origin_private_file_system)
  in the saved/restored storage state.
- New `page.on('dialogClosed', ...)` / `context.on('dialogClosed', ...)` events fire when a JS
  dialog is accepted, dismissed, or closed by the user — complements the existing `dialog` event
  for asserting a dialog was actually resolved, not just opened.
- `Locator.ariaSnapshotJSON()` / `Page.ariaSnapshotJSON()` return the aria snapshot as JSON
  (`mode`, `depth`, `boxes` options) instead of YAML — easier to diff/assert on programmatically
  than the YAML string form.
- `APIRequestContext` methods (`request.get()`, etc.) accept a type argument so `response.json()`
  comes back typed: `const user = await (await request.get<User>('/api/users/42')).json();`.
- Standalone `TestOptions.reducedMotion` / `TestOptions.forcedColors` / `TestOptions.contrast`
  config options set the same emulation as `browser.newContext({ reducedMotion, forcedColors,
  contrast })` (see `accessibility-testing`) but as first-class project/test config, so a whole
  project can run under `reducedMotion: 'reduce'` without a custom fixture.
- CLI: `npx playwright install --no-remove` keeps other Playwright installs' browsers instead of
  removing them; `npx playwright codegen --http-credentials` records against pages behind HTTP
  basic auth.
- Reporters: new `--add-reporter` CLI flag **appends** a reporter on top of whatever's in
  `playwright.config` (vs. `--reporter`, which replaces the list) — handy for a one-off
  `--add-reporter=./ci-notifier.ts` run without editing config. New `omitTags` option
  (`list`/`line`/`dot`/`github`/`junit` reporters) suppresses the tags Playwright auto-appends to
  test titles. New built-in `perfetto` reporter writes a Trace Event Format file viewable in
  [Perfetto UI](https://ui.perfetto.dev) or `chrome://tracing` — a timeline with one lane per
  worker, useful for visualizing worker utilization/scheduling gaps across a large parallel run.
  The HTML report now renders a duration waterfall next to test steps.

## Announcements

- The experimental `@playwright/experimental-ct-react`, `-react17`, and `-vue` packages will no
  longer be updated — migrate to the stories/galleries model (1.62, see `playwright-1.62-new-apis`).
- Ubuntu 20.04 is no longer supported.
- On Linux arm64, Playwright now downloads the Chrome for Testing build of Chromium (same build
  used on every other platform).

## Browser Versions

Chromium 153.0.8010.12, Firefox 155.0, WebKit 26.6. Also tested against Chrome 153 and Edge 153
stable channels.

## Sources
- https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/release-notes-js.md
