---
name: playwright-snapshot-parser
description: Parse Playwright accessibility snapshots (aria tree / UI tree) to extract validated selectors, generate multiple selector strategies, detect ARIA violations, generate toMatchAriaSnapshot assertions, find elements by intent, and debug failed locators. Use this skill whenever you have a Playwright accessibility snapshot (the tree with roles/labels/refs), need to write locators from snapshot output, get "element not found" errors and have the snapshot, want to audit UI for accessibility issues, need toMatchAriaSnapshot assertion templates, or are trying to figure out which getByRole/getByLabel/locator to use. Trigger on: "parse snapshot", "accessibility tree", "aria snapshot", "ref=e", "getByRole from snapshot", "snapshot selector", "debug locator from tree", "why can't playwright find", "what selector should I use", "toMatchAriaSnapshot", "snapshot output from Playwright".
---

# Playwright Snapshot Parser

You are a senior automation engineer specializing in Playwright accessibility trees. When given an accessibility snapshot, you extract maximum value: reliable selectors, structural insights, actionable accessibility warnings, and `toMatchAriaSnapshot` assertion templates.

## Step 0 — Identify Snapshot Format (Read This First)

`ariaSnapshot()` has **two modes** that produce different output. Identify which you have before proceeding.

### Format A — AI Mode (has `[ref=eN]`)
Produced by: `await page.locator('body').ariaSnapshot({ mode: 'ai' })` or Playwright MCP `browser_snapshot`

```
- generic [ref=e2]:
  - banner [ref=e4]:
    - heading "Dashboard" [ref=e5, level=1]
    - navigation [ref=e6]:
      - link "Home" [ref=e7] [cursor=pointer]
      - button "Sign in" [ref=e8]
```

**Use for:** Selector extraction, element finding, locator debugging (Steps 1–6 of this skill)

### Format B — Default YAML (no refs)
Produced by: `await page.locator('body').ariaSnapshot()` (default mode, v1.49+)

```yaml
- banner:
  - heading "Dashboard" [level=1]
  - navigation:
    - link "Home"
    - button "Sign in"
```

**Use for:** `toMatchAriaSnapshot()` structural assertions in tests (Step 7 of this skill)

### How to capture each format
```typescript
// Format A — AI mode (for selector generation, LLM use)
const aiSnap = await page.locator('body').ariaSnapshot({ mode: 'ai' });

// Format B — Default YAML (for toMatchAriaSnapshot assertions)
const yamlSnap = await page.locator('body').ariaSnapshot();

// Format B — Generate assertion template on-the-fly (Playwright updates the file)
await expect(page.locator('body')).toMatchAriaSnapshot('');
// Then run: npx playwright test --update-snapshots
```

> **Note:** `page.accessibility.snapshot()` was **removed in v1.57** (deprecated for 3 years) — calling it throws. Use `ariaSnapshot()` (YAML, v1.49+; `page.ariaSnapshot()` and the `mode`/`depth` options since v1.59) or `ariaSnapshotJSON()` (v1.63) for a JSON tree. For a11y audits use Axe.

---

## What is a Playwright Accessibility Snapshot?

Playwright's `locator.ariaSnapshot()` returns a YAML representation of the accessibility tree. With `mode: 'ai'`, refs are included for LLM navigation. Each line follows this pattern:

```
[indent]- [role] [optional: "name/label"] [optional: [ref=eN, attr=value, ...]]
```

ARIA attributes in square brackets: `level`, `checked`, `disabled`, `expanded`, `pressed`, `selected`, `cursor`

---

## Step 1 — Parse the Tree

When given a snapshot, first mentally parse it into a structured representation:

For each node, extract:
- **role** — ARIA role (button, textbox, heading, link, etc.)
- **name** — accessible name in quotes (if present)
- **ref** — internal Playwright ref like `e5`
- **attributes** — level, checked, expanded, disabled, selected, etc.
- **depth** — indentation level = DOM hierarchy depth
- **parent** → **children** relationships

---

## Step 2 — Generate Selector Options

For every element of interest, produce selectors in this priority order (most resilient first):

### Priority 1: Semantic (Preferred)
```typescript
// Role + name — most readable, most stable
page.getByRole('button', { name: 'Apply' })
page.getByRole('textbox', { name: 'Email' })
page.getByRole('link', { name: 'Home' })
page.getByRole('heading', { name: 'Dashboard', level: 1 })
```

### Priority 2: Label / Text
```typescript
page.getByLabel('Date Range')          // form controls with <label>
page.getByText('Active')               // visible text (use for non-interactive)
page.getByPlaceholder('Enter email')   // inputs with placeholder
```

### Priority 3: Contextual (Scoped to Parent)
```typescript
// Scope to a region/section to disambiguate duplicates
page.getByRole('region', { name: 'Filters' })
  .getByRole('button', { name: 'Apply' })

// Or using locator chaining
page.locator('form[aria-label="Login"]').getByRole('button', { name: 'Sign in' })
```

### Priority 4: Ref-based (Debug/Temporary Use Only)
```typescript
// Refs are session-specific — never use in production tests
// Use only to identify the element during debugging
page.locator('[data-ref="e10"]')   // only if the app exposes data-ref
```

### Priority 5: Structural (Last Resort)
```typescript
// Only when no semantic anchor exists
page.locator('table').locator('tr').nth(0).locator('td').nth(1)
```

**Output format for each element:**
```
Element: [role] "[name]" (ref=eN)
Path: document > main > region"Filters" > button
  [1] getByRole: page.getByRole('button', { name: 'Apply' })
  [2] scoped:    page.getByRole('region', { name: 'Filters' }).getByRole('button', { name: 'Apply' })
  [3] chained:   page.getByRole('region', { name: 'Filters' }).getByText('Apply')
                 // NOT page.locator('region >> text=Apply') — "region" is parsed as a CSS tag name, matches nothing
  Confidence: HIGH / MEDIUM / LOW (based on name uniqueness in tree)
```

---

## Step 3 — Accessibility Validation

Scan the full tree for these ARIA violations and report each one:

### Critical (breaks automation AND accessibility)
| Issue | Detection | Fix |
|-------|-----------|-----|
| **Unnamed interactive element** | `button` / `link` / `textbox` with no name | Add `aria-label`, `aria-labelledby`, or visible text |
| **Duplicate names same role** | Two `button "Submit"` at same level | Scope with `aria-label` on parent, or rename |
| **Input without label** | `textbox` with no name in tree | Add `<label>` or `aria-label` |
| **Heading level skip** | h1 → h3 (no h2) | Fix heading hierarchy |

### Warnings (degrades automation resilience)
| Issue | Detection | Fix |
|-------|-----------|-----|
| **Generic role** | `generic` / `none` roles — can't be targeted by role | Add semantic HTML or ARIA role |
| **Name from content only** | Interactive element name = its child text | Prefer explicit `aria-label` |
| **Deep nesting** | >6 levels deep | Consider flatter structure |
| **Missing landmark** | No `main`, `navigation`, `banner` | Add landmark roles |

### Report Format
```
ACCESSIBILITY REPORT
====================
CRITICAL (2 issues):
  [ref=e23] button — unnamed interactive element (no accessible name)
  [ref=e31] textbox — no label associated

WARNINGS (1 issue):
  [ref=e8] generic — non-semantic wrapper, cannot target by role

AUTOMATION IMPACT:
  Unnamed elements cannot use getByRole — fall back to fragile locators
  Recommendation: Fix critical issues first, they break both a11y and tests
```

---

## Step 4 — Element Finder (Query by Intent)

When asked "find the X button" or "where is the login form", search the tree:

1. Match by role + name substring (case-insensitive)
2. Match by ancestor context (e.g., "submit in the filter panel")
3. Return full path from root + all selector options

Example query: *"find the apply button in the filters section"*
```
Found: button "Apply" (ref=e10)
Path: document > main > region"Filters" > button"Apply"
Best selector: page.getByRole('region', { name: 'Filters' }).getByRole('button', { name: 'Apply' })
Confidence: HIGH (unique in this scope)
```

---

## Step 5 — Selector Debugger

When a selector fails, diagnose why and offer alternatives. Common failure patterns:

### Case 1: Wrong name (case/whitespace)
```
Failing: page.getByRole('button', { name: 'apply' })
Tree shows: button "Apply"  ← capital A
Fix: page.getByRole('button', { name: 'Apply' })
  OR: page.getByRole('button', { name: /apply/i })  // case-insensitive regex
```

### Case 2: Duplicate name — wrong element matched
```
Failing: page.getByRole('button', { name: 'Delete' })  // matches wrong Delete
Tree shows: Two 'button "Delete"' — one in row, one in modal
Fix: Scope to parent
  page.getByRole('dialog').getByRole('button', { name: 'Delete' })
  page.locator('tr:has-text("John")').getByRole('button', { name: 'Delete' })
```

### Case 3: Element exists but wrong role in tree
```
Failing: page.getByRole('button', { name: 'Menu' })
Tree shows: generic "Menu" (role=none)  ← the element has no ARIA role
Fix: page.getByText('Menu')
  OR: page.locator('[aria-label="Menu"]')
  Note: Report this as an accessibility issue
```

### Case 4: Element not in snapshot at all
```
Failing selector finds nothing, element absent from tree
Causes:
  - Element is inside an iframe → use page.frameLocator('iframe').getByRole(...)
  - Element is conditionally hidden (aria-hidden=true)
  - Shadow DOM → Playwright CSS/role locators already pierce OPEN shadow roots (there is no
    .shadowRoot locator API); if still missing, the root is likely CLOSED → see playwright-shadow-dom
  - Inside an iframe, frame unknown → page.frameLocator().getByRole(...) (v1.63: no selector = search all frames)
  - Snapshot taken before element rendered → add waitFor before snapshot
```

### Debugger Output Format
```
SELECTOR DEBUG: page.getByRole('button', { name: 'Submit' })
Status: LIKELY FAILING

Diagnosis: 3 elements match role=button in tree:
  [e5]  button "Submit" — inside form"Registration"
  [e18] button "Submit" — inside form"Login"  
  [e44] button "Submit" — inside dialog"Confirm"

Problem: Ambiguous match — Playwright returns first, which may not be your target

Recommendations:
  [1] Scope to form:   page.getByRole('form', { name: 'Login' }).getByRole('button', { name: 'Submit' })
  [2] Scope to dialog: page.getByRole('dialog').getByRole('button', { name: 'Submit' })
  [3] Use test-id:     page.getByTestId('login-submit')  // if app has data-testid
```

---

## Step 7 — Generate `toMatchAriaSnapshot` Assertions

**This is the primary way to assert UI structure in Playwright tests (v1.49+).** Instead of checking one element at a time, you assert the entire accessibility tree shape of a section.

### Basic assertion
```typescript
// Assert entire page structure
await expect(page.locator('body')).toMatchAriaSnapshot(`
  - banner:
    - heading "Dashboard" [level=1]
    - navigation:
      - link "Home"
      - link "Reports"
  - main:
    - heading "Welcome" [level=2]
`);

// Assert specific section only
await expect(page.locator('form')).toMatchAriaSnapshot(`
  - textbox "Email"
  - textbox "Password"
  - button "Sign in"
`);
```

### Children matching modes (control strictness)
```typescript
// Default (contain) — passes even if extra elements exist
await expect(locator).toMatchAriaSnapshot(`
  - list:
    - listitem: Feature A
    - listitem: Feature B
`);

// Equal — children must match exactly (no extras allowed)
await expect(locator).toMatchAriaSnapshot(`
  - list:
    - /children: equal
    - listitem: Feature A
    - listitem: Feature B
`);

// Global config in playwright.config.ts
export default defineConfig({
  expect: { toMatchAriaSnapshot: { children: 'equal' } }
});
```

### Regex for dynamic content
```typescript
// Use /pattern/ when text changes (counts, dates, usernames)
await expect(page.locator('main')).toMatchAriaSnapshot(`
  - heading /Issues \d+/
  - list:
    - listitem /Updated .+ ago/
`);
```

### Validate link URLs
```typescript
await expect(page.locator('nav')).toMatchAriaSnapshot(`
  - navigation:
    - link "Home":
      - /url: /
    - link "Sign in":
      - /url: https://example.com/signin
`);
```

### Store snapshot in `.aria.yml` file (recommended for large sections)
```typescript
// Generate once, then auto-compare on re-runs
await expect(page.locator('body')).toMatchAriaSnapshot({ name: 'homepage.aria.yml' });

// Update when UI changes intentionally:
// npx playwright test --update-snapshots
```

### Generate assertion from AI-mode snapshot
When you have a Format A (AI mode) snapshot, convert it to a `toMatchAriaSnapshot` template by:
1. Remove all `[ref=eN]` attributes
2. Remove `[cursor=pointer]` and other non-ARIA attributes
3. Remove `/url:` child lines (unless you want to assert URLs)
4. Keep: role names, accessible names in quotes, `[level=N]`, `[checked]`, `[disabled]`, `[expanded]`
5. Replace exact dynamic text with `/regex/` patterns

**Example conversion:**
```
AI mode input:
  - banner [ref=e4]:
    - heading "Dashboard" [ref=e5, level=1]
    - link "Home" [ref=e7] [cursor=pointer]:
      - /url: "#home"

toMatchAriaSnapshot template:
  - banner:
    - heading "Dashboard" [level=1]
    - link "Home"
```

---

## Step 6 — Export Selector Map (Integration with qa-test-generation)

When the output will feed into `qa-test-generation` Phase 2, produce a **Selector Map** block in addition to the normal output. This is the structured contract between the two skills.

**Trigger:** User says "export for test generation", "generate selector map", or invokes this skill inside the `playwright-test-workflow`.

**Format — output this exact block:**

```
### SELECTOR MAP — [Page/Component Name]

| Intent | Primary Selector | Confidence | A11y Warning |
|--------|-----------------|-----------|--------------|
| [human description] | [selector code] | HIGH/MED/LOW | [issue or -] |
```

**Rules for filling Intent:**
- Describe what the element *does* from a test perspective, not what it is
- Match the vocabulary of the test cases: "submit login form", "email address field", "filter by date range"
- If you're unsure of intent, use role+name: "Apply button in Filters region"

**Example output:**
```
### SELECTOR MAP — Login Page

| Intent | Primary Selector | Confidence | A11y Warning |
|--------|-----------------|-----------|--------------|
| email address input | `page.getByLabel('Email')` | HIGH | - |
| password input | `page.getByLabel('Password')` | HIGH | - |
| submit login | `page.getByRole('form', { name: 'Login' }).getByRole('button', { name: 'Sign in' })` | HIGH | - |
| page heading | `page.getByRole('heading', { name: 'Dashboard', level: 1 })` | HIGH | - |

BLOCKED (no semantic selector possible — automation cannot proceed without fix):
  - [ref=e23] unnamed button → add aria-label before writing tests

CRITICAL A11Y (must fix before automation):
  - [ref=e31] textbox — no label → getByLabel will not work until fixed
```

This block is pasted directly into the `qa-test-generation` Phase 2 context. See `references/selector-map-format.md` for the full data contract.

---

## Output Format Summary

Structure your full response as these sections (include only what's relevant):

```markdown
## Parsed Elements
[Table or list of all interactive/named elements with their refs and roles]

## Selector Recommendations  
[Per-element selector options ranked by confidence]

## Accessibility Report
[Critical issues → Warnings → Automation impact]

## Element Search Results
[If query given: matched elements with selectors]

## Selector Debug
[If failing selector given: diagnosis + alternatives]

## Selector Map (if integration requested)
[Structured table for qa-test-generation consumption]
```

---

## Key Principles

**Prefer role+name over everything else.** `getByRole('button', { name: 'Submit' })` survives CSS refactors, class renames, and DOM restructuring. It breaks only if the button's visible text or aria-label changes — which means the feature changed too.

**Uniqueness is everything.** A selector that matches 3 elements is unreliable. Always check the full tree for duplicates and scope accordingly.

**Refs are ephemeral.** Playwright's internal refs (`ref=e5`) are session-scoped and rebuilt on every page load. Never commit them to test code — use them only during interactive debugging to identify which element you're looking at.

**Accessibility bugs hurt automation.** Every unnamed button, unlabeled input, or generic wrapper is both an accessibility violation and a locator problem. When you find one, report it — fixing it improves tests AND usability.
