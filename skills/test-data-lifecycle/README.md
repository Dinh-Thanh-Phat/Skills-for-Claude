---
triggers:
  - "test data cleanup"
  - "test account"
  - "generateTestEmail"
  - "random email"
  - "test data accumulate"
  - "cleanup strategy"
  - "test isolation data"
  - "leftover data"
  - "database cleanup"
scope:
  - qa
  - e2e
  - playwright
  - test-generation
---

# Test Data Lifecycle Skill

You are a **Senior QA Engineer** who knows that test data left behind is technical debt that silently degrades test reliability over time.

## The Problem

```typescript
// This runs in CI 10x per day, 5 days a week:
test('RG-001: Đăng ký thành công', async ({ page }) => {
  await reg.fillStep1(generateTestEmail(), 'Password123@');
  // Creates 1 real account in DB per run
  // 10 runs/day × 5 days = 50 accounts/week
  // After 1 month: 200+ orphan test accounts
});
```

Accumulated test data causes:
- DB queries slow down → tests become flaky due to timeouts
- List pages paginate → test data appears on page 2+ → `assertListInTable` fails
- Duplicate detection triggers → test fails with "already exists"
- Dev/QA confusion: "Is this a real user or a test account?"

---

## The 3 Strategies

### Strategy A — Ephemeral Data (Preferred for most cases)

Create data → use it → **delete it in the same test**.

```typescript
test('EL-001: Tạo email list mới', async ({ page }) => {
  const name = `AT-EL-001 Test List ${Date.now()}`;

  await listPage.createList(name);
  await listPage.assertListInTable(name);

  // CLEANUP — always runs, even if test fails
  await listPage.deleteList(name).catch(() => {}); // best-effort cleanup
});
```

Use `test.afterEach` for cleanup if the test might fail before reaching cleanup:

```typescript
test.describe('Email Lists', () => {
  let createdListName: string;

  test.afterEach(async ({ page }) => {
    if (createdListName) {
      const listPage = new EmailListPage(page);
      await listPage.goto();
      await listPage.deleteList(createdListName).catch(() => {});
    }
  });

  test('EL-001: Tạo email list', async ({ page }) => {
    createdListName = `AT-EL-001 ${Date.now()}`;
    await listPage.createList(createdListName);
    await listPage.assertListInTable(createdListName);
  });
});
```

### Strategy B — Seeded Data (For stable reference data)

Use pre-seeded, well-known test data that already exists in the test environment. Never create or delete it in tests.

```typescript
// constants.ts — fixed test data that always exists
export const TEST_LIST = 'Phat testing list';       // pre-seeded
export const TEST_EMAILS = {
  primary: 'thanhphat12tna234@gmail.com',           // pre-seeded account
};

// tests use it but NEVER modify or delete it
test('SE-010: Gửi email theo Email List', async ({ page }) => {
  await sendPage.selectEmailList(TEST_LIST); // stable reference
});
```

**Rules for seeded data:**
- Prefix with `[SEED]` or document clearly — never let tests delete it
- Keep a `test-data/seeds.md` documenting what seeded data exists and why
- If a test needs to ADD to seeded data, it must clean up the addition

### Strategy C — Tagged for Cleanup (For accounts/data that can't be cleaned inline)

When you must create data that can't be easily cleaned up (e.g., user accounts requiring admin access to delete), tag it clearly for periodic cleanup:

```typescript
// Always use a recognizable prefix
const testEmail = `at-cleanup-${Date.now()}@test-incard.com`;
// Dev/admin can run: DELETE FROM users WHERE email LIKE 'at-cleanup-%@test-incard.com'
```

---

## Decision Matrix

| Data type | Strategy | Why |
|---|---|---|
| Email list created in test | A — delete in afterEach | Easy to delete via UI |
| Template created in test | A — delete in afterEach | Easy to delete via UI |
| User account created in test | C — tag for cleanup | May need admin to delete |
| Subscribers added to shared list | A — delete after adding | Affects shared list count |
| Pre-existing test list/account | B — seeded, never touch | Stable baseline for all tests |
| Campaign sent in test | B — accept accumulation | Read-only history, low risk |

---

## Naming Conventions

```typescript
// ✅ Good — clearly test data, includes test ID for traceability
`AT-EL-001 Test List ${Date.now()}`
`[AT-SE-001] Send Test ${Date.now()}`
`at-cleanup-${Date.now()}@test-incard.com`

// ❌ Bad — looks like real data, no traceability
`My New List`
`testuser@gmail.com`
`Newsletter Campaign`
```

---

## For Register/Account Tests Specifically

```typescript
// ❌ Current pattern — creates real accounts, no cleanup
await reg.fillStep1(generateTestEmail(), 'Password123@');

// ✅ Better — use a dedicated test domain + track created accounts
const testEmail = `at-rg-${Date.now()}@test-automation.incard.com`;
// After test, record email to a cleanup list
// Periodically: devs DELETE FROM users WHERE email LIKE '%@test-automation.incard.com'
```

Or even better: **ask dev for a teardown API or test-mode flag** that auto-cleans up test accounts.

---

## Checklist — Test Data Review

- [ ] Does this test create any persistent data (accounts, lists, templates, records)?
- [ ] Is there a cleanup path (UI delete, API, afterEach hook)?
- [ ] If using seeded data, does the test mutate it? (If yes → it must restore it)
- [ ] Are created entities named with a recognizable test prefix?
- [ ] After 100 CI runs, will leftover data cause other tests to fail?
- [ ] Is there a periodic cleanup mechanism or runbook for test accounts?
