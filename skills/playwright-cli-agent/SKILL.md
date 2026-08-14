---
name: playwright-cli-agent
description: >-
  Microsoft's official `@playwright/cli` (`playwright-cli`) — a stateless shell-command companion
  to Playwright MCP, ~4x cheaper in tokens (27k vs 114k for a typical flow) because snapshots
  write to disk and each command is a small, independent process call instead of a persistent
  tool-schema/JSON-RPC session. Use when driving a real browser from a coding agent that's
  context-constrained, when live-attaching to a paused failing Playwright test (`--debug=cli`) to
  explore and generate a fix, or when you want CLI-style exploratory automation without wiring up
  an MCP server. Triggers on: "playwright-cli", "@playwright/cli", "playwright cli agent",
  "playwright shell commands", "playwright token efficient browser", "debug=cli", "attach
  playwright-cli", "playwright-cli snapshot".
---

# Playwright CLI (`@playwright/cli`)

A first-party companion to `playwright-mcp-server`, launched early 2026. Same accessibility-snapshot-driven automation model, but exposed as plain shell commands instead of an MCP tool-call protocol — built for agents that need to conserve context.

## Why It Exists — vs `playwright-mcp-server`

| | `@playwright/mcp` (`playwright-mcp-server` skill) | `@playwright/cli` (this skill) |
|---|---|---|
| Protocol | MCP tool calls (JSON-RPC over stdio/SSE) | Plain shell commands (`Bash(playwright-cli:*)`) |
| Per-call cost | Full tool schema resident in context every turn | No schema — each command is a small, independent process |
| Snapshot delivery | Inline or file, config-toggled | Always written to a `.yml` file on disk; agent reads only if it needs to |
| Typical task cost | ~114,000 tokens (official benchmark) | ~27,000 tokens (~4x cheaper, same benchmark) |
| Best for | Persistent session, editor/Desktop MCP integration | High-throughput or context-constrained agent loops, terminal-native agents (Claude Code) |

Both use the same underlying accessibility-tree + `ref` targeting model (e.g. `e15`) — pick the transport that matches your agent's constraints, not a different automation approach.

## Installation

```bash
npm install -g @playwright/cli@latest
playwright-cli --help

# Wire up agent skill files (Claude Code, GitHub Copilot, etc. auto-detect local skills)
playwright-cli install --skills

# If no global install, fall back to npx
npx --no-install playwright-cli --version
npx playwright-cli <command>   # prefix every command with npx when using the local install
```

**Playwright 1.62+ bundles this CLI directly** — if the project already depends on `@playwright/test` 1.62+, `npx playwright cli <command>` works without installing `@playwright/cli` separately. The standalone package still updates independently; prefer it for a version newer than what's bundled, or in a project with no Playwright dependency at all.

## Core Workflow

```bash
playwright-cli open https://example.com
playwright-cli snapshot
# ### Snapshot
# [Snapshot](.playwright-cli/page-2026-02-14T19-22-42-679Z.yml)
#   - textbox "Email" [ref=e1]
#   - textbox "Password" [ref=e2]
#   - button "Sign In" [ref=e3]

playwright-cli fill e1 "user@example.com"
playwright-cli fill e2 "password123" --submit   # --submit presses Enter after filling
playwright-cli click e3
playwright-cli close
```

Targeting also accepts CSS selectors and Playwright locators directly, no snapshot required first:

```bash
playwright-cli click "#main > button.submit"
playwright-cli click "getByRole('button', { name: 'Submit' })"
playwright-cli click "getByTestId('submit-button')"
```

## Command Surface (by category)

- **Core**: `open`, `goto`, `close`, `type`, `click`, `dblclick`, `fill`, `drag`, `drop`, `hover`, `select`, `upload`, `check`, `uncheck`, `snapshot`, `eval`, `dialog-accept`, `dialog-dismiss`, `resize`
- **Navigation**: `go-back`, `go-forward`, `reload`
- **Keyboard/Mouse**: `press`, `keydown`/`keyup`, `mousemove`, `mousedown`/`mouseup`, `mousewheel`
- **Capture**: `screenshot`, `pdf`
- **Tabs**: `tab-list`, `tab-new`, `tab-close`, `tab-select`
- **Storage**: `state-save`/`state-load`, `cookie-*`, `localstorage-*`, `sessionstorage-*`
- **Network**: `route`, `route-list`, `unroute` (same mocking model as `api-network-mocking`, shell-invoked)
- **DevTools**: `console`, `network`/`requests`, `run-code`, `tracing-start`/`tracing-stop`, `video-start`/`video-chapter`/`video-stop`

`eval` is the way to pull data the snapshot doesn't show (element id, class, `data-testid`):

```bash
playwright-cli eval "el => el.getAttribute('data-testid')" e5
```

## Every Action Generates Playwright Code — Test Authoring for Free

Each interaction prints the equivalent TypeScript, using role-based locators when possible:

```bash
playwright-cli fill e1 "user@example.com"
# Ran Playwright code:
# await page.getByRole('textbox', { name: 'Email' }).fill('user@example.com');
```

Collect these into a spec file — but generated code captures actions only, not assertions; add `expect(...)` calls manually. This is a lighter-weight alternative to the full `playwright-test-agents` Planner/Generator pipeline when you just need one or two flows recorded, not a whole suite bootstrapped.

## Live-Attach to a Paused Failing Test (`--debug=cli`)

The highest-value QA workflow this tool unlocks: attach `playwright-cli` directly to a test paused mid-failure, explore the live page, and generate the fix as real Playwright code — instead of guessing from a stack trace and re-running blind.

```bash
# Run in the background; the test pauses at the start
PLAYWRIGHT_HTML_OPEN=never npx playwright test --debug=cli
# ... watch output until "Debugging Instructions" prints a session name, e.g. "tw-abcdef" ...

# Attach to that paused session
playwright-cli attach tw-abcdef

# Step, inspect, and fix live — every playwright-cli action against this session
# still emits the corresponding Playwright code, so a locator update or a
# missed-wait fix is copy-pasteable straight back into the spec.
```

Keep the test process running in the background while exploring; stop it once you've applied a fix, then re-run to confirm green. This complements `flaky-test-prevention` and `playwright-diagnosis-first` — it's the live-inspection step between "test went red" and "here's the root cause."

## Sessions (Multiple Concurrent Browsers)

```bash
playwright-cli -s=mysession open example.com --persistent
playwright-cli -s=mysession click e6
playwright-cli -s=mysession close

playwright-cli list          # all active sessions
playwright-cli close-all
playwright-cli kill-all      # forceful cleanup if a session hangs
playwright-cli show          # visual dashboard: live screencasts + remote control across sessions
```

`--persistent` (with optional `--profile=/path`) keeps a browser profile across restarts — default is in-memory, gone when the session closes.

## Sources

- `skills/playwright-test-workflow/scripts/node_modules/playwright-core/lib/tools/cli-client/skill/SKILL.md` and its `references/playwright-tests.md` / `references/test-generation.md` — the first-party skill file Microsoft ships inside the `playwright-core` npm package itself, vendored into this repo's `playwright-test-workflow` dependencies (verified verbatim, most authoritative available source)
- https://playwright.dev/agent-cli/introduction
- https://github.com/microsoft/playwright-cli
- https://www.npmjs.com/package/@playwright/cli
- https://testcollab.com/blog/playwright-cli
- https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/release-notes-js.md (1.62 — bundled `npx playwright cli` entry point)
- https://testdino.com/blog/playwright-cli
