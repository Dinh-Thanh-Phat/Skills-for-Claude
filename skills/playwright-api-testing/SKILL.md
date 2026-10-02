---
name: playwright-api-testing
description: Playwright API testing using the built-in request fixture and APIRequestContext — test REST and GraphQL endpoints directly without a browser, share auth state with browser sessions, and combine API setup with UI validation in a single test file. Use when testing REST APIs, GraphQL endpoints, or hybrid flows where API data setup precedes UI verification. Triggers on: "playwright API testing", "request fixture playwright", "APIRequestContext", "test API without browser playwright", "playwright REST test", "playwright GraphQL test", "API setup before UI test".
---

# Playwright API Testing (APIRequestContext)

Playwright's built-in `request` fixture sends HTTP requests without launching a browser, and shares authentication state with browser contexts — no extra libraries (Supertest, Axios, Postman) needed.

Distinct from `api-network-mocking` (intercepting browser traffic) — this skill is about testing backend APIs directly.

## The `request` Fixture (Per-Test Context)

Every Playwright test gets a fresh `request` fixture automatically:

```typescript
import { test, expect } from "@playwright/test";

test("POST creates a user and returns 201", async ({ request }) => {
  const response = await request.post("/api/users", {
    data: { name: "Phat", email: "phat@example.com", role: "viewer" },
  });

  expect(response.status()).toBe(201);
  const body = await response.json();
  expect(body.id).toBeTruthy();
  expect(body.email).toBe("phat@example.com");
});
```

## CRUD Test with `test.step`

```typescript
test("full user CRUD lifecycle", async ({ request }) => {
  let userId: string;

  await test.step("CREATE", async () => {
    const res = await request.post("/api/users", {
      data: { name: "Phat", email: "phat@example.com" },
    });
    expect(res.ok()).toBeTruthy();
    userId = (await res.json()).id;
  });

  await test.step("READ", async () => {
    const res = await request.get(`/api/users/${userId}`);
    expect(res.status()).toBe(200);
    expect((await res.json()).name).toBe("Phat");
  });

  await test.step("UPDATE", async () => {
    const res = await request.patch(`/api/users/${userId}`, {
      data: { name: "Phat Updated" },
    });
    expect(res.ok()).toBeTruthy();
  });

  await test.step("DELETE", async () => {
    const res = await request.delete(`/api/users/${userId}`);
    expect(res.status()).toBe(204);
    // Verify gone
    const check = await request.get(`/api/users/${userId}`);
    expect(check.status()).toBe(404);
  });
});
```

## Authentication

### Bearer Token

```typescript
test("authenticated request", async ({ request }) => {
  const res = await request.get("/api/me", {
    headers: { Authorization: `Bearer ${process.env.API_TOKEN}` },
  });
  expect(res.ok()).toBeTruthy();
});
```

### Login and Share State Across Tests

```typescript
// fixtures/auth.ts
import { test as base } from "@playwright/test";

export const test = base.extend({
  request: async ({ playwright }, use) => {
    // Create a long-lived context with auth cookie
    const context = await playwright.request.newContext({
      baseURL: "https://api.example.com",
    });
    // Log in once
    await context.post("/auth/login", {
      data: { username: "admin", password: process.env.ADMIN_PASS },
    });
    await use(context);
    await context.dispose();
  },
});
```

## Sharing Auth State: Browser → API

```typescript
// Sign in via UI, save storage state, reuse in API calls
test.use({ storageState: "auth.json" });

test("API call inherits browser auth cookies", async ({ page }) => {
  // page is already authenticated from auth.json
  await page.goto("/dashboard");

  // page.request (= context.request) shares the browser context's cookie jar, live:
  // sends its cookies and stores any Set-Cookie back into the browser.
  const res = await page.request.get("/api/dashboard/stats");
  expect(res.ok()).toBeTruthy();
});
```

> The standalone `request` fixture is an **isolated** `APIRequestContext`
> (`playwright.request.newContext()`): it does NOT stay in sync with the page's cookies. Use
> `page.request` / `context.request` when API and UI must share a session
> (api-testing docs, "Context request vs global request").
>
> v1.63+: request methods take a response type — `const res = await request.get<User>('/api/users/42'); const user = await res.json(); // typed User`.

## API Setup + UI Validation (Hybrid Pattern)

The most powerful pattern — create test data via API (fast, no UI flakiness), then verify the result in the UI:

```typescript
test("created order appears in UI order list", async ({ request, page }) => {
  // Fast API setup — no login flow, no form fill
  const createRes = await request.post("/api/orders", {
    data: { productId: "prod-42", qty: 3 },
    headers: { Authorization: `Bearer ${process.env.API_TOKEN}` },
  });
  const { id: orderId } = await createRes.json();

  // Now verify in UI
  await page.goto(`/orders/${orderId}`);
  await expect(page.getByRole("heading", { name: `Order ${orderId}` })).toBeVisible();
  await expect(page.getByText("3 items")).toBeVisible();
});
```

## GraphQL

```typescript
test("GraphQL query returns user", async ({ request }) => {
  const res = await request.post("/graphql", {
    data: {
      query: `
        query GetUser($id: ID!) {
          user(id: $id) { id name email }
        }
      `,
      variables: { id: "user-123" },
    },
    headers: { "Content-Type": "application/json" },
  });

  const { data, errors } = await res.json();
  expect(errors).toBeUndefined();
  expect(data.user.email).toBe("expected@example.com");
});
```

## Global API Context in `playwright.config.ts`

Set a `baseURL` so all `request` calls use it:

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    baseURL: "https://api.example.com",
    extraHTTPHeaders: {
      Accept: "application/json",
    },
  },
});
```

Then in tests, just use relative paths: `request.get("/api/users")`.

## Response Assertions

```typescript
// Status
expect(response.ok()).toBeTruthy();          // 200-299
expect(response.status()).toBe(201);

// Headers
expect(response.headers()["content-type"]).toContain("application/json");

// Body
const body = await response.json();
expect(body).toMatchObject({ id: expect.any(String), name: "Phat" });

// Error handling
expect(response.status()).toBe(400);
const err = await response.json();
expect(err.message).toContain("email");
```

## When to Use `request` vs Other Tools

| Tool | Use when |
|---|---|
| `request` fixture | API tests alongside Playwright E2E; auth-state sharing needed |
| `api-network-mocking` skill | Intercepting/mocking browser's own HTTP calls during UI tests |
| Supertest/Axios | Backend unit tests with no Playwright setup |
| `chatbot-api-caller` skill | Testing chatbot API endpoints in the chatbot testing pipeline |

## Sources

- https://playwright.dev/docs/api-testing
- https://getautonoma.com/blog/playwright-api-testing-guide
- https://testdino.com/blog/playwright-api-testing
- https://www.browserstack.com/guide/playwright-api-test
- https://qaskills.sh/blog/playwright-apirequestcontext-storagestate-guide
