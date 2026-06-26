---
name: playwright-ui-mode
description: Use Playwright's interactive UI mode (--ui flag) to develop and debug tests with watch mode, time-travel DOM inspection, locator picking, and test filtering — without re-running from the terminal. Use when writing new tests and you want live feedback on locator changes, when a test is failing locally and you want to step through actions with DOM snapshots, or when you want to pick accurate locators from a live page. Triggers on: "playwright ui mode", "--ui flag", "interactive test runner", "watch mode playwright", "pick locator", "time travel debugging local", "playwright debug locally", "ui mode vs headed", "npx playwright test --ui".
---

# Playwright UI Mode

UI Mode is Playwright's interactive test development environment. It combines watch mode, the Inspector, and Trace Viewer into one live window — run once and iterate without touching the terminal again.

> **Cross-ref:** `playwright-trace-viewer` (post-run CI trace analysis — UI Mode is for *local development*); `test-debug-checklist` (general debugging checklist that references both tools); `playwright-flaky-test-detection` (diagnosing flaky patterns).

---

## 1 — Launch Commands

```bash
# Open UI mode for all tests
npx playwright test --ui

# Filter to a specific file on launch
npx playwright test tests/login.spec.ts --ui

# Expose to network (e.g. Docker / remote machine)
npx playwright test --ui-host=0.0.0.0 --ui-port=8080
```

> When `--ui-host` or `--ui-port` are set, the UI opens in the system browser instead of a dedicated Chromium window — useful for containerised setups.

**UI Mode vs other run modes:**

| Mode | Use when |
|------|----------|
| `--ui` | Writing or debugging tests locally — full interactive IDE |
| `--headed` | Watching a test run once — no interaction, no watch |
| `--debug` | Step-by-step with Playwright Inspector (breakpoints) |
| `npx playwright show-trace` | Analysing a CI artifact after the fact |

---

## 2 — Test Tree and Filtering

The left sidebar shows a tree of all spec files and tests. At the top is a filter bar:

| Filter type | Syntax | Example |
|-------------|--------|---------|
| By name | type in filter bar | `login` |
| By tag | `@tag` in filter bar | `@smoke` |
| By project | project dropdown | `chromium`, `firefox` |
| By status | status buttons | `Failed`, `Passed`, `Skipped` |

Click the **eye icon** next to any test (or the top-level eye) to enable **watch mode** for that test. The eye turns green — any file change re-triggers it automatically.

---

## 3 — Watch Mode

Watch mode monitors every file imported by the running test (spec, fixtures, helpers, page objects) and re-executes on save.

```
Sidebar eye icon → green → save any imported file → test re-runs automatically
```

**Practical workflow:**
1. Open UI mode.
2. Enable watch on the test you're writing.
3. Edit the test or the fixture — the test re-runs within ~200 ms.
4. Iterate on locators without switching to the terminal.

> To watch all tests simultaneously, click the eye at the very top of the sidebar. Use sparingly in large suites — it triggers the full suite on every save.

---

## 4 — Time-Travel Debugging

Each test run shows a **Timeline** at the top and an **Action List** below. Hover (or click) any action to jump to that point in time:

- **Before/After DOM snapshots** — exactly what the page looked like before and after each action.
- **Source tab** — the specific line of test code that triggered the action, with an "Open in VS Code" button.
- **Network tab** — all requests made during the action; filter by type, status, or method; inspect headers and body.
- **Console tab** — browser and test-file logs, distinguishable by icon.
- **Metadata tab** — browser version, viewport, total test duration.

**Double-click** any action on the timeline to expand its time range. Use the slider to scrub frame-by-frame through complex animations or transitions.

> Pop out a DOM snapshot into a separate window (`⊞` icon) to open browser DevTools against the frozen state — useful for inspecting computed CSS or ARIA tree at a specific moment.

---

## 5 — Locator Picker

Click **"Pick locator"** in the toolbar to enter element selection mode:

1. Hover over any element in the live page preview.
2. Playwright highlights the element and suggests a locator in the picker input.
3. The locator follows the recommended hierarchy: role → label → text → `data-testid` → CSS (last resort).
4. Edit the locator directly in the input to test variants — the matching elements highlight in real time.
5. Click **Copy** to copy to clipboard, then paste into your test code.

```typescript
// Picker output example — locators are ARIA-first, not CSS guesses
await page.getByRole('button', { name: 'Submit order' }).click();
await page.getByLabel('Email address').fill('user@example.com');
await page.getByTestId('cart-total').textContent();
```

---

## 6 — Fixture Inspection

UI Mode treats fixtures as first-class actions. The action list shows:

```
▶ beforeAll hook
  ▶ fixture: browser
  ▶ fixture: context
  ▶ fixture: page
  ▶ fixture: loginPage      ← custom fixture with setup/teardown
▶ test body
  → navigate to /dashboard
  → click 'Add item'
  → expect locator to have text
▶ afterAll hook
  ▶ fixture: loginPage (teardown)
```

Step through fixture setup/teardown just like test actions — essential for debugging fixtures that construct authenticated sessions.

---

## 7 — VS Code Integration

If the [Playwright VS Code extension](https://marketplace.visualstudio.com/items?itemName=ms-playwright.playwright) is installed:

- **Sidebar test tree** mirrors UI Mode's test tree — click any test to open it in UI Mode.
- **CodeLens** adds "Run test" / "Debug test" / "Show in UI Mode" above each `test(...)` block.
- **"Open in VS Code"** button inside UI Mode navigates to the failing line in the editor.

Workflow: write tests in VS Code, keep UI Mode open in a side window — save the file, see the result, click the failing action to jump back to the source line.

---

## 8 — Decision: UI Mode vs Trace Viewer

| Situation | Tool |
|-----------|------|
| Writing a new test, want live feedback | **UI Mode** (`--ui`) |
| Test passes locally, fails in CI | **Trace Viewer** (download CI artifact) |
| Investigating a flake, need both pass and fail traces | **Trace Viewer** with `retain-on-failure-and-retries` |
| Picking a locator for an existing page | **UI Mode** locator picker |
| Post-mortem analysis without re-running | **Trace Viewer** |

---

## Sources

- https://github.com/microsoft/playwright/blob/main/docs/src/test-ui-mode-js.md
- https://playwright.dev/docs/test-ui-mode
- https://playwright.dev/docs/running-tests
- https://software-testing-tutorials-automation.com/2026/05/playwright-test-runner-tutorial.html
- https://qaskills.sh/blog/playwright-ui-mode-complete-2026-guide
