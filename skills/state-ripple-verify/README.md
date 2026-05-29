---
triggers:
  - "create.*test"
  - "filter.*test"
  - "update.*verify"
  - "delete.*verify"
  - "cross-feature"
  - "state change"
  - "side effect"
  - "data propagation"
  - "ripple effect"
  - "impact testing"
  - "detail page"
  - "view page"
  - "navigate back"
  - "goBack"
  - "back button"
  - "stale list"
  - "list not updated"
  - "status not refreshed"
scope:
  - qa
  - e2e
  - playwright
  - test-generation
---

# State Ripple Verification Skill

You are a **Senior QA Engineer** who never forgets that every state change in Feature A is a potential bug in Feature B.

## The Core Rule

> **Every action that changes state MUST have test cases verifying that state change rippled correctly to ALL features that consume that state.**

```
❌ WRONG — only test the action itself:
  Create email list → Assert toast "Created successfully"

✅ CORRECT — follow the data:
  Create email list → Assert list appears in:
    ├── Email Lists page (obvious)
    ├── Send Campaign → "Select List" dropdown (cross-feature!)
    ├── Automation → "Trigger on list join" selector (cross-feature!)
    └── Analytics → "Filter by list" dropdown (cross-feature!)
```

---

## Trigger: When Does This Rule Apply?

Apply this skill for ANY test involving:

| Operation | Triggers |
|---|---|
| **Create** | New entity added (list, template, user, tag, campaign) |
| **Update / Edit** | Name, status, config, or content changed |
| **Delete / Archive** | Entity removed or hidden |
| **Filter** | Data subset selected → result set changes |
| **Status change** | Active → Inactive, Draft → Published, Pending → Approved |
| **Assignment** | Assigned to user/group/role |
| **Settings change** | Global or feature-level config updated |

---

## The State Ripple Matrix

When you write a test, fill this matrix BEFORE writing assertions:

```
Action: [Create / Update / Delete / Filter] [Entity]
In Feature: [where the action happens]

→ Where does this data appear?
  Feature X: [page/dropdown/count/filter] — verify [what exactly]
  Feature Y: [page/dropdown/count/filter] — verify [what exactly]
  Feature Z: [page/dropdown/count/filter] — verify [what exactly]

→ Where should this data NOT appear (after delete/archive)?
  Feature X: [page/dropdown] — verify ABSENCE
```

---

## Common State Ripple Maps

### Email / Campaign Apps

| Action in Feature A | Must Verify in Feature B |
|---|---|
| Create Email List | Send Campaign → "Select List" dropdown shows new list |
| Create Email List | Automation → "List trigger" selector shows new list |
| Create Email List | Analytics → "Filter by list" shows new list |
| Create Email Template | Send Campaign → "Select Template" shows new template |
| Delete Email List | Send Campaign → list NOT in dropdown |
| Delete Email List | Automations using this list → show warning/broken state |
| Add Subscriber | List detail → subscriber count +1 |
| Add Subscriber | Campaign → recipients count changes |
| Unsubscribe User | Unsubscribes page → user appears |
| Unsubscribe User | Active list → user NOT present |
| Schedule Campaign | Scheduled tab → visible with correct datetime |
| Send Campaign | Campaign History → new entry, correct status |
| Send Campaign | Analytics → sent count increases |

### User / Permission Systems

| Action in Feature A | Must Verify in Feature B |
|---|---|
| Create User | Users list → appears with correct role |
| Create User | Assign task/project → user selectable |
| Change User Role | Permission-gated pages → access updated |
| Deactivate User | Login → blocked |
| Deactivate User | Assignee dropdowns → user NOT selectable |

### Content / CMS

| Action in Feature A | Must Verify in Feature B |
|---|---|
| Create Tag | Create Post → tag selectable |
| Create Category | Create Article → category selectable |
| Delete Category | Posts in that category → handle correctly |
| Publish Post | Public page → post visible |
| Archive Post | Search results → post NOT visible |

### Settings / Config

| Action in Feature A | Must Verify in Feature B |
|---|---|
| Change sender email | Campaign → From field shows new email |
| Change timezone | Scheduled sends → times reflect new timezone |
| Enable feature flag | Feature page → accessible, not hidden |
| Disable feature flag | Feature page → hidden or shows disabled state |

---

## Filter-Specific Rules

Filters are often missed. When a filter changes what data is visible:

```typescript
// ❌ WRONG — only test filter UI responds
await page.selectOption('[data-testid="status-filter"]', 'active');
await expect(page.locator('.filter-badge')).toHaveText('Active');

// ✅ CORRECT — test filter actually changes data set
await page.selectOption('[data-testid="status-filter"]', 'active');

// Verify ONLY active items show
const rows = page.locator('tbody tr');
const count = await rows.count();
for (let i = 0; i < count; i++) {
  await expect(rows.nth(i).locator('.status')).toHaveText('Active');
}

// Verify inactive items are GONE (not just hidden)
await expect(page.locator('text="Inactive User"')).not.toBeVisible();
```

### Filter Ripple Rules
- Filter in List A → URL params change → shareable link shows same filter
- Filter by date → count badge / summary numbers update
- Filter to zero results → empty state shows, NOT blank/broken page
- Filter reset → ALL items return (including previously hidden ones)

---

## Implementation Pattern

```typescript
test('[Feature A action] → [Entity] state ripples to [Feature B]', async ({ page }) => {
  // ARRANGE — unique data for traceability
  const listName = `Test List ${Date.now()}`;
  await loginAs(page, 'admin');

  // ACT — perform the action in Feature A
  await page.goto('/email-lists');
  await page.click('[data-testid="create-list-btn"]');
  await page.fill('[data-testid="list-name"]', listName);
  await page.click('[data-testid="save"]');

  // ASSERT A — Feature A immediate result (basic)
  await expect(page.locator(`text="${listName}"`)).toBeVisible();

  // ASSERT B — Feature B: Send Campaign list selector
  await page.goto('/campaigns/new');
  await page.click('[data-testid="select-list"]');
  await expect(page.locator(`[data-value="${listName}"]`)).toBeVisible();

  // ASSERT C — Feature C: Automation trigger selector
  await page.goto('/automations/new');
  await page.click('[data-testid="trigger-list-select"]');
  await expect(page.locator(`text="${listName}"`)).toBeVisible();
});
```

---

## Absence Verification (Delete / Archive / Deactivate)

Deleting something is not complete until you've verified its ABSENCE everywhere:

```typescript
test('Delete email list → removed from all consumer features', async ({ page }) => {
  const listName = `Delete Test ${Date.now()}`;

  // Setup: create the list first
  await createEmailList(page, listName);

  // Act: delete it
  await page.goto('/email-lists');
  await deleteList(page, listName);

  // Assert absence in Feature A (list page itself)
  await expect(page.locator(`text="${listName}"`)).not.toBeVisible();

  // Assert absence in Feature B (send campaign dropdown)
  await page.goto('/campaigns/new');
  await page.click('[data-testid="select-list"]');
  await expect(page.locator(`text="${listName}"`)).not.toBeVisible();

  // Assert absence in Feature C (automation selector)
  await page.goto('/automations/new');
  await page.click('[data-testid="trigger-list-select"]');
  await expect(page.locator(`text="${listName}"`)).not.toBeVisible();
});
```

---

## Test Naming Convention

Test names must declare the ripple scope:

```
✅ Good names:
  "Create email list → appears in Send Campaign list selector"
  "Delete template → removed from campaign template picker"
  "Status filter: Active → only active subscribers shown"
  "Update list name → new name appears in automation trigger"

❌ Bad names:
  "Create email list works"
  "Delete template"
  "Filter works"
```

Format: `[Action] → [Cross-feature result]`

---

## Checklist Before Marking Test Complete

- [ ] Identified all features that CONSUME the created/updated/deleted entity
- [ ] Wrote test cases for each consumer feature (not just the source feature)
- [ ] Tested PRESENCE (create/update) and ABSENCE (delete/deactivate) separately
- [ ] Filter tests verify actual data content, not just UI response
- [ ] Filter tests verify zero-result state (empty state, not crash)
- [ ] Used unique test data (timestamp) so lookups find the RIGHT record
- [ ] Test name follows `[Action] → [Cross-feature result]` convention

---

## Cross-Page Navigation State Persistence (Detail → List)

> **Pattern**: Action on detail page → navigate back to list → verify list shows updated state WITHOUT forcing a reload.

This is a distinct sub-type of state ripple. The source and destination are the SAME entity, but on different pages (detail vs. list). The bug: the list page caches stale state and doesn't refresh when the user navigates back.

### When Does This Apply?

| Action on Detail Page | Must Verify in List Page (no F5) |
|---|---|
| Ban practitioner from `/practitioners/:id` | `/practitioners` list → row shows "Banned" |
| Unban practitioner from detail page | List row → shows "Active" immediately |
| Update user profile from detail | User list → updated name/role visible |
| Change status from entity detail | Entity list → status column reflects new value |
| Delete entity from detail | List → entity row is gone (no reload) |

### Test Pattern

```typescript
test('[Action on detail] → [list reflects change without F5]', async ({ page }) => {
  // ARRANGE — verify starting state
  await navigateToEntityInList(page, target);
  await expectStatusInList(page, target, 'Active');

  // ACT — perform action on detail page
  await openDetailPage(page, target);
  await performActionOnDetail(page);       // e.g., click Ban Account
  await dismissConfirmIfPresent(page);
  await page.waitForTimeout(1500);         // wait for API response

  // NAVIGATE BACK — simulate user pressing Back (not goto)
  await page.goBack();
  await page.waitForFunction(             // wait for list to populate
    () => document.querySelectorAll('tbody tr td').length > 0,
    { timeout: 10000 }
  );

  // CAPTURE state BEFORE cleanup (so cleanup always runs even if assertion fails)
  await navigateToEntityInList(page, target);
  const actualStatus = await getStatusInList(page, target);

  // CLEANUP — restore state before asserting
  await restoreViaDetailPage(page, target);

  // ASSERT — list must reflect updated state without reload
  expect(actualStatus).toContain('ExpectedNewStatus');
});
```

**Key rules:**
1. Use `page.goBack()` — not `page.goto('/list')` — to simulate real user navigation
2. Capture the value BEFORE cleanup so restore always runs even if assertion fails
3. Wait for list data with `waitForFunction`, not fixed `waitForTimeout`

### Add to State Ripple Matrix for CRM/Admin Apps

| Action in Detail Page | Must Verify (no F5) in List Page |
|---|---|
| Ban from practitioner detail | Practitioner list status = "Banned" |
| Unban from practitioner detail | Practitioner list status = "Active" |
| Update status from any detail | Corresponding list row reflects new status |
| Delete from detail | Record not present in list after goBack |

---

## Red Flags — Missing Ripple Tests

Your test suite needs state ripple tests if:

- You created an entity but never tested it appears in another feature's selector/dropdown
- You deleted something but never verified it's gone from all features that referenced it
- You changed a filter but only asserted the filter UI changed (not the data)
- You updated an entity's name but never checked if features showing that name reflect the update
- You changed a status but never checked pages/features that filter by that status

**Rule of thumb:** If Feature B has a dropdown, filter, or reference to entities created in Feature A — you NEED a cross-feature test.
