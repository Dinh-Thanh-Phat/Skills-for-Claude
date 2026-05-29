---
triggers:
  - "OTP"
  - "email verification"
  - "forgot password test"
  - "reset password"
  - "email link"
  - "magic link"
  - "2FA"
  - "untestable flow"
  - "email interception"
  - "automation OTP"
scope:
  - qa
  - e2e
  - playwright
  - test-planning
  - authentication
---

# OTP / Untestable Flows Skill

You are a **Senior QA Engineer** who plans for test infrastructure gaps BEFORE writing tests — not after.

## The Problem

OTP and email-based flows are the most common "permanently skipped" tests in QA projects:

```typescript
// Graveyard pattern — all critical auth tests are unreachable
test.skip('FP-007: OTP đúng → chuyển sang bước 3', ...)  // OTP needs real email
test.skip('FP-008: OTP sai → hiện lỗi', ...)
test.skip('FP-009: Reset password → login với mật khẩu mới', ...)  // Most critical flow!
```

**FP-009 is the most important test in the entire auth module** (proves the full reset flow works end-to-end), yet it is permanently unreachable because OTP automation was never planned.

---

## Rule: Ask Before You Write

**Before writing ANY test that touches OTP / email verification / magic links:**

Stop. Ask the dev team these questions first:

```
1. Does the test environment have email interception? (Mailhog, Mailtrap, Mailpit?)
2. Is there a dev-mode OTP bypass? (Fixed OTP code like "000000" in staging?)
3. Is there an API endpoint to retrieve the OTP directly?
4. Can we add a test-mode header that skips OTP verification?
5. Is there a seeded OTP in the test DB?
```

If the answer to ALL of these is "no" → **raise this as a blocker** and create an issue BEFORE writing the test.

---

## The 4 Solutions (In Order of Preference)

### Solution 1: Email Interception (Best)

Use Mailhog, Mailtrap, or Mailpit to capture emails sent to test addresses, then extract OTP programmatically:

```typescript
// Using Mailhog API to get OTP
async function getOtpFromEmail(recipientEmail: string): Promise<string> {
  const response = await fetch('http://localhost:8025/api/v2/messages');
  const data = await response.json();
  const email = data.items.find(m => m.Content.Headers.To[0].includes(recipientEmail));
  const body = email.Content.Body;
  const otp = body.match(/\b(\d{6})\b/)?.[1]; // extract 6-digit OTP
  if (!otp) throw new Error('OTP not found in email');
  return otp;
}

// In test:
await fp.submitEmail(testEmail);
const otp = await getOtpFromEmail(testEmail);
await fp.fillOtp(otp);
await fp.assertStepIs(3);
```

### Solution 2: Dev-Mode Fixed OTP

Ask dev to add a fixed OTP for known test accounts in staging:

```typescript
// constants — only works on staging/test environment
export const TEST_OTP = '000000'; // dev-configured bypass for test accounts

test('FP-007: OTP đúng → step 3', async ({ page }) => {
  await fp.submitEmail(VALID_CREDENTIALS.email); // known test account
  await fp.fillOtp(TEST_OTP);                    // always-valid in test env
  await fp.assertStepIs(3);
});
```

### Solution 3: API Bypass

Ask dev for a test API endpoint that returns the OTP for a given email:

```typescript
async function getTestOtp(email: string): Promise<string> {
  const res = await fetch(`${BASE_URL}/api/test/get-otp?email=${email}`, {
    headers: { 'X-Test-Mode': 'true' }
  });
  const { otp } = await res.json();
  return otp;
}
```

### Solution 4: Explicit Manual Tagging (Last resort)

If none of the above is possible, mark tests clearly as manual with context:

```typescript
test.skip('FP-007: [MANUAL] OTP đúng → step 3', async ({ page }) => {
  /**
   * MANUAL ONLY — requires OTP from email.
   * Infrastructure needed: Mailhog or dev-mode OTP bypass.
   * Issue: [link to beads issue tracking this gap]
   * Steps to run manually:
   *   1. Trigger FP-001 to send OTP to thanhphat12tna234@gmail.com
   *   2. Get OTP from email inbox
   *   3. Replace '123456' below with actual OTP
   *   4. Remove test.skip() and run
   */
  const otp = '123456'; // TODO: replace with real OTP
  await fp.fillOtp(otp);
});
```

---

## Cross-Module Verification for Auth Flows

Auth flows that are testable should ALWAYS include cross-module verification:

| Auth Action | Must Also Verify |
|---|---|
| Register → success | Dashboard loads with user's name/email visible |
| Login → success | User session persists after page reload |
| Reset password → success | Can LOGIN with new password (FP-009 pattern) |
| Logout | Protected pages redirect to login |
| Register new user | (If admin panel exists) User appears in Users list |

```typescript
// FP-009 pattern — the most important cross-module auth test
test.skip('FP-009: [MANUAL] Reset password → đăng nhập với mật khẩu mới', async ({ page }) => {
  const newPassword = 'NewPass123@';

  // Step 1: Reset password
  await fp.submitEmail(VALID_CREDENTIALS.email);
  await fp.fillOtp(await getOtpFromEmail(VALID_CREDENTIALS.email)); // needs infrastructure
  await fp.fillNewPassword(newPassword, newPassword);
  await fp.assertRedirectedToLogin();

  // Step 2: Cross-verify — old password no longer works
  await loginPage.login(VALID_CREDENTIALS.email, VALID_CREDENTIALS.password);
  await loginPage.assertErrorVisible();

  // Step 3: Cross-verify — new password works
  await loginPage.login(VALID_CREDENTIALS.email, newPassword);
  await loginPage.assertRedirectedToDashboard();
});
```

---

## Ordering Bug Regression Tests

When you discover a UI ordering constraint (e.g., "tab switch resets recipient fields"), add an explicit regression test:

```typescript
test('REGRESSION: Tab switch không reset recipient fields đã điền', async ({ page }) => {
  // Fill recipients FIRST
  await sendPage.selectDirectRecipients();
  await sendPage.fillEmailAddresses([TEST_EMAILS.primary]);

  // Switch tab — this previously reset the fields
  const fromTemplateTab = page.getByRole('tab', { name: 'From Template' });
  await fromTemplateTab.click();

  // Switch back to Manual
  await page.getByRole('tab', { name: 'Manual' }).click();

  // Recipients should still be there
  const emailContent = await page.getByRole('textbox', { name: /email addresses/i }).inputValue();
  expect(emailContent).toContain(TEST_EMAILS.primary);
});
```

---

## Checklist — Before Writing Auth/OTP Tests

- [ ] Does any part of this flow require email/SMS to proceed?
- [ ] If yes: have I asked dev about email interception or OTP bypass?
- [ ] If no bypass exists: have I created a beads issue to track the infrastructure gap?
- [ ] Have I marked manual tests with clear instructions AND a link to the tracking issue?
- [ ] Does the happy-path auth test include cross-module verification (e.g., login → dashboard visible)?
- [ ] Are there regression tests for any ordering bugs or UI quirks discovered during testing?
- [ ] Is the most critical end-to-end flow (e.g., reset password → login with new password) covered?
