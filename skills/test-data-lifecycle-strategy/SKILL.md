---
name: test-data-lifecycle-strategy
description: Test data cleanup, isolation, and lifecycle management - beforeEach/afterEach, tagged prefixes, state cleanup
type: skill
---

# Test Data Lifecycle & Cleanup Strategy

## Problem
Tests create data (users, ports, contacts) but don't clean up → data pollution, flaky tests, false dependencies between tests.

## Rule: ACID Test Data

Each test must be **Atomic** (independent), **Consistent** (starts clean), **Isolated** (no shared state), **Durable** (cleanup happens even on failure).

---

## Strategy 1: Tagged Prefix (Simplest)

All test data uses a unique prefix + timestamp. Cleanup is optional (data isolated by tag).

**Pros:** Simple, no cleanup code needed, data persists for manual inspection  
**Cons:** Data accumulates, database grows

### Implementation

```ts
const TEST_PREFIX = 'AutoTest-';
const ts = Date.now();
const testEmail = `${TEST_PREFIX}${ts}@test.com`;
const testName = `${TEST_PREFIX}-${ts}`;
```

**Cleanup (Optional):**
```ts
test.afterAll(async ({ request }) => {
  // Admin endpoint to delete all data with TEST_PREFIX
  await request.delete('/api/admin/cleanup', {
    data: { prefix: TEST_PREFIX },
  });
});
```

**When to use:** Development, CI with large database, manual testing  
**Current project:** ✅ Using this approach (AutoTest-CSV, AutoTest-FileDownload)

---

## Strategy 2: BeforeEach/AfterEach (Recommended)

Clean state before test, cleanup after test (even on failure).

**Pros:** Guaranteed isolation, no data pollution  
**Cons:** Requires cleanup code, slower (setup + teardown per test)

### Implementation

```ts
test.describe('User Management', () => {
  let admin: AdminPage;
  let createdUserIds: string[] = [];

  test.beforeEach(async ({ page }) => {
    admin = new AdminPage(page);
    await admin.goto();
    createdUserIds = [];
  });

  test.afterEach(async () => {
    // Cleanup: delete all users created in this test
    for (const userId of createdUserIds) {
      await admin.deleteUserById(userId);  // API call
    }
  });

  test('ADM-U001: Create user → appears in list', async ({ page }) => {
    const email = `at-adm-u001-${Date.now()}@test.example.com`; // unique — parallel-safe
    const result = await admin.addUser({
      name: 'Test User',
      email,
      password: 'Pass123@',
    });
    createdUserIds.push(result.userId);

    await admin.gotoUsers();
    await expect(page.getByText(email)).toBeVisible();
  });
});
```

**When to use:** Reliable backends, critical tests, CI/CD  
**Best for:** Database state needs strict isolation

---

## Strategy 3: Seeded Data (Setup Once)

Create known data before tests, reference it, cleanup after all tests.

**Pros:** Fast (no per-test setup), realistic (shared state like prod), clear test names  
**Cons:** Tests run in order (can't parallelize), one failure affects others

### Implementation

```ts
test.describe('Port Management', () => {
  let seededPortId: string;

  test.beforeAll(async ({ request }) => {
    // Create once for all tests
    const response = await request.post('/api/ports', {
      data: { name: 'CMIT', location: 'Ho Chi Minh' },
    });
    expect(response.ok()).toBe(true);
    seededPortId = (await response.json()).id; // json() is async — must await
  });

  test.afterAll(async ({ request }) => {
    // Cleanup once after all tests
    await request.delete(`/api/ports/${seededPortId}`);
  });

  test('CSP-001: Export port data → contains seeded port', async ({ page }) => {
    // Use seededPortId in test
    await page.goto(`/admin/ports/${seededPortId}`);
    await expect(page.getByText('CMIT')).toBeVisible(); // without await this ALWAYS passes
  });

  test('CSP-002: Filter ports → shows seeded port', async ({ page }) => {
    // Same seeded data
    await page.goto('/admin/ports');
    await page.getByPlaceholder('search').fill('CMIT');
    expect(page.getByText('CMIT')).toBeVisible();
  });
});
```

**When to use:** Integration tests, shared domain data, API testing

---

## Strategy 4: Database Rollback (Most Reliable)

Wrap each test in a transaction, rollback after completion.

**Pros:** Guaranteed cleanup even on crash, no cleanup code needed  
**Cons:** Requires DB transaction support, backend config

### Implementation (Backend Required)

```ts
test.describe('User Management', () => {
  const transactionIds: string[] = [];

  test.beforeEach(async ({ request }) => {
    // Start transaction
    const txnResponse = await request.post('/api/admin/transaction/begin');
    transactionIds.push(txnResponse.json().txn_id);
  });

  test.afterEach(async ({ request }) => {
    // Rollback transaction
    const txnId = transactionIds.pop();
    await request.post(`/api/admin/transaction/rollback/${txnId}`);
  });

  test('ADM-U001: Create user', async ({ request }) => {
    // Any changes auto-rollback after test
    await request.post('/api/users', {
      data: { email: 'test@example.com', name: 'Test' },
    });
    // No cleanup needed — rollback in afterEach
  });
});
```

**When to use:** Critical workflows, financial data, production-like testing  
**Setup requirement:** Backend must support transactions

---

## Cleanup Checklist

For each test creating data, answer:

- [ ] **What data?** (Users, ports, contacts, tickets)
- [ ] **How to identify?** (ID, email prefix, timestamp)
- [ ] **How to cleanup?** (API delete, DB rollback, tagged prefix)
- [ ] **When?** (beforeEach, afterEach, afterAll, manual)
- [ ] **On failure?** (Cleanup runs even if test fails)

## Examples by Test Type

| Test Type | Strategy | Example |
|-----------|----------|---------|
| User CRUD | BeforeEach/AfterEach | Create user, test, delete via API |
| File upload | Tagged prefix | All uploads use `AutoTest-${ts}` |
| Port import | BeforeAll/AfterAll | Seed ports once, all tests use them |
| Ticket workflow | Database rollback | Wrap in transaction, auto-rollback |
| Admin actions | POM with cleanup | POM method records created IDs, afterEach deletes |

## Anti-Patterns ❌

```ts
// ❌ WRONG: No cleanup
test('Create user', async ({ page }) => {
  await admin.addUser({ ... });
  // User persists → test pollution
});

// ❌ WRONG: Cleanup in test
test('Create and delete user', async ({ page }) => {
  const user = await admin.addUser({ ... });
  await admin.deleteUser(user.id);  // Mixes setup/test/cleanup
});

// ❌ WRONG: Global cleanup
let userId: string;
test('Create user 1', async () => {
  const user = await admin.addUser({ ... });
  userId = user.id;  // Global state
});
test.afterAll(async () => {
  await admin.deleteUser(userId);  // Cleanup happens too late
});
```

## References

- [Test Data Cleanup Guide](https://www.workwithloop.com/blog/keeping-your-test-data-clean-with-beforeeach-aftereach)
- [Test Isolation Principles](https://app.studyraid.com/en/read/11292/352303/test-isolation-principles)
- [Playwright Lifecycle Hooks](https://www.browserstack.com/guide/playwright-before-all)
- [CI/CD Cleanup Strategies](https://www.thegreenreport.blog/articles/techniques-for-effective-test-data-cleanup-in-cicd/)

---

## Cross-references (test data — 3 skills, 1 goal)

- **this skill** — "nên dùng strategy nào?" decision guide (dùng khi planning)
- **`test-data-lifecycle`** — rule "always clean up" + 3 strategies phổ biến (dùng khi viết test)
- **`test-isolation`** — broader isolation: state, cookies, auth, parallel (dùng khi test fail do shared state)
