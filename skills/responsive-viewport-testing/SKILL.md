---
name: responsive-viewport-testing
description: >-
  Patterns for responsive and viewport testing in Playwright — mobile emulation, breakpoint
  testing, hamburger menus, touch targets, device descriptors. Use when writing tests for mobile
  layouts, responsive design breakpoints, or touch interactions. Triggers on: "mobile test",
  "responsive", "viewport", "hamburger menu", "mobile layout", "breakpoint", "setViewportSize",
  "mobile emulation", "touch", "tablet", "device".
triggers:
  - "mobile test"
  - "responsive"
  - "viewport"
  - "hamburger menu"
  - "breakpoint"
  - "setViewportSize"
  - "touch"
  - "tablet"
---

# Responsive / Viewport Testing

## Core Rule

`setViewportSize` alone ≠ mobile emulation. It only changes screen size — no touch, no mobile user agent, no deviceScaleFactor. Always use `devices[...]` for real mobile emulation.

## Pattern 1: Device Descriptors (Preferred)

```typescript
import { devices } from '@playwright/test';

// playwright.config.ts — separate project per device
export default defineConfig({
  projects: [
    { name: 'desktop', use: { viewport: { width: 1280, height: 720 } } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'] } },
    { name: 'tablet', use: { ...devices['iPad Pro'] } },
  ],
});

// devices['Pixel 7'] bundles: viewport + userAgent + hasTouch + isMobile + deviceScaleFactor
```

## Pattern 2: Per-Test Viewport Override (Breakpoint Testing)

For boundary tests without creating separate projects:

```typescript
test('hamburger visible below 768px', async ({ page }) => {
  await page.setViewportSize({ width: 767, height: 900 });
  await page.goto('/');
  await expect(page.getByTestId('hamburger-btn')).toBeVisible();
  await expect(page.getByRole('navigation')).toBeHidden();

  // Open nav via hamburger
  await page.getByTestId('hamburger-btn').click();
  await expect(page.getByRole('navigation')).toBeVisible();
});

test('nav visible at 768px+', async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 900 });
  await page.goto('/');
  await expect(page.getByRole('navigation')).toBeVisible();
  await expect(page.getByTestId('hamburger-btn')).toBeHidden();
});
```

## Pattern 3: Touch Interaction (Custom Context)

`setViewportSize` has no touch. Create full context for touch interactions:

```typescript
test('swipe gesture works on mobile', async ({ browser }) => {
  // ✅ Full mobile context — viewport + touch + mobile UA
  const ctx = await browser.newContext({
    viewport: { width: 375, height: 812 },
    hasTouch: true,
    isMobile: true,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)...',
  });
  const page = await ctx.newPage();
  await page.goto('/carousel');
  await page.locator('.carousel').tap();
  // swipe
  await page.touchscreen.tap(200, 400);
});
```

## Pattern 4: Breakpoint Matrix Testing

```typescript
const BREAKPOINTS = [
  { name: 'mobile', width: 375, expectHamburger: true },
  { name: 'mobile-max', width: 767, expectHamburger: true },
  { name: 'tablet-min', width: 768, expectHamburger: false },
  { name: 'desktop', width: 1280, expectHamburger: false },
];

for (const bp of BREAKPOINTS) {
  test(`nav layout at ${bp.width}px (${bp.name})`, async ({ page }) => {
    await page.setViewportSize({ width: bp.width, height: 900 });
    await page.goto('/');

    if (bp.expectHamburger) {
      await expect(page.getByTestId('hamburger-btn')).toBeVisible();
    } else {
      await expect(page.getByRole('navigation')).toBeVisible();
    }
  });
}
```

## Pattern 5: Touch Target Size (Accessibility)

```typescript
// WCAG 2.5.5 — minimum 44×44px touch targets
const buttons = page.getByRole('button');
const count = await buttons.count();
for (let i = 0; i < count; i++) {
  const box = await buttons.nth(i).boundingBox();
  if (box) {
    expect(box.width, `Button ${i} too narrow`).toBeGreaterThanOrEqual(44);
    expect(box.height, `Button ${i} too short`).toBeGreaterThanOrEqual(44);
  }
}
```

## Pattern 6: Dark Mode + Viewport Combined

```typescript
test('mobile dark mode layout', async ({ browser }) => {
  const ctx = await browser.newContext({
    ...devices['Pixel 7'],
    colorScheme: 'dark',
  });
  const page = await ctx.newPage();
  await page.goto('/');
  await expect(page.locator('body')).toHaveCSS('background-color', 'rgb(18, 18, 18)');
});
```

## Gotchas

| Gotcha | Fix |
|---|---|
| `setViewportSize` — no touch events | Use `browser.newContext({ hasTouch: true, isMobile: true })` |
| `devices['Pixel 7']` vs custom viewport | `devices` bundles all mobile props; custom only sets size |
| Hamburger state persists across tests | Always `page.goto()` to reset state; don't share context |
| Sticky elements need scroll to trigger | `page.evaluate(() => window.scrollTo(0, 500))` then assert |
| CSS transitions catch mid-animation state | `toBeVisible()` retries through transition automatically |
| `deviceScaleFactor: 2` doubles screenshot size | Normalize in visual regression: set consistent `deviceScaleFactor` |

## Checklist

- [ ] Mobile emulation: using `devices['Pixel 7']` not raw `setViewportSize` alone
- [ ] Touch interactions: `hasTouch: true` + `isMobile: true` in context
- [ ] Breakpoints: testing just below AND just above CSS breakpoint values
- [ ] Hamburger: tested open AND closed states
- [ ] Touch targets: `boundingBox()` ≥ 44×44px for interactive elements
- [ ] Fresh navigation before each viewport test (no state carryover)

