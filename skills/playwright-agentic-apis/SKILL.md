---
name: playwright-agentic-apis
description: Playwright 1.59 agentic testing APIs — locator.normalize() to canonicalize brittle selectors, page.pickLocator() for interactive element discovery, page.screencast for precise annotated video recording. Use when migrating CSS/XPath locators to ARIA-best-practice form, exploring unfamiliar UIs interactively, or recording annotated test videos. Triggers on: "locator.normalize", "pickLocator", "screencast", "normalize locator", "interactive locator picker", "annotated video recording", "Playwright 1.59".
---

# Playwright 1.59 Agentic Testing APIs

Three new APIs shipped in Playwright 1.59 (April 2026) that change how tests are authored and debugged.

## 1. `locator.normalize()` — Canonicalize Brittle Selectors

Converts a CSS/XPath locator to the best-practice ARIA-role or test-ID equivalent. Use it to mechanically fix legacy selectors caught by `playwright-deprecated-selectors` or code review.

```typescript
// ❌ Before: brittle CSS
const btn = page.locator('div.submit-btn > span');
const canonical = await btn.normalize();
// returns: page.getByRole('button', { name: 'Submit' })

// Use the output directly:
const normalized = await page.locator('#user-menu').normalize();
await normalized.click();
```

**When to use:** Run `normalize()` on any locator flagged as fragile. The output is the expression you should write into your test file — replace the old selector with the canonical string.

> Note: `normalize()` needs a live page to inspect the DOM. It won't resolve without a running browser context.

---

## 2. `page.pickLocator()` — Interactive Element Discovery

Enters an interactive mode where hovering highlights elements and returns a `Locator` for the clicked element. Useful when authoring tests for unfamiliar UIs or troubleshooting "which element is this?".

```typescript
// In a script or REPL context:
const picked = await page.pickLocator();
console.log(picked.toString());
// Example output: page.getByRole('textbox', { name: 'Email address' })

// Cancel without picking:
await page.cancelPickLocator();
```

**Workflow:**
1. Open the page in headed mode.
2. Call `page.pickLocator()` — browser enters highlight mode.
3. Hover over the target element; click to confirm.
4. The returned `Locator` is already canonicalized (ARIA-based / test-ID).
5. Copy the `.toString()` output into your test.

---

## 3. `page.screencast` — Precise Annotated Video Recording

Replaces the `video: 'on'` config option when you need fine-grained control: start/stop within a test, action overlays, chapter markers, or live frame streaming.

```typescript
test('checkout flow with annotated recording', async ({ page }) => {
  const cast = page.screencast;

  await page.goto('/shop');
  await cast.start({ path: 'recordings/checkout.webm' });

  await cast.showChapter('Add to cart', { description: 'User adds item', duration: 3000 });
  await page.getByRole('button', { name: 'Add to cart' }).click();

  await cast.showActions({ position: 'bottom', duration: 2000 });
  await page.getByRole('link', { name: 'Checkout' }).click();

  await cast.showChapter('Payment', { description: 'Filling payment details' });
  await page.getByLabel('Card number').fill('4242424242424242');

  await cast.stop();
});
```

### Full API Reference

| Method | Purpose |
|--------|---------|
| `cast.start({ path, onFrame, size })` | Begin recording; `onFrame` callback for live streaming |
| `cast.stop()` | End recording, flush file |
| `cast.showActions({ position, duration, fontSize, cursor })` | Overlay action annotations (clicks, fills); returns a disposable; `cursor: 'pointer'\|'none'` since 1.61 |
| `cast.hideActions()` | Remove action annotations |
| `cast.showChapter(title, { description, duration })` | Add a chapter title overlay |
| `cast.showOverlay(html)` | Inject custom HTML overlay |
| `cast.showOverlays()` / `cast.hideOverlays()` | Bulk toggle visibility |

**Live streaming (no file):**
```typescript
await cast.start({
  onFrame: ({ data, viewportWidth, viewportHeight, timestamp }) => {
    // frame is an OBJECT: data = JPEG Buffer; timestamp added in 1.61
    ws.send(data);
  }
});
```

---

## Companion: `browserContext.setStorageState()`

Also new in 1.59 — clears cookies, localStorage and IndexedDB for all origins (in current versions also OPFS entries and virtual WebAuthn credentials) on an existing context and loads a new state without creating a new context. Useful for mid-test auth switches. If the new state contains passkey credentials, the virtual authenticator is installed automatically.

```typescript
// Switch to a different user mid-test without a new context
// Argument is a file path or a storage-state object — NOT { path }
await context.setStorageState('auth/admin-state.json');
```

Prefer this over `browser.newContext()` when your test needs to verify behavior across two roles without paying the browser-context startup cost.

---

## Quick Reference — Choosing the Right API

| Goal | API |
|------|-----|
| Fix a legacy CSS/XPath selector | `locator.normalize()` |
| Discover locator for an unknown element | `page.pickLocator()` |
| Record annotated test video | `page.screencast.start()` / `.stop()` |
| Switch auth mid-test | `context.setStorageState()` |

## Sources

- [Playwright v1.59.0 Release — GitHub](https://github.com/microsoft/playwright/releases/tag/v1.59.0)
- [Playwright 1.59 Release: New Features for Agentic Testing — TestDino](https://testdino.com/blog/playwright-release-guide)
- [What's New in Playwright 1.59 — Bug0](https://bug0.com/blog/whats-new-playwright-1-59)
- API: https://github.com/microsoft/playwright/blob/main/docs/src/api/class-screencast.md, class-browsercontext.md#browser-context-set-storage-state (corrected 2026-10-02)
