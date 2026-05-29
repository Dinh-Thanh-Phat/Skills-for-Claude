# Selector Map — Data Contract

This document defines the exchange format between `playwright-snapshot-parser` (producer) and `qa-test-generation` (consumer).

## Purpose

`playwright-snapshot-parser` produces a Selector Map from actual UI snapshots.
`qa-test-generation` consumes it in Phase 2 to write automation with verified selectors instead of guesses.

---

## Format

The Selector Map is a Markdown table block with a header and optional BLOCKED/CRITICAL sections. It is passed as conversational context — no file, no JSON, just paste into the chat.

```
### SELECTOR MAP — [Page or Component Name]

| Intent | Primary Selector | Confidence | A11y Warning |
|--------|-----------------|-----------|--------------|
| [intent] | `[selector]` | HIGH | - |
| [intent] | `[selector]` | MEDIUM | [warning] |

BLOCKED (cannot be targeted semantically):
  - [ref=eN] [role] — [reason] → [required fix]

CRITICAL A11Y (breaks automation until fixed):
  - [ref=eN] [issue description]
```

---

## Field Definitions

### Intent
Human-readable description of what the element does from a test perspective.
- Use action verbs matching your test case language: "submit form", "filter by date", "open menu"
- Must be unique within the page — if two buttons share an intent label, qualify them: "submit login form" vs "submit registration form"

### Primary Selector
The single best selector for this element, as a TypeScript code string.
- Always use the highest-confidence selector from the snapshot parser's priority ranking
- Scoped selectors preferred over bare role selectors when disambiguation is needed

### Confidence
- **HIGH** — unique element, unambiguous name, stable landmark anchoring
- **MEDIUM** — unique but name could change (e.g., dynamic text), or relies on text matching
- **LOW** — structural selector, positional, or element has a11y issue that makes semantic targeting fragile

### A11y Warning
- `-` if none
- Short description of the a11y issue that affects this selector's reliability

---

## BLOCKED Entries

An element is BLOCKED when no semantic selector is possible. Causes:
- Unnamed interactive element (button/link with no accessible name)
- Input without label
- Generic/none role with no aria-label

BLOCKED elements must NOT appear in automation test code. Raise an a11y bug ticket first.

---

## Conflict Resolution Rules

When `qa-test-generation` has assumed a selector that conflicts with the Selector Map:

| Situation | Rule |
|-----------|------|
| Map has HIGH confidence selector | Use map selector. Discard the assumption. |
| Map has MEDIUM confidence selector | Use map selector. Add `// verify: name may change` comment. |
| Map has LOW confidence selector | Use map selector. Add `// TODO: fix a11y to get stable selector`. |
| Element is BLOCKED | Do NOT write a selector. Write `// BLOCKED: [reason] — fix a11y issue first`. |
| Element missing from map | Use semantic guess. Add `// UNVERIFIED: run playwright-snapshot-parser to validate`. |
| Map selector differs from assumption (both HIGH) | Snapshot wins — it reflects actual DOM. |

---

## Example

Given a Login page snapshot, the Selector Map might be:

```
### SELECTOR MAP — Login Page

| Intent | Primary Selector | Confidence | A11y Warning |
|--------|-----------------|-----------|--------------|
| email address input | `page.getByLabel('Email')` | HIGH | - |
| password input | `page.getByLabel('Password')` | HIGH | - |
| submit login | `page.getByRole('form', { name: 'Login' }).getByRole('button', { name: 'Sign in' })` | HIGH | - |
| show password toggle | `page.getByRole('button', { name: 'Show password' })` | HIGH | - |
| forgot password link | `page.getByRole('link', { name: 'Forgot password?' })` | HIGH | - |

CRITICAL A11Y:
  - [ref=e44] textbox — placeholder only, no label → getByLabel fails until <label> added
```

A test generated from this map:
```typescript
test('login with valid credentials', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@test.com');
  await page.getByLabel('Password').fill('secret123');
  await page.getByRole('form', { name: 'Login' }).getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL('/dashboard');
});
```
