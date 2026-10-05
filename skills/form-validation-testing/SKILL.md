---
name: form-validation-testing
description: Patterns for testing form validation UI in Playwright — inline error messages, required fields, submit button states, async server-side validation, multi-field dependencies. Use when writing tests for any form with validation: login, registration, settings, or any form that shows inline error messages or disables the submit button. Triggers on: "form validation", "inline error", "required field", "submit button disabled", "validation message", "async validation", "email already taken", "field error".
---

# Form Validation Testing

## Core Rule

Validation may trigger on **blur** (most common), **change** (live), or **submit** (deferred).
Identify which the form uses before writing assertions.

| Mode | When error appears | Test approach |
|---|---|---|
| `onBlur` | After Tab/click-away | `fill()` → `press('Tab')` → assert error |
| `onChange` | Every keystroke (debounced) | `fill()` → wait for debounce or `expect()` auto-retry → assert |
| `onSubmit` | Only after clicking Submit | `click(Submit)` → assert error |
| `hybrid` | onSubmit first, then onBlur after first submit | Test both phases |

Also cover **paste** and **autofill** — they may skip onChange/onBlur and silently bypass validation.

```typescript
// Paste — may not fire onChange in some React forms
// Clipboard API needs permission (Chromium); use ControlOrMeta so it also works on macOS
await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
await page.getByLabel('Email').focus();
await page.evaluate(() => navigator.clipboard.writeText('test@example.com'));
await page.keyboard.press('ControlOrMeta+V');
await page.getByLabel('Email').press('Tab');
await expect(page.getByLabel('Email')).toHaveValue('test@example.com'); // prove paste happened
await expect(page.getByText('Invalid')).toBeHidden();                  // otherwise this passes vacuously

// Autofill — Chrome auto-fills without firing some events
await page.locator('input[autocomplete="email"]').evaluate(
  (el: HTMLInputElement) => { el.value = 'auto@example.com'; el.dispatchEvent(new Event('input', { bubbles: true })); }
);
```

## Patterns

### 1. Trigger blur-based validation
```typescript
// ✅ Fill → Tab away → assert error appears
await page.getByLabel('Email').fill('invalid-email');
await page.getByLabel('Email').press('Tab'); // trigger blur/change event
await expect(page.getByText('Please enter a valid email')).toBeVisible();
```

### 2. Assert validation message clears when fixed
```typescript
// ✅ Test BOTH directions: error appears AND disappears
await page.getByLabel('Email').fill('invalid');
await page.getByLabel('Email').press('Tab');
await expect(page.getByText('Invalid email')).toBeVisible();

await page.getByLabel('Email').fill('valid@example.com');
await page.getByLabel('Email').press('Tab');
await expect(page.getByText('Invalid email')).toBeHidden(); // must clear too!
```

### 3. Submit button state transitions
```typescript
// ✅ Assert disabled → enabled transition
await expect(page.getByRole('button', { name: 'Submit' })).toBeDisabled();

await page.getByLabel('Email').fill('valid@example.com');
await page.getByLabel('Name').fill('John Doe');

await expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled();
```

### 4. Async server-side validation (e.g. "email already taken")
```typescript
// ✅ Mock the async validation endpoint
await page.route('**/api/validate/email', r =>
  r.fulfill({ status: 200, body: JSON.stringify({ taken: true }) })
);
await page.getByLabel('Email').fill('taken@example.com');
await page.getByLabel('Email').press('Tab');
// Let Playwright's default auto-retry wait for async server response
await expect(page.getByText('Email already in use')).toBeVisible();
```

### 5. Multi-field dependencies (password confirm)
```typescript
// ✅ Test each failure mode separately, then combined
// Case 1: Passwords don't match
await page.getByLabel('Password').fill('Pass123@');
await page.getByLabel('Confirm Password').fill('different');
await page.getByLabel('Confirm Password').press('Tab');
await expect(page.getByText('Passwords do not match')).toBeVisible();

// Case 2: Fix mismatch — error clears
await page.getByLabel('Confirm Password').fill('Pass123@');
await page.getByLabel('Confirm Password').press('Tab');
await expect(page.getByText('Passwords do not match')).toBeHidden();
```

### 6. Required fields — submit empty form
```typescript
// ✅ Click submit without filling anything — all required errors appear
await page.getByRole('button', { name: 'Submit' }).click();
await expect(page.getByText('Name is required')).toBeVisible();
await expect(page.getByText('Email is required')).toBeVisible();
await expect(page.getByText('Password is required')).toBeVisible();
```

### 7. Assert on message text, NOT CSS class
```typescript
// ❌ Fragile — class names change with refactors
await expect(page.locator('.field-error')).toBeVisible();

// ✅ Resilient — user-visible text
await expect(page.getByText('Please enter a valid email')).toBeVisible();
await expect(page.getByRole('alert')).toContainText('Email is required');
```

## Gotchas

| Gotcha | Fix |
|---|---|
| Submit button not enabling after fill | Use `press('Tab')` to trigger React controlled input blur event |
| Async validation timeout | Remove `{ timeout: 0 }`, let default timeout auto-retry |
| `locator.fill()` triggers "required" error mid-fill | Expected — Tab after fill, THEN assert |
| Asserting error without Tab first | Always `press('Tab')` before asserting inline errors |
| Testing only error appearance, not clearance | Every "error appears" test needs "error disappears" assertion |
| Multi-field validation tested only combined | Test each field invalid alone, then combined |

## Test Coverage Checklist per Form

- [ ] Each required field: error appears on submit/blur AND clears when valid input provided
- [ ] Submit button: disabled with incomplete/invalid data, enabled when all valid
- [ ] Async validation: route mocked, auto-retry handles timing
- [ ] Multi-field dependencies (confirm password, date range): each combination tested
- [ ] Error messages: asserting text content, NOT CSS class presence
- [ ] Validation clears: for every "error appears" case, a matching "error disappears" assertion

