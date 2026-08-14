---
name: api-network-mocking
description: >-
  Playwright network interception and API mocking patterns. Use when mocking API responses in E2E
  tests, testing error states, simulating network failures, or verifying API contracts. Triggers
  on: "mock API", "mock response", "intercept request", "network mock", "page.route", "MSW", "giả
  lập API", "mock dữ liệu".
triggers:
  - "mock API"
  - "mock response"
  - "intercept request"
  - "network mock"
  - "page.route"
  - "MSW"
  - "giả lập API"
  - "mock dữ liệu"
  - "simulate error"
  - "test without backend"
scope:
  - qa
  - e2e
  - playwright
  - api
---

# API Network Mocking Skill

You are a **Senior QA Engineer** using Playwright's network interception to test UI behavior against controlled API responses.

## Core Law

> **Mocks are for testing UI behavior, not backend logic.**
> Mock APIs to test: error states, loading states, edge cases, network failures.
> Never mock APIs to skip testing real integrations — integration tests must hit real endpoints.

---

## When to Mock vs Not Mock

| Scenario | Mock? | Why |
|----------|-------|-----|
| Testing error message display | YES | Control when/what error occurs |
| Testing loading spinner behavior | YES | Delay response artificially |
| Testing empty state UI | YES | Return empty array reliably |
| Testing happy path on staging | NO | Verify real integration |
| Testing payment flow | NO | Must hit real (test) payment API |
| Testing auth | NO | Must verify real JWT/session flow |

---

## Playwright Native: `page.route()`

### Mock a successful response
```typescript
test('MOCK-001: Dashboard shows user list', async ({ page }) => {
  await page.route('**/api/users', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        users: [
          { id: '1', name: 'Nguyen Van A', email: 'a@test.com' },
          { id: '2', name: 'Tran Thi B', email: 'b@test.com' },
        ],
      }),
    });
  });

  await page.goto('/dashboard');
  await expect(page.locator('[data-testid="user-row"]')).toHaveCount(2);
});
```

### Mock an error state
```typescript
test('MOCK-002: Shows error message on API failure', async ({ page }) => {
  await page.route('**/api/users', async route => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'Internal server error' }),
    });
  });

  await page.goto('/dashboard');
  await expect(page.locator('[data-testid="error-banner"]')).toBeVisible();
  await expect(page.locator('[data-testid="error-banner"]')).toContainText('error');
});
```

### Mock a network failure
```typescript
test('MOCK-003: Shows offline message on network failure', async ({ page }) => {
  await page.route('**/api/users', async route => {
    await route.abort('failed'); // simulate connection reset
  });

  await page.goto('/dashboard');
  await expect(page.locator('[data-testid="network-error"]')).toBeVisible();
});
```

### Simulate slow response (loading state)
```typescript
test('MOCK-004: Shows loading spinner while fetching', async ({ page }) => {
  await page.route('**/api/users', async route => {
    await new Promise(resolve => setTimeout(resolve, 2000)); // 2s delay
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ users: [] }),
    });
  });

  await page.goto('/dashboard');
  await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
  await expect(page.locator('[data-testid="loading-spinner"]')).not.toBeVisible();
});
```

---

## Modifying Real Responses (Pass-Through with Modification)

```typescript
test('MOCK-005: Filter out archived items from real response', async ({ page }) => {
  await page.route('**/api/users', async route => {
    const response = await route.fetch(); // get real response
    const data = await response.json();

    const filtered = {
      ...data,
      users: data.users.filter((u: any) => !u.archived),
    };

    await route.fulfill({ response, body: JSON.stringify(filtered) });
  });

  await page.goto('/dashboard');
});
```

---

## Route Patterns

```typescript
// Exact URL
await page.route('https://api.example.com/users', handler);

// Glob pattern — matches any URL containing /api/users
await page.route('**/api/users**', handler);

// Regex
await page.route(/\/api\/users\/\d+/, handler);

// Block all images to speed up tests
await page.route('**/*.{png,jpg,gif,svg}', route => route.abort());
```

---

## Mock Data Organization

```
tests/
  mocks/
    users.mock.ts        // user API fixtures
    errors.mock.ts       // error response fixtures
  helpers/
    mock-api.ts          // reusable mock setup helpers
```

```typescript
// tests/mocks/users.mock.ts
export const MOCK_USERS = {
  empty: { users: [], total: 0 },
  single: { users: [{ id: '1', name: 'Test User', email: 'test@example.com' }], total: 1 },
  error: { message: 'Database connection failed' },
};

// tests/helpers/mock-api.ts
export async function mockUsersEndpoint(page: Page, fixture: keyof typeof MOCK_USERS, status = 200) {
  await page.route('**/api/users', route =>
    route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_USERS[fixture]),
    })
  );
}
```

---

## Intercepting and Asserting Request Payloads

```typescript
test('MOCK-006: Form submits correct payload', async ({ page }) => {
  let capturedPayload: any;

  await page.route('**/api/users', async route => {
    capturedPayload = JSON.parse(route.request().postData() || '{}');
    await route.fulfill({ status: 201, body: JSON.stringify({ id: 'new-1' }) });
  });

  await page.goto('/users/create');
  await page.fill('[name="name"]', 'Test User');
  await page.fill('[name="email"]', 'test@example.com');
  await page.click('[type="submit"]');

  expect(capturedPayload.name).toBe('Test User');
  expect(capturedPayload.email).toBe('test@example.com');
});
```

---

## Contract Testing (Schema Validation)

```typescript
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string().email(),
  role: z.enum(['admin', 'user']),
});

test('CONTRACT-001: /api/users response matches schema', async ({ request }) => {
  const response = await request.get('/api/users');
  expect(response.status()).toBe(200);

  const data = await response.json();
  const parsed = z.object({ users: z.array(UserSchema), total: z.number() }).safeParse(data);

  expect(
    parsed.success,
    `Schema validation failed: ${JSON.stringify(parsed.error?.errors)}`
  ).toBe(true);
});
```

---

## WebSocket Mocking (`routeWebSocket`, Playwright 1.48+)

```typescript
await page.routeWebSocket('wss://example.com/ws', ws => {
  ws.onopen(() => ws.send(JSON.stringify({ type: 'hello' })));
  ws.onmessage(frame => {
    const msg = JSON.parse(frame.payload as string);
    if (msg.type === 'subscribe') ws.send(JSON.stringify({ type: 'data', value: 42 }));
  });
});
```
See also `realtime-websocket-testing` skill for complete patterns.

## GraphQL Mocking — Match by operationName

GraphQL endpoints look identical at the URL level. Match by request body:
```typescript
await page.route('**/graphql', async route => {
  const post = JSON.parse(route.request().postData() || '{}');
  if (post.operationName === 'GetUsers') {
    await route.fulfill({ status: 200, body: JSON.stringify({ data: { users: [...] } }) });
  } else {
    await route.continue();
  }
});
```

## HAR Replay (`routeFromHAR`) — Record real traffic once, replay deterministically

```typescript
// Record (do once during a happy-path session)
await page.routeFromHAR('tests/har/dashboard.har', { update: true });
await page.goto('/dashboard');

// Replay (test runs)
await page.routeFromHAR('tests/har/dashboard.har');
await page.goto('/dashboard');
// All matched requests served from the HAR file — fully offline test.
```

## `route.continue()` with Header Injection

```typescript
await page.route('**/api/**', route =>
  route.continue({ headers: { ...route.request().headers(), 'X-Test-Mode': '1' } })
);
```

## `times` Option (Playwright 1.39+)

```typescript
// Mock first 3 calls, then let the rest through
await page.route('**/api/data', route => route.fulfill({ body: '[]' }), { times: 3 });
```

## Removing Routes Mid-Test

```typescript
const handler = async (route: Route) => route.fulfill({ ... });
await page.route('**/api/data', handler);

// ... actions with mocked API ...

await page.unroute('**/api/data', handler); // restore real API
```

---

## Checklist

- [ ] Mock is testing UI behavior, not backend logic
- [ ] Mock data stored in `tests/mocks/` (not inline in test)
- [ ] Error scenarios tested (500, 404, network abort)
- [ ] Loading state tested (delayed response)
- [ ] Empty state tested
- [ ] Mock data committed alongside test in same PR as API contract change
- [ ] Contract test exists for any external API this app consumes
- [ ] Real integration test also exists for the same flow

---

## Sources
- Playwright network mocking: playwright.dev/docs/mock
- Playwright route API: playwright.dev/docs/network
- MSW + Playwright: github.com/mswjs/playwright
