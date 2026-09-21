---
name: playwright-1.63-new-apis
description: Use Playwright 1.63 (September 2026) new APIs including named test locks for shared-resource serialization, subtree-wide cross-frame locators, Locator.visible() for visible-only matching, test.step() subtitle/params for richer reporter output, selective trace snapshot capture (dom/aria/screen), Locator.ariaSnapshotJSON(), and the --add-reporter CLI flag. Use when two tests fight over the same external account/service and need serialization without a global setup lock file, searching for an element across iframes without chaining frameLocator() per frame, filtering a locator to only currently-visible matches, attaching structured metadata to a test.step() for custom reporters, trimming trace file size by capturing only some snapshot types, or appending a reporter (e.g. a CI dashboard reporter) without overriding the configured ones. Triggers on: "playwright 1.63", "playwright test lock", "test.step subtitle params", "playwright cross-frame locator", "frameLocator no selector", "Locator.visible", "playwright aria trace", "trace snapshots dom aria screen", "ariaSnapshotJSON", "--add-reporter", "playwright perfetto reporter".
---

# Playwright 1.63 New APIs

Released September 4, 2026, ~6 weeks after 1.62. Breaking change: Ubuntu 20.04 no longer supported; Linux arm64 now downloads the Chrome for Testing build of Chromium (same as other platforms) instead of a separate Chromium build.

## 1. Test Locks — Serialize Tests on a Shared Resource

Declare a named lock so tests touching the same external resource (a shared staging account, a rate-limited third-party API, a singleton DB seed) never run concurrently, even across files and workers:

```typescript
test('update user settings', { lock: 'user-settings' }, async ({ page }) => {
  // never runs at the same time as any other test holding the 'user-settings' lock
});
```

`test.describe()` also accepts a `lock` option to apply it to a whole group, and a test can hold multiple locks. This replaces ad-hoc workarounds like a single dedicated worker/project or a custom file-lock fixture for tests that can't be parallelized because they share external state.

## 2. Cross-Frame Locators — No More Per-Frame Chaining

`page.frameLocator()` / `frame.frameLocator()` called **with no selector** now searches any frame in the subtree, not just the frame it's chained from:

```typescript
// Finds the button in ANY frame on the page, without knowing which iframe it's in.
await page.frameLocator().getByRole('button', { name: 'Submit' }).click();
```

Useful for iframe-heavy pages (payment widgets, embedded editors, ad frames) where the target frame's identity is unstable or unknown — previously required either guessing the frame selector or walking `page.frames()` manually.

## 3. `Locator.visible()` — Visible-Only Matching

```typescript
await page.locator('button').visible().click();
```

Filters a locator to elements passing Playwright's visibility check (attached, non-zero size, no `visibility: hidden`/`display: none`, not clipped to zero). Useful when the same selector matches both a hidden template/duplicate (e.g. a mobile-nav clone hidden at desktop width) and the real interactive element — avoids the classic "strict mode violation: resolved to 2 elements" from `:visible` CSS pseudo-class workarounds.

## 4. `test.step()` Subtitle & Params

```typescript
await test.step('Login', async () => {
  // ...
}, { subtitle: 'as admin', params: { user: 'admin' } });
```

Reporters receive these via `testStep.subtitle` and `testStep.params`. Lets a custom/CI reporter render "Login — as admin" instead of a bare step name, or group/filter steps by structured `params` — useful for data-driven tests where the same step runs once per fixture row and you want the report to show which row failed without stuffing it into the step title string.

## 5. Selective Trace Snapshots

`trace.snapshots` now accepts an object instead of just a boolean, to capture only the snapshot types you need:

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    trace: {
      mode: 'on',
      snapshots: { dom: true, aria: true, screen: true },
    },
  },
});
```

Trims trace file size for CI artifact storage when you only care about, say, `screen` (screenshots) and not full DOM snapshots, or vice versa.

## 6. Aria Traces — Trace Viewer "Display Aria" Mode

When `aria` and `screen` snapshots are recorded (see #5), the trace viewer's new **Display Aria** mode shows the action screenshot side by side with the accessibility-tree snapshot at that point in time — makes it far faster to spot an accessible-name/role regression from a trace than reconstructing it from the DOM snapshot. Pairs with `Locator.ariaSnapshotJSON()`, which returns the same aria snapshot as JSON (previously YAML-only via `ariaSnapshot()`) for programmatic diffing in a custom assertion or reporter.

## 7. `--add-reporter` CLI Flag

```bash
npx playwright test --add-reporter=./my-ci-reporter.ts
```

Appends a reporter to the ones already configured in `playwright.config.ts` instead of replacing them — useful for a one-off CI run that needs an extra reporter (e.g. a dashboard uploader) without editing the config or duplicating the full `reporter: [...]` array on the command line.

## 8. Other Additions

- `BrowserContext.newContext({ httpCredentials })` now accepts an array of credentials (multiple realms/domains in one context).
- `BrowserContext.storageState()` gains an `opfs` option to persist Origin Private File System data alongside cookies/localStorage/IndexedDB.
- New events `page.on('dialogClosed')` / `browserContext.on('dialogClosed')` — fires after a dialog (alert/confirm/prompt) is dismissed, complementing the existing `dialog` (open) event.
- `TestOptions.reducedMotion`, `TestOptions.forcedColors`, `TestOptions.contrast` — standalone per-test options for the corresponding `prefers-reduced-motion` / `forced-colors` / `prefers-contrast` emulation (previously only settable via `page.emulateMedia()`).
- Built-in `perfetto` reporter — emits a Perfetto-format trace for timeline visualization in `ui.perfetto.dev` or Chrome's trace viewer.

## Sources
- https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/release-notes-js.md
- [Playwright 1.63 Release: Test Locks, Aria Traces and More — TestDino](https://testdino.com/blog/playwright-1-63-release)
- [Release v1.63.0 — microsoft/playwright GitHub](https://github.com/microsoft/playwright/releases/tag/v1.63.0)
