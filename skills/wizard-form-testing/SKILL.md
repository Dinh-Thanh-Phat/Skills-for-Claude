---
name: wizard-form-testing
description: Patterns for testing multi-step forms and wizards in Playwright — step navigation, per-step validation, back-button state preservation, step indicator assertions, completion redirect. Use when writing tests for any wizard, stepper, multi-step form, onboarding flow, or checkout process with multiple discrete steps. Triggers on: "wizard", "stepper", "multi-step form", "onboarding", "checkout steps", "step navigation", "back button preserves", "step indicator", "step validation".
---

# Multi-Step Wizard / Form Testing

## Core Pattern: test.step() per wizard step

Wrap each step in `test.step()` for named HTML report entries and precise failure pinpointing.

```typescript
test('Complete onboarding wizard', async ({ page }) => {
  await test.step('Step 1: Personal Info', async () => {
    await page.getByLabel('Full Name').fill('Alice Nguyen');
    await page.getByLabel('Email').fill('alice@example.com');
    await page.getByRole('button', { name: 'Next' }).click();
    await expect(page.getByRole('heading', { name: 'Step 2: Address' })).toBeVisible();
  });

  await test.step('Step 2: Address', async () => {
    await page.getByLabel('Street').fill('123 Main St');
    await page.getByLabel('City').fill('Ho Chi Minh City');
    await page.getByRole('button', { name: 'Next' }).click();
  });

  await test.step('Step 3: Review & Submit', async () => {
    await expect(page.getByText('alice@example.com')).toBeVisible(); // review shows data
    await page.getByRole('button', { name: 'Submit' }).click();
  });

  // Use waitForURL instead of deprecated waitForNavigation
  await page.waitForURL('**/onboarding/success');
  await expect(page.getByText('Registration complete')).toBeVisible();
});
```

## Step Indicator Assertions

Assert the wizard's own state machine is correct after each navigation:

```typescript
// After clicking Next on Step 1:
await expect(page.getByRole('tab', { name: 'Step 2' })).toHaveAttribute('aria-selected', 'true');
await expect(page.getByRole('tab', { name: 'Step 1' })).toHaveAttribute('aria-current', 'false');

// Or check progress bar
await expect(page.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '2');

// Or check step label / breadcrumb
await expect(page.getByTestId('active-step')).toHaveText('Step 2 of 4');
```

## Back Button — Verify Data Preserved

```typescript
await test.step('Step 2: Fill then go back', async () => {
  await page.getByLabel('City').fill('New York');

  // ✅ Use wizard's "Back" button — NOT page.goBack() (browser history may not work)
  await page.getByRole('button', { name: 'Back' }).click();

  // Assert Step 1 data still populated
  await expect(page.getByLabel('Full Name')).toHaveValue('Alice Nguyen');
  await expect(page.getByLabel('Email')).toHaveValue('alice@example.com');
});

// Go forward again — Step 2 data must still be there
await page.getByRole('button', { name: 'Next' }).click();
await expect(page.getByLabel('City')).toHaveValue('New York');
```

## Per-Step Validation (Isolated — No Replay)

Test validation for each step without repeating all previous steps:

```typescript
// ✅ Option A: URL-based navigation (if wizard supports step URLs)
await page.goto('/wizard/step-2');

// ✅ Option B: Pre-fill prior steps via localStorage/API
test('Step 2: Street is required', async ({ page }) => {
  // Inject step 1 state directly
  await page.goto('/wizard');
  await page.evaluate(() => {
    sessionStorage.setItem('wizard_step1', JSON.stringify({
      name: 'Alice', email: 'alice@example.com'
    }));
  });
  await page.reload();
  await page.goto('/wizard/step-2');

  // Now test step 2 validation in isolation
  await page.getByRole('button', { name: 'Next' }).click();
  await expect(page.getByText('Street is required')).toBeVisible();
});
```

## Completion

```typescript
// ✅ waitForURL (not deprecated waitForNavigation)
await page.getByRole('button', { name: 'Submit' }).click();
await page.waitForURL('**/confirmation', { timeout: 5000 });
await expect(page.getByText('Your order is confirmed')).toBeVisible();
await expect(page.getByText('Order #')).toBeVisible();
```

## What Tests to Write

| Scenario | Priority |
|---|---|
| Happy path end-to-end | Must have |
| Per-step required field validation | Must have |
| Back button preserves entered data | Must have |
| Completion redirect to correct URL | Must have |
| Step indicator shows correct active step | Should have |
| Direct URL access to later step (should redirect or show error) | Should have |
| All step order permutations | Skip — combinatorial explosion, not worth it |

## Gotchas

| Gotcha | Fix |
|---|---|
| `page.goBack()` doesn't work in URL-based wizard | Use wizard's own "Back" button element |
| "Execution context was destroyed" on step transition | Await navigation completion before next action |
| Validation errors appear async (debounced) | `press('Tab')` first, then `expect().toBeVisible()` |
| Per-step validation requires replaying all prior steps | Use fixture/localStorage injection to skip prior steps |
| SPA wizard: `waitForNavigation` deprecated | Use `page.waitForURL(pattern)` for step transitions |

## Resume / Abandoned Wizard

Many wizards persist progress (localStorage / server draft). Test the resume flow:

```typescript
test('Resume wizard after closing browser', async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto('/wizard');
  await page.getByLabel('Full Name').fill('Alice');
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByLabel('Street').fill('123 Main');
  // Close mid-wizard
  await ctx.close();

  // New session — wizard should offer to resume
  const ctx2 = await browser.newContext();
  const page2 = await ctx2.newPage();
  await page2.goto('/wizard');
  await expect(page2.getByText(/resume|continue/i)).toBeVisible();
  await page2.getByRole('button', { name: /resume/i }).click();
  await expect(page2.getByLabel('Street')).toHaveValue('123 Main');
});
```

## Deep-Link to Mid-Step

URL-based wizards (e.g. `/wizard/step-3`) must redirect if prerequisites not met:

```typescript
test('Direct access to step 3 without completing step 1+2 redirects', async ({ page }) => {
  await page.goto('/wizard/step-3');
  // Spec says: redirect to first incomplete step
  await expect(page).toHaveURL(/\/wizard\/step-1/);
});
```

## Validation Skipping a Step (Conditional Branches)

Some wizards skip steps based on earlier answers. Test both branches:

```typescript
test('Selecting "Personal" skips Tax-ID step', async ({ page }) => {
  await page.getByLabel('Account type').selectOption('Personal');
  await page.getByRole('button', { name: 'Next' }).click();
  // Should go straight to "Address" (step 3), skipping "Tax-ID" (step 2 for Business)
  await expect(page.getByRole('heading', { name: 'Address' })).toBeVisible();
});
```

## Checklist

- [ ] Each step wrapped in `test.step('Step N: Label', ...)`
- [ ] Step indicator asserted after each Next/Back navigation
- [ ] Back button: uses wizard's button (not `page.goBack()`), prior data verified
- [ ] Per-step validation: tested in isolation with state injection (no replay)
- [ ] Completion: `page.waitForURL()` asserts final redirect
- [ ] Validation errors: `press('Tab')` triggers blur before asserting

