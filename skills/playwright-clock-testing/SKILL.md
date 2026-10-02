---
name: playwright-clock-testing
description: Playwright Clock API for time-sensitive test scenarios — freeze Date.now(), advance timers with fastForward/runFor, test session timeouts, countdown timers, scheduled tasks, and timezone-dependent UIs without real waiting. Use when tests depend on the current date/time, need to fast-forward through waiting periods, or verify timer-driven behavior. Triggers on: "playwright clock", "page.clock", "setFixedTime", "fastForward", "runFor", "fake clock", "time control test", "test timer", "test countdown", "test session timeout", "test auto logout", "mock date".
---

# Playwright Clock API

Installs a fake implementation of `Date`, `setTimeout`, `setInterval`, `requestAnimationFrame`, and `performance` — letting you freeze or advance time programmatically instead of waiting in real time.

---

## Method Selection Guide

| Goal | Method | Timers fire? |
|------|--------|--------------|
| Fix today's date in UI (datepickers, "Today" labels) | `setFixedTime` | Real schedule |
| Jump ahead like "laptop lid closed for a while" | `install` + `fastForward` | Each due timer fires **at most once** |
| Simulate passage of time, fire all intermediate timers | `install` + `runFor` | Yes, every callback, in order |
| Jump to a specific instant and freeze there | `install` + `pauseAt` | Due timers at most once while jumping; then none until `runFor`/`fastForward`/`pauseAt`/`resume` |
| Resume after pausing | `resume()` | Real schedule |

---

## 1. `setFixedTime` — Simplest: Freeze the Date Only

Fixes what `Date.now()` and `new Date()` return. Does **not** install a fake timer engine — `setTimeout`/`setInterval` still fire on the real clock.

```typescript
test('dashboard shows today\'s date', async ({ page }) => {
  await page.clock.setFixedTime(new Date('2026-06-20T09:00:00'));
  await page.goto('/dashboard');
  await expect(page.getByTestId('current-date')).toHaveText('June 20, 2026');
});
```

Use for: date pickers that default to "today", greeting banners, date-formatted API responses displayed in UI.

---

## 2. `install` + `fastForward` — Jump Ahead, Fire Due Timers At Most Once

`fastForward` jumps the clock forward. Timers that became due during the jump **are fired, but each at most once** — equivalent to the user closing the laptop lid and reopening it. A `setInterval(fn, 1000)` crossed by a 30-minute jump fires once, not 1800 times. Use `runFor` when every tick matters.

```typescript
test('session expiry warning appears at 25 minutes', async ({ page }) => {
  await page.clock.install({ time: new Date('2026-06-20T08:00:00') });
  await page.goto('/app');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('secret');
  await page.getByRole('button', { name: 'Sign in' }).click();

  // Jump 25 minutes without waiting 1500 seconds of real time
  await page.clock.fastForward('25:00');

  await expect(page.getByRole('alertdialog', { name: 'Session expiring' })).toBeVisible();
});

test('auto-logout fires after 30 minutes of inactivity', async ({ page }) => {
  await page.clock.install();
  await page.goto('/app');
  await page.clock.fastForward('30:00');
  await expect(page).toHaveURL('/login');
});
```

---

## 3. `install` + `runFor` — Advance Time AND Fire All Intermediate Timers

`runFor` advances the clock **and** calls every `setTimeout`/`setInterval` that falls within the duration, in chronological order. Use when the feature-under-test reacts to each timer tick (progress bars, countdown UI updates, polling).

```typescript
test('countdown timer ticks correctly from 05:00 to 04:57', async ({ page }) => {
  await page.clock.install({ time: 0 });
  await page.goto('/quiz');
  await page.getByRole('button', { name: 'Start Quiz' }).click();

  await expect(page.getByTestId('countdown')).toHaveText('05:00');

  // Advance 3 seconds — each setInterval(fn, 1000) tick fires individually
  await page.clock.runFor(3000);

  await expect(page.getByTestId('countdown')).toHaveText('04:57');
});

test('polling banner refreshes every 10 seconds', async ({ page }) => {
  await page.clock.install();
  await page.goto('/live-status');
  const initialText = await page.getByTestId('status-banner').textContent();

  await page.clock.runFor(10000); // fire the first poll tick

  const updatedText = await page.getByTestId('status-banner').textContent();
  expect(updatedText).not.toBe(initialText);
});
```

---

## 4. `pauseAt` + `resume` — Stop at an Exact Instant

```typescript
test('midnight promotion banner appears exactly at 00:00', async ({ page }) => {
  await page.clock.install({ time: new Date('2026-12-31T23:59:55') });
  await page.goto('/shop');

  // Jump to midnight and freeze
  await page.clock.pauseAt(new Date('2027-01-01T00:00:00'));
  await expect(page.getByText('Happy New Year! 50% off everything')).toBeVisible();

  // Resume normal time to test the banner auto-close
  await page.clock.resume();
  await expect(page.getByText('Happy New Year!')).not.toBeVisible({ timeout: 10000 });
});
```

---

## 5. `setSystemTime` — Move the Clock Without Resetting Timer Schedules

`setSystemTime` shifts what `Date.now()` returns mid-test without cancelling or rescheduling already-registered timers. Use when you need to simulate a date change after timers are already running.

```typescript
test('banner updates on day rollover without resetting running timers', async ({ page }) => {
  await page.clock.install({ time: new Date('2026-12-31T23:59:50') });
  await page.goto('/new-year-countdown');

  // Timers already registered. Move system time forward 15 s into new year.
  await page.clock.setSystemTime(new Date('2027-01-01T00:00:05'));
  await page.clock.runFor(5000);  // fire remaining timers after the shift

  await expect(page.getByText('Happy New Year 2027!')).toBeVisible();
});
```

**`setSystemTime` vs `fastForward`**: `fastForward` fires all timers between now and the target; `setSystemTime` only moves the Date — timers still need `runFor`/`fastForward` to fire after the shift.

---

## Time Format Reference

All time-advance methods accept:

| Format | Example | Meaning |
|--------|---------|---------|
| Milliseconds (number) | `3000` | 3 seconds |
| `"mm:ss"` string | `'05:00'` | 5 minutes |
| `"hh:mm:ss"` string | `'01:30:00'` | 1.5 hours |

---

## Key Rule: Install Clock BEFORE `page.goto()`

The fake clock must be installed before the page loads so all timers registered during page init are captured:

```typescript
// ✅ Correct order
await page.clock.install({ time: new Date('2026-06-20') });
await page.goto('/app');

// ❌ Wrong — page already registered timers with the real clock
await page.goto('/app');
await page.clock.install();
```

`setFixedTime` is the exception — it can be called after `goto()` when you only need to fix the date display, not control timers.

---

## Quick Lookup

| Use Case | Code |
|----------|------|
| Fix today's date in UI | `page.clock.setFixedTime(new Date('2026-06-20'))` |
| Test 30-min auto-logout | `page.clock.install(); page.goto(); page.clock.fastForward('30:00')` |
| Test countdown timer updates | `page.clock.install(); page.goto(); page.clock.runFor(5000)` |
| Pause at midnight exactly | `page.clock.pauseAt(new Date('2027-01-01T00:00:00'))` |
| Resume after pause | `page.clock.resume()` |

## Sources

- [Clock API — Playwright Docs](https://playwright.dev/docs/clock)
- [clock.md — microsoft/playwright GitHub](https://github.com/microsoft/playwright/blob/main/docs/src/clock.md)
- [Playwright Clock & Time Control: Complete 2026 Testing Guide — Qaskills](https://qaskills.sh/blog/playwright-clock-time-control-testing-guide)
- [Clock | Playwright Python Docs](https://playwright.dev/python/docs/clock)
