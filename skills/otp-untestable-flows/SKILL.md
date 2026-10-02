---
name: otp-untestable-flows
description: Plan OTP and email verification test infrastructure BEFORE writing auth tests to avoid permanently-skipped tests. Use when writing tests involving OTP, email verification, magic links, forgot password, or 2FA. Triggers on: "OTP", "email verification", "forgot password test", "reset password", "email link", "magic link", "2FA", "untestable flow", "email interception".
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

Use Mailhog, Mailtrap, or Mailpit to capture emails sent to test addresses, then extract OTP programmatically.

> ⚠️ The code below is **MailHog-specific** (`/api/v2/messages`, `Content.Headers.To`). MailHog is
> effectively unmaintained (no release since ~2020 — UNVERIFIED this session); Mailpit and Mailtrap
> have different APIs/response shapes (Mailpit uses `/api/v1/...` — exact schema UNVERIFIED). Adapt the
> fetch + JSON paths to the tool you actually run, and throw if nothing matches (don't return empty).

```typescript
// MailHog v2 API only
async function getOtpFromEmail(recipientEmail: string): Promise<string> {
  const response = await fetch('http://localhost:8025/api/v2/messages');
  const data = await response.json();
  const email = data.items.find(m => m.Content.Headers.To[0].includes(recipientEmail));
  const body = email.Content.Body;
  const otp = body.match(/\b(\d{6})\b/)?.[1];
  if (!otp) throw new Error('OTP not found in email');
  return otp;
}

await fp.submitEmail(testEmail);
const otp = await getOtpFromEmail(testEmail);
await fp.fillOtp(otp);
await fp.assertStepIs(3);
```

### Solution 2: Dev-Mode Fixed OTP

Ask dev to add a fixed OTP for known test accounts in staging:

```typescript
export const TEST_OTP = '000000'; // dev-configured bypass for test accounts

test('FP-007: OTP đúng → step 3', async ({ page }) => {
  await fp.submitEmail(VALID_CREDENTIALS.email);
  await fp.fillOtp(TEST_OTP); // always-valid in test env
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

| Auth Action | Must Also Verify |
|---|---|
| Register → success | Dashboard loads with user's name/email visible |
| Login → success | User session persists after page reload |
| Reset password → success | Can LOGIN with new password (FP-009 pattern) |
| Logout | Protected pages redirect to login |
| Register new user | (If admin panel exists) User appears in Users list |

```typescript
// FP-009 pattern — the most important cross-module auth test
test('FP-009: Reset password → đăng nhập với mật khẩu mới', async ({ page }) => {
  const newPassword = 'NewPass123@';

  await fp.submitEmail(VALID_CREDENTIALS.email);
  await fp.fillOtp(await getOtpFromEmail(VALID_CREDENTIALS.email));
  await fp.fillNewPassword(newPassword, newPassword);
  await fp.assertRedirectedToLogin();

  // Cross-verify — old password no longer works
  await loginPage.login(VALID_CREDENTIALS.email, VALID_CREDENTIALS.password);
  await loginPage.assertErrorVisible();

  // Cross-verify — new password works
  await loginPage.login(VALID_CREDENTIALS.email, newPassword);
  await loginPage.assertRedirectedToDashboard();
});
```

---

## SMS OTP vs Email OTP

SMS OTP infrastructure differs from email:
- **Twilio test credentials** receive SMS without sending — query test inbox via API
- **MessageBird Inbox** — similar
- **Dev-mode fixed SMS**: ask dev to make staging accept a hardcoded code (e.g. `123456`)

```typescript
// Twilio test-receiver pattern
async function getSmsOtp(phoneNumber: string): Promise<string> {
  const r = await fetch(`https://api.twilio.com/.../Messages.json?To=${phoneNumber}`, {
    headers: { Authorization: 'Basic ' + btoa(`${SID}:${TOKEN}`) },
  });
  const body = (await r.json()).messages[0].body;
  return body.match(/\b(\d{6})\b/)![1];
}
```

## TOTP Authenticator App (Google Authenticator / Authy)

For tests of TOTP 2FA, generate the code locally from the shared secret.
**otplib v13** (13.5.0, 2026-08-21) **removed the `authenticator` export** — the old
`authenticator.generate(secret)` no longer exists. Current API (async):
```typescript
import { generate } from 'otplib';             // npm i otplib  (v13+)
const secret = process.env.TOTP_TEST_SECRET!;   // shared with test user setup
const code = await generate({ secret });
await page.getByLabel('6-digit code').fill(code);
```
Sync variant `generateSync` needs a sync crypto plugin (`@otplib/plugin-crypto-node`). Pinned to
v12? See the v12 adapter migration guide: https://otplib.yeojz.dev/guide/v12-adapter.html

## Mobile (Maestro / Android) OTP paths

The Playwright helpers above don't apply inside a Maestro flow. Options, best first:
1. **Same infra, fetched by script** — call the dev bypass API / mail-catcher from a Maestro
   `runScript` (GraalJS `http.get`) and `inputText: ${output.otp}`. Same "ask dev first" rule applies.
2. **Fixed test OTP / test-number prefix** agreed with dev (e.g. a staging rule for test phone numbers).
3. **Android emulator SMS** — `adb emu sms send 5551234 "Your code is 123456"` delivers a real SMS to
   the emulator (emulator only; a real device needs a real SMS). See `android-17-qa-gate`.
4. **OTP shown on screen** (dev builds / demo) — `extractTextWithAI` (Maestro Cloud login required,
   experimental, `optional: true` by default → set `optional: false`). See `maestro-ai-assertions`.
Physical iOS devices are not supported by Maestro CLI 2.11.0 — plan iOS OTP tests on simulators.

## Rate-Limit on Resend OTP

Many systems lock OTP requests after N retries within X minutes. Test the boundary:
```typescript
test('OTP resend rate-limit kicks in after 3 attempts in 60s', async ({ page }) => {
  for (let i = 0; i < 3; i++) await page.click('text=Resend code');
  await page.click('text=Resend code');
  await expect(page.getByText(/too many attempts|please wait/i)).toBeVisible();
});
```

## Checklist — Before Writing Auth/OTP Tests

- [ ] Does any part of this flow require email/SMS to proceed?
- [ ] If yes: have I asked dev about email interception or OTP bypass?
- [ ] If no bypass exists: have I created a beads issue to track the infrastructure gap?
- [ ] Have I marked manual tests with clear instructions AND a link to the tracking issue?
- [ ] Does the happy-path auth test include cross-module verification?
- [ ] Is the most critical end-to-end flow (reset password → login with new password) covered?
