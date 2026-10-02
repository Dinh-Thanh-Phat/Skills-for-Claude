---
name: playwright-component-testing
description: Playwright component testing with the stories-and-gallery model (Playwright 1.62+) — the built-in `mount('story/id', props)` fixture from plain @playwright/test mounts a story rendered by YOUR dev server, in a real browser. Use when writing isolated component tests for React, Vue, Svelte, Solid or any framework; testing component props, state transitions, accessibility and visual states; migrating off the frozen @playwright/experimental-ct-* packages; or choosing between Playwright CT and Vitest/JSDOM. Triggers on: "component test playwright", "mount component", "@playwright/experimental-ct", "playwright CT", "story gallery playwright", "*.story.tsx", "Fixtures.mount", "test React component in browser", "playwright component", "CT setup", "migrate experimental-ct".
---

# Playwright Component Testing (Stories & Gallery, 1.62+)

A component test is a **regular Playwright test** that runs against a small **story gallery** page served by **your own dev server**. No dedicated CT runtime, no bundler integration, no extra npm packages — the built-in `mount` fixture of `@playwright/test` drives it.

> **Status (as of 2026-10-02, Playwright 1.63):** the old `@playwright/experimental-ct-react` / `-ct-react17` / `-ct-vue` packages **will no longer be updated** (npm latest: 1.62.1; `-ct-svelte` stopped at 1.58.2; `-ct-solid` is deprecated). Main-branch docs say they are removed — "stay on Playwright 1.62 until you have migrated". New work: use the model below. See "Legacy CT (≤1.62)" at the end.

## When to Use CT vs E2E

| Use CT when… | Use E2E when… |
|---|---|
| Testing a component in isolation (props, states, events) | Testing user flows across pages/routes |
| Multiple visual variants / states | Integration with backend / auth |
| Accessibility of a single component | Full-stack data flows |
| Faster feedback on UI logic | Confirming the whole app works together |

## CT vs Vitest/JSDOM (which skill to use)

See also `vitest-unit-testing`. Pick by **rendering environment**, not by the phrase "component test":
- **`vitest-unit-testing`** — JSDOM (simulated DOM), fastest, best for logic, hooks, and components that don't depend on real layout/paint. Default for unit + most component tests.
- **`playwright-component-testing`** (this skill) — real browser engine. Use when the test needs real CSS/layout, true browser events, visual states, or Playwright locators/traces.

## The Model — Three Concepts

- **Story** — a tiny wrapper component that embeds the component under test in **one** scenario: hard-coded props, mock data, providers, recorded callbacks. Lives next to the component in `*.story.tsx` (or `.ts/.jsx/.js/.vue`); **each named export is one story**.
- **Gallery** — one page served by your dev server (under `playwright/gallery/`) exposing `window.mount({ story, props })` and `window.unmount()`, rendering into `#root`. Framework-specific, **owned by you**.
- **`mount` fixture** — navigates to the gallery (`baseURL`), calls `window.mount()` with the story id + props, returns a **Locator** for the gallery root.

Everything the component needs is set up **inside the story** (runs in the browser). Everything the test asserts is observable **through the page** (DOM, URL, network).

## Setup

### 1. Get a gallery

The fastest route, per the official docs: `npx playwright init-skills`, then ask your coding agent *"Set up component testing using the playwright-component-testing skill."* (Note: Playwright's installed skill has the **same name** as this local skill.) `init-skills` appears in main-branch docs; whether it ships in 1.63 is UNVERIFIED — check `npx playwright --help`.

Gallery contract if you write it by hand (a few dozen lines):
- Single page under `playwright/gallery/`, served by **your** dev server (Vite apps reuse the running dev server; other setups run a small standalone Vite server next to the app).
- Discovers `*.story.*` files; `window.mount({ story, props })` renders the story into `#root`; `window.unmount()` tears down. Unknown story / render error → rejects → the test's `mount()` throws.
- **Reuses the rendering root** across calls so `component.update(props)` reconciles instead of remounting (state preserved).
- Imports your global CSS like the app entry does; the body of `window.mount` is where app-wide setup (old `beforeMount`/`afterMount`) goes.

### 2. Configure Playwright (plain `@playwright/test`)

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  projects: [
    {
      name: 'components',
      testDir: './tests/components',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: 'http://localhost:5173/playwright/gallery/index.html', // mount() navigates here
        serviceWorkers: 'block',  // app SW must not shadow page.route() mocks
        reuseContext: true,       // reuse context per worker — big speedup for CT suites
      },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173/playwright/gallery/index.html',
    reuseExistingServer: !process.env.CI,
  },
});
```

Run: `npx playwright test --project=components` (add `--ui` for UI mode).

## Writing Stories and Tests

```tsx
// src/components/Button.story.tsx — one export per scenario
import { Button } from './Button';

export const Primary  = () => <Button title="Submit" />;
export const Disabled = () => <Button title="Submit" disabled />;
```

```typescript
// tests/components/button.spec.ts
import { test, expect } from '@playwright/test';

test('renders primary button', async ({ mount }) => {
  const component = await mount('components/Button/Primary');
  await expect(component.getByRole('button')).toHaveText('Submit');
});

test('disabled button is disabled', async ({ mount }) => {
  const component = await mount('components/Button/Disabled');
  await expect(component.getByRole('button')).toBeDisabled();
});
```

**Story ids** = path under `src/` without `.story.*` + export name (`components/Button/Primary`); any unique suffix also works (`mount('Button/Primary')`). Ids are strings → renaming a story breaks specs at **runtime**.

## Testing Patterns

### Callbacks / events → record state into a hidden input

No callback marshalling across Node.js/browser. The **story owns the state** and records the observable outcome; the test asserts with a retrying web-first assertion:

```tsx
// src/components/Button.story.tsx
import { useState } from 'react';
import { Button } from './Button';

export const CountsClicks = () => {
  const [clicks, setClicks] = useState(0);
  return <>
    <Button title="Submit" onClick={() => setClicks(c => c + 1)} />
    <form hidden><input data-testid="click-count" readOnly value={String(clicks)} /></form>
  </>;
};
```

```typescript
test('counts clicks', async ({ mount }) => {
  const component = await mount('components/Button/CountsClicks');
  await component.getByRole('button').click();
  await expect(component.getByTestId('click-count')).toHaveValue('1');
});
```

One `data-testid` input per observed value (`String(...)` scalars, `JSON.stringify(...)` payloads). Negative case: act, then assert the value did **not** change.

### Per-test props (typed)

```tsx
export const WithTitle = ({ title = 'Default' }: { title?: string }) => <Button title={title} />;
```

```typescript
import type { WithTitle } from '../../src/components/Button.story';
const component = await mount<typeof WithTitle>('Button/WithTitle', { title: 'Hello' });
```

Props must be plain serializable data — callbacks belong inside the story. (1.63: story ids can also be typed via the generated `Stories` registry.)

### Prop transitions without remount — `update()` / `unmount()`

```typescript
const component = await mount('components/Counter/Default', { value: 1 });
await expect(component.getByTestId('value')).toHaveText('1');
await component.update({ value: 2 });          // same root, state preserved
await expect(component.getByTestId('value')).toHaveText('2');
await component.unmount();
```

### Network mocking — plain `page.route()` before `mount()`

```typescript
test('renders the error state', async ({ page, mount }) => {
  await page.route('**/api/items', route => route.fulfill({ status: 500 }));
  const component = await mount('components/ItemList/Default');   // mount navigates
  await expect(component.getByRole('alert')).toContainText('Something went wrong');
});
```

MSW users can start `setupWorker` inside a story/decorator instead.

### Visual states

```typescript
await expect(await mount('Button/Primary')).toHaveScreenshot('primary.png');
await expect(await mount('Button/Disabled')).toHaveScreenshot('disabled.png');
```

Screenshot the returned root locator, not the page.

### Accessibility

```typescript
import AxeBuilder from '@axe-core/playwright';

test('button has no a11y violations', async ({ mount, page }) => {
  await mount('components/Button/Primary');
  const results = await new AxeBuilder({ page }).include('#root').analyze();
  expect(results.violations).toEqual([]);
});
```

### Debugging a story

Open the gallery URL in a browser and run `await window.mount({ story: 'components/Button/Primary' })` in DevTools — exactly what the fixture does. Drop the `hidden` attribute on the recording form while developing to watch state live.

## Anti-Patterns

```typescript
// ❌ Reaching into internals (instance, refs, state) — not supported
// ✓ Record effects into the DOM via the story, assert through the page

// ❌ One parameterized mega-story driven by many props
// ✓ One named export per scenario (Primary, Disabled, WithLongTitle) — the story file IS the spec

// ❌ Registering page.route() after mount() — mount navigates, the request already happened
// ✓ Route first, then mount

// ❌ page.waitForTimeout(1000)
// ✓ Web-first assertions: await expect(component.getByRole('row')).toHaveCount(5)
```

## Legacy CT (≤1.62) — `@playwright/experimental-ct-*`

Only for projects pinned to ≤1.62. Old style: JSX inline in the test (`mount(<Button onClick={spy} />)`), a separate `playwright-ct.config.ts` with `ctPort` / `ctViteConfig`, `playwright/index.tsx` with `beforeMount`/`afterMount`, an experimental `router` fixture.

Migration map (official):

| Experimental CT | Story gallery |
|---|---|
| `mount(<Button onClick={spy} />)` | Stateful story records the effect in a hidden input; assert with `toHaveValue()` |
| Plain data props | `mount(id, props)` |
| JSX children / slots | One story export per composition (Vue: `.story.vue` for slot-heavy cases) |
| `component.update(<Button count={2} />)` | `component.update({ count: 2 })` |
| `component.unmount()` | `component.unmount()` |
| `beforeMount` / `afterMount` | Body of the gallery's `window.mount` (global) or story decorators |
| `hooksConfig` | Props interpreted by the story: `mount('App/Routing', { route: '/dashboard' })` |
| `router` fixture | `page.route()` in the test, or MSW `setupWorker` in a story |
| `playwright/index.html` | Gallery's `index.html` + entry imports |
| `ctViteConfig`, `ctPort`, `ctTemplateDir` | Gone — your dev server; port lives in `webServer` / `baseURL` |
| `defineConfig` from the ct package | Plain `defineConfig` from `@playwright/test` |

Migrate incrementally while pinned to 1.62: add the gallery + `components` project next to the old CT project, port spec by spec, then remove the `@playwright/experimental-ct-*` dependency, `playwright/index.html`, `playwright/index.ts`, `playwright/.cache`, and upgrade.

## Sources
- https://github.com/microsoft/playwright/blob/main/docs/src/test-components-js.md — official component testing guide + migration table (read 2026-10-02)
- https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/release-notes-js.md — 1.62 (stories model), 1.63 (experimental packages no longer updated)
- npm registry: @playwright/experimental-ct-react / -vue latest 1.62.1, -svelte 1.58.2, -solid deprecated (checked 2026-10-02)
