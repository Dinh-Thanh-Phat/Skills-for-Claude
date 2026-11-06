---
name: playwright-1.65-new-apis
description: >-
  Use Playwright 1.65 (November 2026) new features and breaking changes: Bun test runner
  (`bunx --bun playwright test`), `failures` reporter and `onlyFailures` option for html/json/junit,
  built-in `-exclusive-` lock, description-only `test.skip/fixme/fail/slow`,
  `PLAYWRIGHT_TRANSFORM_CACHE_DIR`, `CDPSession.send` timeout/signal, `TestRun.mode`, plus breaking
  changes (inert elements, empty shard fails, RFC 6265 cookies, proxy credentials, aria names,
  `params` appended, blob reporter cleans dir). Use when upgrading to 1.65 or triaging CI failures
  right after the upgrade. Triggers on: "playwright 1.65", "bunx --bun playwright", "onlyFailures",
  "failures reporter", "-exclusive- lock", "pass-with-no-tests", "No tests found shard",
  "useDefineForClassFields", "PLAYWRIGHT_TRANSFORM_CACHE_DIR".
---

# Playwright 1.65 New APIs

Released 2026-11-05 (Chromium 158, Firefox 159, WebKit 27.2; also tested on Chrome 157 / Edge 156).
Node.js 20 is no longer tested; Docker images ship Node.js 26. Read the breaking changes first.

## Breaking changes — check before upgrading

1. **Class fields**: `useDefineForClassFields` follows `tsconfig.json` (on for ES2022+ or unset
   `target`). A field initializer reading a constructor parameter property now throws — move it
   into the constructor or set `"useDefineForClassFields": false`.
2. **Inert elements**: click/check/tap/fill/clear/selectOption wait for the element to stop being
   `inert`; they time out if it stays inert (e.g. page behind an open modal).
3. **Sharding**: a sharded run fails with "No tests found" when *no* shard matches tests; allow
   with `--pass-with-no-tests`. An empty shard still passes if other shards have tests.
   (Check `--only-changed` / grep-filtered shard jobs — see `test-parallelization`.)
4. **Cookies follow RFC 6265**: URL-filtered `cookies()` no longer returns host-only cookies for
   subdomains or `Path=/api` cookies for `/apiv2`; `Path=/foo/` no longer matches `/foo`;
   nameless cookies send `Cookie: x`.
5. **Proxy credentials** in `launch({ proxy })` answer only proxy challenges, no longer sent to
   sites. Use `httpCredentials` for site auth.
6. **Accessible names / aria snapshots exclude non-rendered text** (unslotted text, closed
   `<details>`): `getByRole` name matches, `ariaSnapshot`, `toMatchAriaSnapshot` can change —
   re-baseline snapshots.
7. **`APIRequestContext` `params`** (string/`URLSearchParams`) are *appended* to the URL's query,
   not replacing it.
8. `.css/.less/.scss` imports in tests load as empty modules (file must exist).
9. **Blob reporter** again deletes its output dir before writing (1.64 kept other files) — don't
   write other artifacts into the blob dir when merging shards.
10. CommonJS `test(` locations now point at the callee start (`a.spec.ts:3:7`), matching ESM.

## Reporters: failures only

```ts
// playwright.config.ts
reporter: [
  ['failures'],                       // prints failures + successful retries live, then summary
  ['html', { onlyFailures: true }],   // keep only unexpected, flaky, interrupted tests
],
```
`onlyFailures` also works for `json` and `junit` — smaller CI artifacts for large suites.

## Test runner

```ts
test('restart the server', { lock: '-exclusive-' }, async () => {}); // runs only when nothing else runs
test('upload a file', async () => { test.skip('Not implemented yet'); }); // description-only
```
Description-only form works for `skip`, `fixme`, `fail`, `slow` and is recorded as an annotation.
Use `-exclusive-` sparingly (it serializes the run); prefer isolation (see `test-isolation`).

- `PLAYWRIGHT_TRANSFORM_CACHE_DIR=<dir>` — transpile cache location (shared multi-user Linux hosts).
- `CDPSession.send(method, params, { timeout, signal })` — bound CDP calls.
- `TestRun.mode` — suite execution mode, readable in `Reporter.preprocess`.

## Bun (experimental)

`bunx --bun playwright test` (without `--bun` it runs on Node). Bun transpiles TS itself (no
Babel/cache). Limits: no watch mode, `--tsconfig`/JSX options ignored, no custom ESM loaders,
stack traces lack async frames and API names omit class (`click` vs `locator.click`), test
console output missing from trace/UI mode. Keep CI on Node unless you have a reason.

## Sources
- https://github.com/microsoft/playwright/blob/main/docs/src/release-notes-js.md (Version 1.65)
- https://registry.npmjs.org/@playwright/test (latest 1.65.0, published 2026-11-05)
