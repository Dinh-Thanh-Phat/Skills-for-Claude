---
name: mcp-server-testing
description: Test an MCP (Model Context Protocol) server itself — as the system under test, not as a tool your agent calls. Covers in-memory unit testing (no transport), MCP Inspector's scriptable CLI mode for CI, schema-drift checks against tool contracts, and the MCP-specific security surface (token passthrough, confused deputy, tool poisoning). Distinct from playwright-mcp-server/maestro-mcp-workflow (those document consuming an MCP server as a tool); this is for verifying an MCP server you build or integrate is correct and safe. Triggers on: "test MCP server", "MCP Inspector", "mcp-inspector --cli", "MCP conformance", "test my mcp tool", "tool poisoning", "token passthrough mcp", "InMemoryTransport", "FastMCP test", "MCP server CI".
---

# Testing MCP Servers

Testing an MCP server means verifying the server itself — its tools, resources, prompts, and protocol behavior — not verifying an agent's use of someone else's MCP server. Three layers, cheapest first.

## Layer 1 — In-Memory Unit Tests (no transport, no subprocess)

Fastest feedback loop: connect a `Client` straight to the server object in the same process, skipping stdio/HTTP transport entirely.

**Python SDK (official `mcp` v2.x — `from mcp import Client`, `from mcp.server import MCPServer`):**
```python
from mcp import Client
from server import mcp          # the MCPServer instance itself — no process, no port

async with Client(mcp) as client:                 # Client(mcp, raise_exceptions=True) to surface server errors in tests
    result = await client.call_tool("add", {"a": 1, "b": 2})
    assert not result.is_error                    # a raising tool is a RESULT (is_error=True), not an exception
    assert result.structured_content == {"result": 3}
```

> `result.data == 3` is the **FastMCP** (jlowin `fastmcp`, now 4.x) client API, not the official
> SDK's — official v2 returns `content` (for the model), `structured_content` (for code) and
> `is_error`. Always assert `is_error` on negative-input cases.

**TypeScript SDK** uses the equivalent `InMemoryTransport` pair — connect a client and server transport to each other in-process instead of spawning a child. Use this tier for the bulk of your suite: assert on tool output shape, error responses for bad input, and resource/prompt content, all in milliseconds with no process spawn.

## Layer 2 — MCP Inspector: Interactive + Scriptable CLI

`@modelcontextprotocol/inspector` is the official dev tool for exercising a server end-to-end, over its real transport (stdio or HTTP), as three interfaces from one package:

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

For a fleet of servers or repeatable presets (fixtures for tools/resources/prompts/OAuth flows), use `--config path/to/config.json --server <name>` instead of ad-hoc args — this is how you turn a manual Inspector session into a versioned, CI-checked-in test fixture.

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
- https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md
- https://labs.cloudsecurityalliance.org/agentic/agentic-mcp-security-best-practices-v1/
