---
name: cross-module-verify
description: Enforce cross-module verification in E2E tests for workflows that span multiple app areas. Use when testing any workflow where action in Module A should produce visible results in Module B. Triggers on: "test workflow", "test send", "test create", "test integration", multi-step workflow tests.
---

# Cross-Module Verification Skill

You are a **Senior QA Engineer** ensuring E2E tests follow data through the full system — not just the entry point.

## The Problem

Most E2E tests only verify the module where the action happens. Real bugs often live in the side effects — what happens to the data *after* it leaves Module A.

```
User clicks "Send Email"
    ↓
Module A: Email Composer — ✅ tested (toast appears)
    ↓
Module B: Campaign History — ❌ not tested (never navigate here)
    ↓
Module C: Analytics Dashboard — ❌ not tested
```

A test that never reaches Module B cannot catch bugs in Module B.

---

## Cross-Module Map — Common App Workflows

| Action (Module A) | Must Also Verify In (Module B) |
|---|---|
| Send email | Campaign History → new entry with correct status |
| Create template | Templates list → template appears |
| Add subscriber to list | List detail → subscriber count +1, name visible |
| Unsubscribe user | Unsubscribes list → user appears |
| Schedule campaign | Scheduled tab → campaign visible with correct time |
| Upload file/image | Media library → file visible with correct metadata |
| Create user | Users list → user appears with correct role |
| Submit form | Admin panel / records view → entry created |
| Delete record | List page → record gone (even after refresh) |
| Change settings | Pages that USE the setting → reflect new value |
| Subscribe to YEARLY plan | Transactions page → amount must be yearly price (≥ $80), NOT monthly price |
| Subscribe to MONTHLY plan | Transactions page → amount must match monthly price |
| Any subscription created | Subscriptions page → Start date AND End date show valid dates (not "Invalid Date") |

---

## Business Value Cross-Module Validation

> **Rule**: When Module A has entity TYPE attributes (plan type, role, category), Module B's related NUMERIC/CONTENT values must be validated for CORRECTNESS per type — not just format or presence.

Format validation (`date matches MM/DD/YYYY`) is not enough. Business validation asks: **is the VALUE correct for this entity type?**

### Pattern: Entity Type → Expected Value in Downstream Module

```
Module A: Subscriptions
  Entity attribute: plan type = YEARLY

Module B: Transactions
  ❌ Format check only: amount matches $XX.XX → ALWAYS PASSES even with wrong amount
  ✅ Business check: THIS yearly subscriber's transaction amount == YEARLY_PRICE (not MONTHLY_PRICE)
```

### Implementation

```typescript
test('YEARLY subscription → transaction amount is yearly price (not monthly)', async ({ page }) => {
  // Navigate to source module to find entity type
  await page.goto('/subscriptions');
  const yearlyPractitioner = await getFirstYearlySubscriberName(page);
  expect(yearlyPractitioner).not.toBeNull();

  // Navigate to downstream module
  await page.goto('/transactions');

  // KEY: validate the VALUE of THIS entity's record — not "some row somewhere > N"
  // (`amounts.some(a => a > 50)` passes as long as ANY other row is big, even if this one is wrong)
  const row = page.getByRole('row').filter({ hasText: yearlyPractitioner! });
  await expect(row).toHaveCount(1);
  await expect(row.getByRole('cell', { name: /\$/ })).toHaveText(formatUsd(YEARLY_PRICE)); // exact price from the price list / API
  await expect(row).not.toContainText(formatUsd(MONTHLY_PRICE));
});
```

### Cross-Module Business Value Map (add to as you discover patterns)

| Entity in Module A | Attribute | Module B | Value Rule |
|---|---|---|---|
| Subscription | plan = YEARLY | Transactions | amount ≥ yearly_price (NOT monthly_price) |
| Subscription | any | Subscriptions | Start date AND End date must be valid dates |
| User | role = Admin | Admin portal | has admin-only controls visible |
| Campaign | status = Sent | Analytics | sent count > 0 |

### Anti-Pattern to Avoid

```typescript
// ❌ Format-only — always passes even when value is wrong
expect(amount).toMatch(/^\$\d+\.\d{2}$/);  // "$29.00" passes — but it's the wrong amount!

// ✅ Business validation — fails when value is incorrect for entity type
expect(amount).toBeGreaterThan(50);  // fails when yearly plan shows monthly price
```

---

## Verification Depth Levels

### Level 1 — Surface (weak — avoid for critical flows)
```typescript
// Only checks the action worked in the current module
await page.click('[data-testid="send-btn"]');
await expect(page.locator('.success-toast')).toBeVisible();
```

### Level 2 — Same-Page Outcome (minimum acceptable)
```typescript
// Verifies data is in the correct final state on the same page
await page.click('[data-testid="save"]');
await expect(page.locator('.status')).toHaveText('Saved');
await page.reload(); // confirm persistence
await expect(page.locator('.status')).toHaveText('Saved');
```

### Level 3 — Cross-Module (required for E2E tests)
```typescript
// Verify in the downstream module where results should appear
await sendEmail(page, { subject, to });

await page.goto('/campaign-history');
await expect(page.locator(`text="${subject}"`)).toBeVisible();
await expect(page.locator('.status').first()).toHaveText('Sent');
```

### Level 4 — Full Chain (for critical business flows)
```typescript
// Follow data through every module it touches
await sendEmail(page, { subject, to });

// Module B: Campaign History
await page.goto('/campaign-history');
await expect(page.locator(`text="${subject}"`)).toBeVisible();

// Module C: Analytics (if applicable)
await page.goto('/analytics');
await expect(page.locator('.emails-sent-count')).not.toHaveText('0');
```

---

## Implementation Pattern

```typescript
test('[Action] → [Cross-Module Outcome]', async ({ page }) => {
  // ARRANGE
  const testData = {
    subject: `Cross-Module Test ${Date.now()}`,
    recipient: 'target@example.com',
  };
  await loginAs(page, 'admin');

  // ACT — action in Module A
  await page.goto('/module-a');
  await performAction(page, testData);

  // ASSERT A — Module A immediate feedback (optional)
  await expect(page.locator('.success-message')).toBeVisible();

  // ASSERT B — Module B cross-module verification (REQUIRED)
  await page.goto('/module-b');
  await verifyInModuleB(page, testData);

  // ASSERT C — Module C (if data flows further)
  // await page.goto('/module-c');
  // await verifyInModuleC(page, testData);
});
```

---

## Helper Pattern — Reusable Verification Functions

Break cross-module verification into helpers to keep tests readable:

```typescript
// helpers/verify.ts
export async function verifyEmailInHistory(
  page: Page,
  { subject, recipient, status = 'Sent' }: EmailVerifyOptions
) {
  await page.goto('/campaign-history');
  const row = page.locator('tbody tr').filter({ hasText: subject }).first();
  await expect(row).toBeVisible();
  await expect(row.locator('.status')).toHaveText(status);
  await expect(row).toContainText(recipient);
}

// In test:
await sendEmail(page, testData);
await verifyEmailInHistory(page, { subject: testData.subject, recipient: testData.to });
```

---

## Checklist — Cross-Module Verification

For any E2E test covering a multi-module workflow:

- [ ] Identified all modules the action touches (not just the entry point)
- [ ] Test navigates to each downstream module to verify
- [ ] Uses unique test data (timestamp) so cross-module lookups find the right record
- [ ] Verifies the correct record exists (not just "any record")
- [ ] Verifies key fields: status, content, counts — not just presence
- [ ] Test name reflects the cross-module scope: "send email → campaign history entry"
- [ ] If data should NOT appear somewhere (delete, unsubscribe) — verify absence too

---

## Red Flags — Tests That Need Cross-Module Coverage

If your test:
- Only stays on one page/URL the entire test
- Only asserts on toast messages, loading spinners, or redirects
- Has no `page.goto()` after the main action
- Tests a "create/send/publish" action but never verifies the result list

→ It is missing cross-module verification. Add it.
