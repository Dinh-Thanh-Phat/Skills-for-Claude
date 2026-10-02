---
name: playwright-1.60-new-apis
description: Playwright 1.60 (May 2026) new APIs — locator.drop() for synthetic external file/data drop on upload zones, tracing.startHar() for on-demand HAR recording, test.abort() to fail a test immediately from a fixture/hook/route handler, ARIA bounding boxes for AI-friendly assertions, and errorContext for richer assertion failure diagnostics. Use when testing file-drop upload zones, unifying HAR recording with traces, aborting tests on precondition failure, or diagnosing assertion failures with ARIA context. Triggers on: "locator.drop", "drop file", "tracing.startHar", "HAR trace", "test.abort", "abort test", "ARIA bounding box", "errorContext", "Playwright 1.60".
---

# Playwright 1.60 New APIs

Released May 2026. Six headline features that improve drag-and-drop testing, HAR recording, test guardrails, and failure diagnostics.

---

## 1. `locator.drop()` — Synthetic File/Data Drop

Simulates an external drag-and-drop onto an element. Dispatches `dragenter`, `dragover`, and `drop` with a synthetic `DataTransfer` — works across Chromium, Firefox, and WebKit. Ideal for testing file-upload zones that use `drop` events instead of `<input type=file>`.

```typescript
// Drop a file onto an upload zone (files: path | path[] | {name,mimeType,buffer} | array of those)
await page.getByTestId('upload-zone').drop({
  files: [{ name: 'report.csv', mimeType: 'text/csv', buffer: Buffer.from('a,b\n1,2') }],
});
await expect(page.getByText('report.csv')).toBeVisible();

// Drop clipboard-like data (mime-type → string map)
await page.getByTestId('upload-zone').drop({
  data: { 'text/plain': 'hello world', 'text/uri-list': 'https://example.com' },
});
```

Payload is `{ files?, data? }`; other options: `position`, `timeout`. There is **no** `target` option — `drop()` simulates an *external* drop. For element-to-element drag (e.g. Kanban card → column) use `locator.dragTo(target)`.

If the target's `dragover` listener does not call `preventDefault()`, Playwright treats the drop as rejected, dispatches `dragleave`, and `drop()` **throws**.

> Use `locator.drop()` for upload-zone tests instead of `setInputFiles()` — `setInputFiles()` only works on `<input type=file>` elements, not custom drop targets.

---

## 2. `tracing.startHar()` / `tracing.stopHar()` — HAR as First-Class Tracing API

Before 1.60, capturing HAR required the `recordHar` context option set at context creation. Now HAR recording can be started/stopped on demand via the tracing API. Signature: `tracing.startHar(path, options?)` — the HAR is written to **that path** (a separate file, not embedded in `trace.zip`) when `stopHar()` is called or the returned `Disposable` is disposed. Only one HAR recording per `Tracing` instance at a time.

```typescript
// ✅ 1.60+
await context.tracing.startHar('artifacts/network.har', { urlFilter: '**/api/**' });

await page.goto('/dashboard');
// ... test actions ...

await context.tracing.stopHar();   // network.har written here

// Or scope it with explicit resource management:
await using har = await context.tracing.startHar('trace.har');
// HAR finalized when `har` goes out of scope
```

**Options** (same as `recordHar`):
| Option | Values | Effect |
|--------|--------|--------|
| `content` | `"omit"` \| `"embed"` \| `"attach"` | Response body handling (default `attach` for `.zip` path, `embed` otherwise) |
| `mode` | `"full"` \| `"minimal"` | `minimal` = only what is needed to replay/route from HAR (omits sizes, timing, cookies, security…) |
| `urlFilter` | glob / RegExp | Only record matching URLs |
| `resourcesDir` | path | With `content: 'attach'`, put bodies in this dir (not compatible with `.zip`) |

---

## 3. `test.abort()` — Fail Fast on Unrecoverable Misuse

`test.abort(message?)` aborts the currently running test **by throwing** — the test is immediately marked **failed** (not skipped), and the message is included in the failure error. Callable from a fixture, hook, or route handler. There is no `testInfo.abort()`.

Use it as a guardrail when the test is doing something it must never do (e.g. hitting a shared/production endpoint):

```typescript
test('does not publish to the shared page', async ({ page }) => {
  await page.route('**/publish', route => {
    test.abort('Tests must not publish to the shared page. Use the `clone` option.');
    return route.abort();
  });
  // ...
});
```

**Precondition not met (feature flag off, seed data missing)? That is a skip, not an abort** — use runtime `test.skip(condition, reason)`:

```typescript
test.beforeEach(async ({ page }) => {
  const count = await page.locator('[data-testid="product-card"]').count();
  test.skip(count === 0, 'No products seeded — cannot run cart tests');
});
```

> `test.abort()` = "this test is broken/misused → FAIL now". `test.skip(cond)` = "this environment can't run it → SKIP". Using abort for env preconditions turns infra gaps into red builds; using skip for misuse hides real problems (see `skip-vs-fail`).

---

## 4. ARIA Bounding Boxes — `boxes: true` on `ariaSnapshot()`

The `boxes` option appends each element's bounding box `[box=x,y,w,h]` to the ARIA snapshot string. Makes snapshots useful for AI-driven or coordinate-aware assertions.

```typescript
// Without boxes (default)
const snapshot = await page.ariaSnapshot();
// - heading "Dashboard" [level=1]
// - button "Export"

// With boxes
const snapshotWithBoxes = await page.ariaSnapshot({ boxes: true });
// - heading "Dashboard" [level=1] [box=24,48,320,36]
// - button "Export" [box=680,48,96,32]

// Useful for asserting layout — e.g., button is in the top-right
const lines = snapshotWithBoxes.split('\n');
const exportLine = lines.find(l => l.includes('"Export"'));
// parse [box=x,y,w,h] and assert x > 500 for right-aligned button
```

---

## 5. `errorContext` — ARIA Snapshot at Assertion Failure

`testInfoError.errorContext` now contains additional diagnostic information at the moment an `expect()` matcher fails. For locator assertions, this is the ARIA snapshot of the matched element's subtree — giving you the actual DOM structure rather than just a string diff.

This is surfaced automatically in the HTML report and Trace Viewer error panel for 1.60+. No code change required to benefit from it.

```typescript
// When this assertion fails:
await expect(page.getByRole('dialog')).toContainText('Order confirmed');

// The error report now includes:
// errorContext: ARIA snapshot of <dialog> at failure time:
//   - dialog
//     - heading "Payment failed" [level=2]
//     - paragraph "Your card was declined."
// → immediately shows you what IS in the dialog, not just what wasn't found
```

---

## 6. JSON Pretty-Print in Trace Viewer

The Trace Viewer network panel now has a pretty-print toggle for JSON response bodies. No test-code change needed — just toggle in the UI when debugging.

---

## Quick Reference

| Feature | API / Flag | Use When |
|---------|-----------|----------|
| Drop files/data on element | `locator.drop({ files, data })` | Upload/drop zones (element→element drag: `dragTo`) |
| On-demand HAR recording | `tracing.startHar(path)` / `stopHar()` | Start/stop HAR mid-test without `recordHar` |
| Fail test at runtime | `test.abort(message)` | Detected misuse (forbidden endpoint); preconditions → `test.skip(cond)` |
| ARIA layout assertions | `page.ariaSnapshot({ boxes: true })` | AI-driven tests, layout verification |
| Richer assertion errors | automatic via `errorContext` | Always on in 1.60+ |

## Sources

- [Playwright 1.60 Release — TestDino](https://www.testdino.com/blog/playwright-1-60-release)
- [Release v1.60.0 — GitHub microsoft/playwright](https://github.com/microsoft/playwright/releases/tag/v1.60.0)
- [Release Notes — Playwright Docs](https://playwright.dev/docs/release-notes)
