---
name: toast-transient-testing
description: Patterns for testing toast notifications and transient UI elements in Playwright — elements that auto-disappear. Use when writing tests that assert on toasts, snackbars, banners, or any notification that auto-dismisses. Prevents race condition where toast disappears before assertion runs. Triggers on: "toast", "snackbar", "notification", "alert message", "auto-dismiss", "transient element", "success message", "error message appears briefly".
triggers:
  - "toast"
  - "snackbar"
  - "auto-dismiss"
  - "transient element"
  - "success message"
  - "notification appears"
---

# Toast / Transient Notification Testing

## Core Problem

Toast disappears in 3-5 seconds. If assertion runs after dismiss → `toBeVisible()` fails intermittently.

## Pattern 1: Auto-Retrying Assertion (Primary)

Playwright's `expect().toBeVisible()` retries automatically. Assert immediately after action — no `waitForTimeout` in between.

```typescript
const toast = page.getByRole('alert'); // error/urgent toasts
// or
const toast = page.getByRole('status'); // success/informational toasts

await page.getByRole('button', { name: 'Save' }).click();
// ✅ Assert immediately — auto-retries until visible
await expect(toast).toBeVisible({ timeout: 5000 });
await expect(toast).toHaveText('Saved successfully');
```

## Pattern 2: Assert Appears AND Disappears

Test the full lifecycle — toast shows then auto-dismisses.

```typescript
await page.getByRole('button', { name: 'Delete' }).click();
const toast = page.getByRole('alert');

// Toast appears
await expect(toast).toBeVisible({ timeout: 3000 });
await expect(toast).toContainText('Deleted successfully');

// Toast dismisses (beyond auto-dismiss window)
await expect(toast).toBeHidden({ timeout: 8000 });
```

## Pattern 3: Freeze Time with page.clock (Most Reliable)

Prevent auto-dismiss entirely during assertion. Best for slow CI environments.

```typescript
// ⚠️ install() alone does NOT freeze time — after install the fake clock keeps running.
// Install BEFORE navigation (must precede any other clock call), then pauseAt to freeze.
await page.clock.install({ time: new Date('2026-01-01T10:00:00') }); // a bit BEFORE the pause time
await page.goto('/settings');                                          // page loads with timers running
await page.clock.pauseAt(new Date('2026-01-01T10:01:00'));            // now timers are frozen

await page.getByRole('button', { name: 'Save' }).click();
const toast = page.getByRole('alert');

// Toast visible — clock frozen, auto-dismiss never triggers
await expect(toast).toBeVisible();
await expect(toast).toHaveText('Changes saved');
await expect(toast).not.toHaveClass(/error/);

// Advance clock to trigger dismiss
await page.clock.runFor(5000);
await expect(toast).toBeHidden();
```

## Pattern 4: Sync with API Response First

When toast appears after API call, wait for response before asserting toast.

```typescript
// ✅ Guarantee API completed before asserting toast
const [response] = await Promise.all([
  page.waitForResponse(r => r.url().includes('/api/save') && r.status() === 200),
  page.getByRole('button', { name: 'Save' }).click(),
]);
await expect(page.getByRole('status')).toBeVisible({ timeout: 3000 });
await expect(page.getByRole('status')).toContainText('Saved');
```

## Pattern 5: Handle Blocking Toasts (addLocatorHandler)

When toasts block other interactions mid-test, auto-dismiss them.

```typescript
// ✅ Auto-close any toast that blocks the next action
await page.addLocatorHandler(
  page.locator('.toast-container'),
  async (container) => {
    while (await container.count() > 0) {
      await container.first().getByRole('button', { name: 'Close' }).click();
    }
  }
);
// Now test can proceed even if unexpected toasts appear
```

## Pattern 6: Multiple Toasts (Stacked)

```typescript
// Target specific toast from a stack
const successToast = page.getByRole('status').filter({ hasText: 'Saved' });
const errorToast = page.getByRole('alert').filter({ hasText: 'Failed' });

await expect(successToast).toBeVisible();
await expect(errorToast).not.toBeVisible(); // confirm no error toast
```

## Semantic Locators

| Toast Type | ARIA Role | Playwright Locator |
|---|---|---|
| Success / informational | `status` | `getByRole('status')` |
| Error / urgent | `alert` | `getByRole('alert')` |
| Generic (class-based) | — | `locator('[class*="toast"]')` |
| Snackbar | `status` or `alert` | inspect with ariaSnapshot first |

## Gotchas

| Gotcha | Fix |
|---|---|
| Race condition: toast gone before assertion | Assert immediately after action — no `waitForTimeout` between |
| Multiple stacked toasts | `locator.filter({ hasText })` to target specific one |
| Toast in DOM but invisible (`opacity: 0`) | Use `toBeVisible()` (checks CSS), not `toBeAttached()` |
| `page.clock.pauseAt` stops all timers | Only use when you need to freeze — may affect other timers. `install()` alone does NOT freeze |
| Hardcoded `waitForTimeout` before assertion | Replace with `expect().toBeVisible({ timeout: N })` |

## Pattern 7: Toast With Action Button (Undo / Retry)

```typescript
await page.click('[data-testid="delete"]');
const toast = page.getByRole('alert');
await expect(toast).toContainText('Item deleted');
// Click action while toast still visible
await toast.getByRole('button', { name: /Undo/i }).click();
// Verify undo took effect
await expect(page.getByText('Item deleted')).toBeHidden();
await expect(page.getByText('My Item')).toBeVisible();
```

## Pattern 8: Toast Stack / Queue Limit

Many libraries cap visible toasts (e.g. max 3 at a time). Trigger several and verify behavior:

```typescript
for (let i = 0; i < 5; i++) await triggerToast(page, `Msg ${i}`);
// If the library enqueues, all 5 will show eventually
// If it limits to 3, only the latest 3 are visible
const visible = await page.getByRole('alert').count();
expect(visible).toBeLessThanOrEqual(3);
```

## Pattern 9: ARIA `aria-live` Polite vs Assertive

- `aria-live="polite"` → wait until current speech finishes (success toast)
- `aria-live="assertive"` → interrupt screen reader immediately (error toast)
- `role="status"` → polite by default; `role="alert"` → assertive by default

Assert the correct role for the toast's severity:
```typescript
// Error toast must use role="alert" (assertive)
await expect(page.locator('[data-toast-type="error"]')).toHaveAttribute('role', 'alert');
// Success toast should use role="status" (polite)
await expect(page.locator('[data-toast-type="success"]')).toHaveAttribute('role', 'status');
```

## Checklist

- [ ] Asserting on `getByRole('alert')` or `getByRole('status')` — not CSS class
- [ ] No `waitForTimeout` between action and toast assertion
- [ ] Toast appears AND disappears both tested (lifecycle complete)
- [ ] Slow CI: `page.clock.install()` used to freeze auto-dismiss
- [ ] Multiple toasts: using `filter({ hasText })` to target correct one

