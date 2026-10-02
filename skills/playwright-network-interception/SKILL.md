---
name: playwright-network-interception
description: Use when writing Playwright tests that need to mock API responses, intercept HTTP requests, simulate network conditions (slow/offline), block third-party requests, or make flaky API-dependent tests deterministic. Triggers on: "mock API response", "intercept request", "stub network", "fake backend", "test without real API", "block analytics", "simulate slow network", "network mocking".
---

# Playwright Network Interception

Make API-dependent tests deterministic by controlling network traffic at the route level.

## Core pattern

Always register `page.route()` BEFORE the action that triggers the request:

```ts
// ✅ Correct — route registered first
await page.route('**/api/users', route =>
  route.fulfill({ json: [{ id: 1, name: 'Alice' }] })
)
await page.goto('/dashboard')

// ❌ Wrong — request already fired
await page.goto('/dashboard')
await page.route('**/api/users', ...) // too late
```

## The 4 route decisions

| Method | When to use |
|---|---|
| `route.fulfill({ json, status })` | Replace response entirely (happy path, error states) |
| `route.continue()` | Pass through unchanged |
| `route.abort()` | Simulate network failure / blocked request |
| `route.fetch()` then `route.fulfill()` | Modify real response (add/remove fields) |

## Fixture pattern — keep mocks out of test files

```ts
// fixtures/api-mocks.ts
export const mockUsers = [{ id: 1, name: 'Alice', role: 'admin' }]
export const mockError = { message: 'Internal Server Error' }

// test file
import { mockUsers, mockError } from '../fixtures/api-mocks'

await page.route('**/api/users', route =>
  route.fulfill({ status: 200, json: mockUsers })
)
```

## Prevent mock leakage between tests

Routes registered on the test's own `page`/`context` fixture die with that context — each test
gets a fresh one, so `beforeEach(unrouteAll)` is unnecessary there. Leakage only happens when you
share a context/page across tests (worker-scoped fixture, `beforeAll` page, `test.describe.serial`):

```ts
// Default: scope to the test block — route only exists in this test
test('shows error state', async ({ page }) => {
  await page.route('**/api/users', route =>
    route.fulfill({ status: 500, json: mockError })
  )
})

// Only for a SHARED page/context: remove routes explicitly (unrouteAll since v1.41)
test.afterEach(async () => {
  await sharedPage.unrouteAll({ behavior: 'ignoreErrors' })
})
```

## Common scenarios

### Mock specific endpoint, pass through everything else
```ts
await page.route('**/*', route => {
  if (route.request().url().includes('/api/users')) {
    route.fulfill({ json: mockUsers })
  } else {
    route.continue()
  }
})
```

### Block analytics / third-party noise
```ts
await page.route('**/(analytics|tracking|hotjar)/**', route => route.abort())
```

### Simulate slow API (skeleton loading test)
```ts
await page.route('**/api/products', async route => {
  await new Promise(r => setTimeout(r, 2000))
  await route.continue()
})
```

### Modify real response (keep most fields, override one)
```ts
await page.route('**/api/user/me', async route => {
  const response = await route.fetch()
  const body = await response.json()
  await route.fulfill({ json: { ...body, role: 'admin' } })
})
```

## 80/20 rule

- **80% of tests**: mock API calls → fast, deterministic CI
- **20% of tests**: hit real endpoints → catch real integration bugs

Never mock 100%. Keep at least one smoke test per critical API hitting the real endpoint.

## Assertion on intercepted requests

```ts
const requestPromise = page.waitForRequest('**/api/checkout')
await page.click('[data-testid="buy-button"]')
const request = await requestPromise
expect(request.postDataJSON()).toMatchObject({ itemId: '123', qty: 1 })
```
