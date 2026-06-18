---
name: web-vitals-ux
description: >-
  Measure performance AS a UX dimension — Core Web Vitals (LCP, INP, CLS) plus TTFB — on a live
  web page, and judge them against Google's research-backed thresholds. Use whenever evaluating
  whether a page/flow "feels slow", when complementing a UX evaluation, or when the user asks
  about "performance", "Core Web Vitals", "LCP/INP/CLS", "page speed", "tải chậm", "trang chậm",
  "đo hiệu năng web", "lighthouse". Produces measured numbers + good/needs-improvement/poor verdict
  per metric. Complements ux-heuristic-evaluation (slow load is real friction). Measurements are
  OBSERVED; do NOT guess numbers — run the measurement.
---

# Web Vitals as UX

Slow is a usability defect. **53% of mobile visits are abandoned if load takes >3s**; a 0.1s mobile
speed-up lifted retail conversions ~8.4% (Google/Deloitte). So performance is a UX dimension, not a
separate concern — this skill makes it measurable. Companion to [[ux-heuristic-evaluation]].

## Thresholds (Google, 75th percentile; judge mobile & desktop separately)
Source: https://web.dev/articles/defining-core-web-vitals-thresholds , https://web.dev/articles/inp

| Metric | What it captures | Good | Needs work | Poor |
|---|---|---|---|---|
| **LCP** Largest Contentful Paint | loading — when main content appears | ≤ 2.5 s | ≤ 4.0 s | > 4.0 s |
| **INP** Interaction to Next Paint (replaced FID 2024-03) | responsiveness to input | ≤ 200 ms | ≤ 500 ms | > 500 ms |
| **CLS** Cumulative Layout Shift | visual stability | ≤ 0.1 | ≤ 0.25 | > 0.25 |
| TTFB (diagnostic) | server response | ≤ 0.8 s | ≤ 1.8 s | > 1.8 s |

These four bands are **hard, citable** — assert them. Don't invent other absolute speed thresholds.

## How to measure (no Lighthouse install needed)
Run against a real page with Playwright; capture is OBSERVED evidence.

1. **PRIMARY — native `PerformanceObserver` (CSP-proof, always works).** Inject via `addInitScript`
   BEFORE navigation so it's armed at load. CDN script injection is often **blocked by the site's
   Content Security Policy** (verified live: unpkg was blocked on a real site) — so don't rely on it.
   ```js
   await page.addInitScript(() => {
     window.__lcp = 0; window.__cls = 0;
     new PerformanceObserver(l => { for (const e of l.getEntries()) window.__lcp = e.startTime; })
       .observe({ type: 'largest-contentful-paint', buffered: true });
     new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; })
       .observe({ type: 'layout-shift', buffered: true });
   });
   // after load: const {__lcp,__cls} = await page.evaluate(...); TTFB:
   // performance.getEntriesByType('navigation')[0].responseStart
   ```
2. **For INP (and to cross-check), add the `web-vitals` lib** — but use a **CSP-allowed** CDN. Check the
   page's CSP `script-src`; many allow `cdn.jsdelivr.net` (`https://cdn.jsdelivr.net/npm/web-vitals@4/dist/web-vitals.iife.js`).
   If injection throws a CSP error, fall back to PerformanceObserver and report INP as n/a.
3. **INP needs a real interaction** — after load, perform a representative click/type that triggers JS,
   THEN read `onINP`. A trivial click on empty space may not register; if INP stays null, say
   **"n/a (no measurable interaction)"** — never report 0.
4. **If `lighthouse` / `playwright-lighthouse` IS installed**, prefer it for a full lab run
   (`lhr.audits['largest-contentful-paint'].numericValue`).

Measure on a representative cold load; note throttle (Lighthouse defaults to mobile slow-4G). Run 3×
and report the median — single runs are noisy.

## Report
```
# Web Vitals — [page]  (device: mobile/desktop · runs: N median)
| Metric | Value | Verdict |
| LCP | 3.1 s | Needs work |
| INP | 180 ms | Good (after click on X) |
| CLS | 0.32 | Poor — content jumps |
| TTFB | 0.6 s | Good |
Worst offender: [metric] → [likely cause: big hero image / late font / no width-height on imgs].
```
Tie findings back to UX: a Poor CLS = "content jumps under the user's tap"; a Poor LCP = "blank/slow
first paint" (this is the OBSERVED backing for a heuristic 'visibility of system status' note).

## Limits
- Lab numbers ≠ field (real-user) numbers. Say "lab". Real field data needs CrUX/RUM.
- INP without interaction is unmeasurable — don't fabricate it.
