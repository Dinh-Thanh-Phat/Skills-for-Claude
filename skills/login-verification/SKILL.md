---
name: login-verification
description: Always verify test credentials work manually before writing automated login tests — prevents entire suites failing because of invalid accounts. Use when setting up a new test environment, when all tests fail at beforeEach, or when writing login helper functions. Triggers on: "writing login helper", "test credentials", "all tests fail beforeEach", "login not working", "beforeEach fails", "test account", "staging credentials", "auth smoke".
type: skill
scope: playwright, e2e, automation, test-setup
triggers:
  - "writing login helper"
  - "test credentials"
  - "all tests fail beforeEach"
  - "login not working"
  - "beforeEach fails"
  - "auth smoke"
---

# Login Verification

## Purpose

Prevent 33 misleading test failures because test credentials are invalid. A broken login account makes every feature test fail at `beforeEach` — that's an environment bug, not a feature bug.

## Rules

**1. Manually verify login before any automation.**
Open the target URL in a real browser, log in with the exact test credentials, confirm dashboard loads. Do this yourself — don't assume.

**2. Credentials from `.env` only — never hardcoded.**
```typescript
// .env (gitignored)
TEST_EMAIL=verified@example.com
TEST_PASSWORD=SecurePass123!

// test helper
const CREDENTIALS = {
  email: process.env.TEST_EMAIL!,
  password: process.env.TEST_PASSWORD!,
};
```

**3. Verify account state before automating:**
- Email confirmed/verified?
- Account not locked/suspended?
- MFA disabled for test account?
- Password not expired?
- Correct role/permissions for the features being tested?

**4. Add auth smoke test as FIRST test in every suite.**
```typescript
test('auth smoke: login succeeds', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.TEST_EMAIL!);
  await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page).toHaveURL(/dashboard/, { timeout: 60000 });
});
```

**5. Post-login assertion in `beforeEach` — confirm login actually worked.**
```typescript
test.beforeEach(async ({ page }) => {
  await login(page);
  await expect(page).not.toHaveURL(/login/); // confirm we're in
  await expect(page.getByRole('navigation')).toBeVisible({ timeout: 10000 });
});
```

**6. Login helper surfaces the actual error message.**
```typescript
async function login(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.TEST_EMAIL!);
  await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: 'Login' }).click();

  // ⚠️ Do NOT check `page.url()` right after click() — the redirect hasn't happened yet,
  // so the URL is still /login even on a SUCCESSFUL login → false "Login failed".
  // Wait (web-first) for the redirect; only on failure read the on-page error and rethrow.
  try {
    await expect(page).not.toHaveURL(/\/login/, { timeout: 30_000 });
  } catch (e) {
    const alerts = page.locator('[role="alert"], .error, .notification--error');
    const errorMsg = (await alerts.allTextContents()).join(' | ') || '(no error message found)';
    throw new Error(
      `Login failed. Page shows: "${errorMsg}". Check credentials and account status.`,
      { cause: e },
    );
  }
}
```

**7. Cold-start environments (Replit): increase login timeout to 60-90s.**
```typescript
await expect(page).toHaveURL(/dashboard/, { timeout: 90000 });
```

## Credential Checklist (run before first session on any environment)

```
[ ] Open browser → navigate to login URL manually
[ ] Enter test credentials → submit
[ ] No "email not verified" error
[ ] No "account suspended/locked" error
[ ] Redirected to expected post-login page
[ ] Account has correct role for tests being run
[ ] MFA disabled for test account
[ ] Record working credentials in .env (not in test file)
[ ] .env added to .gitignore
```

## When All Tests Fail at beforeEach

Diagnosis order:
1. Run auth smoke test alone — does it pass?
2. If smoke fails → check the error message on the login page
3. Verify account state manually in browser
4. Check if environment is up (`curl -I https://your-app.com`)
5. ONLY debug feature tests after login confirmed working

## Anti-Patterns

| Anti-Pattern | Problem |
|---|---|
| Assuming credentials from memory are valid | Passwords expire, accounts get locked |
| Hardcoded credentials in spec files | Security risk, hard to rotate |
| No post-login URL assertion in `beforeEach` | Login "succeeds" but user still on `/login` |
| 30s timeout on cold-start environment | First request wakes instance — takes 30-60s |
| Running 33 tests when login is broken | All fail — noise drowns real bugs |

