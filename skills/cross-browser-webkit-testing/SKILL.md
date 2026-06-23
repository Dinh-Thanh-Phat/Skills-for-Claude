---
name: cross-browser-webkit-testing
description: >-
  Catch rendering/behavior bugs that appear in ONE browser engine but not others — especially
  Safari/WebKit-only CSS breakage (text clipping, fl-/grid gap, backdrop-filter, :has(), sticky,
  100vh, date inputs, -webkit- prefixes) that Chromium-only testing silently misses. Use whenever
  you test a website's layout/UX, when a bug "only happens on Safari/iPhone", when you ran tests in
  Chromium only and need engine coverage, or the user says "cross-browser", "test on Safari",
  "WebKit", "Firefox", "iPhone Safari", "trình duyệt khác", "lỗi trên Safari", "test đa trình duyệt".
  Playwright bundles WebKit (the real Safari engine) and Firefox — no Mac/real device needed. Pair
  with responsive-viewport-testing (size) and ux-heuristic-evaluation (a clipped heading is a UX bug
  you must still confirm by screenshot, per evidence discipline).
triggers:
  - "cross-browser"
  - "cross browser"
  - "test on Safari"
  - "Safari bug"
  - "WebKit"
  - "Firefox"
  - "iPhone Safari"
  - "only on Safari"
  - "lỗi trên Safari"
  - "test đa trình duyệt"
  - "trình duyệt khác"
scope:
  - qa
  - e2e
  - playwright
  - responsive
  - cross-browser
---

# Cross-Browser / WebKit Testing

## Core Law

> **Chromium-only testing is half a test.** Playwright ships three real engines — **Chromium**
> (Chrome/Edge), **WebKit** (the actual Safari engine, on Win/Linux too), and **Firefox** (Gecko).
> A layout that's perfect in Chromium can clip, overflow, or mis-wrap in WebKit because the engines
> differ on flex/grid `gap`, font metrics, `backdrop-filter`, `:has()`, `100vh`, `position:sticky`,
> and `-webkit-` prefixes. If you only ran Chromium, you have NOT tested Safari — and most of a
> Vietnamese/global audience's mobile traffic is iOS Safari.

**You do NOT need a Mac or a real iPhone.** `npm i -D @playwright/test && npx playwright install webkit`
gives you the WebKit engine that powers Safari. (Caveat in §Limits: WebKit-on-Playwright ≈ Safari,
not byte-identical — font rendering and a few media features differ.)

## When this fires vs. its neighbors
- **This skill** = same viewport, *different engine* → engine-specific bugs.
- [[responsive-viewport-testing]] = same engine, *different size* → breakpoint bugs.
- Run BOTH for a real layout audit: a bug can be size-only, engine-only, or size×engine.
- A finding here (e.g. "heading clipped in WebKit") is still subject to **evidence discipline**
  ([[ux-heuristic-evaluation]], [[feedback_visual-bug-native-screenshot-only]]): a measured overflow
  is a hypothesis — confirm it in a native-res screenshot of THAT engine before reporting.

---

## The fastest high-value check: multi-engine screenshot + metric diff

Most engine bugs are visual. The cheapest detector is: load the same URL in all three engines,
measure overflow/clipping, screenshot each, and **diff the numbers + look at the images**. This is a
standalone Node script — no test harness, no app routes needed. Run it from a dir with
`@playwright/test` installed.

```js
// cross-browser-diff.mjs — node cross-browser-diff.mjs
import { chromium, webkit, firefox } from '@playwright/test';
import fs from 'fs';

const URL = process.argv[2] || 'https://example.com/';
const OUT = './xbrowser-shots'; fs.mkdirSync(OUT, { recursive: true });
const engines = { chromium, webkit, firefox };
const report = {};

for (const [name, type] of Object.entries(engines)) {
  const browser = await type.launch();
  // emulate an iPhone-ish viewport in EVERY engine so differences are engine, not size
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 35000 });
  await page.waitForTimeout(1800);
  const m = await page.evaluate(() => {
    const de = document.documentElement, vw = de.clientWidth;
    // Text CLIPPING is sneaky and a single heuristic MISSES it (verified live: a hero <h1> was
    // visibly cut mid-word in all 3 engines while scrollWidth===clientWidth and docOverflow===0).
    // So flag TWO independent signals, and STILL treat screenshots as the real verdict:
    const clipped = [];
    for (const el of document.querySelectorAll('h1,h2,h3,p,span,a,button,li')) {
      const cs = getComputedStyle(el), r = el.getBoundingClientRect();
      if (r.width < 40 || !el.innerText) continue;
      const overflowsBox = (cs.overflow==='hidden'||cs.overflowX==='hidden'||cs.textOverflow==='clip')
        && el.scrollWidth - el.clientWidth > 2;            // signal A: cut by its own overflow
      const pastViewport = r.right > vw + 2 && r.left < vw; // signal B: text runs off-screen right
      const nowrapWide = cs.whiteSpace.includes('nowrap') && el.scrollWidth > vw; // signal C
      if (overflowsBox || pastViewport || nowrapWide)
        clipped.push({ tag: el.tagName, right: Math.round(r.right), vw,
          why: overflowsBox?'overflow':pastViewport?'pastViewport':'nowrap',
          txt: (el.innerText||'').slice(0,35).replace(/\s+/g,' ') });
    }
    return { docOverflow: de.scrollWidth - de.clientWidth, clippedCount: clipped.length,
             clipped: clipped.slice(0, 8) };
  });
  await page.screenshot({ path: `${OUT}/${name}-fold.png` });
  report[name] = m;
  await browser.close();
}
fs.writeFileSync(`${OUT}/diff.json`, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
// THEN OPEN THE 3 *-fold.png AND LOOK — this is non-negotiable. The metrics above are a triage
// aid, not a verdict: clipping can render visibly while every numeric probe reads 0 (text painted
// past the box without changing scrollWidth). A number that DIFFERS across engines = a strong
// engine-specific lead; identical numbers do NOT mean "no bug" — confirm in the images.
```

Read it as: **docOverflow or clippedCount that differs across engines = engine-specific bug.**
Same numbers everywhere = the bug (if any) is not engine-specific — go to responsive-viewport-testing.

---

## In a Playwright test suite: one project per engine

```ts
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'webkit',   use: { ...devices['Desktop Safari'] } },   // Safari engine
    { name: 'firefox',  use: { ...devices['Desktop Firefox'] } },
    { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },   // WebKit + touch + iOS UA
  ],
});
// npx playwright test --project=webkit   (run one engine)
// npx playwright test                    (all engines)
```

`devices['iPhone 13']`/`['iPhone 15']` use the **WebKit** engine → this is your closest
no-device proxy for real iPhone Safari. `devices['Pixel 7']` uses Chromium (Android Chrome).

---

## WebKit/Safari-specific bug catalog — what to look for first

These are the failures that pass in Chromium and break in Safari. Check them explicitly.

| Symptom | Likely cause in WebKit/Safari | What to check |
|---|---|---|
| **Heading/text cut off mid-word, no scrollbar** | font metrics differ → text is wider in WebKit; container has `overflow:hidden`/`nowrap` | the `clippedCount` probe above; give text room to wrap |
| Gaps missing between flex items | older WebKit ignored `gap` on flexbox | verify `gap` renders; fallback margins |
| Frosted-glass panel looks solid/wrong | `backdrop-filter` needs `-webkit-backdrop-filter` | add the prefix |
| Layout depends on parent state and breaks | `:has()` support/behavior differs by Safari version | test the actual Safari version range |
| Bottom content hidden under toolbar on iOS | `100vh` includes the dynamic toolbar in iOS Safari | use `100dvh`/`-webkit-fill-available` |
| `position: sticky` not sticking | sticky inside `overflow` ancestor / table quirks | check ancestor overflow |
| Date/time/number input looks/behaves differently | native control styling diverges | don't assert Chromium-only pixels |
| Smooth-scroll / scroll-snap janky | partial support | progressive enhancement |
| Flash of invisible/oversized text | font-loading / `font-display` differences | check `font-display: swap` |
| Form autofill yellow, focus rings differ | engine defaults | don't treat as a bug; normalize if needed |

**Heuristic:** if a bug report says "only on iPhone/Safari" and the page uses `backdrop-filter`,
`gap`, `100vh`, `:has()`, or tight `overflow:hidden` text — start there.

---

## Workflow

1. **Reproduce in the engine the user named** (or all three if unspecified). Don't debug a
   "Safari bug" in Chromium — you'll see nothing.
2. **Diff engines** with the script above; the metric that differs localizes the bug.
3. **Confirm visually** in the offending engine's native-res screenshot (evidence discipline).
4. **Match the symptom** to the catalog → name the likely CSS cause as a *hypothesis* (you observed
   the symptom, not the code — mark root cause PREDICTED until the CSS is confirmed).
5. **Report per-engine**: "Chromium ✅ / WebKit ❌ (heading clipped) / Firefox ✅", with the
   screenshot from the failing engine. Per-engine status makes the regression obvious to devs.

## Report shape
```
# Cross-browser — [page]  (viewport: 390×844)
| Check            | Chromium | WebKit | Firefox |
| heading wraps    | ✅       | ❌ clip | ✅      |
| docOverflow (px) | 0        | 9      | 0       |
WebKit-only: hero <h1> clipped 9px right (font wider in WebKit + overflow:hidden).
Evidence: xbrowser-shots/webkit-fold.png. Root cause (PREDICTED): nowrap container.
```

## Limits
- **WebKit-in-Playwright ≈ Safari, not identical.** Engine is the same; **font rendering**,
  some DRM/media, and a few `@media` features differ from real Safari on macOS/iOS. For pixel-exact
  Safari or real iOS gestures, confirm on a real device / BrowserStack. Say "WebKit (Safari engine)"
  not "Safari" in reports unless you tested a real device.
- WebKit on Windows/Linux can't test Safari-version-specific behavior (you get the bundled version).
- This finds *rendering/behavior* divergence, not performance — pair with [[web-vitals-ux]].

## Setup
```bash
npm i -D @playwright/test
npx playwright install webkit firefox chromium
```

## Sources
- Playwright browsers (bundled WebKit/Firefox): https://playwright.dev/docs/browsers
- Playwright emulation / devices: https://playwright.dev/docs/emulation
- WebKit `gap`/`backdrop-filter`/`:has()` support: https://caniuse.com (check per-feature)
