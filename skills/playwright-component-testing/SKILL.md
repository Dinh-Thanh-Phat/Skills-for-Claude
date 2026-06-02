---
name: playwright-component-testing
description: Playwright experimental component testing — mount real UI components in a real browser without a full app server. Use when writing isolated component tests for React, Vue, Svelte, or Solid; testing component props, events, slots, accessibility, and UI states; or migrating from Vitest/JSDOM or Cypress Component Testing to Playwright CT. Triggers on: "component test playwright", "mount component", "@playwright/experimental-ct", "playwright CT", "test React component in browser", "playwright component", "CT setup".
---

# Playwright Component Testing (Experimental CT)

Mount a real component in Chromium/Firefox/WebKit — no full app, no dev server. Same Playwright locators, traces, and CI pipeline as your E2E suite.

## When to Use CT vs E2E

| Use CT when… | Use E2E when… |
|---|---|
| Testing a component in isolation (props, slots, events) | Testing user flows across pages/routes |
| Multiple visual variants / states | Integration with backend / auth |
| Accessibility of a single component | Full-stack data flows |
| Faster feedback on UI logic | Confirming the whole app works together |

## Setup

```bash
# For React
npm install --save-dev @playwright/experimental-ct-react vite @vitejs/plugin-react

# For Vue
npm install --save-dev @playwright/experimental-ct-vue vite @vitejs/plugin-vue

# For Svelte
npm install --save-dev @playwright/experimental-ct-svelte vite @sveltejs/vite-plugin-svelte
```

Create `playwright-ct.config.ts` (separate from your E2E config):

```typescript
import { defineConfig, devices } from '@playwright/experimental-ct-react';

export default defineConfig({
  testDir: './src',           // co-locate tests next to components
  testMatch: '**/*.ct.tsx',  // or *.ct.spec.tsx
  use: {
    ctPort: 3100,
    ctViteConfig: {
      // treat as a normal Vite project — aliases, env vars, plugins all work
      resolve: {
        alias: { '@': new URL('./src', import.meta.url).pathname },
      },
    },
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

Run CT:

```bash
npx playwright test --config playwright-ct.config.ts
npx playwright test --config playwright-ct.config.ts --ui   # UI mode
```

## Writing Tests — the `mount` Fixture

```typescript
// components/Button.ct.tsx
import { test, expect } from '@playwright/experimental-ct-react';
import Button from './Button';

test('renders with label', async ({ mount }) => {
  const component = await mount(<Button label="Save" />);

  await expect(component).toContainText('Save');
  await expect(component.getByRole('button')).toBeEnabled();
});

test('calls onClick when clicked', async ({ mount }) => {
  let clicked = false;
  const component = await mount(
    <Button label="Save" onClick={() => { clicked = true; }} />
  );

  await component.getByRole('button').click();
  expect(clicked).toBe(true);
});

test('disabled state', async ({ mount }) => {
  const component = await mount(<Button label="Save" disabled />);

  await expect(component.getByRole('button')).toBeDisabled();
});
```

## Provider Setup with `beforeMount`

Wrap all components in providers (theme, router, i18n, store) via `playwright/index.tsx`:

```typescript
// playwright/index.tsx  ← Playwright CT picks this up automatically
import { beforeMount, afterMount } from '@playwright/experimental-ct-react/hooks';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from './theme';

beforeMount(async ({ App }) => {
  return (
    <MemoryRouter>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </MemoryRouter>
  );
});
```

## Network Mocking — `router` Fixture

The experimental `router` fixture intercepts fetch/XHR inside the component — same API as `page.route()`:

```typescript
import { test, expect } from '@playwright/experimental-ct-react';
import ProductCard from './ProductCard';

test('shows product name from API', async ({ mount, router }) => {
  // intercept before mounting
  await router.route('/api/product/42', async route => {
    await route.fulfill({
      json: { id: 42, name: 'Widget Pro', price: 9.99 },
    });
  });

  const component = await mount(<ProductCard productId={42} />);

  await expect(component.getByTestId('product-name')).toHaveText('Widget Pro');
  await expect(component.getByTestId('product-price')).toHaveText('$9.99');
});

test('shows error state on API failure', async ({ mount, router }) => {
  await router.route('/api/product/42', route => route.fulfill({ status: 500 }));

  const component = await mount(<ProductCard productId={42} />);

  await expect(component.getByRole('alert')).toBeVisible();
});
```

## Re-Rendering and Updating Props

```typescript
test('updates when props change', async ({ mount }) => {
  const component = await mount(<Badge count={0} />);
  await expect(component).toContainText('0');

  await component.update(<Badge count={5} />);
  await expect(component).toContainText('5');
});
```

## Accessibility Testing in CT

```typescript
import AxeBuilder from '@axe-core/playwright';

test('button has no a11y violations', async ({ mount, page }) => {
  await mount(<Button label="Delete" variant="danger" />);
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

## Custom Fixtures for Repeated Setup

```typescript
// fixtures.ts
import { test as baseTest } from '@playwright/experimental-ct-react';

type Fixtures = { authedComponent: typeof baseTest['mount'] };

export const test = baseTest.extend<Fixtures>({
  authedComponent: async ({ mount }, use) => {
    // wrap every mount call in an AuthProvider
    const authedMount = (component: JSX.Element) =>
      mount(<AuthProvider user={testUser}>{component}</AuthProvider>);
    await use(authedMount as any);
  },
});
```

## Anti-Patterns

```typescript
// ❌ Don't test implementation details (internal state, refs)
expect(component._reactInternals.state.count).toBe(3);

// ✓ Test from the user's perspective
await expect(component.getByRole('status')).toHaveText('3 items');

// ❌ Don't mount the entire app for a component test — defeats the purpose
await mount(<App />);

// ✓ Mount only the component under test
await mount(<DataTable rows={mockRows} />);

// ❌ Don't use hardcoded waits
await page.waitForTimeout(1000);

// ✓ Await Playwright's auto-waiting locators
await expect(component.getByRole('row')).toHaveCount(5);
```

## CI Integration

```yaml
# .github/workflows/ct.yml
- name: Run Component Tests
  run: npx playwright test --config playwright-ct.config.ts
  # CT runs in Node — no emulator, no full server needed
  # Artifacts: traces, screenshots captured same as E2E
```

## Sources
- https://playwright.dev/docs/test-components — Official Playwright CT docs
- https://www.browserstack.com/guide/component-testing-react-playwright — BrowserStack 2026 guide
- https://getautonoma.com/blog/playwright-best-practices-2026 — Playwright best practices 2026
