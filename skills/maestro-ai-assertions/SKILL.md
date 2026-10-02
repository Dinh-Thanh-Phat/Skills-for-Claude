---
name: maestro-ai-assertions
description: |
  Maestro's three LLM-powered assertion commands for mobile UI testing: assertWithAI (natural-language visual validation), extractTextWithAI (screen text extraction to variable), and assertNoDefectsWithAI (automatic UI defect detection — clipped text, overlaps). Use when standard element-based assertions are insufficient, when testing dynamic/generated content, CAPTCHA, OTP screens, or running visual smoke checks.
  Triggers on: "assertWithAI", "extractTextWithAI", "assertNoDefectsWithAI", "maestro AI assertion", "maestro visual assertion", "LLM assertion mobile", "maestro CAPTCHA", "maestro OTP test", "AI mobile test command".
---

# Maestro AI Assertion Commands

Maestro ships three LLM-powered commands for scenarios where element selectors can't reach what you need to assert. All three are **experimental** — `optional: true` by default, meaning a failure is logged but does not stop the flow. Set `optional: false` to make them blocking.

---

## 1 — `assertWithAI`

Takes a screenshot of the current screen and asks an LLM whether the natural-language assertion is true. Returns `pass` / `fail`.

**Use when:** The assertion requires reasoning about visual layout or dynamic content that has no stable element ID — OTP prompts, CAPTCHA, rendered chart labels, conditionally composed UI.

```yaml
# Minimal form — assertion string directly
- assertWithAI: "A 6-digit two-factor authentication input is visible"

# Map form — add optional: false to fail the flow on mismatch
- assertWithAI:
    assertion: "The checkout summary shows exactly 3 line items and a total amount"
    optional: false

# Multi-step example: login then assert OTP screen
- tapOn: "Sign in"
- assertWithAI:
    assertion: "An OTP prompt with space for 6 digits is visible on screen"
    optional: false
```

**Key rules:**
- Write assertions as declarative present-tense facts, not questions.
- Be specific — "3 line items" is better than "some items".
- Default `optional: true` lets the flow continue on failure; logs the result in the run report.
- Requires Maestro Cloud authentication (free account is enough) — there is no local/bring-your-own LLM option. See Configuration below.
- Reports: `~/.maestro/tests/<timestamp>/ai-(<flow name>).json` + `ai-report-(<flow name>).html`.

---

## 2 — `extractTextWithAI`

Takes a screenshot and uses an LLM to extract a text value matching your query. Stores the result in `${aiOutput}` (or a custom variable).

**Use when:** You need a dynamically generated value from the screen to use in subsequent steps — CAPTCHA text, OTP codes, confirmation numbers, search result titles.

```yaml
# Simple form — query as a string, output goes to ${aiOutput}
- extractTextWithAI: "The CAPTCHA value shown on screen"
- inputText: ${aiOutput}

# Map form — custom output variable
- extractTextWithAI:
    query: "The order confirmation number"
    outputVariable: confirmationCode
    optional: false
- tapOn: "Track order ${confirmationCode}"

# Extract and assert: get search result title, tap it
- extractTextWithAI: "Title of the first search result"
- tapOn: ${aiOutput}
```

**Key rules:**
- Frame the query as "The [thing] shown/visible on screen."
- Default `optional: true` — if LLM extraction fails, `${aiOutput}` may be empty; guard downstream steps.
- Combine with `runScript` if you need to transform the extracted value.

---

## 3 — `assertNoDefectsWithAI`

Takes a screenshot and runs it through a pre-built LLM prompt that checks for common UI defects: text/elements clipped at edges, overlapping components, items not centered in containers.

**Use when:** You want a visual smoke check without writing per-element assertions. Add it after navigating to a screen you want to certify "looks correct."

```yaml
# Basic usage — add to any flow after navigation
- tapOn: "Settings"
- assertNoDefectsWithAI:

# Explicit blocking mode
- assertNoDefectsWithAI:
    optional: false
```

**Output:** Generates an **HTML + JSON** report under `~/.maestro/tests/<timestamp>/` (same `ai-…` naming as `assertWithAI`). The "screenshot crops" detail is UNVERIFIED.

**Key rules:**
- Treat as a smoke check, not a pixel-perfect visual diff — it detects layout breakage, not minor spacing regressions.
- One invocation per screen state you want to certify; don't call it on every step.
- Requires Maestro Cloud AI backend.

---

## When to Use Which

| Scenario | Command |
|---|---|
| Assert something visually complex is present | `assertWithAI` |
| Read dynamic generated text for use in next step | `extractTextWithAI` |
| Certify a screen has no obvious layout defects | `assertNoDefectsWithAI` |
| Standard element is findable by ID/text/role | Use `assertVisible` / `assertTrue` instead |

---

## Configuration (AI Backend)

```yaml
# In your Maestro workspace config or via CLI flag:
# MAESTRO_CLOUD_API_KEY=<key> maestro test flow.yaml

# Or set locally for dev:
# export MAESTRO_AI_API_KEY=<your-openai-or-maestro-cloud-key>
```

Refer to [Maestro AI configuration docs](https://docs.maestro.dev/api-reference/configuration/ai-configuration) for provider setup.

---

## Sources
- [assertWithAI — Maestro Docs](https://docs.maestro.dev/reference/commands-available/assertwithai)
- [extractTextWithAI — Maestro Docs](https://docs.maestro.dev/reference/commands-available/extracttextwithai)
- [assertNoDefectsWithAi — Maestro Docs](https://docs.maestro.dev/api-reference/commands/assertnodefectswithai)
- [AI Features and MCP Server — DeepWiki / Maestro](https://deepwiki.com/mobile-dev-inc/Maestro/6.5-ai-features-and-mcp-server)
- [Advanced Maestro Testing: Event Validation & AI-Powered Test Generation — Trendyol Tech / Medium](https://medium.com/trendyol-tech/advanced-maestro-testing-event-validation-ai-powered-test-generation-0bb86f3ca481)
