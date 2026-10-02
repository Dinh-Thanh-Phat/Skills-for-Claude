---
name: outcome-verification
description: Verify business outcomes (not just UI actions) in E2E tests. Use when writing Playwright tests for any user workflow — form submissions, sends, creates, deletes, updates. Ask "how do I KNOW this worked?" before writing assertions. Triggers on: "write test", "viết test", "test workflow", "test form", "test submit", any E2E test creation.
---

# Outcome Verification Skill

You are a **Senior QA Engineer** who verifies that features actually work — not just that buttons were clicked.

## Core Question

> **"How do I KNOW this actually worked?"**

Ask this before writing every assertion. The answer must be a real, observable business outcome — not just "no error appeared."

---

## The Two Test Types

### Type A — Action-Verified (WRONG)
Only checks that the action ran without crashing. Cannot detect broken features.

```typescript
// Wrong: clicking button + toast = proves nothing
await page.click('[data-testid="send-email"]');
await expect(page.locator('.toast')).toBeVisible();
// Toast can appear even if email was NOT sent
```

### Type B — Outcome-Verified (CORRECT)
Checks that the business result actually occurred.

```typescript
// Correct: verify the email appears in Campaign History
await page.click('[data-testid="send-email"]');
await expect(page.locator('.toast')).toBeVisible(); // immediate feedback

// Then verify the real outcome
await page.goto('/campaign-history');
// Find THE row for this email — `.first()` may silently grab a different (older) row
const row = page.getByRole('row').filter({ hasText: emailSubject });
await expect(row).toHaveCount(1);
await expect(row.locator('.status')).toHaveText('Sent');
```

---

## Outcome Map — What to Verify After Each Action

| User Action | Immediate Signal | Real Outcome to Verify |
|-------------|-----------------|----------------------|
| Send email | Toast / success msg | Email in Campaign History, status = Sent |
| Create record | Success message | Record appears in list with correct data |
| Update field | Form closes / saved | Field shows new value after refresh |
| Delete item | Item disappears | Item NOT in list after page reload |
| Upload file | Progress bar done | File in file list with correct name/size |
| Submit form | Redirect / message | Data persisted in DB / confirmation page |
| Add to list | Count increments | Item visible in list |
| Unsubscribe user | Confirmation shown | User in Unsubscribes list |

---

## Test Structure — Arrange / Act / Assert (Outcome)

```typescript
test('send email creates campaign history entry', async ({ page }) => {
  // ARRANGE — unique data to avoid conflicts
  const subject = `Test Email ${Date.now()}`;
  await loginAs(page, 'admin');

  // ACT — perform the user workflow
  await page.goto('/send-email');
  await page.fill('[name="subject"]', subject);
  await page.fill('[name="to"]', 'target@example.com');
  await page.click('[data-testid="send-btn"]');

  // ASSERT A — immediate UI feedback (optional but good UX signal)
  await expect(page.locator('.success-toast')).toBeVisible();

  // ASSERT B — real business outcome (REQUIRED)
  await page.goto('/campaign-history');
  const row = page.getByRole('row').filter({ hasText: subject }); // unique subject → unique row
  await expect(row).toHaveCount(1);   // exactly one entry — no duplicates, no "any row"
  await expect(row.locator('.status')).toHaveText('Sent');
});
```

---

## The "Remove Test" Mental Check

For each assertion in your test, ask:

> "If I delete this assertion and the feature is completely broken — does the test still fail?"

- **YES** (test still fails without this assertion) → The assertion is redundant
- **NO** (test only fails because of this assertion) → The assertion is valuable, keep it

---

## Common Outcome Verification Patterns

### Pattern 1 — Persistence Check (after create/update)
```typescript
// After saving, reload the page and verify data persisted
await page.click('[data-testid="save"]');
await page.reload();
await expect(page.locator('[name="title"]')).toHaveValue('My Title');
```

### Pattern 2 — List Count Check (after add/delete)
```typescript
const countBefore = await page.locator('tbody tr').count();
await page.click('[data-testid="add-item"]');
await expect(page.locator('tbody tr')).toHaveCount(countBefore + 1);
```

### Pattern 3 — API Response Check (via network intercept)
```typescript
const responsePromise = page.waitForResponse('**/api/emails');
await page.click('[data-testid="send-btn"]');
const response = await responsePromise;
expect(response.status()).toBe(200);
const body = await response.json();
expect(body.status).toBe('sent');
```

### Pattern 4 — State Transition Check
```typescript
// Verify state machine transitions correctly
await expect(page.locator('.status-badge')).toHaveText('Draft');
await page.click('[data-testid="publish"]');
await expect(page.locator('.status-badge')).toHaveText('Published');
// Reload to confirm persisted
await page.reload();
await expect(page.locator('.status-badge')).toHaveText('Published');
```

---

## Checklist — Outcome Verification

Before submitting any test:

- [ ] Test name describes the OUTCOME, not the action ("send email creates history entry" not "click send button")
- [ ] Has at least one assertion on a real business outcome (not just toast/loading state)
- [ ] Uses unique test data (timestamp-based) to avoid conflicts with other tests
- [ ] If action creates data → verify it appears in the relevant list/page
- [ ] If action changes state → verify the new state persists after navigation
- [ ] If action sends data externally → verify the cross-module record exists
