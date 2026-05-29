---
name: visual-regression-testing
description: Playwright built-in visual/screenshot regression testing. Use when testing UI appearance, detecting unintended visual changes, comparing screenshots against baselines. Triggers on: "visual test", "screenshot test", "visual regression", "UI regression", "snapshot test", "toMatchSnapshot", "kiểm tra giao diện", "chụp màn hình so sánh".
triggers:
  - "visual test"
  - "screenshot test"
  - "visual regression"
  - "toMatchSnapshot"
  - "UI regression"
  - "snapshot test"
  - "baseline screenshot"
  - "kiểm tra giao diện"
scope:
  - qa
  - e2e
  - playwright
  - visual
---

# Visual Regression Testing Skill

You are a **Senior QA Engineer** using Playwright's built-in visual comparison to catch unintended UI changes before they reach production.

## Core Law

> **Visual regression tests are NOT a replacement for functional assertions.**
> They are a safety net for appearance. Both must coexist.

---

## What This Covers

Playwright compares screenshots pixel-by-pixel against stored baseline images. If the difference exceeds a threshold → test fails and shows a diff image.

**Use for:**
- Layout changes (spacing, alignment, overflow)
- Color/theme changes
- Component regressions after CSS refactor
- Critical UI pages that must look exactly right

**Do NOT use for:**
- Testing if a button works (use functional assertion)
- Testing dynamic content (mask or use functional assertion instead)
- Replacing `toHaveText`, `toBeVisible`, `toHaveCount`

---

## Setup

```typescript
// playwright.config.ts
export default defineConfig({
  expect: {
    toMatchSnapshot: {
      maxDiffPixelRatio: 0.02, // allow 2% pixel difference
    },
  },
  use: {
    viewport: { width: 1280, height: 720 }, // lock viewport
  },
});
```

---

## Basic Pattern

```typescript
test('VR-001: Login page looks correct', async ({ page }) => {
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  // Wait for a real signal that the page is interactive:
  await expect(page.getByRole('main')).toBeVisible();
  // And for fonts (visual stability depends on this):
  await page.evaluate(() => document.fonts.ready);

  await expect(page).toMatchSnapshot('login-page.png');
});

// ❌ Never use `waitUntil: 'networkidle'` here — hangs on SPAs / streaming /
//    polling apps and is unreliable as a stability signal.
```

### Element-level snapshot (preferred when possible)
```typescript
test('VR-002: Button states', async ({ page }) => {
  await page.goto('/components');

  const button = page.locator('[data-testid="primary-button"]');
  await expect(button).toMatchSnapshot('primary-button.png');
});
```

---

## Stability Checklist Before Taking Snapshots

### 1. Disable CSS animations
```typescript
// In beforeEach or test setup
await page.addStyleTag({
  content: `
    *, *::before, *::after {
      animation-duration: 0s !important;
      transition-duration: 0s !important;
    }
  `,
});
```

### 2. Mask dynamic content
```typescript
await expect(page).toMatchSnapshot('dashboard.png', {
  mask: [
    page.locator('[data-testid="current-time"]'),
    page.locator('[data-testid="live-counter"]'),
    page.locator('.user-avatar'), // user-specific images
  ],
});
```

### 3. Wait for stable state — NO networkidle, NO waitForTimeout
```typescript
await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
const chart = page.locator('[data-testid="chart"]');
await expect(chart).toBeVisible();

// Wait for the chart's render-complete signal — fonts loaded, image render done.
// Prefer a real signal over a fixed sleep:
await page.evaluate(() => document.fonts.ready);
await expect(chart).toHaveAttribute('data-rendered', 'true');  // if app exposes one
// or freeze time and let Playwright auto-retry the snapshot:
await page.clock.install();

await expect(page).toMatchSnapshot('dashboard.png');
```

If the chart has no real "ready" signal, ask the dev to expose one (e.g. `data-rendered`,
custom event). Do NOT fall back to `waitForTimeout(500)` — it is unreliable and the snapshot
will flake on slower machines.

---

## Baseline Management

### First run — creates baseline
```bash
npx playwright test --update-snapshots
```
Baseline files stored in: `tests/__snapshots__/`

### Reviewing changes
```bash
npx playwright show-report
# Opens HTML report with Expected / Actual / Diff view
```

### Updating baseline intentionally (after approved UI change)
```bash
# Update specific test
npx playwright test visual.spec.ts --update-snapshots

# Commit updated baseline
git add tests/__snapshots__/
git commit -m "chore: update visual baselines after [feature name] redesign"
```

### CI — never auto-update baselines in CI
```typescript
// playwright.config.ts — CI should only compare, never update
updateSnapshots: process.env.CI ? 'none' : 'missing',
```

---

## Threshold Configuration

```typescript
// Tight threshold — exact match required (icons, logos)
await expect(page.locator('.logo')).toMatchSnapshot('logo.png', {
  maxDiffPixels: 0,
});

// Loose threshold — allow minor anti-aliasing differences
await expect(page).toMatchSnapshot('full-page.png', {
  maxDiffPixelRatio: 0.05, // 5% difference OK
});

// Absolute pixel count (for small elements)
await expect(button).toMatchSnapshot('button.png', {
  maxDiffPixels: 100, // allow up to 100 pixels different
});
```

---

## Cross-Platform Gotcha

Screenshots differ between macOS, Linux, and Windows (pixel rounding, font rendering). Solutions:

**Option A: Run visual tests in Docker (recommended for CI)**
```bash
# Use same Docker image locally and in CI
docker run --rm -v $(pwd):/work mcr.microsoft.com/playwright:v1.44.0-jammy npx playwright test --project=chromium
```

**Option B: Store platform-specific baselines**
```
tests/__snapshots__/
  login-page-linux.png    # CI baseline
  login-page-darwin.png   # local Mac baseline
```

**Option C: Use maxDiffPixelRatio to absorb font rendering differences**
```typescript
maxDiffPixelRatio: 0.03  // 3% covers most cross-platform font differences
```

---

## Test Organization

```
tests/
  visual/
    login.visual.spec.ts
    dashboard.visual.spec.ts
    components.visual.spec.ts
  __snapshots__/
    login.visual.spec.ts-snapshots/
      login-page-chromium-linux.png  # auto-named with browser+OS
```

---

## When to Create vs Skip Visual Tests

| Situation | Do |
|-----------|-----|
| Page has exact layout requirement (marketing, login) | CREATE visual test |
| Component used across many pages | CREATE visual test for component |
| Page with lots of dynamic data | SKIP full-page, use element-level with masking |
| Admin/internal tool with frequent UI changes | SKIP or very loose threshold |
| New feature under active development | SKIP until feature stabilizes |

---

## Checklist — Before Committing Visual Tests

- [ ] Viewport locked in config (not relying on default)
- [ ] CSS animations disabled for stable comparison
- [ ] Dynamic content masked (timestamps, avatars, live counters)
- [ ] `networkidle` or explicit element wait before snapshot
- [ ] Baseline generated on target platform (Linux/Docker for CI)
- [ ] `updateSnapshots: 'none'` in CI config
- [ ] Baseline files committed to git
- [ ] Test has functional assertion PLUS visual assertion (not just visual)

---

## Quick Fix Guide

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Test fails every run with tiny diff | Animation still running | Disable animations |
| Test fails in CI but passes locally | OS/font rendering diff | Use Docker or increase maxDiffPixelRatio |
| Test fails due to timestamp/counter | Dynamic content not masked | Add mask: [...] |
| Baseline outdated after intentional redesign | Need to update | Run with --update-snapshots, review diff, commit |
| Test always fails by 0px diff | Pixel rounding | Set maxDiffPixels: 2 |

---

## Sources
- Playwright visual comparisons: playwright.dev/docs/test-snapshots
- Visual testing guide: testdino.com/blog/playwright-visual-testing
- Cross-platform stability: arbisoft.com/blogs/playwright-visual-testing
