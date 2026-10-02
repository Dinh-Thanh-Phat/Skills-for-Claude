---
name: ui-error-classification
description: Classify UI error messages as expected behavior vs production bug before writing assertions or filing bugs. Use when a test sees an error message on screen, when deciding if a UI error is a bug or correct behavior, when "test fails because error message appears", "form shows error", "something went wrong", "lỗi xuất hiện trên UI", "test báo lỗi nhưng tôi không chắc là bug không". CRITICAL: Always invoke this before deciding whether to fix the test or file a bug.
scope: playwright, qa, bug-classification, forms, ui-testing
---

# UI Error Classification Skill

**The most common QA mistake:** treating ALL visible error messages as bugs. Some errors are the correct, expected behavior. Some are production failures. Mixing these up wastes dev time (false bugs) or lets real bugs slip through.

---

## The Core Rule

> **Input đúng → nhận error = BUG**
> **Input sai → nhận error = PASS (expected)**

```
User fills form correctly + submits → "Something went wrong" → 🔴 BUG
User leaves required field empty + submits → "Field required" → ✅ EXPECTED
```

---

## Classification Table

| Scenario | Error type | Verdict | Test action |
|---|---|---|---|
| Missing required field → "This field is required" | Validation error | ✅ Expected | Test should assert this message appears |
| Invalid email format → "Invalid email" | Validation error | ✅ Expected | Assert message appears |
| All fields valid + submit → "Something went wrong" | API/Server error | 🔴 BUG | File bug, lock test with `test.fail(true, 'BUG-xxx')` (see `skip-vs-fail`) |
| All fields valid + submit → "Please email us directly" | API/Server error | 🔴 BUG | Same |
| Page load → blank white screen | Render error | 🔴 BUG | File bug |
| Filter applied → wrong results shown | Logic error | 🔴 BUG | File bug |
| Dialog opened → wrong content | Data error | 🔴 BUG | File bug |
| Correct password → "Invalid credentials" | Auth error | 🔴 BUG | File bug |
| Empty search → "No results found" | Empty state | ✅ Expected | Assert empty state |
| 3rd party unavailable → error message | Dependency failure | ⚠ Investigate | Check if fallback expected |

---

## Classification Decision Tree

```
User provided valid/correct input?
├── NO  → Did the error message match the validation rule?
│         ├── YES → ✅ EXPECTED BEHAVIOR → test should assert this
│         └── NO  → 🔴 BUG (wrong error message for the rule)
│
└── YES → Did the operation succeed?
          ├── YES → ✅ Pass
          └── NO  → 🔴 BUG → file bug report, write failing test to document it
```

---

## Form Validation vs API Error

This is the most common confusion point in form testing.

### Expected: Client-side Validation Error
Triggered BEFORE form submission (or immediately on submit before API call). Source: browser `validity` API or JS validation.

```typescript
// This is CORRECT — test should assert this appears
test('Empty name field shows required error', async ({ page }) => {
  await page.getByRole('button', { name: 'Submit' }).click();
  // No API call made yet
  const isInvalid = await page.getByRole('textbox', { name: 'Full Name' })
    .evaluate((el: HTMLInputElement) => !el.validity.valid);
  expect(isInvalid).toBe(true); // ✅ Correct assertion
});
```

### Bug: Server/API Error After Valid Submission
Triggered AFTER API call. Source: backend returns 4xx/5xx. User input was valid.

```typescript
// This test SHOULD FAIL — it documents a production bug
test('TC-FORM-REAL-001: Contact form submission [BUG-FORM-001]', async ({ page }) => {
  // No mock — real API
  await page.getByRole('textbox', { name: 'Full Name' }).fill('John Smith');
  await page.getByRole('textbox', { name: 'Email' }).fill('john@company.com');
  await page.getByRole('button', { name: 'Submit' }).click();
  
  // EXPECTED: success message
  // ACTUAL: "Something went wrong" — production API is broken
  await expect(page.getByRole('heading', { name: 'Success!' })).toBeVisible();
  // ^ This assertion CORRECTLY FAILS to document BUG-FORM-001
});
```

---

## How to Tell the Difference During Testing

### Step 1: Check what happened in Network tab
- **No API call made** → validation error → expected behavior
- **API call made, returned 4xx/5xx** → server/API error → likely bug

### Step 2: Check if the error is conditional on input quality
- Try submitting with INVALID data → same error? → might be validation
- Try submitting with VALID data → still same error? → bug

### Step 3: Check error message tone
- "Please fill in this field" / "Invalid format" → validation (expected)
- "Something went wrong" / "Please try again" / "Contact us at..." → server error (bug)

---

## Writing Tests for Known Production Bugs

When the API is broken and you want to document it:

```typescript
// ✅ Pattern: real test that intentionally fails + documents the bug
test('TC-FORM-REAL-001: Form submission works [BUG-API-001]', async ({ page }) => {
  // Comment: No mock — hits real API
  // EXPECTED: "Thank you!" heading
  // ACTUAL (BUG-API-001): "Something went wrong" — POST /api/contact returns 500
  // This test will auto-pass when the API is fixed
  
  // ... fill form ...
  await expect(page.getByRole('heading', { name: 'Thank you!' })).toBeVisible();
  // ^ Intentionally failing assertion — this is the test serving as a bug tracker
});
```

**Benefits:**
- Bug is documented in test suite, not just Jira
- Test auto-passes when bug is fixed → CI becomes the regression detector
- Dev knows exactly what to look for

---

## Mocked Tests vs Real Tests

**Always have both:**

| Test type | Purpose | Mock? |
|---|---|---|
| `TC-FORM-SUBMIT-001` | Verify frontend handles success state correctly | ✅ Mock API |
| `TC-FORM-SUBMIT-004` | Verify frontend handles error state correctly | ✅ Mock 500 |
| `TC-FORM-REAL-001` | Verify production API actually works end-to-end | ❌ Real API |

**Why you need the real test:** Mocked tests can all pass while production is completely broken. One real (non-mocked) test catches this.

> "Mocked tests passing ≠ production works."

---

## Severity Levels of UI Errors

| Visual | Severity | Source | Example |
|---|---|---|---|
| 🔵 Info | INFORMATIONAL | UX hint | "Tip: use Tab to navigate" |
| 🟡 Warning | EXPECTED degradation | Partial failure | "Live data unavailable, showing cached values" |
| 🟠 Error | RECOVERABLE | User-fixable | "Network slow, retry" with Retry button |
| 🔴 Critical | BUG (most likely) | Server / bug | "Something went wrong" with no retry path |

Test should assert the **correct severity** for the scenario, not just "an error appeared".

## 3rd-Party Iframe Errors (Calendly, Stripe, YouTube...)

Errors INSIDE a 3rd-party iframe are NOT your bug, BUT the user still can't complete the flow.

```typescript
// Check inside the Calendly iframe, not the outer page
const calFrame = page.frameLocator('iframe[src*="calendly.com"]');
const has404 = await calFrame.getByText(/404|not found/i).isVisible().catch(() => false);
if (has404) {
  // Don't file as YOUR bug — file as "3rd-party config" bug:
  //   Calendly link is broken — wrong account / unpublished event
}
```

## Partial Degradation

When some widgets fail but the page is still usable:
```typescript
// Dashboard with 5 widgets, 1 fails
const widgets = page.locator('[data-widget]');
const failed = widgets.filter({ has: page.locator('[data-error]') });
const ok = await widgets.count() - await failed.count();
// Verify: most widgets work, failed widgets show error state, not blank
expect(ok).toBeGreaterThanOrEqual(3);
await expect(failed.first().getByRole('button', { name: /retry/i })).toBeVisible();
```

## Filing a Bug vs Fixing the Test

| Situation | Action |
|---|---|
| Error message correct for the input → test assertion wrong | Fix the test assertion |
| Valid input → error appears → real production problem | File bug report, write intentionally-failing real test |
| Test was asserting the wrong expected behavior all along | Fix test + update assertion |
| Screenshot shows error the user never intended | Investigate: is it a known bug or new regression? |
