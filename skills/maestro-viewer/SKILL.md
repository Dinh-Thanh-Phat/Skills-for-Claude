---
name: maestro-viewer
description: |
  Official Maestro MCP server (built into CLI 2.6.0+) with Maestro Viewer — a web app that
  embeds an iOS simulator, Android emulator, or physical device directly inside your coding agent
  or browser so you can watch every MCP command execute in real time and interact with the device
  without leaving the agent. Use when you want to: set up the official (not third-party) Maestro
  MCP server, use Maestro Viewer for live device visibility in Claude Code/Cursor/Copilot, or
  understand the difference between the official MCP and the slapglif/maestro-mcp community server.
  Triggers on: "maestro viewer", "maestro mcp server", "official maestro mcp", "maestro mcp 2.6",
  "embed device in coding agent", "maestro live device", "maestro claude code mcp".
---

# Maestro Viewer + Official MCP Server

Maestro CLI **v2.6.0** (May 2026) ships its own MCP server built directly into the CLI — no
separate clone or npm install. The headline feature is **Maestro Viewer**: a web app that
embeds a live iOS simulator, Android emulator, or physical device inside your coding-agent
window, letting you watch every MCP command execute in real time.

> **When to use this skill vs `maestro-mcp-workflow`:**
> This skill covers the **official** `mobile-dev-inc/maestro-mcp` server (run via `maestro mcp`).
> The `maestro-mcp-workflow` skill covers the **community** `slapglif/maestro-mcp` server (npm clone).
> The official server requires only CLI 2.6.0 and is the recommended starting point for new setups.

---

## Setup (≈2 minutes)

### 1 — Install / upgrade Maestro CLI (≥ 2.6.0)

```bash
# macOS / Linux
curl -fsSL "https://get.maestro.mobile.dev" | bash

# Or upgrade if already installed
maestro upgrade
```

### 2 — Start the MCP server

```bash
maestro mcp
# → Starts the official MCP server on stdio (no port binding)
# → Prints the JSON config block to paste into your agent
```

### 3 — Wire into your coding agent

Paste the config the command prints, or add manually:

**Claude Code / Claude Desktop (`~/.claude/settings.json` or project `.claude/settings.json`)**

```json
{
  "mcpServers": {
    "maestro": {
      "command": "maestro",
      "args": ["mcp"]
    }
  }
}
```

**VS Code / Cursor / GitHub Copilot (`.vscode/mcp.json`)**

```json
{
  "servers": {
    "maestro": {
      "type": "stdio",
      "command": "maestro",
      "args": ["mcp"]
    }
  }
}
```

No `pnpm install`, no cloning a repo — the CLI IS the server.

---

## Maestro Viewer

Once the MCP server is running, open Maestro Viewer:

```bash
# The Viewer URL is printed when the MCP server starts, typically:
open http://localhost:9999/viewer

# Or open from within your coding agent:
# "Open Maestro Viewer"  → agent calls the open_viewer MCP tool
```

**What Viewer shows:**
- Live render of the connected device (simulator, emulator, or physical device)
- Each MCP tool call highlighted in real time as the agent executes it
- Tap/type directly in the Viewer to interact manually alongside the agent
- Screenshot preview after every `take_screenshot` call

**Why it matters:** You can iterate on a mobile feature or debug a failing test and see the exact
device state the agent sees — no mental model, no lag, no surprise failures.

---

## Key MCP Tools (available to your agent)

| Tool | What it does |
|---|---|
| `run_flow` | Execute a Maestro YAML flow file |
| `take_screenshot` | Capture and return device screenshot (auto-downscaled to avoid LLM token limits) |
| `inspect_hierarchy` | Dump the full UI element tree (element IDs, text, bounds) |
| `tap_on` | Tap an element by id, text, or coordinates |
| `input_text` | Type into the focused element |
| `assert_visible` | Assert an element is visible; returns pass/fail |
| `scroll_down` | Scroll the current screen |
| `open_viewer` | Open Maestro Viewer in the system browser |
| `validate_flow` | Validate YAML syntax before running |

`take_screenshot` **downscales** images before returning them — this is a deliberate design
choice so screenshot calls don't burn through LLM vision-token budgets in long agent sessions.

---

## Self-Healing Workflow

When a flow fails, the agent automatically:

1. Calls `inspect_hierarchy` to get the current live element tree.
2. Cross-references the failing step's selector against what's actually on screen.
3. Proposes the corrected `id:` or `text:` value.
4. Re-runs the flow to confirm the fix.

You can also prompt this manually:

> "The checkout.yaml flow fails on step 3. Inspect the current hierarchy and fix the selector."

---

## YAML Error Pinpointing (2.6.0)

Error messages now include exact line and column numbers:

```
Error in flows/checkout.yaml, line 14, col 5:
  Unknown command 'tapOn_' — did you mean 'tapOn'?
```

Previously Maestro reported file-level errors without position info, making typos hard to locate
in long YAML files.

---

## Decision Table: Official MCP vs Community MCP vs Studio

| Need | Use |
|---|---|
| New MCP setup, quickest path | **This skill** — `maestro mcp` (official, built-in) |
| Existing slapglif/maestro-mcp setup | `maestro-mcp-workflow` skill (community server) |
| Visual IDE for recording flows / inspecting elements | `maestro-studio` skill (`maestro studio`) |
| Running flows in CI without agent | `maestro test` CLI directly |
| AI assertions in YAML (`assertWithAI`) | `maestro-ai-assertions` skill |

---

## Compatible Coding Agents

Claude Code, Claude Desktop, Cursor, GitHub Copilot (VS Code), Codex, Codex Desktop, Gemini CLI,
Windsurf, JetBrains AI Assistant — any MCP-compatible tool works.

---

## Sources

- [Maestro CLI 2.6.0: Introducing Maestro Viewer — maestro.dev blog](https://maestro.dev/blog/maestro-cli-v2-6-0)
- [Maestro MCP Server — official docs](https://docs.maestro.dev/get-started/maestro-mcp)
- [Maestro MCP: An Introduction — maestro.dev blog](https://maestro.dev/blog/maestro-mcp-an-introduction)
- [Official Maestro MCP GitHub — mobile-dev-inc/maestro-mcp](https://github.com/mobile-dev-inc/maestro-mcp)
