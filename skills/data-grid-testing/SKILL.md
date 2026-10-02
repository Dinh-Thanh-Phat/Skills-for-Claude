---
name: data-grid-testing
description: Patterns for testing data grids and tables in Playwright — virtual scroll, sort, filter, pagination, infinite scroll, AG Grid column virtualization. Use when writing tests for tables, data grids, or list views that have sort/filter/pagination/infinite scroll, especially with virtual scrolling (AG Grid, TanStack Table, react-virtual). Triggers on: "table", "data grid", "AG Grid", "sort column", "filter table", "pagination", "infinite scroll", "virtual scroll", "row count wrong", "column not found".
---

# Data Grid / Table Testing

## Core Rule

With virtual scroll, **only visible rows are in the DOM**. `getByRole('row').count()` returns visible rows, not total data count.

## Sort Testing

```typescript
// 1. Click column header to sort ascending
await page.getByRole('columnheader', { name: 'Name' }).click();

// 2. Collect visible cell values (adjust selector for your grid)
const values = await page.locator('[data-col="name"]').allTextContents();

// 3. Compare with sorted version
expect(values).toEqual([...values].sort((a, b) => a.localeCompare(b)));

// 4. Click again for descending
await page.getByRole('columnheader', { name: 'Name' }).click();
const descValues = await page.locator('[data-col="name"]').allTextContents();
expect(descValues).toEqual([...descValues].sort((a, b) => b.localeCompare(a)));
```

## Filter Testing

```typescript
// Option A: Assert UI result with locator.filter()
await page.getByPlaceholder('Search...').fill('Alice');
await page.getByPlaceholder('Search...').press('Enter');
// Only Alice row remains, Bob row gone
await expect(page.getByRole('row').filter({ hasText: 'Alice' })).toHaveCount(1);
await expect(page.getByRole('row').filter({ hasText: 'Bob' })).toHaveCount(0);

// Option B: Intercept API to verify query params (more reliable for complex filters)
const filterRequest = page.waitForRequest(r =>
  r.url().includes('/api/users') && r.url().includes('search=Alice')
);
await page.getByPlaceholder('Search...').fill('Alice');
await page.getByPlaceholder('Search...').press('Enter');
await filterRequest; // verify correct params sent to server
```

## Pagination Testing

```typescript
// ⚠️ page.getByRole('row') ALSO matches the header row → 10 data rows count as 11.
// Scope to the body rows (tbody, or the grid's body rowgroup / AG Grid '.ag-center-cols-container').
const bodyRows = page.locator('tbody').getByRole('row');

// Assert page 1 content and count
await expect(bodyRows).toHaveCount(10); // rows per page
const firstRowText = await bodyRows.first().textContent();

// Navigate to page 2
await page.getByRole('button', { name: 'Next page' }).click();
await expect(bodyRows).toHaveCount(10);
// Different data on page 2
await expect(bodyRows.first()).not.toHaveText(firstRowText!);

// Assert page indicator
await expect(page.getByText('Page 2 of 5')).toBeVisible();
```

## Infinite Scroll

```typescript
// ✅ Scroll the GRID CONTAINER, not window
const gridContainer = page.locator('.ag-body-viewport'); // adjust selector
const initialCount = await page.getByRole('row').count();

// Scroll to bottom of container
await gridContainer.evaluate(el => el.scrollTop = el.scrollHeight);
// Brief pause for render (only acceptable non-data wait)
await page.waitForFunction(
  ([container, prevCount]) => container.querySelectorAll('[role="row"]').length > prevCount,
  [await gridContainer.elementHandle(), initialCount]
);

const newCount = await page.getByRole('row').count();
expect(newCount).toBeGreaterThan(initialCount);
```

### Count total rows across all virtual scroll pages
```typescript
// Use Set of unique IDs to avoid double-counting recycled DOM nodes
const seenIds = new Set<string>();
const container = page.locator('.grid-container');

while (true) {
  const rows = page.getByRole('row');
  const ids = await rows.evaluateAll(els => els.map(el => el.getAttribute('data-row-id')));
  ids.filter(Boolean).forEach(id => seenIds.add(id!));

  const scrolledFurther = await container.evaluate(el => {
    const prev = el.scrollTop;
    el.scrollTop = el.scrollHeight;
    return el.scrollTop !== prev; // false = already at bottom
  });
  if (!scrolledFurther) break;
}
expect(seenIds.size).toBe(expectedTotalRows);
```

## AG Grid Specific

```typescript
// Column virtualization: off-screen columns removed from DOM
// ✅ Option A: Disable for tests in gridOptions
// { suppressColumnVirtualisation: true }

// ✅ Option B: Scroll to column before asserting
await page.evaluate(() => {
  (window as any).gridApi.ensureColumnVisible('email');
});
await expect(page.locator('[col-id="email"]').first()).toBeVisible();

// Row selection (grid intercepts clicks — use row-level click)
await page.locator('.ag-row').first().click();
await expect(page.locator('.ag-row-selected')).toHaveCount(1);

// Filter with AG Grid filter input
await page.locator('.ag-header-cell[col-id="name"] .ag-filter-icon').click();
await page.locator('.ag-filter-body input').fill('Alice');
await expect(page.locator('.ag-row')).toHaveCount(1);
```

## Gotchas

| Gotcha | Fix |
|---|---|
| Row count off by one | `getByRole('row')` includes the header row — scope to `tbody` / body rowgroup |
| `getByRole('row').count()` returns partial data | Virtual scroll — only rendered rows in DOM. Use ID Set pattern for total |
| Column locator returns 0 results | AG Grid removes off-screen columns — `suppressColumnVirtualisation` or scroll to column |
| `locator.check()` on row checkbox ignored | Grid intercepts — click the row element or use grid's selection API |
| `window.scrollTo()` doesn't load more rows | Scroll the grid container element, not window |
| Sort flaky across page turns | Verify sort stability across pages, or validate at API layer |

## Checklist

- [ ] Sort: values collected from visible rows, compared with `.sort()`
- [ ] Filter: `locator.filter()` verifies matching AND non-matching rows
- [ ] Pagination: content changes between pages, row count correct, indicator updates
- [ ] Infinite scroll: scrolling grid container (not `window`)
- [ ] Virtual scroll total count: using ID Set pattern (not just `.count()`)
- [ ] AG Grid: `suppressColumnVirtualisation` set in test config or scroll-to-column before asserting

