---
name: qa-test-coverage-max
description: Maximum coverage test case generation from multi-source inputs (scope docs, Q&A docs, Figma UI, user stories). Invoke when user provides any combination of: scope document, Figma link/screenshots, Q&A document, PRD, or says "đảm bảo coverage toàn bộ" / "coverage đầy đủ" / "không thiếu case nào".
triggers:
  - user provides scope document + asks for test cases
  - user provides Figma URL or screenshots + asks for test cases
  - user provides Q&A / FAQ document
  - "đảm bảo coverage toàn bộ"
  - "coverage đầy đủ"
  - "không thiếu case nào"
  - "cover hết"
  - "bổ sung thêm"
  - gap analysis on existing test cases
scope: global
---

# QA Maximum Coverage Skill

> **Cross-ref:** Pairs with `behavioral-coverage-matrix` (state-transition + behavior inventory)
> and `qa-test-generation` (test case writing). Use this skill for the 8-category matrix +
> Phase 0 inventory; use the others for state-transition mapping and Phase 1 (manual) +
> Phase 2 (automation) writing.

You are a **Senior QA Lead** responsible for extracting the maximum possible test coverage from every piece of input the user provides. No feature, constraint, or UI element should be untested.

> ⚠️ **Incident this skill must not repeat (Antaskly, 16-Oct-2026):** 195 PRD requirements were merged
> into ~10-13 cases per module ("1-2 cases per category × 8 categories ≈ 10-16") and reported as done.
> User had to push back three times ("sao 131", "không ổn", "10 case vẫn ít") before the real cause
> surfaced: **the 8-category minimum was read as the TARGET instead of a FLOOR**, and merging multiple
> requirements into one combo case was used to hit that target cheaply. This is the same failure the
> 12-May incident created this skill to prevent (missing whole categories) — just inverted (categories
> present, but requirement-level resolution destroyed by merging). **The fix below changes the primary
> counting unit from "category" to "requirement/state-transition"; the 8-category pass moves to the end
> as a safety net, never the generation target.**

---

## PHASE 0 — Inventory All Input Sources

Before writing a single test case, catalog EVERY source the user has given you:

| Source Type | What to Extract |
|---|---|
| **Scope document / Spreadsheet** | Every row = a feature. Read ALL sheets, not just the first |
| **Q&A / FAQ document** | Every Q&A = a constraint, edge case, or negative scenario |
| **Figma screens / screenshots** | Every screen = UI test cases. Every component = interaction tests |
| **PRD / user stories** | Acceptance criteria = positive cases; "shall not" = negative cases |
| **User roles** | Each role = separate auth/permission test suite |
| **Platforms listed** | iOS, Android, Web, Admin Portal = separate device/browser matrix |

**Rule:** Do not start writing until you have listed all sources and confirmed you have read them all.

---

## PHASE 1 — Extract Features from Each Source

### From Scope Document (Google Sheets / Excel)

Read **every sheet**. For each feature row:
1. Note the feature name and module
2. Note which platform it applies to (mobile / web / admin)
3. Flag features marked as "out of scope" — write 1 negative case confirming they are NOT accessible
4. Flag features with constraints (e.g., "web only", "admin only") — write boundary cases for those constraints

### From Q&A / FAQ Document

Each Q&A item maps to one or more test cases:

| Q&A Pattern | Test Case Type |
|---|---|
| "What happens if user does X?" | Edge case or negative |
| "Feature Y is only on platform Z" | Platform boundary test |
| "User can reset via website only" | Negative: cannot reset via mobile |
| "Data kept for 30 days" | Data retention edge case |
| "Duplicate names allowed if different email" | Negative: same name + same email should be rejected |
| "GDPR delete via admin portal" | Admin-only flow test |

### From Figma Screens / Screenshots

For EACH screen visible in Figma, extract:

**Layout & Navigation:**
- [ ] Screen title/header displayed correctly
- [ ] Navigation bar / back button functional
- [ ] Empty state rendered when no data
- [ ] Loading skeleton / spinner shown during data fetch

**Interactive Elements (for each button, field, toggle, picker):**
- [ ] Tap/click triggers correct action
- [ ] Disabled state looks and behaves correctly
- [ ] Error state shows inline validation message
- [ ] Success state shows correct feedback

**Data Display:**
- [ ] Correct data shown for the current user/context
- [ ] Truncation handled for long text (no overflow)
- [ ] Icons and badges appear per spec (e.g., "!" alert icon, unread dot)
- [ ] Sort / filter / search UI works as per design

**Special Figma UI Patterns:**
- Any icon not in generic UI → write specific test case for it
- Any flow with multiple steps → write test for each step and for abandoning mid-flow
- Any modal / bottom sheet → write open, interact, close, dismiss-by-tap-outside
- Any form → write submit with valid data, submit with invalid data, cancel/back

---

## PHASE 2 — 8-Category Coverage Matrix

For EVERY module, ensure ALL 8 **mandatory** categories are covered. Mark any mandatory category with 0 cases as a **gap**.

> **Canonical set** = the 8 categories enforced by the `qa-coverage` Stop hook and `qa-router`
> (`bd create … --labels qa-coverage,<category>`): POS / NEG / EDGE / SEC / A11Y / BOUNDARY / STATE / ERROR.
> Same set in `behavioral-coverage-matrix`. Do not substitute other categories for these.

**Mandatory (8):**

| # | Category | Symbol | What to Cover |
|---|---|---|---|
| 1 | **Positive (POS)** | ✅ | Happy path with valid data, expected user flow |
| 2 | **Negative (NEG)** | ❌ | Invalid input, missing required fields, wrong format |
| 3 | **Edge (EDGE)** | 🔲 | Special chars, unicode/emoji, 0 items, 1 item, many items, duplicate submit |
| 4 | **Security (SEC)** | 🔒 | SQL injection, XSS, auth bypass, unauthorized access/role, session expiry, brute force |
| 5 | **Accessibility (A11Y)** | ♿ | VoiceOver/TalkBack, Dynamic Type, keyboard nav, color contrast |
| 6 | **Boundary (BOUNDARY)** | 📏 | min/max length, min-1/max+1, numeric limits, date ranges, pagination edges |
| 7 | **State (STATE)** | 🔄 | State transitions (draft→published, active→deleted), persistence after reload/relaunch, ripple to other modules |
| 8 | **Error (ERROR)** | ⚠️ | Network fail/timeout, 4xx/5xx, error recovery & retry, error message correctness |

**Additional (optional columns — add when relevant, not counted as gaps):**

| Category | Symbol | What to Cover |
|---|---|---|
| **UI / Visual** | 🎨 | Layout correct, empty state, loading state, icons, truncation |
| **Performance (PERF)** | ⚡ | Load time with large data sets, scroll performance, cold launch time |
| **Platform/Device** | 📱 | iOS-specific, Android-specific, mobile browser, desktop browser, responsive |

**Minimum per module (mandatory):**
- POS: ≥ 2 cases (at least 1 happy path, 1 alternate success)
- NEG: ≥ 2 cases
- EDGE: ≥ 1 case (special character / empty / many items)
- SEC: ≥ 1 case for any module that accepts user input or requires auth
- A11Y: ≥ 1 case for any core flow (login, main feature action)
- BOUNDARY: ≥ 1 case per input with a limit (length, number, date)
- STATE: ≥ 1 case for any module that creates/changes data or has statuses
- ERROR: ≥ 1 case for any module that calls the network/API

**Optional (when relevant):**
- UI: ≥ 1 case per distinct screen in that module
- PERF: ≥ 1 case for any list/gallery with potentially large data
- Platform: ≥ 1 case if feature has platform-specific behaviour noted in scope/Q&A

---

## PHASE 3 — Gap Analysis Before Declaring Done

Run this checklist before saying "coverage is complete":

### Coverage by Source
```
[ ] Every row in scope document → at least 1 test case
[ ] Every Q&A constraint → at least 1 test case (usually negative or edge)
[ ] Every Figma screen → at least 1 UI test case
[ ] Every user role → at least 1 auth/permission test case
[ ] Every platform listed in scope → at least 1 platform test case
```

### Coverage by Category
```
[ ] POS count > 0 for every module
[ ] NEG count > 0 for every module
[ ] EDGE count > 0 for every module
[ ] SEC count > 0 for every module with user input or login
[ ] A11Y count > 0 for at least core flows (login, main CRUD action)
[ ] BOUNDARY count > 0 for every module with limited inputs
[ ] STATE count > 0 for every module that creates/changes data or has statuses
[ ] ERROR count > 0 for every module that calls the network/API
--- optional ---
[ ] UI count > 0 for every module with a distinct screen
[ ] PERF count > 0 for every module with lists, galleries, calendars
[ ] Platform count > 0 for any feature marked platform-specific in scope
```

### Common Gap Areas (always check these explicitly)
```
[ ] Account lifecycle: create, read, update, delete, restore
[ ] Error recovery: what happens after a failed network call?
[ ] Session / auth: token expiry, concurrent sessions, re-login
[ ] Data boundaries: empty list, 1 item, max items, pagination
[ ] Form submission: partial submit, network drop mid-submit, duplicate submit
[ ] File upload: invalid format, large file, network drop during upload
[ ] Notifications: permission denied, tapping notification deep link
[ ] Subscription / payment: renewal, cancellation, upgrade, downgrade
[ ] GDPR / data deletion: account delete clears all data
[ ] Cross-module: action in module A → reflected in module B
```

---

## PHASE 4 — Case Writing Standards

Each test case MUST have ALL fields populated — no placeholders:

```
ID:          [MODULE_PREFIX]-[NNN]  e.g. AUTH-001, SEC-004, UI-FIG-003
Module:      Exact module name from scope document
Description: Specific, not generic. BAD: "Test login". GOOD: "Login with valid email+password → redirects to Home"
Pre-condition: Numbered list. Include: app state, data that must exist, user role, platform
Steps:       Numbered. Each step = 1 action. Include exact input values.
Test Data:   Concrete values (not "valid email" — use "user@test.com")
Priority:    critical / high / medium (based on business impact)
Expected:    Numbered outcomes. Must be verifiable, not vague.
             BAD: "Works correctly". GOOD: "1. Client appears in list\n2. Toast: 'Client saved'"
```

### Priority Assignment Rules

| Priority | Criteria |
|---|---|
| critical | Auth, data loss, payment, security, GDPR |
| high | Core CRUD, main user flows, cross-module effects |
| medium | Edge cases, accessibility, browser compat, performance |

---

## PHASE 5 — Output Format

When generating test cases from multiple sources, output:

1. **Source Inventory** — list of all documents/screens read
2. **Feature-to-Case Mapping** — table: Feature | Cases Generated | Categories Covered
3. **Gap Report** — list any features with < 2 cases or missing categories
4. **Test Cases** — organized by module, using the `tc()` helper or standard table format
5. **Final Count** — total by module and by category

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Wrong | Fix |
|---|---|---|
| Generic descriptions like "Test feature X - scenario N" | Untestable, no actual verification | Write specific scenario with concrete data |
| Missing pre-conditions | Tester can't reproduce | Always specify app state + data + user role |
| Expected output: "No errors" | Can't verify — what does success look like? | Specify exact UI state, data change, message |
| 0 security cases for a module with user input | SQL injection / XSS can happen in any text field | Add ≥ 1 SEC case per input module |
| Only happy-path cases | Bugs live in sad paths | Always pair each POS with at least 1 NEG |
| Declaring done without running gap analysis | Coverage illusion | Always run Phase 3 checklist before stopping |
| Reading only the first sheet of a scope spreadsheet | Features in other sheets are missed | Always read ALL sheets |
