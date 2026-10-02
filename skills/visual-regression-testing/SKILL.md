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
    // Page/locator screenshots use toHaveScreenshot. (toMatchSnapshot is ONLY for
    // Buffer/string values — expect(page).toMatchSnapshot(...) throws.)
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.02, // allow 2% pixel difference
      // animations: 'disabled' is already the default for toHaveScreenshot
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

  await expect(page).toHaveScreenshot('login-page.png');
  // Playwright 1.62+: a `.webp` name stores a lossless WebP baseline (smaller repo):
  // await expect(page).toHaveScreenshot('login-page.webp');
});

// ❌ Never use `waitUntil: 'networkidle'` here — hangs on SPAs / streaming /
//    polling apps and is unreliable as a stability signal.
```

### Element-level snapshot (preferred when possible)
```typescript
test('VR-002: Button states', async ({ page }) => {
  await page.goto('/components');

  const button = page.locator('[data-testid="primary-button"]');
  await expect(button).toHaveScreenshot('primary-button.png');
});
```

---

## Stability Checklist Before Taking Snapshots

### 1. Disable CSS animations
`toHaveScreenshot` already defaults to `animations: 'disabled'` (finite animations fast-forwarded,
infinite ones reset). Only inject CSS for edge cases it misses (e.g. JS-driven transitions):
```typescript
// In beforeEach or test setup — optional, edge cases only
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
await expect(page).toHaveScreenshot('dashboard.png', {
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

// toHaveScreenshot itself retries until two consecutive screenshots match (stability wait).
// If you need fixed time (clocks/relative dates), call page.clock.install() BEFORE page.goto()
// — installing after load does nothing for already-scheduled timers.
await expect(page).toHaveScreenshot('dashboard.png');
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
Baseline files stored by default next to the spec in `<spec-file>-snapshots/`
(e.g. `tests/visual/login.visual.spec.ts-snapshots/login-page-chromium-linux.png`).
To use a central folder, set `snapshotPathTemplate` in config, e.g.
`snapshotPathTemplate: '{testDir}/__snapshots__/{testFilePath}/{arg}{ext}'`.

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
git add tests/**/*-snapshots/      # or your snapshotPathTemplate folder
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

## Beyond Native Playwright: Visual Testing SaaS Tools (2026)

Native Playwright visual comparison is free and sufficient for many projects. Move to a SaaS tool when you need AI-powered noise filtering, cross-browser cloud rendering, or component-library integration.

### Decision Guide

| Situation | Recommended tool |
|-----------|-----------------|
| Small team, free budget, simple pixel comparison | **Native Playwright** |
| Storybook component library as primary deliverable | **Chromatic** |
| BrowserStack user, CI-first, multi-browser rendering | **Percy** (5,000 free snapshots/mo) |
| Enterprise, multi-platform, Figma-to-test design system | **Applitools Eyes** |

### Tool Summaries

**Native Playwright** — zero cost, pixel-by-pixel comparison, runs in your own CI. Best features-to-price ratio for teams that don't need AI filtering. Platform rendering differences require Docker to stabilize.

**Chromatic** — built around Storybook; snapshots components automatically and highlights changes in a PR review workflow. No AI layer — pixel-diff based. Right choice only if you're Storybook-first.

**Percy (BrowserStack)** — DOM snapshot model: captures DOM → renders in real cloud browsers → compares. More deterministic than local screenshots. Free tier: 5,000 snapshots/month, unlimited users. Best for straightforward CI/CD pipelines.

**Applitools Eyes** — AI visual engine (not pixel comparison): understands layout vs. content changes, supports Strict / Layout / Content / Dynamic modes, handles cross-browser font rendering without false positives. Genuine 2026 differentiator: Figma plugin (Eyes 10.22, Jan 2026) lets you compare designs directly against screenshots — no equivalent in Percy or Chromatic. Most expensive; justified for large design systems with frequent multi-browser coverage requirements.

### Percy Integration (Playwright)

```typescript
// Install: npm install --save-dev @percy/playwright @percy/cli
// Set env: PERCY_TOKEN=<project_token>

import { percySnapshot } from '@percy/playwright';

test('visual: dashboard', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page.getByRole('main')).toBeVisible();
  await percySnapshot(page, 'Dashboard - default state');
});
```

```bash
# Run via Percy CLI (wraps your test command)
npx percy exec -- npx playwright test visual/
```

Percy renders in its cloud and posts a PR comment with visual diffs — no local baseline management.

---

## Sources
- [Playwright visual comparisons — playwright.dev](https://playwright.dev/docs/test-snapshots)
- [Visual testing guide — testdino.com](https://testdino.com/blog/playwright-visual-testing)
- [Cross-platform stability — arbisoft.com](https://arbisoft.com/blogs/playwright-visual-testing)
- [Visual Regression Testing Tools 2026 — Bug0](https://bug0.com/knowledge-base/visual-regression-testing-tools)
- [Chromatic vs Percy vs Applitools 2026 — PkgPulse](https://www.pkgpulse.com/guides/chromatic-vs-percy-vs-applitools-visual-regression-2026)
- [Applitools vs Percy Comparison 2026 — Delta-QA](https://delta-qa.com/en/blog/applitools-vs-percy-comparison-2026/)
