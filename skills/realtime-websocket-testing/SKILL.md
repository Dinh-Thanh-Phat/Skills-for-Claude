---
name: realtime-websocket-testing
description: Patterns for testing real-time UI in Playwright — WebSocket mocking, proxy/inject mode, live update assertions, polling verification, SSE, chat-like interfaces. Use when writing tests for features that update in real time without user action: notifications, live dashboards, chat, collaborative editing, price feeds, status polling. Triggers on: "websocket", "real-time", "live update", "polling", "SSE", "chat", "notifications", "routeWebSocket", "push notification", "live data", "intercept websocket", "mock websocket playwright", "fake websocket server", "ws mocking".
---

# Real-Time / WebSocket UI Testing

## Core Rule

Never use `waitForTimeout` for real-time updates. Use **retrying assertions** with explicit timeout.

## WebSocket Mocking — routeWebSocket

### 1. Mock incoming messages
```typescript
// ✅ Register BEFORE navigation — WS connects on page load
// The handler runs when the page opens the socket — WebSocketRoute has NO onopen/onmessage
// (only send / onMessage / onClose / close / connectToServer / protocols / url).
await page.routeWebSocket('wss://api.example.com/ws', ws => {
  ws.send(JSON.stringify({ type: 'notification', message: 'New order received' }));
});
await page.goto('/notifications');
await expect(page.getByText('New order received')).toBeVisible();
```

### 2. Simulate timed message sequence
```typescript
await page.routeWebSocket('**/ws/chat', ws => {
  ws.send(JSON.stringify({ user: 'Alice', text: 'Hello' }));
  setTimeout(() => {
    ws.send(JSON.stringify({ user: 'Bob', text: 'Hi there' }));
  }, 100);
});
await page.goto('/chat');
await expect(page.getByText('Hello')).toBeVisible();
await expect(page.getByText('Hi there')).toBeVisible();
```

### 3. Simulate server-side events in response to user action
```typescript
await page.routeWebSocket('**/ws', ws => {
  ws.onMessage(message => {           // message: string | Buffer
    const msg = JSON.parse(message.toString());
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

## WebSocketRoute API Reference

| Method | Description |
|---|---|
| `ws.send(message)` | Send a message from server → client |
| `ws.onMessage(handler)` | Handle client → server message |
| `ws.onClose(handler)` | Handle connection close |
| `ws.close()` | Close the connection from the server side |
| `ws.connectToServer()` | Proxy mode: connect to the real server AND intercept |

## Proxy + Inject Mode — `connectToServer`

Full mocking (above) is best for fast, backend-free tests. When you need **real data but want to inject specific edge cases** (an error frame, a malformed payload) on top of a live server, proxy it:

```typescript
test('handles upstream error gracefully', async ({ page }) => {
  await page.routeWebSocket('wss://stream.example.com/', async ws => {
    const server = await ws.connectToServer();
    server.onMessage(message => {
      const parsed = JSON.parse(message.toString());
      if (parsed.type === 'price') {
        // Inject an error instead of the real price update
        ws.send(JSON.stringify({ type: 'error', code: 503, message: 'Upstream unavailable' }));
      } else {
        ws.send(message); // pass everything else through unchanged
      }
    });
  });
  await page.goto('/trading');
  await expect(page.locator('.error-banner')).toBeVisible();
});
```

## Simulate Disconnect / Reconnect

```typescript
test('reconnects after server drop', async ({ page }) => {
  let connectionCount = 0;
  await page.routeWebSocket('wss://api.example.com/ws', ws => {
    connectionCount++;
    if (connectionCount === 1) {
      setTimeout(() => ws.close(), 100); // drop the first connection
    } else {
      ws.send(JSON.stringify({ type: 'connected', attempt: connectionCount }));
    }
  });
  await page.goto('/realtime-feature');
  await expect(page.locator('.reconnecting')).not.toBeVisible({ timeout: 5000 });
});
```

## Decision Table: Mock vs Proxy vs Real

| Scenario | Approach |
|---|---|
| Fast unit-style tests, no real backend | Full mock (`routeWebSocket` without `connectToServer`) |
| Test error/edge handling on top of real data | Proxy + inject (`connectToServer` + intercept specific messages) |
| Integration tests against a staging WS server | No route — let connections pass through unmodified |
| Assert what the client sends | Collect in `onMessage` handler + `expect.poll()` |

## HAR / Trace Recording (Playwright 1.61+)

WebSocket frames are automatically captured in traces — no extra config beyond enabling tracing:

```typescript
// playwright.config.ts
use: { trace: 'retain-on-failure' }  // WS frames appear in the trace Network tab
```

Open the trace (`npx playwright show-trace trace.zip`) → **Network → WebSocket** shows every sent/received frame with timestamps.

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
- [ ] Error/edge cases on live data: proxy with `connectToServer` + inject, don't full-mock

## Sources
- https://playwright.dev/docs/api/class-websocketroute
- https://playwright.dev/docs/api/class-websocket
- https://playwright.dev/docs/release-notes

