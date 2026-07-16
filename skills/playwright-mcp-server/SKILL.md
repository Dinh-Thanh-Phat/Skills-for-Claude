---
name: playwright-mcp-server
description: Official Microsoft Playwright MCP server (@playwright/mcp) — exposes ~40 browser automation tools (browser_navigate, browser_click, browser_snapshot, etc.) that AI agents call via MCP to drive a real browser using accessibility snapshots instead of screenshots. Use when wiring Claude Desktop/VS Code/Cursor to a live browser for AI-driven test authoring, exploratory automation, or agentic QA workflows. Triggers on: "playwright mcp", "@playwright/mcp", "playwright mcp server", "AI agent browser", "browser_snapshot", "browser_click mcp", "playwright mcp setup", "claude browser automation", "browser_find", "browser_drop mcp", "browser_run_code_unsafe".
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

---

## Core Tool Inventory (~40 tools)

| Category | Tools |
|----------|-------|
| Navigation | `browser_navigate`, `browser_go_back`, `browser_go_forward`, `browser_reload` |
| Snapshot | `browser_snapshot` (accessibility tree), `browser_screenshot` (vision mode) |
| Interaction | `browser_click`, `browser_type`, `browser_fill`, `browser_select_option`, `browser_check`, `browser_uncheck`, `browser_hover` |
| Tabs / Windows | `browser_tab_new`, `browser_tab_switch`, `browser_tab_close` |
| Network | `browser_network_requests` (inspect traffic), `browser_route_add` (mock routes) |
| Storage | `browser_storage_state_save`, `browser_storage_state_load` |
| Tracing | `browser_trace_start`, `browser_trace_stop` |
| File / Download | `browser_file_upload`, `browser_download_wait` |

---

## Session Persistence

Login state, cookies, and localStorage **persist between tool calls within a session**. Log in once with `browser_navigate` + `browser_fill` + `browser_click`, then all subsequent calls share that auth context — no re-login per tool call.

---

## Inline Snapshot Response Mode

By default, action tools write the snapshot to a file and return a link. Switch to inline mode for agents that process the full tree in-context:

```json
"args": ["@playwright/mcp@latest", "--snapshot-response-mode", "inline"]
```

Inline mode is better for multi-step reasoning; file mode reduces prompt size for long flows.

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
- **`--output-max-size` (v0.0.76)** — caps response payload size for any tool call; pair with `--snapshot-response-mode file` (already documented above) when driving pages with very large accessibility trees.

---

## Typical Agentic Workflow

```
1. Agent calls browser_navigate { url: "https://app.example.com/login" }
   → server returns accessibility snapshot

2. Agent calls browser_fill { ref: "e12", value: "user@example.com" }
   → server fills email field, returns updated snapshot

3. Agent calls browser_fill { ref: "e14", value: "secret" }
4. Agent calls browser_click { ref: "e15" }   ← "Sign in" button
   → now authenticated; snapshot shows dashboard

5. Agent calls browser_storage_state_save { path: "auth.json" }
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
- [6 Most Popular Playwright MCP Servers for AI Testing in 2026 — Bug0](https://bug0.com/blog/playwright-mcp-servers-ai-testing)
- [microsoft/playwright-mcp — Releases (v0.0.71–v0.0.78)](https://github.com/microsoft/playwright-mcp/releases)
