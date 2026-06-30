---
name: playwright-websocket-testing
description: Use when writing Playwright tests that need to mock, intercept, or assert WebSocket connections for real-time features (live chat, notifications, streaming dashboards, multiplayer). Triggers on: "playwright websocket", "routeWebSocket", "mock websocket playwright", "test websocket", "intercept websocket", "fake websocket server", "real-time feature test playwright", "ws mocking".
---

# Playwright WebSocket Testing

Test WebSocket-driven features deterministically using `page.routeWebSocket()` and `browserContext.routeWebSocket()`. This is separate from HTTP route mocking (`page.route()`) — WebSocket connections require their own routing API.

## Core: `page.routeWebSocket()`

Register a WebSocket route **before** navigating to the page that opens the connection:

```typescript
await page.routeWebSocket('wss://chat.example.com/ws', ws => {
  ws.onMessage(message => {
    // Receive a client message, reply with a mock server response
    if (message === 'ping') ws.send('pong')
  })
})
await page.goto('/chat')
```

`browserContext.routeWebSocket()` applies the mock to **all pages** in the context — useful for fixtures:

```typescript
// fixtures/ws-mock.ts
import { test as base } from '@playwright/test'

export const test = base.extend({
  wsMock: async ({ context }, use) => {
    await context.routeWebSocket('wss://api.example.com/realtime', ws => {
      ws.onMessage(msg => {
        const event = JSON.parse(msg.toString())
        if (event.type === 'subscribe') ws.send(JSON.stringify({ type: 'subscribed', channel: event.channel }))
      })
    })
    await use(null)
  },
})
```

## WebSocketRoute API

| Method | Description |
|---|---|
| `ws.send(message)` | Send a message from server → client |
| `ws.onMessage(handler)` | Handle client → server message |
| `ws.onClose(handler)` | Handle connection close |
| `ws.close()` | Close the connection from server side |
| `ws.connect()` | Forward to real server (passthrough mode) |
| `ws.connectToServer()` | Proxy mode: connect to real server AND intercept |

## Common Scenarios

### 1 — Full mock (no real server)

```typescript
test('shows incoming notification', async ({ page }) => {
  await page.routeWebSocket('wss://notify.example.com/', ws => {
    ws.onMessage(() => {}) // ignore client messages
    // Push a notification 200ms after connection opens
    setTimeout(() => {
      ws.send(JSON.stringify({ type: 'notification', text: 'Your order shipped!' }))
    }, 200)
  })
  await page.goto('/dashboard')
  await expect(page.getByRole('alert')).toContainText('Your order shipped!')
})
```

### 2 — Proxy + inject (real server with intercepted messages)

```typescript
test('handles server error gracefully', async ({ page }) => {
  await page.routeWebSocket('wss://stream.example.com/', async ws => {
    const server = await ws.connectToServer()
    server.onMessage(message => {
      const parsed = JSON.parse(message.toString())
      if (parsed.type === 'price') {
        // Inject an error instead of the real price update
        ws.send(JSON.stringify({ type: 'error', code: 503, message: 'Upstream unavailable' }))
      } else {
        ws.send(message) // pass through everything else
      }
    })
  })
  await page.goto('/trading')
  await expect(page.locator('.error-banner')).toBeVisible()
})
```

### 3 — Assert messages sent by the client

```typescript
test('client sends correct subscription message', async ({ page }) => {
  const messages: string[] = []

  await page.routeWebSocket('wss://api.example.com/ws', ws => {
    ws.onMessage(msg => {
      messages.push(msg.toString())
      // Echo back a mock subscription ACK
      ws.send(JSON.stringify({ type: 'subscribed' }))
    })
  })

  await page.goto('/feed')
  await page.getByRole('button', { name: 'Subscribe to live updates' }).click()
  await expect.poll(() => messages).toContainEqual(
    expect.stringContaining('"type":"subscribe"')
  )
})
```

### 4 — Simulate disconnect / reconnect

```typescript
test('reconnects after server drop', async ({ page }) => {
  let connectionCount = 0

  await page.routeWebSocket('wss://api.example.com/ws', ws => {
    connectionCount++
    if (connectionCount === 1) {
      // Drop first connection immediately
      setTimeout(() => ws.close(), 100)
    } else {
      ws.send(JSON.stringify({ type: 'connected', attempt: connectionCount }))
    }
  })

  await page.goto('/realtime-feature')
  // Wait for reconnect banner to disappear
  await expect(page.locator('.reconnecting')).not.toBeVisible({ timeout: 5000 })
})
```

## Decision Table: WS Mock vs Proxy vs Real

| Scenario | Approach |
|---|---|
| Fast unit-style tests, no real backend | Full mock (`routeWebSocket` without `connectToServer`) |
| Test error handling / edge cases on top of real data | Proxy + inject (`connectToServer` + intercept specific messages) |
| Integration tests against staging WS server | No route (let connections pass through unmodified) |
| Assert what the client sends | Collect in `onMessage` handler + `expect.poll()` |

## HAR / Trace Recording (Playwright 1.61+)

WebSocket frames are automatically captured in traces and HAR recordings — no extra config needed:

```typescript
// playwright.config.ts
use: {
  trace: 'retain-on-failure',  // WebSocket frames included in Network tab
}
```

Open the Trace Viewer (`npx playwright show-trace trace.zip`) → Network → WebSocket section shows all sent/received frames with timestamps.

## Sources
- https://playwright.dev/docs/api/class-websocketroute
- https://playwright.dev/docs/api/class-websocket
- https://playwright.dev/docs/release-notes
- https://github.com/microsoft/playwright/releases
