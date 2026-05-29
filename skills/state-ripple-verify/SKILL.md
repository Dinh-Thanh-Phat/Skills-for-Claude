---
name: state-ripple-verify
description: Verify every state change (create/update/delete/filter) propagates correctly to ALL features that consume that state. Use when writing tests for any action that modifies persistent state. Triggers on "state change", "create test", "delete test", "filter test", "update test", "state ripple", "downstream effects", "side effects test".
triggers:
  - "state change"
  - "state ripple"
  - "downstream effects"
  - "side effects test"
  - "create test"
  - "delete test"
  - "filter test"
  - "update test"
scope: playwright, e2e-testing, qa
---

# State-Ripple Verification

## Core Rule

> **Every state change has downstream consumers. A test that only verifies the source module is incomplete.**

When module A changes state (creates/updates/deletes/filters a record), test must also verify every module B that **reads, derives, or counts** that state reflects the change correctly.

Related skill: `cross-module-verify` covers explicit workflows (Send Email → Campaign History). This skill covers **all silent consumers** you may not think to test — list counts, dropdowns, aggregations, search indexes, caches.

---

## The Ripple Map — Common Consumers

| State Change in A | Hidden Consumers (B, C, D...) |
|---|---|
| Create record | List view count · search index · related-dropdowns · totals · empty-state · pagination total |
| Update field | Detail view · list-column value · referenced-by views · search match · cached display · audit log |
| Delete record | List · count · dropdowns (must not appear) · related-records (orphan handling) · undo history · trash bin |
| Status change (Draft→Published) | Public site · sitemap · search index · feed/RSS · cache invalidation · related-collection filters |
| Filter applied | Result count · pagination · "no results" state · count badge · URL query string · breadcrumb |
| User role change | Permission-gated UI · admin lists · audit log · session refresh · invitation lists |
| Settings/Globals change | Every page that reads the setting · cached pages · SSG/ISR rebuild |
| Subscription created | Transactions · invoices · entitlements · usage counters |

---

## Pattern: ARRANGE → ACT → ASSERT-A → ASSERT-RIPPLE

```typescript
test('delete blog category → removes from list AND post-edit dropdown', async ({ page }) => {
  // ARRANGE — unique data
  const name = `TEST_AUTO Category ${Date.now()}`;
  const id = await createCategory(page, name);

  // ACT — state change in module A
  await deleteCategory(page, id);

  // ASSERT-A — immediate confirmation
  await expect(page.getByRole('status')).toContainText(/deleted/i);

  // ASSERT-RIPPLE — every consumer reflects the change
  // 1. List view no longer contains it
  await page.goto('/admin/categories');
  await expect(page.getByText(name)).toHaveCount(0);

  // 2. Post-edit dropdown no longer offers it
  await page.goto('/admin/posts/create');
  await page.getByLabel('Category').click();
  await expect(page.getByRole('option', { name })).toHaveCount(0);

  // 3. Public site /categories/<slug> returns 404
  const r = await page.request.get(`/categories/${slugify(name)}`, { failOnStatusCode: false });
  expect(r.status()).toBe(404);

  // 4. Search by the deleted name returns no results
  await page.goto('/search?q=' + encodeURIComponent(name));
  await expect(page.getByText(/no results/i)).toBeVisible();
});
```

---

## Ripple Verification Per Operation Type

### CREATE

```typescript
// After create, verify:
// (a) record in list with correct fields
// (b) total count incremented
// (c) appears in any dropdown that lists this entity
// (d) appears in search by name/slug
// (e) pagination total updated
// (f) "empty state" no longer shown if it was previously empty
// (g) public-facing route (if any) serves 200 within ISR window
```

### UPDATE

```typescript
// After update, verify:
// (a) detail view shows new value (reload to confirm persistence)
// (b) list view column shows new value
// (c) every place that derives from the field updates
//     (e.g. update name → email signature, audit log, references)
// (d) search by NEW value finds it; search by OLD value does NOT
// (e) cached pages rebuilt (or stale-while-revalidate served new within window)
```

### DELETE

```typescript
// After delete, verify:
// (a) gone from list (re-search, paginate to be sure)
// (b) gone from every dropdown
// (c) related records: orphan handled per spec (cascade / nullify / block)
// (d) public route 404 (and was 200 before)
// (e) total count decremented
// (f) if "trash bin" exists: record in trash; if not: truly gone
// (g) re-creating with same slug/name: allowed or blocked per spec
```

### FILTER / SEARCH

```typescript
// After applying filter, verify:
// (a) result list contains only matching rows
// (b) NON-matching rows verifiably absent (not "≥ 1 row" — exact filter check)
// (c) count badge reflects filtered count, not total
// (d) pagination total = filtered count
// (e) "no results" state shown when 0 matches
// (f) URL reflects filter (so refresh preserves state)
// (g) clearing filter restores original list
```

### STATUS CHANGE (Draft → Published, Active → Archived)

```typescript
// After status change, verify:
// (a) badge in admin UI reflects new status
// (b) record appears/disappears from public-facing list per status
// (c) public detail page becomes reachable/404 per status
// (d) sitemap regenerated (if applicable)
// (e) cache invalidated (ISR/SWR)
// (f) audit log records who/when changed status
```

---

## Anti-Patterns

```typescript
// ❌ "Test passes because deletion didn't crash"
await deleteCategory(page, id);
await expect(page.getByRole('status')).toContainText('Deleted');
// No ripple check → doesn't catch list still showing it, dropdown still offering it

// ❌ "Test passes because A says success" — doesn't check B
await page.goto('/admin/categories');
await deleteRow(page, name);
// Done. But /admin/posts/create dropdown still has it = real bug missed

// ❌ Filter test asserting only ≥ 1 matching row
await filter('color', 'red');
expect(await rows.count()).toBeGreaterThan(0);  // could be all rows including non-red
// → must assert exact filter + non-matching absent
```

---

## Discovering Ripple Consumers — Audit Question

For every entity in the system, ask:

> **"Who reads this? Who counts this? Who shows this in a list, dropdown, badge, or chart?"**

List every consumer found, then write a single ripple test per state-change op covering ALL of them. This is faster than discovering a missed consumer via production bug.

Use these techniques to find consumers:
- Grep code for the entity's model name / API endpoint
- Map relationships in the DB schema (foreign keys point to consumers)
- Walk the public site looking for places that display the entity
- Ask the dev: "Where else does this show up?"

---

## Checklist

- [ ] Identified every consumer (list, dropdown, count, public route, search, cache)
- [ ] Each consumer has an assertion in the test
- [ ] Negative consumers tested too: "should NOT appear in X" for delete
- [ ] Public-facing route checked when status/visibility changed
- [ ] Cache/ISR considered when status changes
- [ ] Filter test asserts BOTH matching present AND non-matching absent
- [ ] Test uses unique data (timestamp) so cross-module lookups find the right record

---

## Links

- `cross-module-verify` — explicit workflow A → B verification (this skill covers silent consumers in addition)
- `outcome-verification` — "how do I KNOW it worked" mental check
- `behavioral-coverage-matrix` — every state-change op needs a ripple test in the matrix
