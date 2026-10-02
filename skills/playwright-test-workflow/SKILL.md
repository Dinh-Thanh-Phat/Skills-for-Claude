---
name: playwright-test-workflow
description: Orchestrate the full Playwright test creation workflow combining qa-test-generation (requirements → manual test cases → automation) with playwright-snapshot-parser (actual UI snapshot → verified selectors). Use this skill when starting a complete test creation session for a feature, when you want test cases AND automation written with verified selectors, when the user says "test this page from scratch", "full test workflow", "write complete tests for X", "generate tests with real selectors", or when you want to avoid guessed locators in automation code. This is the entry point for end-to-end test creation — it tells you which skill to use at each stage and how to pass data between them.
---

# Playwright Test Workflow — Orchestrator

This skill sequences `qa-test-generation` and `playwright-snapshot-parser` together into one coherent workflow. Each skill does one thing well; this workflow tells you when to use which and how data flows between them.

---

## The Problem This Solves

Without this workflow, automation tests end up with guessed locators:
```typescript
// ❌ Guessed — may never have existed in the DOM
await page.click('[data-testid="submit-btn"]');
await page.fill('[name="email"]', 'test@test.com');
```

With this workflow, locators are verified against actual UI before any test code is written.

---

## Step 0 — Coverage Filter + Behavior Inventory

**0a. Invoke `behavioral-coverage-matrix` để build behavior inventory trước.**
Không có inventory → không biết scope → không thể đảm bảo coverage.

**0b. Sau đó apply coverage filter** — với mỗi behavior trong inventory, hỏi:

> **"If this test is removed, would a real bug escape to production?"**
> → NO → Skip it. Don't write the test.
> → YES → Proceed to Step 1.

**Skip these — they don't catch real bugs:**
- Static labels, page titles, button text
- Layout, spacing, colors
- Elements with no business logic
- Flows already covered by unit tests

**Always test these:**
- User journeys that change data (create / edit / delete)
- Auth and permission boundaries
- Validation that blocks a bad state
- Cross-module effects (action in A must reflect in B)

---

## Full Workflow (4 Steps)

```
STEP 0: Coverage filter                    [ask the filter question — skip non-value tests]
STEP 1: Requirements → Manual Test Cases   [skill: qa-test-generation Phase 1]
STEP 2: Review + UI Snapshot              [user action + Playwright command]
STEP 3: Snapshot → Selector Map           [skill: playwright-snapshot-parser Step 6]
STEP 4: Selector Map + Tests → Automation [skill: qa-test-generation Phase 2 Path A]
```

---

## Step 1 — Generate Manual Test Cases

> **Pre-step:** Trước khi invoke `qa-test-generation`, chạy `behavioral-coverage-matrix` để build behavior inventory. Nếu bỏ qua, test cases sẽ thiếu behaviors quan trọng.

**Invoke:** `behavioral-coverage-matrix` → sau đó `qa-test-generation`

**Input:** Feature requirements, user story, or a description of the page/workflow being tested

**What happens:**
- Generates comprehensive manual test cases (happy path, negative, edge cases, boundaries)
- Saves to `.md` file
- **Stops** and waits for user to review

**Gate:** Do NOT proceed to Step 2 until the user has reviewed the manual test cases and said "ok" / "confirmed" / "looks good".

---

## Step 2 — Take the Actual UI Snapshot

**Who does this:** The user (or Claude via Playwright MCP if available)

**What to run:**
```typescript
// (page.accessibility.snapshot() was removed in Playwright 1.57 — do not use)

// Option A: AI-mode snapshot with [ref=eN] (Playwright 1.59+) — best for selector extraction
const aiSnap = await page.ariaSnapshot({ mode: 'ai' });
console.log(aiSnap);

// Option B: Aria snapshot (Playwright 1.49+) — preferred for assertions, tree format
const snap = await page.locator('body').ariaSnapshot();
console.log(snap);

// Option C: Specific component only
const formSnap = await page.locator('form').ariaSnapshot();
console.log(formSnap);
```

**When to snapshot:**
- Take the snapshot while the page is in its **default loaded state** (before any actions)
- If testing a modal/dialog: open it first, then snapshot
- If testing a form with multiple states: snapshot each state separately

**Gate:** Paste the raw snapshot output into the chat before proceeding to Step 3.

---

## Step 3 — Parse Snapshot → Selector Map

**Invoke:** `playwright-snapshot-parser`

**Input:** The raw snapshot text pasted from Step 2

**Explicitly request:** "export selector map for test generation"

**What happens:**
- Parses all interactive elements
- Generates ranked selector options per element
- Produces accessibility report (critical issues and warnings)
- Outputs a `### SELECTOR MAP` block (Step 6 of the parser skill)

**Gate:** Before Step 4 — check the BLOCKED and CRITICAL A11Y sections:
- If there are CRITICAL A11Y issues affecting your test cases: pause and raise a11y bug tickets first
- BLOCKED elements cannot be automated — skip those test cases or create a bug ticket for the dev team
- If all critical elements have HIGH confidence selectors: proceed to Step 4

---

## Step 4 — Write Automation Using Verified Selectors

**Invoke:** `qa-test-generation` (Phase 2, Path A)

**Input:** The manual test cases from Step 1 + the `### SELECTOR MAP` block from Step 3

**What happens:**
- Each test step is matched to a Selector Map entry by Intent
- Automation code uses verified selectors — no guesses
- BLOCKED elements get `// BLOCKED` comments instead of broken selectors
- A11y warnings become inline `// A11Y BUG` comments
- **Cleanup hooks added for every test that creates persistent data** (see Step 4b)

**Output:** Complete `.spec.ts` test file, ready to run

---

## Step 4b — Add Cleanup for Every Data-Creating Test (MANDATORY)

**Invoke:** `test-data-lifecycle` (to select correct strategy)

For every test case that creates persistent data (records, accounts, items), the generated automation MUST include `test.afterEach()` cleanup. Never rely on end-of-test-body cleanup — it does not run when the test fails.

```typescript
// Pattern — required for any test creating real data
test.describe('[Feature Name]', () => {
  let createdItemName: string; // declared outside test so afterEach can access it

  test.afterEach(async ({ page }) => {
    if (createdItemName) {
      // Prefer API: await page.request.delete(`/api/items/${createdItemName}`).catch(() => {});
      // Fallback UI: navigate → find → delete
      createdItemName = '';
    }
  });

  test('TC-001: Create item', async ({ page }) => {
    createdItemName = `AT-TC001-${Date.now()}`; // assign early so afterEach can clean up even on failure
    // ... test steps
  });
});
```

**Gate:** Before calling Step 4 complete — confirm that every test case with `Creates:` or `Deletes:` in its manual spec has a corresponding `afterEach` cleanup block.

---

## Decision Tree — When to Skip Steps

```
Have requirements?
  YES → Start at Step 1
  NO  → Ask user for requirements before anything

Have manual test cases already (user provides .md)?
  YES → Skip Step 1, go to Step 2
  NO  → Step 1

Have the actual UI built and accessible?
  YES → Take snapshot (Step 2)
  NO  → Write automation with UNVERIFIED comments (qa-test-generation Path B)
        Come back and validate when UI is ready

Have an existing snapshot (user pastes it)?
  YES → Skip Step 2, go to Step 3
  NO  → Step 2
```

---

## Handling Conflicts Between Steps

### Conflict: Test case expects a button but snapshot has no matching element

**Scenario:** TC-003 says "click the Save Draft button" but no such button appears in the Selector Map.

**Resolution:**
1. Search the snapshot parser output — did the button parse under a different name?
2. If genuinely missing: note `// MISSING: 'Save Draft' button not found in snapshot — verify page state`
3. Ask user: "Was the page in the right state when you took the snapshot?"

### Conflict: Selector Map has element but test case intent is ambiguous

**Scenario:** Selector Map has `submit login` and `submit registration` but test case just says "submit form".

**Resolution:**
- Look at the test case context to determine which form
- Use the scoped selector from the map
- Rename the test case step to be specific: "submit the login form"

### Conflict: A11y issue makes selector LOW confidence

**Scenario:** Selector Map shows `password input` with confidence LOW + `A11y Warning: placeholder only, no label`.

**Resolution:**
- Use the map's selector anyway (it's the best available)
- Add comment: `// A11Y BUG: no <label> — selector may break if placeholder text changes`
- File the a11y issue as a bug, not just a warning

---

## Output Checklist

Before calling the workflow complete, verify:

- [ ] Manual test cases reviewed and confirmed by user
- [ ] Snapshot taken from actual running UI (not mocked)
- [ ] All CRITICAL A11Y issues documented (even if not fixed yet)
- [ ] All BLOCKED elements have `// BLOCKED` comments in test code (not silently skipped)
- [ ] No locators with `[data-testid=...]` guesses or `[name=...]` guesses — only verified selectors or UNVERIFIED comments
- [ ] Test file runs without import errors
- [ ] Every test that creates persistent data has `test.afterEach()` cleanup (not end-of-body cleanup)

---

## Quick Reference — Which Skill for What

| Task | Use Skill |
|------|-----------|
| Generate test cases from requirements | `qa-test-generation` Phase 1 |
| Take and interpret a UI snapshot | `playwright-snapshot-parser` |
| Export verified selectors for test writing | `playwright-snapshot-parser` Step 6 |
| Write automation with verified selectors | `qa-test-generation` Phase 2 Path A |
| Write automation without snapshot (fallback) | `qa-test-generation` Phase 2 Path B |
| Debug a failing locator | `playwright-snapshot-parser` Step 5 |
| Full workflow from zero | `playwright-test-workflow` (this skill) |

---

## Three Workflow Scenarios

### Scenario A — Test-First Development
> Use when: You have requirements but the UI may or may not be built yet.

```
Requirements → Manual Tests [GATE: review] → Snapshot → Selector Map → Automation
```

**Step-by-step:**

| # | Action | Skill | Input | Output |
|---|--------|-------|-------|--------|
| 1 | Fill requirements template | — | Feature description | `templates/requirements.md` |
| 2 | Generate manual test cases | `qa-test-generation` Phase 1 | requirements.md | `data/outputs/test-cases-{feature}-{date}.md` |
| 3 | **GATE: User reviews and confirms** | — | — | — |
| 4 | Capture UI snapshot | `scripts/take-snapshot.ts` | URL | `data/outputs/snapshots/{feature}-snapshot.txt` |
| 5 | Parse snapshot → Selector Map | `playwright-snapshot-parser` Step 6 | snapshot.txt | `### SELECTOR MAP` block |
| 6 | Write automation (Path A) | `qa-test-generation` Phase 2 | test-cases.md + Selector Map | `tests/{feature}.spec.ts` |
| 6a | Add afterEach cleanup for data-creating tests | `test-data-lifecycle` | spec file | updated spec with cleanup hooks |
| 7 | Run and verify | `npx playwright test` | spec file | pass/fail |

**Shell script (nếu có):** `bash scripts/scenario-a.sh <feature> <url>`

> ⚠️ Scripts này chỉ tồn tại trong một số projects. Nếu không có → thực hiện từng step thủ công theo bảng trên. Không cần scripts để follow workflow.

**Example E2E — FCCX Login:**
```bash
bash scripts/scenario-a.sh "login" "https://exchange.fccx.io/signin"
# Step 1: Fill requirements.md for login feature
# Step 2 (Claude): Generate manual tests → data/outputs/test-cases-login-20260427.md
# Step 4 (auto): Snapshot → data/outputs/snapshots/login-snapshot.txt
# Step 5 (Claude): Parse → SELECTOR MAP with Log in / Sign Up selectors
# Step 6 (Claude): Automation → tests/login.spec.ts
```

Resulting test uses verified selectors:
```typescript
// ✅ Verified from snapshot — not guessed
await page.getByRole('banner').getByRole('link', { name: 'Log in' }).click();
```

---

### Scenario B — Snapshot-First Development
> Use when: UI already exists and you need tests for it. Start from what's actually there.

```
Snapshot → Extract All Elements + Selector Map → Generate Test Cases [GATE: review] → Automation
```

**Step-by-step:**

| # | Action | Skill | Input | Output |
|---|--------|-------|-------|--------|
| 1 | Capture snapshot (or use existing) | `scripts/take-snapshot.ts` | URL or existing file | `data/outputs/snapshots/{feature}-snapshot.txt` |
| 2 | Full parse: elements + Selector Map + a11y report | `playwright-snapshot-parser` all steps | snapshot.txt | Element list + `### SELECTOR MAP` block |
| 3 | Generate test cases based on actual UI | `qa-test-generation` Phase 1 | Selector Map (as context) | `data/outputs/test-cases-{feature}-{date}.md` |
| 4 | **GATE: User reviews test cases** | — | — | — |
| 5 | Write automation (Path A, Map from Step 2) | `qa-test-generation` Phase 2 | test-cases.md + Selector Map | `tests/{feature}.spec.ts` |
| 6 | Run and verify | `npx playwright test` | spec file | pass/fail |

**Key difference from Scenario A:** Selector Map is produced in Step 2, before test cases are written — so test generation in Step 3 knows EXACTLY which elements exist.

**Shell script:** `bash scripts/scenario-b.sh <feature> <url>`
Or with existing snapshot: `bash scripts/scenario-b.sh <feature> --snapshot=data/outputs/snapshots/fccx-snapshot.txt`

**Example E2E — FCCX Homepage (using the tree you provided):**
```bash
bash scripts/scenario-b.sh "fccx-homepage" --snapshot=data/outputs/snapshots/fccx-snapshot.txt
# Step 2 (Claude): Parse → found 16 interactive elements, 3 CRITICAL a11y issues
# Step 3 (Claude): Generate tests → exchange table, nav links, Log in / Sign Up flow
# Step 5 (Claude): Automation → tests/fccx-homepage.spec.ts
```

---

### Scenario C — Debug & Fix
> Use when: A test is failing. You need to understand why the selector broke and fix it.

```
Capture Failure → Fresh Snapshot → Diagnose (Selector Debugger) → Fix → Re-run
```

**Step-by-step:**

| # | Action | Skill | Input | Output |
|---|--------|-------|-------|--------|
| 1 | Run failing test, capture output | `npx playwright test` | spec file | `data/outputs/debug/{feature}-failure.log` |
| 2 | Fill debug report template | — | failure log + failing selector | `templates/debug-report.md` |
| 3 | Capture fresh snapshot of current UI | `scripts/take-snapshot.ts` | URL | `data/outputs/snapshots/{feature}-debug.txt` |
| 4 | Diagnose: why does the selector fail? | `playwright-snapshot-parser` Step 5 | snapshot + failing selector | Diagnosis + alternatives |
| 5 | Apply fix to spec file | — | suggested selector | Updated `tests/{feature}.spec.ts` |
| 6 | Re-run to verify fix | `npx playwright test` | spec file | must pass |

**Shell script:** `bash scripts/scenario-c.sh <spec-file> <url>`

**Example E2E — FCCX Exchange Table:**
```
Failing: page.getByRole('combobox', { name: 'Currency' })
Error:   strict mode violation — no element matches

Step 3: Fresh snapshot taken
Step 4 (Claude diagnosis):
  Tree shows: combobox [ref=e156] — NO accessible name
  Problem: The combobox has no aria-label. 'Currency' doesn't exist in the tree.
  Fix option 1: page.getByRole('combobox')  // only combobox on page — fragile
  Fix option 2: // BLOCKED until dev adds aria-label="Currency"
  A11y bug to file: combobox [ref=e156] missing accessible name

Step 5: Update spec with LOW confidence fallback + bug comment:
  page.getByRole('combobox')  // A11Y BUG: missing aria-label — ticket #XXX
```

---

## File I/O Summary

```
data/outputs/
├── test-cases-{feature}-{date}.md       ← Phase 1 output
├── selector-map-{feature}.md            ← Snapshot parser output (Step 6)
├── snapshots/
│   ├── {feature}-snapshot.txt           ← Raw aria snapshot
│   └── {feature}-debug-{datetime}.txt   ← Debug snapshot (Scenario C)
└── debug/
    ├── {feature}-failure-{datetime}.log ← Test failure output
    └── {feature}-debug-{datetime}.md    ← Debug report

tests/
└── {feature}.spec.ts                    ← Final automation output
```

---

## Skill Trigger Map (Manual vs Automatic)

| Step | Trigger Type | How to trigger |
|------|-------------|----------------|
| Take snapshot | **Manual** — run script | `npx tsx scripts/take-snapshot.ts <url> <output>` |
| Parse snapshot | **Manual** — invoke Claude | "Parse this snapshot + export selector map" |
| Generate manual tests | **Manual** — invoke Claude | Skill `qa-test-generation` with requirements |
| Generate automation | **Manual** — invoke Claude | "Phase 2" after confirming test cases |
| Debug selector | **Manual** — invoke Claude | Paste snapshot + failing selector |
| Full scenario | **Script-guided** | `bash scripts/workflow.sh` |

No steps are fully automatic — every Claude step requires human review at the gate before continuing. This is intentional: automation without human-reviewed test logic produces tests that always pass but prove nothing.

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/workflow.sh` | Interactive menu — pick scenario A/B/C |
| `scripts/scenario-a.sh <feature> <url>` | Test-First end-to-end |
| `scripts/scenario-b.sh <feature> <url>` | Snapshot-First end-to-end |
| `scripts/scenario-c.sh <spec> <url>` | Debug & Fix end-to-end |
| `scripts/take-snapshot.ts` | Playwright snapshot capture utility |

## Templates Reference

| Template | Use |
|----------|-----|
| `templates/requirements.md` | Scenario A input — describe feature before test generation |
| `templates/debug-report.md` | Scenario C input — describe the failure before diagnosis |
| `templates/selector-map-output.md` | Output template — fill after snapshot parser Step 6 |
