---
name: playwright-trace-viewer
description: Debug failed Playwright tests with Trace Viewer — configure trace recording modes, read time-travel DOM/network/console snapshots, download CI artifacts, and identify root causes without re-running tests. Use when a test fails in CI and you need to understand why, when investigating flaky tests, or when setting up trace collection for a new test suite. Triggers on: "trace viewer", "playwright trace", "trace.zip", "show-trace", "test failed in CI", "debug CI failure", "retain-on-failure", "on-first-retry trace", "time-travel debugging", "trace artifact".
---

# Playwright Trace Viewer

Trace Viewer is Playwright's built-in time-travel debugger. It records every action, DOM state, network call, and console log, then lets you scrub through the execution frame-by-frame after the test has finished — essential for diagnosing CI failures you can't reproduce locally.

> **Cross-ref:** `test-debug-checklist` (quick single-test checklist that references trace as Phase 3); `playwright-1.60-new-apis` (`tracing.startHar()` — HAR recording via trace API); `playwright-1.61-new-apis` (new video retention modes and WebSocket capture in traces).

---

## 1 — Configure Tracing in playwright.config.ts

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    // Simple: choose a mode string
    trace: 'retain-on-failure',

    // Advanced: fine-grained control
    trace: {
      mode: 'on-first-retry',
      screenshots: true,   // screenshot at every action (on by default)
      snapshots: true,     // DOM snapshots before/after each action (on by default; true = { dom: true })
      sources: true,       // embed test source code (on by default)
      attachments: true,   // include test.info().attach() data (on by default)
    },
  },
});
```

**1.63+: choose snapshot types per action** — `snapshots` also accepts an object:

```typescript
use: {
  trace: {
    mode: 'retain-on-failure',
    snapshots: { dom: true, aria: true, screen: true },
    // dom    = DOM snapshot + network activity
    // aria   = aria (accessibility-tree) snapshot of the page per action
    // screen = screenshot of the page per action
  },
},
```

With `aria` + `screen` recorded, the trace viewer's **Display Aria** mode shows the action screenshot side by side with the aria snapshot; hovering an aria node highlights it on the screenshot — fast way to spot accessible-name/role regressions.

---

## 2 — Trace Mode Decision Table

| Mode | Records when | Artifact size | Best for |
|------|-------------|---------------|----------|
| `'retain-on-failure'` | Every run; keeps runs that failed (even if a later retry passes) | Low | Default CI — no artifacts on green runs (recording cost still paid) |
| `'retain-on-first-failure'` | First run only; keeps it if it failed | Low | Cheap failure forensics without retry traces |
| `'on-first-retry'` | First retry only; always kept | Very low | CI with `retries ≥ 1` — only traces tests that needed a retry |
| `'on-all-retries'` | Every retry; always kept | Low–Medium | Many retries, want each retry's trace |
| `'retain-on-failure-and-retries'` | Every run; keeps any failed run **or** any retry | Medium | Flake forensics — compare first-fail vs. later-pass |
| `'on'` | Every run, always kept | High | Active debugging sessions; not suitable for long-term CI |
| `'off'` | Never | None | Performance benchmarks where trace overhead matters |

(Semantics per the official `TestOptions.trace` reference.)

**Rule:** Start with `retain-on-failure`. Switch to `on-first-retry` once you enable `retries: 1` or higher. Use `retain-on-failure-and-retries` when you need to distinguish a genuine failure from a flaky retry pass.

---

## 3 — What a Trace Captures (5 Layers)

| Layer | What you see | Debugging use |
|-------|-------------|---------------|
| **Action Timeline** | Every Playwright action — duration, status, locator | Spot which step failed and how long it took |
| **DOM Snapshots** | Complete page state before AND after each action (Before / After tabs) | Verify the element existed, check DOM structure changes |
| **Network Activity** | All HTTP requests — headers, payloads, status codes, timing | Find failed API calls that prevent buttons from loading |
| **Console Logs** | Browser + test-file `console.*` output, JS errors | Surface hidden JS exceptions |
| **Log (per action)** | Playwright's internal action log — scrolling into view, waiting for visible/enabled/stable | Read auto-wait timeout reasons |
| **Source Code** | Test code linked to the currently selected action | Jump directly to the failing test line without leaving the viewer |

---

## 4 — Viewing Traces

### Locally (after a run)
```bash
# Direct from test-results (Playwright writes trace.zip automatically)
npx playwright show-trace test-results/<test-name>/trace.zip

# Or open the HTML report — it embeds a trace link per failing test
npx playwright show-report
```

### Online (no install)
Upload any `trace.zip` to **[trace.playwright.dev](https://trace.playwright.dev)** — runs entirely in browser, no data sent to server.

### From UI mode
Traces are automatically available per test when running `npx playwright test --ui`.

---

## 5 — CI Artifact Workflow (GitHub Actions)

```yaml
- name: Run Playwright tests
  run: npx playwright test

- name: Upload trace artifacts
  uses: actions/upload-artifact@v4
  if: ${{ !cancelled() }}      # upload even when tests fail
  with:
    name: playwright-traces-${{ github.run_id }}
    path: test-results/
    retention-days: 7          # 7 days for feature branches; 30 for main
```

After the CI run:
1. Go to the workflow run → **Artifacts** → download `playwright-traces-<run-id>.zip`
2. Unzip: `unzip playwright-traces-*.zip -d ./traces`
3. View: `npx playwright show-trace ./traces/test-results/<test-name>/trace.zip`

---

## 6 — Time-Travel Debugging Workflow

```
1. Open trace viewer → see Action Timeline on the left
2. Click the failing action (marked in red or the last action before error)
3. Inspect DOM Snapshot → Before tab: state BEFORE the action
                         → After tab:  state AFTER  the action
4. Did the element exist? → No → check selector or app bug
                          → Yes but hidden → check visibility / z-index
5. Switch to Network tab → look for failed API calls (4xx/5xx) near the failure
6. Switch to Console tab → look for JS errors at the failure time
7. Switch to Source tab  → confirm exact line that triggered the action
```

**Key habit:** Always check the **Network tab first** when an element "never appears" — a failing backend call is the most common hidden cause.

---

## 7 — Performance Analysis with Traces

The Timeline view doubles as a lightweight performance profiler:

- **Slow actions** — the Actions list shows each action's duration; scan for outliers (any color-coding threshold is UNVERIFIED)
- **Waiting on network** — cross-reference the action duration with the Network tab; if the action waited and a slow API call happened simultaneously, the backend is the bottleneck
- **Auto-wait storms** — the action's **Log** tab (not Console) shows repeated `waiting for element to be visible/enabled/stable` lines; indicates the selector matches a different element than intended, or an overlay/animation blocks it
- **Step labels (1.63+)** — API steps show their target locator/URL as a subtitle next to the step title, and custom `test.step(..., { subtitle, params })` values render there too

For a whole-run timeline across workers, the built-in `perfetto` reporter (1.63) writes a Trace Event file viewable in ui.perfetto.dev.

For full performance testing, use `performance-analyzer` (Playwright-based metrics) or `llm-load-testing` (for LLM endpoints). Trace Viewer is for per-test forensics, not load simulation.

---

## Sources

- [Trace Viewer — Playwright Docs](https://playwright.dev/docs/trace-viewer)
- https://github.com/microsoft/playwright/blob/main/docs/src/test-api/class-testoptions.md (trace modes, snapshots object) + release-notes-js.md 1.63 — updated 2026-10-02
- [Trace Viewer Intro — Playwright Docs](https://playwright.dev/docs/trace-viewer-intro)
- [Playwright Trace Viewer Complete 2026 Guide — qaskills.sh](https://qaskills.sh/blog/playwright-trace-viewer-complete-guide-2026)
- [Ultimate Guide to Playwright Trace Viewer: Master Time-Travel Debugging — Momentic](https://momentic.ai/blog/the-ultimate-guide-to-playwright-trace-viewer-master-time-travel-debugging)
- [How to Use Playwright Trace Viewer to Debug Failures — SentinelQA](https://sentinelqa.com/blog/how-to-use-playwright-trace-viewer-to-debug-failures)
- [Playwright Debugging Guide: Faster CI Fixes with Traces — TestDino](https://testdino.com/blog/playwright-debugging-guide)
