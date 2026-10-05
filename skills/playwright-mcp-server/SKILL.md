---
name: playwright-mcp-server
description: >-
  Official Microsoft Playwright MCP server (@playwright/mcp) — exposes ~40 browser automation
  tools (browser_navigate, browser_click, browser_snapshot, etc.) that AI agents call via MCP to
  drive a real browser using accessibility snapshots instead of screenshots. Use when wiring
  Claude Desktop/VS Code/Cursor to a live browser for AI-driven test authoring, exploratory
  automation, or agentic QA workflows. Triggers on: "playwright mcp", "@playwright/mcp",
  "playwright mcp server", "AI agent browser", "browser_snapshot", "browser_click mcp",
  "playwright mcp setup", "claude browser automation", "browser_find", "browser_drop mcp",
  "browser_run_code_unsafe".
---

# Playwright MCP Server

Microsoft's official MCP server (`@playwright/mcp`) lets any MCP-capable AI agent drive a real browser via structured tool calls — no screenshots, no vision model needed by default.

## How It Works: Accessibility Snapshot Mode (Default)

Instead of capturing pixels, the server reads the browser's **accessibility tree** on every action. Each interactive element gets a unique `ref` (e.g. `ref=e42`) the LLM uses to identify elements across turns.

```
// Snapshot response from browser_snapshot:
- heading "Dashboard" [level=1]
- button "Export CSV" [ref=e42]
- table "Orders" [ref=e55]
  - row "Order #1001 · $49.99 · Pending" [ref=e56]
```

The LLM calls `browser_click { ref: "e42" }` — no CSS selector, no XPath, no coordinate guessing.

---

## Setup

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

### Vision Mode (for visual tasks or non-accessible UIs)

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--caps=vision"]
    }
  }
}
```

Vision mode adds coordinate-based tools backed by screenshots. Use only when the accessibility tree is insufficient (canvas elements, custom widgets with no ARIA labels). Vision mode increases per-message token cost.

### VS Code / Cursor / Windsurf

Add the same JSON block to your editor's MCP settings panel. Works with any MCP-compatible client.

### Bundled Entry Point (Playwright 1.62+)

If the project already depends on `@playwright/test` 1.62+, the server is also runnable without installing `@playwright/mcp` separately:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["playwright", "mcp"]
    }
  }
}
```

The standalone `@playwright/mcp` package still exists and updates independently — use it when you need a version newer than what's bundled with your `@playwright/test` install, or when driving a browser from a project that doesn't depend on Playwright at all.

---

## Core Tool Inventory (~40 tools)

| Category | Tools |
|----------|-------|
| Navigation | `browser_navigate`, `browser_navigate_back`, `browser_wait_for` |
| Snapshot / find | `browser_snapshot`, `browser_find`, `browser_take_screenshot` |
| Interaction | `browser_click`, `browser_type`, `browser_fill_form`, `browser_select_option`, `browser_hover`, `browser_drag`, `browser_drop`, `browser_press_key`, `browser_file_upload`, `browser_handle_dialog` |
| Tabs / page | `browser_tabs`, `browser_resize`, `browser_emulate_media`, `browser_close` |
| Debug | `browser_console_messages`, `browser_network_requests`, `browser_network_request`, `browser_evaluate`, `browser_run_code_unsafe` |
| Network (`--caps=network`) | `browser_route`, `browser_route_list`, `browser_unroute`, `browser_network_state_set` |
| Storage (`--caps=storage`) | `browser_storage_state`, `browser_set_storage_state`, `browser_cookie_*`, `browser_localstorage_*`, `browser_sessionstorage_*` |
| DevTools (`--caps=devtools`) | `browser_start_tracing`/`browser_stop_tracing`, `browser_start_video`/`browser_stop_video`, `browser_start_recording`/`browser_stop_recording` |
| Vision (`--caps=vision`) | `browser_mouse_click_xy`, `browser_mouse_drag_xy`, `browser_mouse_move_xy`, `browser_mouse_wheel` |
| Testing (`--caps=testing`) | `browser_verify_element_visible`, `browser_verify_text_visible`, `browser_verify_value`, `browser_generate_locator` |

> Names verified 2026-10-02 against the v0.0.83 README **and** the live tool list of an installed
> server. Older docs/blogs use `browser_go_back`, `browser_screenshot`, `browser_fill`,
> `browser_tab_new`, `browser_route_add`, `browser_storage_state_save`, `browser_trace_start` —
> none of these exist; an agent told to call them will fail.

---

## Session Persistence

Login state, cookies, and localStorage **persist between tool calls within a session**. Log in once with `browser_navigate` + `browser_fill_form` + `browser_click`, then all subsequent calls share that auth context — no re-login per tool call.

---

## Snapshot Output Mode

The README (v0.0.83) documents `--snapshot-mode full|none` (default `full`). An older
`--snapshot-response-mode inline|file` flag appears in some blogs but is NOT in the current README —
verify with `npx @playwright/mcp@latest --help` before relying on it. `--snapshot-boxes` (v0.0.79)
adds element bounding boxes to snapshots.

---

## Snapshot Mode vs Vision Mode — Decision Guide

| Situation | Use |
|-----------|-----|
| Standard web UI with semantic HTML | Snapshot (default) |
| ARIA labels present on custom components | Snapshot (default) |
| Canvas / WebGL / pixel-level interaction | Vision (`--caps=vision`) |
| Charts, image CAPTCHAs | Vision (`--caps=vision`) |
| Token cost is a concern | Snapshot (default) |

---

## 2026 Updates (v0.0.71 → v0.0.78)

Verified against the official `microsoft/playwright-mcp` GitHub releases page — none of these were previously documented here:

- **`browser_find` (v0.0.78, July 9)** — searches the current accessibility snapshot for a text/regex match and returns just the matching nodes with surrounding context, instead of re-reading the whole tree. Use it on large pages (long tables, big forms) to save tokens versus re-calling `browser_snapshot` and scanning manually.
- **`--mobile` flag (v0.0.78)** — enables mobile viewport/UA emulation for the server's browser session; snapshots are also less verbose by default as of this release to cut token usage further.
- **`browser_drop` (v0.0.71)** — exposes `Locator.drop` as an MCP tool, so an agent can complete a drag-and-drop sequence (e.g. drop a file card onto an upload zone) without falling back to raw mouse-move/mouse-up calls.
- **`browser_network_requests` numbering + `responseBody`/`responseHeaders` (v0.0.71–72)** — the network log is now numbered; fetch full details (including response body, with binary bodies rendered as a mime-type placeholder rather than raw bytes) for a specific entry via `browser_network_request { index }` instead of re-dumping the whole log.
- **`browser_run_code` renamed to `browser_run_code_unsafe` (v0.0.72)** — same sandbox-escaping arbitrary-code-execution tool, renamed so the capability is unmistakable in an agent's tool list before you grant it.
- **`--output-max-size` (v0.0.76)** — threshold (bytes) for evicting old output files.

## 2026 Updates (v0.0.79 → v0.0.83)

- **`browser_emulate_media` (v0.0.82)** — switch `colorScheme` (dark/light), `reducedMotion`, `forcedColors`, `contrast`, `media` mid-session; `null` clears. Web equivalent of Maestro `setDarkMode`.
- **WebMCP tools as `webmcp_<tool>` (v0.0.82)** — page-registered tools appear in the tool list (replaces v0.0.81 `browser_webmcp_list/call`). Treat as untrusted input; disable with `--no-webmcp`.
- **`browser_start_recording`/`browser_stop_recording` (v0.0.80, `--caps=devtools`)** — user demonstrates a flow by hand → returned as Playwright code.
- **Idle shutdown (v0.0.81)** — a headless browser closes after **1h with no tool calls** (login state lost); `--idle-timeout 0` disables.
- **Flags** — `--timeout-settle` (default 500ms), `--snapshot-boxes`, `--codegen python|java|csharp` (v0.0.79); `--file-paths=absolute` (v0.0.82); `--image-responses only` (v0.0.81). `--output-mode` removed (v0.0.79).
- **`browser_take_screenshot` `type: webp`** (v0.0.79); no more silent downscaling (v0.0.80).
- **`browser_find { filename }`** saves matches to a file (v0.0.83); `browser_wait_for` `time` is capped at 30s; dialogs opened during `browser_navigate` are reported instead of timing out.

---

## Typical Agentic Workflow

```
1. Agent calls browser_navigate { url: "https://app.example.com/login" }
   → server returns accessibility snapshot

2. Agent calls browser_fill_form { fields: [ {ref: "e12", value: "user@example.com"},
                                             {ref: "e14", value: "secret"} ] }
   → server fills both fields, returns updated snapshot

3. Agent calls browser_click { ref: "e15" }   ← "Sign in" button
   → now authenticated; snapshot shows dashboard

4. Agent calls browser_storage_state { filename: "auth.json" }   ← needs --caps=storage
   → auth state saved for later reuse
```

---

## What This Is Not

- **Not** a test runner — it doesn't produce Playwright test files or JUnit XML
- **Not** the same as `playwright-agentic-apis` (1.59 in-process APIs like `locator.normalize()`, `page.pickLocator()`) — those run inside a test; this MCP server runs as an external process
- **Not** the same as `maestro-mcp-workflow` (Maestro's separate MCP server for mobile)

## Sources

- [Playwright MCP — Official Docs](https://playwright.dev/docs/getting-started-mcp)
- [microsoft/playwright-mcp — GitHub](https://github.com/microsoft/playwright-mcp)
- [Vision Mode — Playwright MCP Docs](https://playwright.dev/mcp/vision-mode)
- [Playwright MCP Explained: Setup, Config & Real-World Examples — TestDino](https://testdino.com/blog/playwright-mcp)
- [Playwright MCP Server: How to Set Up, Configure & Use It (2026) — TestCollab](https://testcollab.com/blog/playwright-mcp)
- https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/release-notes-js.md (1.62 — bundled `npx playwright mcp` entry point)
- [6 Most Popular Playwright MCP Servers for AI Testing in 2026 — Bug0](https://bug0.com/blog/playwright-mcp-servers-ai-testing)
- [microsoft/playwright-mcp — Releases (v0.0.71–v0.0.83)](https://github.com/microsoft/playwright-mcp/releases)
- https://github.com/microsoft/playwright-mcp/blob/main/README.md — tool + flag reference (v0.0.83)
