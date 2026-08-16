---
name: mcp-server-testing
description: >-
  Test an MCP (Model Context Protocol) server itself — as the system under test, not as a tool
  your agent calls. Covers in-memory unit testing (no transport), MCP Inspector's scriptable CLI
  mode for CI, schema-drift checks against tool contracts, and the MCP-specific security surface
  (token passthrough, confused deputy, tool poisoning). Distinct from
  playwright-mcp-server/maestro-mcp-workflow (those document consuming an MCP server as a tool);
  this is for verifying an MCP server you build or integrate is correct and safe. Covers Inspector
  v2's CLI breaking changes from v1 (target ordering, exit codes, --catalog vs --config). Triggers
  on: "test MCP server", "MCP Inspector", "mcp-inspector --cli", "MCP conformance", "test my mcp
  tool", "tool poisoning", "token passthrough mcp", "InMemoryTransport", "FastMCP test", "MCP
  server CI", "MCP Inspector v2", "inspector v1 to v2".
---

# Testing MCP Servers

Testing an MCP server means verifying the server itself — its tools, resources, prompts, and protocol behavior — not verifying an agent's use of someone else's MCP server. Three layers, cheapest first.

## Layer 1 — In-Memory Unit Tests (no transport, no subprocess)

Fastest feedback loop: connect a `Client` straight to the server object in the same process, skipping stdio/HTTP transport entirely.

**Python SDK:**
```python
async with Client(mcp) as client:
    result = await client.call_tool("add", {"a": 1, "b": 2})
    assert result.data == 3
```

**TypeScript SDK** uses the equivalent `InMemoryTransport` pair — connect a client and server transport to each other in-process instead of spawning a child. Use this tier for the bulk of your suite: assert on tool output shape, error responses for bad input, and resource/prompt content, all in milliseconds with no process spawn.

## Layer 2 — MCP Inspector: Interactive + Scriptable CLI

`@modelcontextprotocol/inspector` is the official dev tool for exercising a server end-to-end, over its real transport (stdio or HTTP), as three interfaces from one package. **As of v2.0.0 (July 28, 2026) this is a ground-up rewrite** — same package name and `npx` entry point, but the CLI surface changed in ways that silently break naive CI scripts (see "V2 CLI Gotchas" below). v1 is deprecated (security fixes only); pin `npx @modelcontextprotocol/inspector@v1-latest` if you must stay on it. v2 requires Node `>=22.19.0`.

```bash
npx @modelcontextprotocol/inspector          # web UI — manual exploration
npx @modelcontextprotocol/inspector --cli    # scriptable CLI — CI / automation
npx @modelcontextprotocol/inspector --tui    # terminal UI
```

The `--cli` mode is the one that matters for QA/CI — it's a real MCP client that spawns your server as a subprocess (or connects over HTTP) and drives one JSON-RPC method per invocation:

```bash
# List tools
npx @modelcontextprotocol/inspector --cli node build/index.js --method tools/list

# Call a tool — key=value args
npx @modelcontextprotocol/inspector --cli node build/index.js \
  --method tools/call --tool-name mytool \
  --tool-arg key=value --tool-arg another=value2

# Call a tool — JSON-valued arg, or all args as one JSON blob
npx @modelcontextprotocol/inspector --cli node build/index.js \
  --method tools/call --tool-name mytool \
  --tool-arg 'options={"format": "json", "max_tokens": 100}'
# --tool-args-json '{"zip":"10001"}'   # alternative: single JSON object

# Resources / prompts
npx @modelcontextprotocol/inspector --cli node build/index.js --method resources/list
npx @modelcontextprotocol/inspector --cli node build/index.js \
  --method resources/read --uri resource_uri_here
npx @modelcontextprotocol/inspector --cli node build/index.js \
  --method prompts/get --prompt-name promptname --prompt-args key=value

# Remote server over HTTP, with auth header
npx @modelcontextprotocol/inspector --cli https://my-mcp-server.example.com \
  --transport http --header "X-API-Key: your-api-key" --method tools/list
```

**CI-friendly output**: add `--format json` and pipe to `jq` for assertions —
```bash
npx @modelcontextprotocol/inspector --cli node build/index.js \
  --method tools/list --format json | jq '.result.tools | length'
```

**Exit codes** (check these in CI instead of parsing text):

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Usage / unexpected error |
| 2 | No MCP app found |
| 3 | Authentication required |
| 4 | Server unreachable |
| 5 | Tool error or not found |

Non-zero exits also write a JSON error envelope to stderr (`code`, `message`, `status`, `url`) — assert on that envelope rather than screen-scraping human text.

For a fleet of servers or repeatable presets (fixtures for tools/resources/prompts/OAuth flows), use `--config path/to/config.json --server <name>` instead of ad-hoc args — this is how you turn a manual Inspector session into a versioned, CI-checked-in test fixture. **`--config` is read-only** in v2 — it errors if the file is missing and the Inspector never writes to it, which is what you want for a checked-in CI fixture. `--catalog <path>` is the separate, writable-by-the-Inspector variant (auto-created/seeded if missing, editable from the web UI) — reach for it only when you want the Inspector itself to manage the server list. The two flags are mutually exclusive with each other and with an ad-hoc target.

### V2 CLI Gotchas for CI (breaking changes from v1, verified against the v1→v2 migration guide)

- **The target must come first, with no flags in between, or it's silently dropped.** v2 reads the leading run of non-dash tokens as the server target; the first `--flag` ends that run. `--cli node build/index.js --method tools/list` works; `--cli --method tools/list node build/index.js` does **not** error — it silently discards the target and falls back to your default catalog, so the check appears to pass while quietly running against the wrong server. Always put the target (command or URL) immediately after `--cli`, before any other flag.
- **`--` reverses meaning under `--cli`.** On the web/TUI clients, everything after `--` goes to the target (same as v1). Under `--cli` it's the opposite: everything *before* `--` is the target (and its own flags), everything *after* is the Inspector's own options — e.g. `mcp-inspector --cli node build/index.js --server-flag -- --method tools/list`. Needed only when the target itself takes dash-prefixed flags.
- **A failing tool call now exits non-zero.** v1 exited `0` even when a `tools/call` came back `isError: true` (the RPC succeeded even though the tool failed). v2 exits `5` for `isError: true` or a not-found tool. A CI step chaining `inspector --cli … --method tools/call … && next-step` that silently continued past a failing tool in v1 will now correctly stop in v2 — expect this to surface as "v2 broke my pipeline" the first time it catches a real, previously-masked failure. Parse the failure via `2>&1 | tail -1 | jq .error`, not by matching stdout prose.
- **Ambiguous URLs no longer guess a transport.** With no `--transport`, v2 infers it *only* from an exact `/mcp` or `/sse` URL path suffix; anything else (including a trailing slash) now errors with `Transport type not specified and could not be determined from URL`, where v1 silently fell back to SSE. Pass `--transport http` or `--transport sse` explicitly for any server whose URL doesn't end in one of those two suffixes.
- **New CLI-only methods**: `initialize` (connect-only probe returning `serverInfo`/`protocolVersion`/`capabilities`/`instructions` — a cheap connectivity smoke test), `servers/list` / `servers/show` (read the catalog/config without connecting to anything, redacting secret-bearing fields).
- **OAuth for CI**: v1's CLI had no OAuth support at all. v2 adds `--stored-auth-only` — never opens a browser or waits on the interactive loopback callback, fails fast with `auth_required` if no token is already in the shared store (`~/.mcp-inspector/storage/oauth.json`). This is the flag to reach for when a fixture server requires auth in a headless pipeline.

## Layer 3 — Schema-Drift and Security Checks

**Schema drift**: a tool's declared JSON-schema input contract silently diverging from what the handler actually accepts/returns breaks LLM tool routing without touching business logic. Snapshot `tools/list` output (via `--format json`) in CI and diff it against a committed baseline — any unreviewed shape change should fail the build, the same discipline `playwright-snapshot-parser` applies to UI snapshots.

**MCP-specific security surface** (test these explicitly, they're not generic web-app bugs):
- **Token passthrough** — a server MUST NOT accept a token that wasn't issued specifically for it. Test by presenting a token minted for a different audience/resource and asserting rejection, not silent forwarding.
- **Confused deputy** — a server acting on a client's behalf with its own elevated credentials; test that a tool call can't be used to make the server perform an action the *calling client* isn't itself authorized for.
- **Tool poisoning** — malicious or drifted tool descriptions that steer an LLM into unintended calls; diff tool `description` fields the same way you diff schemas.
- **SSRF via tool args** — any tool that accepts a URL/host argument should be fuzzed with internal/link-local targets (`169.254.169.254`, `localhost`, RFC1918 ranges) and asserted to reject or explicitly allow-list them.

Token handling additionally requires expiration/rotation enforcement on the server side — a Layer 2 CLI check against an expired or wrong-audience token should return exit code 3.

## What This Is Not

- **Not** `playwright-mcp-server` / `maestro-mcp-workflow` — those document *consuming* a first-party MCP server as an automation tool. This skill is for testing an MCP server (yours, or a third party's) as the thing under test.
- **Not** `llm-red-teaming` — that skill red-teams an LLM/chatbot's *conversational* output (jailbreaks, prompt injection into the model). MCP server testing is protocol/contract/transport-level, closer to API testing than to LLM-judge evaluation, though the two overlap where a tool-poisoning payload is itself a prompt-injection vector.
- **Not** a conformance certification — as of this writing the MCP spec's official conformance test-suite is roadmapped but not yet shipped; Inspector's CLI mode is the closest available tool for protocol-level checks today.

## Sources
- https://github.com/modelcontextprotocol/inspector
- https://raw.githubusercontent.com/modelcontextprotocol/inspector/main/clients/cli/README.md
- https://raw.githubusercontent.com/modelcontextprotocol/inspector/main/docs/v1-to-v2-migration.md
- https://github.com/modelcontextprotocol/inspector/releases
- https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md
- https://labs.cloudsecurityalliance.org/agentic/agentic-mcp-security-best-practices-v1/
