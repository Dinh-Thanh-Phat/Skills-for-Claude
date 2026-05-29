---
name: realtime-websocket-testing
description: Patterns for testing real-time UI in Playwright — WebSocket mocking, live update assertions, polling verification, SSE, chat-like interfaces. Use when writing tests for features that update in real time without user action: notifications, live dashboards, chat, collaborative editing, price feeds, status polling. Triggers on: "websocket", "real-time", "live update", "polling", "SSE", "chat", "notifications", "routeWebSocket", "push notification", "live data".
---

# Real-Time / WebSocket UI Testing

## Core Rule

Never use `waitForTimeout` for real-time updates. Use **retrying assertions** with explicit timeout.

## WebSocket Mocking — routeWebSocket

### 1. Mock incoming messages
```typescript
// ✅ Register BEFORE navigation — WS connects on page load
await page.routeWebSocket('wss://api.example.com/ws', ws => {
  ws.onopen(() => {
    ws.send(JSON.stringify({ type: 'notification', message: 'New order received' }));
  });
});
await page.goto('/notifications');
await expect(page.getByText('New order received')).toBeVisible();
```

### 2. Simulate timed message sequence
```typescript
await page.routeWebSocket('**/ws/chat', ws => {
  ws.onopen(() => {
    ws.send(JSON.stringify({ user: 'Alice', text: 'Hello' }));
    setTimeout(() => {
      ws.send(JSON.stringify({ user: 'Bob', text: 'Hi there' }));
    }, 100);
  });
});
await page.goto('/chat');
await expect(page.getByText('Hello')).toBeVisible();
await expect(page.getByText('Hi there')).toBeVisible();
```

### 3. Simulate server-side events in response to user action
```typescript
await page.routeWebSocket('**/ws', ws => {
  ws.onmessage(frame => {
    const msg = JSON.parse(frame.payload as string);
    if (msg.type === 'subscribe') {
      ws.send(JSON.stringify({ type: 'data', value: 42.5 }));
    }
  });
});
await page.goto('/live-price');
await expect(page.getByTestId('price-display')).toHaveText('42.5');
```

### 4. Multi-context: sender + receiver (chat test)
```typescript
const context1 = await browser.newContext();
const context2 = await browser.newContext();
const page1 = await context1.newPage();
const page2 = await context2.newPage();

await page1.goto('/chat?user=Alice');
await page2.goto('/chat?user=Bob');

await page1.getByRole('textbox', { name: 'Message' }).fill('Hello Bob');
await page1.keyboard.press('Enter');

// Assert message appears on Bob's page (with explicit timeout for WS transit)
await expect(page2.getByText('Hello Bob')).toBeVisible({ timeout: 3000 });
```

## Polling / SSE Testing

```typescript
// ✅ Mock polling endpoint to change response over time
let callCount = 0;
await page.route('**/api/job-status', async route => {
  callCount++;
  await route.fulfill({
    body: JSON.stringify({ status: callCount > 2 ? 'complete' : 'processing' })
  });
});
await page.goto('/job-status');
// Retrying assertion waits until status reaches 'complete'
await expect(page.getByText('complete')).toBeVisible({ timeout: 10000 });
// Verify polling actually happened (not just one request)
expect(callCount).toBeGreaterThan(2);
```

## Capture WebSocket Traffic (Read-Only)

```typescript
// Observe WS traffic without mocking
const messages: string[] = [];
page.on('websocket', ws => {
  ws.on('framereceived', frame => messages.push(frame.payload as string));
  ws.on('framesent', frame => messages.push(frame.payload as string));
});
await page.goto('/live-dashboard');
await page.click('#subscribe-button');
// Assert WS message was sent
expect(messages.some(m => JSON.parse(m).type === 'subscribe')).toBe(true);
```

## Gotchas

| Gotcha | Fix |
|---|---|
| `waitForTimeout(N)` for updates | Replace with `expect(locator).toBeVisible({ timeout: N })` |
| `networkidle` on WS connections | Never fires for long-lived WS — use retrying assertions |
| `page.on('websocket')` misses events | Must register handler BEFORE `page.goto()` |
| Message ordering flaky on real WS | Mock the WS with `routeWebSocket` — real network order is non-deterministic |
| `page.routeWebSocket` vs `browserContext.routeWebSocket` | Use `browserContext` for multi-page tests |
| WS mock not working in older Playwright | `routeWebSocket` added in Playwright v1.48+ — check version |

## Checklist

- [ ] `routeWebSocket` / `page.on('websocket')` registered BEFORE `page.goto()`
- [ ] No `waitForTimeout` — using `expect().toBeVisible({ timeout: N })`
- [ ] Message ordering tested with mocked WS (not live network)
- [ ] Multi-user scenarios: separate browser contexts, not separate pages
- [ ] Polling: verify both UI state AND request count (confirms polling happened)
- [ ] WS traffic: `page.on('websocket')` for inspecting sent/received frames

