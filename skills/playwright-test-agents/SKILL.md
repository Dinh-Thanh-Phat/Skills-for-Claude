---
name: playwright-test-agents
description: |
  Playwright's official three-agent workflow for AI-assisted test creation and maintenance:
  Planner (explores the app, writes a Markdown test plan), Generator (converts the plan to
  executable .spec.ts files, verifies selectors live), and Healer (reruns failing tests,
  distinguishes regression from drifted locator, proposes repairs). Use when you want to:
  bootstrap E2E test coverage with AI from a running app, auto-fix selector drift without
  manually debugging, or understand the official Playwright agentic test workflow.
  Triggers on: "playwright test agents", "playwright init-agents", "playwright planner generator healer",
  "playwright ai test generation", "playwright ai test workflow", "playwright agent setup".
---

# Playwright Test Agents (Planner / Generator / Healer)

Playwright ships three official AI agents (v1.56+) that work as a **pipeline**: the Planner
explores the running app and writes a test plan, the Generator converts it to `.spec.ts` files,
and the Healer auto-repairs failing tests. All three are MCP-backed agent definitions — they
run inside your AI coding tool (Claude Code, VS Code Copilot, etc.).

---

## Prerequisites

- Playwright **v1.56+** (`npm install --save-dev @playwright/test`)
- A running local dev server (agents browse it live)
- A MCP-compatible coding tool: Claude Code, GitHub Copilot (VS Code ≥ 1.105), Codex, or OpenCode

---

## One-time Setup

```bash
# Generate agent definition files for your project
npx playwright init-agents --loop=claude        # Claude Code
npx playwright init-agents --loop=vscode        # GitHub Copilot (VS Code)
npx playwright init-agents --loop=codex         # Codex
npx playwright init-agents --loop=opencode      # OpenCode
```

What gets written (verified in playwright `lib/agents/generateAgents.js`):

| Loop | Agent definitions | MCP config |
|------|-------------------|------------|
| `claude` | `.claude/agents/planner.md`, `generator.md`, `healer.md` | `.mcp.json` |
| `vscode` | `.github/agents/*.agent.md` | `.vscode/mcp.json` |
| `opencode` | `.opencode/prompts/*.md` | opencode config |

Plus, if your test project has none, a default **seed test** (e.g. `tests/seed.spec.ts`) — the test the Planner runs first to get global setup, project dependencies, fixtures and hooks, and which it uses as the example for generated tests.

Conventional layout afterwards:

```
repo/
  .claude/agents/ (or .github/agents/)   # agent definitions
  specs/                                 # Markdown test plans (Planner output)
    basic-operations.md
  tests/                                 # generated tests (Generator output)
    seed.spec.ts
  playwright.config.ts
```

Regenerate whenever you update Playwright (`npm update @playwright/test && npx playwright init-agents --loop=<same loop>`).

---

## The Three Agents

### 1 — Planner

**What it does:** Runs the seed test (global setup, fixtures, hooks), browses the running app as a
user would, and writes a Markdown plan under `specs/` (e.g. `specs/checkout.md`) with numbered
scenarios, steps, and expected outcomes. Optional input: a PRD for context.

**Invoke:**

```
// In your coding agent (e.g. Claude Code), with tests/seed.spec.ts in context:
"Use the Playwright Planner to explore the checkout flow and write a test plan."
```

**Output — `specs/checkout.md` (example):**

```markdown
## Scenario 1: Guest checkout with valid card
1. Navigate to /products
2. Click "Add to cart" on "Widget Pro"
3. Click cart icon → "Proceed to checkout"
4. Fill shipping form (name, address, zip)
5. Enter card number 4242424242424242, exp 12/28, CVV 123
6. Click "Place order"
Expected: Order confirmation page with order number visible

## Scenario 2: Checkout with invalid card
...
```

**Tips:**
- Give the Planner a one-paragraph description of the app and the flow to cover.
- Let it run uninterrupted — it opens a real browser and navigates live.
- Review the plan before passing it to the Generator; edit any steps that shouldn't be automated.

---

### 2 — Generator

**What it does:** Reads a plan from `specs/`, generates `.spec.ts` files under `tests/`, and performs
each scenario live in a browser to verify selectors and assertions as it goes.

**Invoke:**

```
"Use the Playwright Generator to create tests from specs/checkout.md."
```

**Output:** executable `tests/**/*.spec.ts` files (header comments `// spec: specs/...` and
`// seed: tests/seed.spec.ts`), using `getByRole`, `getByLabel`, `getByText` locators verified
against the live page. Official docs note generated tests *may still include initial errors* — that
is what the Healer is for.

**What makes it different from Codegen:** The Generator verifies selectors by actually performing
each interaction — it won't emit a selector that doesn't work on the running app. Codegen records
without validation.

---

### 3 — Healer

**What it does:** Runs the test suite in debug mode, inspects failures (console logs, network
requests, ARIA snapshots), and proposes minimal repairs. It distinguishes:

- **Selector drift** (element moved / renamed) → heals with updated locator
- **Real regression** (functionality broken) → marks test as `test.skip` with a comment + stops healing

**Invoke:**

```
"Use the Playwright Healer to fix the failing tests."
```

**Healer decision logic:**

```
test fails
  ↓
Healer opens browser in debug mode
  ↓
Checks console errors + network tab + ARIA snapshot
  ↓
Element missing?  →  compare old/new ARIA snapshot  →  propose updated locator
  ↓
Functionality missing?  →  annotate with test.skip + regression note  →  stop
  ↓
Re-run to confirm fix
```

The Healer **never silently changes an assertion** to make a test pass — it only updates the
locator when the element exists but moved.

---

## End-to-End Workflow

```
1. Start dev server:   npm run dev   (or your equivalent)
2. Plan:               "Planner: explore the registration flow"
                        → produces test-plan.md
3. Review:             Edit test-plan.md if needed (remove or clarify steps)
4. Generate:           "Generator: create tests from test-plan.md"
                        → produces registration.spec.ts
5. Run:                npx playwright test registration.spec.ts
6. Heal (if failures): "Healer: fix failing tests in registration.spec.ts"
7. Commit:             tests/ directory → PR
```

Estimated first-time coverage for a typical 5-scenario flow: **~15–30 minutes end-to-end**.

---

## Decision Table: Agents vs Other Test Creation Methods

| Method | When to use |
|---|---|
| **Playwright Agents** (this skill) | Greenfield coverage: app is running, no tests exist yet |
| `playwright-mcp-server` | AI navigates the app for exploratory/ad-hoc tasks; not generating tests |
| `self-healing-test-automation` | Existing suite with selector drift; AI repair via Anthropic SDK |
| `playwright-bdd-gherkin` | Team uses Gherkin + product owners write scenarios |
| Manual authoring + POM | Fine-grained control over test structure; large existing suite |

---

## Anti-Patterns

```
❌  Running the Generator without reviewing the test plan first
    → Agent may generate tests for flows that shouldn't be automated (e.g., payment with real card)

❌  Invoking the Healer for every red test automatically
    → Healer marks real regressions as .skip — review skips weekly, don't let them pile up

❌  Forgetting to regenerate agents after a Playwright version bump
    → Agents encode the version's tool schema; stale agents may use deprecated tools

✓  Keep test-plan.md in version control — it's the spec artifact, not a temp file
✓  Seed file (seed.spec.ts) controls imports/fixtures across all generated tests — customize it
```

---

## Sources

- [Playwright Test Agents — official docs](https://playwright.dev/docs/test-agents)
- [Playwright Agents: Planner, Generator and Healer in Action — DEV Community](https://dev.to/playwright/playwright-agents-planner-generator-and-healer-in-action-5ajh)
- [Playwright Test Agents Guide 2026 — TestDino](https://testdino.com/blog/playwright-test-agents)
- [Playwright Test Agents — qaskills.sh guide](https://qaskills.sh/blog/playwright-test-agents-planner-generator-healer-guide)
- [Playwright Agents in Action — TestMu AI](https://www.testmuai.com/blog/playwright-agents/)
