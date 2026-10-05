---
name: async-loading-state-testing
description: Patterns for testing async UI states in Playwright — spinners, skeleton screens, lazy-loaded content, progressive loading. Use when writing tests for features with loading indicators, async data fetching, skeleton UI, or any operation where UI transitions from loading to loaded state. Triggers on: "spinner", "skeleton", "loading state", "lazy load", "async content", "networkidle", "waitForResponse", "loading indicator".
---

# Async Loading State Testing

## Core Rule

Never wait for a loading state to appear — wait for it to **disappear** or for the **final content** to appear.

## Key Patterns

### 1. Wait for spinner/loader to disappear
```typescript
// ✅ Auto-retries until hidden — no arbitrary timeout
await expect(page.locator('.spinner')).toBeHidden();
await expect(page.locator('[data-testid="skeleton"]')).toBeHidden();

// ✅ Then assert real content is present
await expect(page.locator('[data-testid="user-list"]')).toBeVisible();
```

### 2. Anchor on final content (not loading state)
```typescript
// ✅ Playwright auto-waits through intermediate loading states
await page.click('#load-data');
await expect(page.getByRole('row')).toHaveCount(10); // waits until rows appear
```

### 3. Sync with backend using waitForResponse
```typescript
// ✅ IMPORTANT: start waiting BEFORE the trigger action
const responsePromise = page.waitForResponse(
  r => r.url().includes('/api/users') && r.status() === 200
);
await page.click('#refresh');
await responsePromise; // then assert UI
await expect(page.getByRole('row')).toHaveCount(10);
```

### 4. Skip animation delays with page.clock
```typescript
// ✅ Skip skeleton screen delay entirely — more reliable than real waits
// install() MUST come before page.goto() and before any other clock call,
// otherwise the page's timers are real and fastForward cannot control them.
await page.clock.install();
await page.goto('/page');
await page.clock.fastForward(1000);
await expect(page.locator('.skeleton')).toBeHidden();
await expect(page.locator('.content')).toBeVisible();
```

### 5. Lazy-loaded content — scroll first, then assert
```typescript
// ✅ Scroll the container to trigger load, then assert new items
await page.locator('.list-container').evaluate(el => el.scrollTop = el.scrollHeight);
await expect(page.getByRole('listitem')).toHaveCount(20);
```

### 6. Route with delay — simulate slow responses
```typescript
// ✅ Test loading state actually shows during slow request
await page.route('**/api/data', async route => {
  await new Promise(r => setTimeout(r, 500)); // simulate latency
  await route.fulfill({ body: JSON.stringify({ items: [] }) });
});
await page.goto('/page');
// Assert spinner IS visible during load
await expect(page.locator('.spinner')).toBeVisible();
// Then assert it disappears
await expect(page.locator('.spinner')).toBeHidden();
```

## Gotchas

| Gotcha | Fix |
|---|---|
| `networkidle` — unreliable, NEVER use for testing | Wait for specific elements or API responses instead |
| `waitForResponse` catches wrong request | Add predicate: `r.url().includes('/api/x') && r.status() === 200` |
| Skeleton + real content share same selector | Assert on specific text content, not just visibility |
| Service Workers (MSW) intercept before `page.route()` | Add `serviceWorkers: 'block'` to context options |
| `waitForTimeout` as loading wait | Replace with `expect(spinner).toBeHidden()` |

## Testing Checklist per Async Feature

- [ ] No `waitForTimeout` or `networkidle`
- [ ] Spinner/skeleton asserted as hidden BEFORE checking content
- [ ] `waitForResponse` started BEFORE the trigger action (not after)
- [ ] Lazy-load: scroll container (not window), then assert count
- [ ] `page.clock.install()` BEFORE `goto`, then `page.clock.fastForward()` for animation-delayed skeletons
- [ ] Loading state actually visible during slow request (tested with route delay)

