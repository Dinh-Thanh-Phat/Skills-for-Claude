---
name: accessibility-testing
description: Playwright + axe-core accessibility (a11y) testing against WCAG standards. Use when adding accessibility tests, checking WCAG compliance, testing screen reader compatibility, or auditing a11y regressions. Triggers on: "accessibility test", "a11y test", "axe-core", "WCAG", "screen reader", "kiểm tra accessibility", "kiểm tra trợ năng".
triggers:
  - "accessibility test"
  - "a11y test"
  - "axe-core"
  - "WCAG"
  - "screen reader"
  - "aria"
  - "kiểm tra accessibility"
  - "kiểm tra trợ năng"
  - "tab navigation"
scope:
  - qa
  - e2e
  - playwright
  - accessibility
---

# Accessibility Testing Skill

You are a **Senior QA Engineer** implementing automated accessibility checks to prevent WCAG violations from shipping undetected.

## Core Law

> **Automated a11y tools catch ~57% of real WCAG violations** (Deque Systems study, March 2021 — 2,000+ audits / ~300k issues; higher than the commonly cited 20-40%).
> Always combine automated scans with manual keyboard and screen reader testing.
> Automated = fast regression net. Manual = thorough audit.

---

## Setup

```bash
npm install --save-dev @axe-core/playwright
```

```typescript
// tests/accessibility/a11y.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
```

---

## Standalone live-site audit (no test harness, no app routes)

When you need to audit a **live URL** (or a list of routes) ad-hoc — not a CI test suite — run a
single Node script that loops the routes, injects axe, and prints violations. This matches an
exploratory QA pass where you don't have the app's test setup, just the deployed site. axe-core
runs in-page, so it works against any URL.

```js
// a11y-audit.mjs — node a11y-audit.mjs   (needs: npm i -D @playwright/test @axe-core/playwright)
import { chromium } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'fs';

const BASE = process.argv[2] || 'https://example.com';
const ROUTES = ['/', '/about-us', '/contact-us'];        // edit per site (or crawl links first)
const browser = await chromium.launch();
const page = await (await browser.newContext()).newPage();
const out = [];

for (const r of ROUTES) {
  await page.goto(BASE + r, { waitUntil: 'domcontentloaded', timeout: 35000 });
  await page.waitForTimeout(1200);
  const res = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  const blockers = res.violations.filter(v => v.impact === 'critical' || v.impact === 'serious');
  out.push({ route: r,
    total: res.violations.length, critical: blockers.length,
    top: res.violations.slice(0, 8).map(v => ({ id: v.id, impact: v.impact,
      nodes: v.nodes.length, sample: v.nodes[0]?.target?.join(' ') })) });
  console.log(`${r}: ${res.violations.length} violations (${blockers.length} critical/serious)`);
}
await browser.close();
fs.writeFileSync('a11y-audit.json', JSON.stringify(out, null, 2));
```

Use this for a quick site-wide a11y read; for a permanent regression net, graduate the findings
into the test-suite pattern below. Keyboard/focus/contrast-over-image still need the manual
supplements (see end of file) — axe catches ~57%, not all. Pair engine coverage with
[[cross-browser-webkit-testing]] and performance with [[web-vitals-ux]] for a full UX-quality sweep.

## Basic Pattern: Navigate → Scan → Assert

```typescript
test('A11Y-001: Login page has no critical violations', async ({ page }) => {
  await page.goto('/login');
  // Wait for a real ready signal — NOT networkidle (hangs on SPAs/polling, unreliable)
  await expect(page.getByRole('main')).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
```

---

## WCAG Tag Reference

| Tag | Standard | What it covers |
|-----|---------|----------------|
| `wcag2a` | WCAG 2.0 Level A | Minimum compliance (must have) |
| `wcag2aa` | WCAG 2.0 Level AA | Standard compliance (legal requirement in many regions) |
| `wcag21a` | WCAG 2.1 Level A | Mobile + cognitive |
| `wcag21aa` | WCAG 2.1 Level AA | Mobile + cognitive standard |
| `wcag22aa` | WCAG 2.2 Level AA | Latest standard (2023) |
| `best-practice` | axe best practices | Beyond WCAG |

**Recommended minimum for new projects:** `['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']`
(WCAG 2.2 AA is the current W3C Recommendation and the compliance target.)

**WCAG 3.0 status (2026-10):** still a W3C **Working Draft** (latest WD 2026-09-10; Candidate
Recommendation expected ~2027, final no earlier than 2028). It is NOT a compliance target — don't
tag tests or bugs against WCAG 3 requirements.

**axe-core version note:** current `axe-core` / `@axe-core/playwright` = **4.13.0**. Minor axe
upgrades add/deprecate rules (e.g. 4.12 added `aria-tab-name`, deprecated
`landmark-complementary-is-top-level`), so violation counts and rule IDs can shift after an upgrade —
pin the version and re-baseline any `exclude`/known-issue lists when you bump it.
Source: https://github.com/dequelabs/axe-core/releases

---

## Violation Severity Levels

| Severity | Action |
|----------|--------|
| `critical` | Block CI — fix before merge |
| `serious` | Block CI — fix before merge |
| `moderate` | Warn — fix within sprint |
| `minor` | Log — fix when time allows |

```typescript
// Fail on critical/serious only (pragmatic for legacy codebases)
const results = await new AxeBuilder({ page })
  .withTags(['wcag2a', 'wcag2aa'])
  .analyze();

const blocker = results.violations.filter(
  v => v.impact === 'critical' || v.impact === 'serious'
);

expect(blocker).toEqual([]);
```

---

## Useful Patterns

### Exclude known unfixable issues (temporary)
```typescript
const results = await new AxeBuilder({ page })
  .withTags(['wcag2a', 'wcag2aa'])
  .exclude('#legacy-widget')     // known third-party issue
  .exclude('.charts-container')  // charting library known gap
  .analyze();
```

### Scan only specific section
```typescript
const results = await new AxeBuilder({ page })
  .include('[data-testid="main-form"]') // only scan the form
  .withTags(['wcag2aa'])
  .analyze();
```

### Combine with functional test
```typescript
test('FORM-001: Contact form — functional + a11y', async ({ page }) => {
  await page.goto('/contact');

  // Functional assertion
  await expect(page.locator('h1')).toHaveText('Contact Us');

  // A11y scan for the form only
  const results = await new AxeBuilder({ page })
    .include('form')
    .withTags(['wcag2aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
```

---

## Readable Violation Reporting

```typescript
// Helper to print clear violation info on failure
function formatViolations(violations: any[]) {
  return violations.map(v => ({
    id: v.id,
    impact: v.impact,
    description: v.description,
    nodes: v.nodes.map((n: any) => n.target).join(', '),
    helpUrl: v.helpUrl,
  }));
}

test('A11Y-002: Dashboard', async ({ page }) => {
  await page.goto('/dashboard');
  const results = await new AxeBuilder({ page }).withTags(['wcag2aa']).analyze();

  expect(
    formatViolations(results.violations),
    `Found ${results.violations.length} violations`
  ).toEqual([]);
});
```

---

## Keyboard Navigation Testing (Manual supplement)

```typescript
test('A11Y-003: Form navigable by keyboard only', async ({ page }) => {
  await page.goto('/login');

  // Start focus at page top
  await page.keyboard.press('Tab');
  await expect(page.locator(':focus')).toHaveAttribute('name', 'email');

  await page.keyboard.press('Tab');
  await expect(page.locator(':focus')).toHaveAttribute('name', 'password');

  await page.keyboard.press('Tab');
  await expect(page.locator(':focus')).toHaveAttribute('type', 'submit');

  // Submit via keyboard
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/\/dashboard/);
});
```

---

## Focus Management After Dynamic Actions

```typescript
test('A11Y-004: Modal focus trap', async ({ page }) => {
  await page.goto('/users');
  await page.click('[data-testid="add-user-btn"]');

  // Focus should move to modal
  await expect(page.locator('[role="dialog"]')).toBeVisible();
  await expect(page.locator('[role="dialog"] :focus')).toBeVisible();

  // Escape should close and return focus to trigger
  await page.keyboard.press('Escape');
  await expect(page.locator('[data-testid="add-user-btn"]')).toBeFocused();
});
```

---

## Common Violations and Fixes

| Violation | axe Rule | Fix |
|-----------|---------|-----|
| Image no alt text | `image-alt` | `<img alt="description">` |
| Form label missing | `label` | `<label for="id">` or `aria-label` |
| Low color contrast | `color-contrast` | Fix CSS color ratio ≥ 4.5:1 |
| Button no accessible name | `button-name` | Add text content or `aria-label` |
| Heading level skipped | `heading-order` | Use h1→h2→h3 sequentially |
| Link no discernible text | `link-name` | Add aria-label or text content |
| Interactive element not focusable | `tabindex` | Remove `tabindex="-1"` or add keyboard handler |

---

## CI Integration

```typescript
// playwright.config.ts — add a11y project
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  {
    name: 'a11y',
    testMatch: '**/accessibility/*.spec.ts',
    use: { ...devices['Desktop Chrome'] },
  },
]
```

```bash
# Run only a11y tests in CI
npx playwright test --project=a11y
```

---

## What Automated Tests CANNOT Catch (Manual required)

- **Screen reader UX**: Does content make sense when read aloud?
- **Focus order logic**: Is tab order meaningful, not just present?
- **Color contrast for text over images**: axe can't evaluate dynamic backgrounds
- **Cognitive accessibility**: Is the UI understandable for users with cognitive disabilities?
- **Touch target size on mobile**: Real device testing needed (also test via `boundingBox()` ≥ 44×44)
- **ARIA live regions**: Do they announce correctly to screen readers?
- **`prefers-reduced-motion`**: Animations should disable — test by setting `reducedMotion: 'reduce'`
- **`prefers-contrast`**: High-contrast mode — test by setting `forcedColors: 'active'` in context
- **RTL / i18n**: Bidi text, mirrored layout — switch to `ar` or `he` locale and re-scan
- **Skip-links / landmark regions**: Verify `<main>`, `<nav>`, `<aside>` exist and skip-link points to `#main`

```typescript
// Reduced motion + high contrast scan
const ctx = await browser.newContext({
  reducedMotion: 'reduce',
  forcedColors: 'active',
});
const page = await ctx.newPage();
await page.goto('/');
const results = await new AxeBuilder({ page }).withTags(['wcag2aa']).analyze();
```

### Native `prefers-contrast` emulation (distinct from `forcedColors`)

`forcedColors: 'active'` (above) emulates OS-level forced-colors mode (Windows High Contrast). Playwright
separately supports the CSS `prefers-contrast` media feature directly via `page.emulateMedia()` /
`browser.newContext({ contrast })` — use this to test a site's own "more contrast" theme toggle (values:
`'no-preference'` | `'more'`), which is a different code path than forced-colors remapping:

```typescript
// Test the app's own high-contrast theme (not OS forced-colors)
await page.emulateMedia({ contrast: 'more' });
await page.goto('/settings');
const results = await new AxeBuilder({ page }).withTags(['wcag2aa']).analyze();
expect(results.violations).toEqual([]);
```

### `toHaveAccessibleErrorMessage()` — form error assertions

Playwright's accessible-name/description matcher family now includes an assertion for `aria-errormessage`,
closing a gap where form validation errors were only checkable via brittle text-content locators:

```typescript
test('A11Y-005: Invalid email shows accessible error', async ({ page }) => {
  await page.goto('/signup');
  await page.locator('#email').fill('not-an-email');
  await page.locator('#email').blur();

  // Asserts the element pointed to by aria-errormessage, not just visible text
  await expect(page.locator('#email')).toHaveAccessibleErrorMessage('Enter a valid email address');
});
```

### Structural a11y regression — `toMatchAriaSnapshot` / `ariaSnapshotJSON`

axe finds rule violations; it does NOT notice that a heading, landmark, label or role silently
changed. Lock the accessibility tree of critical regions with an aria snapshot (1.49+; works on a
whole `page` since 1.60):

```typescript
test('A11Y-006: Checkout form accessible structure unchanged', async ({ page }) => {
  await page.goto('/checkout');
  await expect(page.getByRole('main')).toMatchAriaSnapshot(`
    - heading "Checkout" [level=1]
    - textbox "Email"
    - textbox "Card number"
    - button "Pay now"
  `);
});

// 1.63+: JSON form for programmatic checks (e.g. every textbox has a name)
const tree = await page.getByRole('main').ariaSnapshotJSON();
```
Store larger snapshots in separate YAML files (supported since 1.50) and update them with
`--update-snapshots` after an intended change. 1.63 also adds standalone `reducedMotion`,
`forcedColors` and `contrast` test options (`test.use({ forcedColors: 'active' })`).

**Rule:** Run automated scan every PR. Run manual screen reader test every major feature release.

---

## Checklist — A11Y Test Review

- [ ] Every page/feature has at least one a11y scan test
- [ ] Scan includes minimum `wcag2a` + `wcag2aa` tags
- [ ] Critical/serious violations block CI
- [ ] Exclusions documented with `// TODO: fix by [date] - reason`
- [ ] Keyboard navigation tested for interactive flows
- [ ] Focus management tested for dialogs/drawers/toasts
- [ ] Manual screen reader test planned for next major release

---

## Sources
- Playwright accessibility testing: https://playwright.dev/docs/accessibility-testing
- axe-core WCAG guide: https://www.qamadness.com/a-you-oriented-guide-to-axe-core-playwright-accessibility-testing/
- Playwright a11y CI guide: https://testdino.com/blog/playwright-accessibility
- Deque Systems 57% coverage study (March 2021): https://www.deque.com/blog/automated-testing-study-identifies-57-percent-of-digital-accessibility-issues/
- axe-core releases: https://github.com/dequelabs/axe-core/releases
- Playwright release notes (aria snapshots 1.49/1.60/1.63): https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/release-notes-js.md
- Playwright release notes (native `contrast` emulateMedia option, `toHaveAccessibleErrorMessage()`): https://playwright.dev/docs/release-notes
