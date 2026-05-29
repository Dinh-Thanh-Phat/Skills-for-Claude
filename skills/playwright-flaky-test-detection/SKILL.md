---
name: playwright-flaky-test-detection
description: Detect data dependencies, timeouts, race conditions causing flaky tests - fix before they ship. Triggers on: "flaky test", "test lúc pass lúc fail", "intermittent failure", "passes sometimes", "diagnosis flaky".
type: skill
triggers:
  - "flaky test"
  - "test lúc pass lúc fail"
  - "intermittent failure"
  - "passes sometimes"
  - "randomly fails"
  - "diagnosis flaky"
---

# Flaky Test Detection & Prevention

> **Cross-ref:** This skill (root-cause focus) is paired with `flaky-test-prevention`
> (prevention rules) and `e2e-test-stability` (the underlying stability principles).
> All three agree on the same rules: no `waitForTimeout`, no `networkidle`, prefer
> web-first assertions, isolate test data. Differences:
> - **this file** → diagnosis-from-symptom workflow (timeout / data dep / race / network)
> - **flaky-test-prevention** → 5-cause framework + selector priority
> - **e2e-test-stability** → patterns for the 7 most-common flake sources

## Definition
**Flaky test:** Test passes sometimes, fails sometimes, without code changes. Usually caused by data dependencies, timeouts, or race conditions.

---

## Root Causes & Detection

### Cause 1: Data Dependency (Hardcoded IDs)

**Symptom:** Test passes on first run, fails on second run

```ts
// ❌ FLAKY: Depends on specific port existing
test('CSP-001: Delete port CMIT', async ({ page }) => {
  await page.goto('/admin/ports');
  await page.getByText('CMIT').click();  // Fails if CMIT not in system
  await admin.deletePort('CMIT');
});
```

**Fix:** Create test-specific data

```ts
// ✅ FIXED: Creates data before test
test('CSP-001: Delete port', async ({ page }) => {
  const portName = `AutoTest-Port-${Date.now()}`;
  
  // Create port for this test
  await admin.createPort(portName);
  
  // Now test on specific data
  await page.goto('/admin/ports');
  await page.getByText(portName).click();
  await admin.deletePort(portName);
});
```

**Detection:** Search test code for hardcoded names
```bash
grep -n "CMIT\|TestUser\|admin@test" tests/**/*.spec.ts
```

---

### Cause 2: Timeout Too Short

**Symptom:** Test fails randomly, especially under load or slow network

```ts
// ❌ FLAKY: 1s timeout might be too short
const element = await page.locator('.result').isVisible({ timeout: 1_000 });
```

**Fix:** Measure actual duration, set timeout to actual × 1.5

```ts
// Measure in manual test:
console.time('export');
await page.getByRole('button', { name: 'Export' }).click();
await page.waitForEvent('download');
console.timeEnd('export');  // Output: ~800ms

// Set timeout generously (800 × 1.5 = 1200ms)
const downloadPromise = page.waitForEvent('download', { timeout: 2_000 });
```

**Detection:** Watch for `timeout:` values < 2000ms
```bash
grep -n "timeout: [0-9]000" tests/**/*.spec.ts
```

---

### Cause 3: Race Condition (Click Before Element Ready)

**Symptom:** Test fails intermittently, passes on retry

```ts
// ❌ FLAKY: Might click before dropdown is populated
await page.getByPlaceholder('Search port').fill('CMIT');
await page.locator('.ant-select-item-option').first().click();  // Not visible yet?
```

**Fix:** Wait for element before action — **NO `waitForTimeout`**

```ts
// ✅ FIXED: Web-first assertion handles the wait for dropdown animation
await page.getByPlaceholder('Search port').fill('CMIT');
const option = page.locator('.ant-select-item-option').filter({ hasText: 'CMIT' });
await expect(option).toBeVisible();   // auto-retries through the animation
await option.click();

// ❌ NEVER use waitForTimeout for animations — use the web-first assertion
// or page.clock.fastForward() if you must skip a specific delay.
```

**Detection:** Tests pass when run alone, fail in parallel
```bash
# Run tests in parallel
npx playwright test --workers=4

# If tests fail, but pass with --workers=1, likely race condition
```

---

### Cause 4: Network Unpredictability

**Symptom:** Test works locally, fails in CI

```ts
// ❌ FLAKY: Network might be slow in CI
await admin.createPort();
await page.goto('/admin/ports');
const visible = await page.getByText('port-name').isVisible({ timeout: 3_000 });
```

**Fix:** Wait for the specific API response, NOT `networkidle`

```ts
// ✅ FIXED: Sync with the actual create-port response
const [resp] = await Promise.all([
  page.waitForResponse(r => r.url().includes('/api/ports') && r.request().method() === 'POST' && r.ok()),
  admin.createPort(),
]);
await page.goto('/admin/ports');
await expect(page.getByText('port-name')).toBeVisible();

// ❌ NEVER use waitForLoadState('networkidle') on SPAs / WebSocket / polling apps —
//    it hangs because something is always in flight.
```

**Detection:** Tests fail in CI, pass locally; add network logging
```bash
# Run with network tracing
npx playwright test --trace=on

# Review trace: Inspect → Network tab
```

---

### Cause 5: State Contamination (Test Order Dependency)

**Symptom:** Test passes alone, fails when run after another test

```ts
// Test A: Creates user
test('A: Create user', async ({ page }) => {
  await admin.createUser('test@example.com');
});

// Test B: Deletes all users (assumes none exist)
test('B: Delete all users should work', async ({ page }) => {
  const users = await page.locator('.user-row').count();
  expect(users).toBe(0);  // ❌ FLAKY: User from Test A still exists
});
```

**Fix:** Each test cleans up after itself

```ts
test.afterEach(async ({ request }) => {
  // Delete all AutoTest-* users
  await request.delete('/api/admin/cleanup?prefix=AutoTest');
});

test('B: Delete all users', async ({ page }) => {
  const users = await page.locator('.user-row').count();
  expect(users).toBe(0);  // ✅ FIXED: Prior tests cleaned up
});
```

**Detection:** Run tests in different order
```bash
# Run in reverse
npx playwright test --order=reverse

# Run with randomized seed
npx playwright test --order=random
```

---

## Flaky Test Detection Checklist

For each test, ask:

- [ ] **Does test create data?** Yes → cleanup in afterEach
- [ ] **Does test depend on existing data?** Yes → create own test data
- [ ] **Timeout < 2 seconds?** Yes → increase to measured × 1.5
- [ ] **Using hardcoded IDs or names?** Yes → use dynamic data
- [ ] **Click/fill without waiting?** Yes → add explicit wait
- [ ] **Passes alone, fails in parallel?** Yes → likely race condition
- [ ] **Passes locally, fails in CI?** Yes → likely timing or network issue

---

## Debugging Failing Tests

### Step 1: Isolate the Test

```bash
# Run just this test
npx playwright test delete-operations.spec.ts -g "DEL-001"

# Run it 10 times to see if flaky
npx playwright test delete-operations.spec.ts -g "DEL-001" --workers=1 --repeat-each=10
```

### Step 2: Record Trace

```bash
# Run with trace
npx playwright test delete-operations.spec.ts -g "DEL-001" --trace=on

# Open trace viewer
npx playwright show-trace trace/delete-operations-DEL-001-chromium/trace.zip
```

### Step 3: Add Debug Logs

```ts
test('DEL-001: Delete user', async ({ page }) => {
  console.log('1. Navigate to users');
  await admin.gotoUsers();
  
  console.log('2. Create user');
  const email = `test-${Date.now()}@example.com`;
  await admin.addUser({ email, ... });
  
  console.log('3. Verify user visible', email);
  await expect(page.getByText(email)).toBeVisible();
  
  console.log('4. Delete user');
  await admin.deleteUser(email);
  
  console.log('5. Verify deleted');
  const exists = await page.getByText(email).isVisible({ timeout: 2_000 }).catch(() => false);
  console.log('User exists after delete:', exists);
  expect(exists).toBe(false);
});
```

### Step 4: Compare Pass vs. Fail

- [ ] Check trace video side-by-side
- [ ] Check DevTools console for errors
- [ ] Check Network tab for failed requests
- [ ] Check browser logs (page.on('console'))

---

## Common Fixes

| Issue | Quick Fix |
|-------|-----------|
| Element not visible | `await expect(el).toBeVisible()` before action |
| Dropdown not populated | `await page.waitForTimeout(500)` after fill |
| Data not persisted | `await page.waitForLoadState('networkidle')` |
| Dialog not appearing | `await page.waitForEvent('dialog')` before click |
| File not uploaded | Check upload progress, use `Promise.all([waitForEvent, click])` |

---

## Prevention Best Practices

1. **Use unique test data** — `AutoTest-${Date.now()}` for every test
2. **Cleanup after each test** — `afterEach()` with data deletion
3. **Wait for specific API response** — `page.waitForResponse(...)` (NOT `networkidle`, which hangs on SPAs)
4. **Measure timeouts** — Don't guess, use actual × 1.5
5. **Run tests parallel** — Find race conditions early
6. **Run with randomized order** — Find state dependencies
7. **Record failures** — Use trace/video to debug CI failures

---

## References

- [Avoiding Flaky Tests](https://betterstack.com/community/guides/testing/avoid-flaky-playwright-tests/)
- [Detect & Fix Flaky Tests](https://www.browserstack.com/guide/playwright-flaky-tests)
- [Debugging Timeouts](https://currents.dev/posts/debugging-playwright-timeouts)
- [Automation Checklist](https://testdino.com/blog/playwright-automation-checklist/)
