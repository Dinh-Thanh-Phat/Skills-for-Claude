---
name: maestro-viewer
description: |
  Official Maestro MCP server (built into CLI 2.6.0+) with Maestro Viewer — a web app that
  embeds an iOS simulator, Android emulator, or physical device directly inside your coding agent
  or browser so you can watch every MCP command execute in real time and interact with the device
  without leaving the agent. Use when you want to: set up the official (not third-party) Maestro
  MCP server, use Maestro Viewer for live device visibility in Claude Code/Cursor/Copilot, or
  understand the difference between the official MCP and the slapglif/maestro-mcp community server.
  Triggers on: "maestro viewer", "official maestro mcp", "official maestro mcp server", "maestro mcp 2.6",
  "embed device in coding agent", "maestro live device", "maestro claude code mcp".
---

# Maestro Viewer + Official MCP Server

Maestro CLI **v2.6.0** (May 2026) ships its own MCP server built directly into the CLI — no
separate clone or npm install. The headline feature is **Maestro Viewer**: a web app that
embeds a live iOS simulator, Android emulator, or physical device inside your coding-agent
window, letting you watch every MCP command execute in real time.

> **When to use this skill vs `maestro-mcp-workflow`:**
> This skill covers the **official** MCP server that ships inside the Maestro CLI (run via `maestro mcp`).
> The old standalone repo `mobile-dev-inc/maestro-mcp` is **archived** (last push 2025-06-23) — do not
> clone it; upgrading the CLI upgrades the MCP server.
> The `maestro-mcp-workflow` skill covers the **community** `slapglif/maestro-mcp` server (now deprecated
> in favour of this one).
>
> **Physical iOS devices are NOT supported** — CLI 2.11.0 stops listing physical iPhones and fails runs
> early with "Physical iOS devices are not yet supported". Use an iOS simulator, Android emulator/device,
> or Chromium (web).

---

## Setup (≈2 minutes)

### 1 — Install / upgrade Maestro CLI (≥ 2.6.0)

```bash
# macOS / Linux
curl -fsSL "https://get.maestro.mobile.dev" | bash

# Or upgrade if already installed
maestro upgrade
```

### 2 — Wire `maestro mcp` into your coding agent

`maestro mcp` is a stdio MCP server — the agent launches it; you don't run it by hand.

**Claude Code CLI** (official docs command):

```bash
claude mcp add maestro -- maestro mcp
# add --scope user / --scope project as needed
```

> Do NOT put `mcpServers` in `~/.claude/settings.json` — Claude Code does not read MCP servers from there.
> After upgrading the CLI: `/mcp` → select **maestro** → **Reconnect**.

**Claude Desktop** (`claude_desktop_config.json`; Windows: `%APPDATA%\Claude\claude_desktop_config.json`).
Desktop launches from a minimal shell, so use the full binary path and pass `JAVA_HOME`:

```json
{
  "mcpServers": {
    "maestro": {
      "command": "<full path to maestro binary>",
      "args": ["mcp"],
      "env": { "JAVA_HOME": "<full JAVA_HOME directory>" }
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

Maestro Viewer is a web app exposed through the `open_maestro_viewer` MCP tool, which returns the
running Viewer URL. To open it, ask your agent:

> open the maestro viewer

There is no fixed port/URL to hard-code — always get it from `open_maestro_viewer`. The Viewer
requires an AI coding agent with Maestro MCP installed.

**What Viewer shows (per docs/blog):**
- Live embedded device (simulator, emulator, or Android physical device — not physical iOS, see above)
- The exact commands Maestro MCP runs, in real time
- Full manual interaction with the embedded device alongside the agent

**Why it matters:** You can iterate on a mobile feature or debug a failing test and see the exact
device state the agent sees — no mental model, no lag, no surprise failures.

---

## Key MCP Tools (available to your agent)

**As of CLI 2.5.0, the tool surface was consolidated** — `run_flow`/`run_flow_files` merged into
`run`, and `tap_on`, `input_text`, `back`, `launch_app`, `stop_app`, `check_flow_syntax`,
`start_device`, `query_docs` were dropped. Interactions (tap, type, assert) now go through `run`
with inline YAML. Official tool list (docs.maestro.dev/get-started/maestro-mcp):

| Tool | What it does |
|---|---|
| `list_devices` | List local devices (Android emulators, iOS simulators, Chromium for web) |
| `inspect_screen` | Current screen's view hierarchy as compact JSON — call before targeting elements, re-call after UI changes |
| `take_screenshot` | Screenshot of the current screen (auto-downscaled to 2000px to save vision tokens) |
| `run` | Execute flows. Exactly one of `{ yaml }` (inline YAML, preferred for exploration), `{ files }`, or `{ dir, include_tags, exclude_tags }`. Syntax is validated as part of the call |
| `cheat_sheet` | Maestro command/syntax cheat sheet — call before authoring unfamiliar commands (no Cloud auth needed) |
| `open_maestro_viewer` | Returns the running Viewer URL |
| `list_cloud_devices` / `run_on_cloud` / `get_cloud_run_status` | Maestro Cloud (see below) |

`take_screenshot` **downscales** images before returning them — this is a deliberate design
choice so screenshot calls don't burn through LLM vision-token budgets in long agent sessions.

> If you set up this MCP server before CLI 2.5.0, drop any tool config referencing `run_flow`,
> `run_flow_files`, or `use_fuzzy_matching` on `tap_on` (all removed) — point agents at `run` instead.

**Android performance (2.6.0):** MCP calls against Android devices now go over a direct ADB
socket instead of TCP port forwarding — **~41% faster** on a simple `assertVisible` flow, and it
removes a flaky forwarding thread that could intermittently drop the connection during longer
agent sessions. No config change needed; this is automatic on CLI ≥ 2.6.0.

---

## Maestro Cloud via MCP (2.5.0+)

The MCP server now exposes **native Maestro Cloud tools**, so an agent can trigger and poll a
cloud run without shelling out to `maestro cloud`:

| Tool | What it does |
|---|---|
| `run_on_cloud` | Submit a flow + app binary to Maestro Cloud asynchronously; returns a dashboard URL |
| `get_cloud_run_status` | Poll a cloud run's status and per-flow results |
| `describe_cloud_run` | New in **2.7.0** — inspect the status and results of a Maestro Cloud run (per the official CHANGELOG). Overlaps in description with `get_cloud_run_status`; the changelog doesn't state whether it replaces or supplements that tool, and the official MCP docs page 403'd to verification — if both appear in your agent's tool list, prefer whichever one is actually offered and treat the other as possibly deprecated. |
| `list_cloud_devices` | List valid `{platform, model, supported_os}` triples for the `device_model` param on `run_on_cloud` |

This is useful when you want the agent to kick off a full-device-matrix cloud run (instead of the
single local simulator/emulator `run` targets) and report back once it completes — e.g. "run this
flow on cloud against an iPhone 15 and an iPhone 13 Mini, then tell me if either failed."

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
- [Maestro CHANGELOG.md — 2.5.0 MCP tool consolidation + native Cloud tools, 2.6.0 CLI details, `describe_cloud_run` tool (2.7.0)](https://github.com/mobile-dev-inc/maestro/blob/main/CHANGELOG.md)
