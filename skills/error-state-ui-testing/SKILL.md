---
name: error-state-ui-testing
description: >-
  Patterns for testing error UI states in Playwright — HTTP errors (4xx/5xx), network failures,
  empty states, error boundaries. Use when writing tests for "what happens when things go wrong"
  scenarios: API failures, offline states, empty data, React/Vue error boundaries. Triggers on:
  "error state", "5xx", "4xx", "network error", "empty state", "error boundary", "page.route",
  "abort", "mock API error", "no data found".
---

# Error State UI Testing

## Core Pattern: Use page.route() to inject errors

No real server errors needed. Mock them all with Playwright network interception.

```typescript
// ✅ Register route BEFORE page.goto() — requests fire immediately on navigation
await page.route('**/api/items', route =>
  route.fulfill({ status: 500, body: JSON.stringify({ error: 'Internal error' }) })
);
await page.goto('/items');
await expect(page.getByText('Something went wrong')).toBeVisible();
```

## By Error Type

### HTTP 5xx — Server error
```typescript
await page.route('**/api/data', r => r.fulfill({ status: 500, body: '{}' }));
await page.goto('/page');
await expect(page.getByRole('alert')).toBeVisible();
await expect(page.getByText('Something went wrong')).toBeVisible();
```

### Network failure — No connection (different from 500)
```typescript
// abort() simulates network disconnection — no response at all
await page.route('**/api/data', r => r.abort('failed'));
await page.goto('/page');
await expect(page.getByText(/unable to connect|offline/i)).toBeVisible();
```

### HTTP 401/403 — Auth redirect
```typescript
await page.route('**/api/profile', r => r.fulfill({ status: 401, body: '{}' }));
await page.goto('/dashboard');
// Assert redirect, NOT inline error message
await expect(page).toHaveURL(/\/login/);
```

### Empty state — No data returned
```typescript
await page.route('**/api/items', r =>
  r.fulfill({ status: 200, body: JSON.stringify([]) })
);
await page.goto('/items');
// Assert empty state visible AND no list items
await expect(page.getByText('No items found')).toBeVisible();
await expect(page.getByRole('row')).toHaveCount(0);
// Also assert loading indicator is gone first
await expect(page.locator('.spinner')).toBeHidden();
```

### React Error Boundary
```typescript
await page.route('**/api/component-data', r => r.fulfill({ status: 500 }));
await page.goto('/page-with-error-boundary');
// ⚠️ The crashed component's DOM is REMOVED — assert fallback UI instead
await expect(page.getByTestId('error-fallback')).toBeVisible();
await expect(page.getByText('Something went wrong. Please refresh.')).toBeVisible();
// ❌ DON'T assert on original component element — it's gone from DOM
```

### Popups and new tabs
```typescript
// page.route() only covers current page
// ✅ Use browserContext.route() to cover all pages including popups
await page.context().route('**/api/data', r => r.fulfill({ status: 500 }));
```

## Gotchas

| Gotcha | Fix |
|---|---|
| Route registered after `goto` → request already fired | Always `page.route()` BEFORE `page.goto()` |
| `page.route()` misses popups/new tabs | Use `browserContext.route()` |
| Error boundary removes component from DOM | Assert on fallback UI selector, not original component |
| Empty state confused with loading state | Assert loading gone AND empty message visible |
| Broad `'**'` pattern catches fonts/images too | Use specific path: `'**/api/items'` |
| 401 triggers redirect, not inline error | Assert `page.url()` change, not error message |

## Coverage Checklist per Data-Fetching Feature

For every feature that fetches data, test ALL of:
- [ ] Success state (happy path)
- [ ] 5xx server error — error message shown to user
- [ ] Network failure — connection error message shown
- [ ] 401/403 — redirect to login page
- [ ] Empty response `[]` — empty state shown, no list items rendered
- [ ] Loading → error transition (spinner disappears before error appears)
- [ ] Error boundary: fallback UI shown (if React/Vue boundary exists)

