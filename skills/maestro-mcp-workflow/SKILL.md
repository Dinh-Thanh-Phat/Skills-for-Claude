---
name: maestro-mcp-workflow
description: |
  Drive Maestro mobile tests via Claude Code using the Maestro MCP server (slapglif/maestro-mcp).
  Use when you want to: generate Maestro YAML flows by describing them in natural language, run/debug
  flows live against a connected emulator or device from Claude Code, inspect the UI hierarchy to fix
  broken selectors, or automate mobile exploratory testing via conversational commands.
  Triggers on: "maestro mcp", "generate maestro flow", "run maestro from claude", "ai mobile testing",
  "maestro claude", "natural language mobile test", "maestro mcp server".
---

# Maestro MCP Workflow

The **maestro-mcp** MCP server exposes 47+ Maestro CLI operations as tools that Claude Code can call
directly. Instead of hand-authoring YAML, describe what you want in English — Claude generates the
flow, runs it on your emulator, and iterates until it passes.

## Setup (one-time)

```bash
# Clone and build the MCP server
git clone https://github.com/slapglif/maestro-mcp.git
cd maestro-mcp/mcp
pnpm install && pnpm build
```

Add to Claude Code's MCP config (`~/.claude/settings.json` or project `.claude/settings.json`):

```json
{
  "mcpServers": {
    "maestro": {
      "command": "node",
      "args": ["/absolute/path/to/maestro-mcp/mcp/dist/index.js"]
    }
  }
}
```

Maestro CLI itself is installed automatically on first use if not present.

**Prerequisites:** Node.js 18+, Android SDK (for Android) or Xcode (for iOS), a running
emulator/simulator or connected device.

## Core Workflow

### 1 — Generate a flow from natural language

Tell Claude what the flow should do:

> "Generate a Maestro flow for com.example.app that logs in with test@example.com / secret, then
> navigates to the Orders tab and asserts the first order is visible."

Claude uses the `flow-generator` agent to produce valid YAML tied to Maestro's command syntax,
then saves it to your flows directory.

### 2 — Run and observe

```
Run flows/login.yaml on the connected Android device
```

Claude executes the flow and streams the result. On failure it automatically:
1. Captures a screenshot of the failure frame.
2. Dumps the current UI hierarchy (CSV of element IDs, text, bounds).
3. Cross-references the hierarchy with the failing step and proposes a corrected selector.

### 3 — Explore interactively

For exploratory sessions — no YAML needed:

> "Tap the Sign Up button, enter 'qa+test@example.com' in the email field, then assert the
> confirmation screen is visible."

Claude drives the live device step-by-step through direct tool calls (`tap`, `inputText`,
`assertVisible`, etc.).

## Tool Categories Available to Claude

| Category | What Claude can do |
|---|---|
| **Flow execution** | Run flows, validate YAML, upload to Maestro Cloud |
| **Device control** | List devices, capture screenshot, record screen |
| **App lifecycle** | Launch/stop app, clear state + keychain, install APK/IPA |
| **UI interactions** | Tap, swipe, scroll, input text, press keys, open deep link |
| **Assertions** | Check visibility, wait for element, extract text |
| **System** | Toggle orientation, airplane mode, run in-app JavaScript |
| **AI assertions** | `assertWithAI` / `extractTextWithAI` for canvas/custom UI |

## Debugging Broken Tests

When a flow fails:

```
The checkout.yaml flow is failing on step "tapOn: checkout__confirm-button".
Inspect the current screen hierarchy and suggest the correct selector.
```

Claude will:
1. Call `inspect-hierarchy` to get the live element tree.
2. Search for the element by label, text, or resource-id.
3. Propose the corrected `id:` or `text:` value and update the YAML.

## Building a Regression Suite at Scale

The approach that produced 30+ flows in three afternoons (real-world report):

1. List your critical user flows in plain English (one sentence each).
2. Ask Claude to generate YAML for all of them in sequence.
3. Run the full suite: `maestro test flows/` — note failures.
4. For each failure, paste the error and ask Claude to fix the selector.
5. Add edge cases Claude surfaces (e.g., button hidden behind keyboard in landscape).

## Anti-Patterns

```
❌ Don't ask Claude to generate a flow without a running emulator — 
   it can't verify selectors without a live hierarchy.

❌ Don't skip validation after generation:
   maestro validate flows/my-flow.yaml  # always validate before committing

✓ Keep MCP sessions short for exploratory work; save the generated YAML 
  to your flows/ directory before ending the session.
```

## Sources

- [slapglif/maestro-mcp — GitHub README](https://github.com/slapglif/maestro-mcp)
- [Maestro MCP: An Introduction — maestro.dev blog](https://maestro.dev/blog/maestro-mcp-an-introduction)
- [Maestro MCP + Claude: AI-Powered Mobile UI Test Automation — Very Good Ventures](https://verygood.ventures/blog/maestro-mcp-claude-mobile-ui-test-automation/)
- [Stop Manual Testing! Claude Code + Maestro MCP — Medium/@tentenco](https://medium.com/@tentenco/stop-manual-testing-how-claude-code-maestro-mcp-disrupt-app-dev-dfd1a2d6425c)
- [Maestro MCP For Mobile Test Automation — getpanto.ai](https://www.getpanto.ai/blog/maestro-mcp-mobile-test-automation)
