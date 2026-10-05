---
name: responsive-viewport-testing
description: Patterns for responsive and viewport testing in Playwright — mobile emulation, breakpoint testing, hamburger menus, touch targets, device descriptors. Use when writing tests for mobile layouts, responsive design breakpoints, or touch interactions. Triggers on: "mobile test", "responsive", "viewport", "hamburger menu", "mobile layout", "breakpoint", "setViewportSize", "mobile emulation", "touch", "tablet", "device".
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
    { name: 'tablet', use: { ...devices['iPad Pro 11'] } },
    // ⚠️ devices['iPad Pro'] does NOT exist — spreading undefined silently gives a desktop project.
    // Valid names live in Playwright's deviceDescriptorsSource.json ('iPad Pro 11', 'iPad Mini', 'iPad (gen 11)'...)
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
  await page.touchscreen.tap(200, 400);
  // Note: Playwright has no built-in swipe — touchscreen only taps. For a swipe, dispatch
  // TouchEvents (touchstart/touchmove/touchend) via locator.dispatchEvent or page.evaluate.
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
// WCAG 2.2 SC 2.5.8 Target Size (Minimum) — Level AA: 24×24 CSS px (legal/compliance floor)
// WCAG SC 2.5.5 Target Size (Enhanced)   — Level AAA: 44×44 CSS px (Apple HIG also 44pt; Material 48dp)
const MIN = 24;            // use 44 if the project targets AAA / platform guidelines
const buttons = page.getByRole('button');
const count = await buttons.count();
for (let i = 0; i < count; i++) {
  const box = await buttons.nth(i).boundingBox();
  if (box) {
    expect(box.width, `Button ${i} too narrow`).toBeGreaterThanOrEqual(MIN);
    expect(box.height, `Button ${i} too short`).toBeGreaterThanOrEqual(MIN);
  }
}
// (2.5.8 also passes undersized targets with enough spacing — a 24px circle must not overlap a neighbor)
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
- [ ] Touch targets: `boundingBox()` ≥ 24×24px (WCAG 2.2 AA, 2.5.8); ≥ 44×44px if targeting AAA (2.5.5) / Apple HIG
- [ ] Fresh navigation before each viewport test (no state carryover)

