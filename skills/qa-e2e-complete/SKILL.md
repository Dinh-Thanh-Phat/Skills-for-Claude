---
name: qa-e2e-complete
description: >-
  Write complete, high-value Playwright E2E automation tests that verify real business outcomes —
  not just UI clicks. Use this skill whenever writing or reviewing automation tests, especially
  when tests "all pass" but features seem broken, when asked to "write proper tests", "fix
  shallow tests", "make tests actually useful", "write automation test suite", or when test cases
  only click buttons without asserting outcomes. This skill prevents the #1 QA anti-pattern:
  tests that always pass regardless of whether the feature works.
---

# QA: Complete E2E Automation Tests

> **Cross-ref:** This skill is the **how-to-write a complete E2E test** view. For the
> underlying rules see: `outcome-verification` (verify business outcome, not action),
> `cross-module-verify` (module A → module B), `state-ripple-verify` (silent downstream
> consumers), `fail-loud` + `soft-assertion-ban` (hard assertions only). Use this skill
> as the umbrella when writing a fresh test suite; the others are referenced as needed.

## The Two Problems This Skill Solves

### Problem 1: Shallow Tests (No Real Value)
Tests that only click buttons and check for toast messages prove nothing. A "Send Email" test that clicks Send and sees a success toast does NOT verify the email was sent — it only verifies the button didn't throw an error.

### Problem 2: Soft Assertions (Always Pass)
```typescript
// ❌ This test can NEVER fail — it's a lie
try {
  await page.click('button');
} catch (e) {
  console.log('error:', e); // swallowed
}
expect(true).toBeTruthy(); // always passes
```

---

## What a Complete E2E Test Looks Like

Every test must follow this 4-part structure with ALL parts present:

```typescript
test.describe('Send Email', () => {
  // ── CLEANUP (runs even when test fails) ──────────────────────────
  let createdSubject: string;

  test.afterEach(async ({ page }) => {
    if (createdSubject) {
      // API cleanup preferred; UI fallback if no API
      await page.request.delete(`/api/campaigns?subject=${createdSubject}`).catch(() => {});
      createdSubject = '';
    }
  });

  test('send email → appears in campaign history', async ({ page }) => {
    // ── PART 1: ARRANGE ───────────────────────────────────────────
    // Create unique test data so tests don't interfere with each other
    createdSubject = `Test Email ${Date.now()}`;
    const recipient = 'qa-test@example.com';
    await loginAs(page, 'admin'); // reusable fixture

    // ── PART 2: ACT ───────────────────────────────────────────────
    await page.goto('/send-email');
    await page.fill('[name="subject"]', createdSubject);
    await page.fill('[name="to"]', recipient);
    await page.click('[data-testid="send-btn"]');

    // ── PART 3: ASSERT ────────────────────────────────────────────
    // 3a. Immediate UI feedback (optional, quick check)
    await expect(page.locator('.success-toast')).toBeVisible();

    // 3b. CROSS-MODULE VERIFICATION (required for E2E)
    // The real proof: did it actually work in the system?
    await page.goto('/campaign-history');
    const row = page.locator('table tbody tr').first();
    await expect(row).toContainText(createdSubject);
    await expect(row.locator('[data-col="status"]')).toHaveText('Sent');
    await expect(row.locator('[data-col="recipient"]')).toContainText(recipient);
  });
});
```

> **Cleanup rule:** Always declare created data in an outer `let` variable, assign inside test, and clean up in `test.afterEach()`. Cleanup at the end of the test body is skipped when the test fails — `afterEach` is not.

---

## Cross-Module Verification Map

For any action, always ask: **"Where else in the system should this show up?"**

| Action (Module A) | Must Verify In (Module B) | What to Assert |
|---|---|---|
| Send email | Campaign History | New row with correct subject, recipient, status=Sent |
| Create template | Templates list | Template appears with correct name and type |
| Add contact to list | Email List detail page | Contact count increments, contact visible |
| Unsubscribe user | Unsubscribes page | User email appears in unsubscribe list |
| Schedule campaign | Campaigns list | Status = Scheduled, correct send date |
| Delete item | List page | Item no longer appears |
| Edit record | Detail page / list | Updated value reflected |

---

## Anti-Patterns: Never Do These

### ❌ 1. Error Swallowing
```typescript
// WRONG — hides all bugs
await page.click('button').catch(() => {});
await page.fill('input', value).catch(() => {});
expect(true).toBeTruthy();
```

### ❌ 2. Assert Only the Action, Not the Outcome
```typescript
// WRONG — proves the button exists, not that it works
await page.click('[data-testid="send-btn"]');
await expect(page.locator('.toast')).toBeVisible(); // toast ≠ email sent
// Missing: check Campaign History
```

### ❌ 3. Hardcoded Test Data Without Uniqueness
```typescript
// WRONG — tests conflict when run in parallel or repeatedly
await page.fill('[name="subject"]', 'Test Subject');
// If previous test left "Test Subject" in history, assertion is ambiguous
```

### ❌ 4. Fixed Waits Instead of Assertions
```typescript
// WRONG — fragile and slow
await page.waitForTimeout(3000);
```

### ❌ 5. Testing Only the Happy Path
```typescript
// WRONG — incomplete coverage
test('send email works', ...) // only tests valid data
// Missing: invalid email, empty subject, network error state
```

---

## Correct Patterns

### ✅ Unique Test Data
```typescript
const testId = Date.now();
const subject = `Campaign ${testId}`;
const email = `test+${testId}@example.com`;
```

### ✅ Real Assertions with Playwright's expect()
```typescript
// Playwright auto-retries these until timeout — no need for sleep
await expect(page.locator('text=Sent')).toBeVisible();
await expect(page.locator('[data-testid="count"]')).toHaveText('5');
await expect(page).toHaveURL(/campaign-history/);
```

### ✅ Resilience for Flaky Infrastructure (e.g. Replit/slow servers)
```typescript
// Use toPass() for retries — still FAILS if it never succeeds
await expect(async () => {
  await page.goto(url);
  await expect(page.locator('h1')).toBeVisible();
}).toPass({ timeout: 30_000 });
```

### ✅ Negative Tests
```typescript
test('send email with empty subject shows error', async ({ page }) => {
  await page.goto('/send-email');
  await page.fill('[name="to"]', 'test@example.com');
  // Leave subject empty
  await page.click('[data-testid="send-btn"]');
  await expect(page.locator('[data-error="subject"]')).toBeVisible();
  await expect(page.locator('[data-error="subject"]')).toContainText('required');
  // Verify NOT in history (action should not have completed)
  await page.goto('/campaign-history');
  await expect(page.locator('table tbody tr').first()).not.toContainText('test@example.com');
});
```

---

## Page Object Model (Recommended for Large Suites)

Separate page interactions from test logic for maintainability:

```typescript
// pages/EmailPage.ts
export class EmailPage {
  constructor(private page: Page) {}

  async sendEmail(data: { subject: string; to: string }) {
    await this.page.goto('/send-email');
    await this.page.fill('[name="subject"]', data.subject);
    await this.page.fill('[name="to"]', data.to);
    await this.page.click('[data-testid="send-btn"]');
  }

  async assertSentSuccessfully() {
    await expect(this.page.locator('.success-toast')).toBeVisible();
  }
}

// pages/CampaignHistoryPage.ts
export class CampaignHistoryPage {
  constructor(private page: Page) {}

  async goto() { await this.page.goto('/campaign-history'); }

  async assertEmailExists(subject: string, status = 'Sent') {
    const row = this.page.locator(`tr:has-text("${subject}")`);
    await expect(row).toBeVisible();
    await expect(row.locator('[data-col="status"]')).toHaveText(status);
  }
}

// tests/send-email.spec.ts
test('send email → appears in history', async ({ page }) => {
  const emailPage = new EmailPage(page);
  const historyPage = new CampaignHistoryPage(page);
  const subject = `Test ${Date.now()}`;

  await emailPage.sendEmail({ subject, to: 'qa@test.com' });
  await emailPage.assertSentSuccessfully();

  // Cross-module: verify in history
  await historyPage.goto();
  await historyPage.assertEmailExists(subject);
});
```

---

## Complete Test Coverage Checklist

For each feature, a complete test suite must cover:

**Happy Path:**
- [ ] Full workflow from start to finish
- [ ] Outcome verified in cross-module (not just on the same page)
- [ ] Correct data values appear (not just "something" appears)

**Negative / Validation:**
- [ ] Required fields missing → error message shown
- [ ] Invalid format → specific error message
- [ ] After failure: system state unchanged (entry NOT in history)

**Edge Cases:**
- [ ] Boundary values (max length, min/max numbers)
- [ ] Special characters in text fields
- [ ] Duplicate data handling

**State Verification:**
- [ ] Before action: expected initial state
- [ ] After action: expected final state in ALL affected modules

---

## Test File Structure (Playwright)

```
tests/
├── email-campaign/
│   ├── send-email.spec.ts       ← happy path + cross-module
│   ├── send-email.negative.spec.ts ← validation + error states
│   ├── templates.spec.ts
│   └── campaign-history.spec.ts
├── pages/                        ← Page Object Models
│   ├── EmailPage.ts
│   ├── CampaignHistoryPage.ts
│   └── TemplatePage.ts
└── fixtures/
    └── auth.ts                   ← reusable login fixture
```

---

## Lesson Learned (from real incident)

> **2026-04-18**: 81 automation tests marked PASS. Campaign history showed no new entries since April 10. Root cause: all tests used `expect(true).toBeTruthy()` + `.catch(() => {})`. Tests proved only "the page didn't crash" — not that emails were sent, templates were saved, or any data was persisted. The entire test suite provided zero regression protection.

**Key takeaway:** An automation suite where all tests pass but the feature is broken is MORE dangerous than no tests — it creates false confidence that blocks bug discovery.
