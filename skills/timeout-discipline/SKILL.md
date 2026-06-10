---
name: timeout-discipline
description: Prevent blind timeout escalation in Playwright/E2E tests. Use when a test is flaky or timing out — BEFORE adjusting any timeout value. Triggers on: "test timeout", "flaky test", "increase timeout", "test bị timeout", "test flaky".
---

# Timeout Discipline Skill

## Core Law

> **Never increase a timeout without first measuring what you're waiting for.**
> Blindly increasing timeouts masks root causes and makes tests slower — not more reliable.

---

## The Anti-Pattern (What I Did Wrong)

```
Test fails at 15s → bump to 25s
Test fails at 25s → bump to 45s  
Test fails at 45s → bump to 90s
...each time: no measurement, just guessing
```

This is **timeout escalation by guessing**. It:
- Wastes 30-90s per test run instead of fixing the real problem
- Hides infrastructure issues (cold starts, slow APIs)
- Creates a false sense of "fixed"

---

## The Correct Process

### Step 1: Measure Before Touching Anything

Before changing a single timeout value, measure actual wait times:

```typescript
// Add timing instrumentation temporarily
const t0 = Date.now();
await page.waitForLoadState('networkidle');
console.log(`networkidle took: ${Date.now() - t0}ms`);

const t1 = Date.now();
await fp.assertStepIs(2);
console.log(`assertStepIs took: ${Date.now() - t1}ms`);
```

Or use Playwright trace viewer:
```bash
npx playwright test --trace on
```

### Step 2: Identify the Bottleneck

Common sources of test timeout:
| Source | Symptoms | Fix |
|--------|----------|-----|
| Server cold start (Replit/staging) | First test slow, rest fast | Warm-up request in global-setup |
| `networkidle` consuming test budget | Test timeout = networkidle + assertion | Reduce networkidle or separate budgets |
| Wrong assertion target | Element never appears | Fix selector, not timeout |
| Missing `await` | Assertion resolves too fast | Add proper awaits |
| Shared test state | Depends on previous test | Fix test isolation |

### Step 3: Set Timeout Based on Measurement

```
Measured max latency = 28s (Replit cold start)
Safety margin = 1.5x
Correct timeout = 42s → set to 45s (one round number above measurement)
```

**One measurement → one timeout value. Not iterative guessing.**

---

## The `.catch(() => {})` Trap

```typescript
// ❌ This hides networkidle timeouts silently
await this.page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
```

If `networkidle` is timing out frequently, you need to know — not hide it.

```typescript
// ✅ Option A: If networkidle truly doesn't matter, remove it
await this.submitButton.click();
// Let Playwright web-first assertions do the waiting

// ✅ Option B: If you need to handle it, log it
await this.page.waitForLoadState('networkidle', { timeout: 15000 }).catch(e => {
  console.warn('networkidle timeout — proceeding:', e.message);
  // intentionally not re-throwing: we proceed to assertion anyway
});
```

---

## When to Ask Instead of Guessing

If after measuring you still can't explain WHY the timeout is happening:

```
Tôi đo được [action X] mất [Y]ms nhưng không hiểu tại sao.
Có thể cung cấp:
- [ ] Server logs / network tab screenshot
- [ ] Thông tin về staging environment (cold start behavior?)
- [ ] Có request nào đang pending không?
```

**2 rounds of measurement → still unclear → ask user.**

---

## The 4 Timeout Scopes — Don't Confuse Them

Playwright has 4 separate timeouts. Increasing the wrong one wastes time:

| Scope | Where set | Default | When to tune |
|---|---|---|---|
| **Test** | `test.setTimeout(N)` or config `timeout` | 30s | Total budget for ONE test (incl. all retries within it) |
| **Action** | `actionTimeout` in `use: {}` | 0 (no cap) | `click()`, `fill()` — per single action |
| **Expect** | `expect.timeout` in config | 5s | `await expect(...)` — per single assertion |
| **Navigation** | `navigationTimeout` in `use: {}` | 30s | `goto()`, `waitForURL()` — cold-start envs need bigger |

```typescript
// Per-test override — only the test that needs it, not the whole suite
test('cold-start dashboard', async ({ page }) => {
  test.setTimeout(90_000);
  await page.goto('/dashboard');
});

// Per-assertion override — keep global default short, override the one slow one
await expect(page.getByText('Done')).toBeVisible({ timeout: 30_000 });
```

## Eliminate Cold Start with `page.clock` or Warm-up

Instead of inflating timeouts to absorb cold-start:
- **Warm-up** in `globalSetup`: one `page.goto(BASE_URL)` to wake the instance
- Or freeze time with `page.clock.install()` and `fastForward()` past internal delays

## Checklist Before Changing Any Timeout

- [ ] Did I measure actual duration with logs or trace?
- [ ] Do I know WHICH operation is consuming the time?
- [ ] Is this a one-time cold start or consistent latency?
- [ ] Am I using `.catch(() => {})` to hide a real problem?
- [ ] Is the new timeout based on measurement × safety margin, not guessing?

---

## Real Example (Auth Tests — April 2026)

**Wrong approach taken:**
- `assertStepIs`: 15000 → 25000 → 45000ms (3 iterations, no measurement)
- Test timeout: 30s → 60s → 90s (3 iterations, no measurement)

**What should have been done:**
1. Add timing logs → discover networkidle = up to 15s, Replit cold start = up to 30s
2. Set `assertStepIs` = 45s (30s cold start × 1.5) in ONE step
3. Set test timeout = 90s (30s cold start + 15s networkidle + 45s assertion + buffer) in ONE step
4. Add warm-up request in `global-setup.ts` to eliminate cold start entirely

---

## Raise the TEST timeout too — not just the action/expect timeout (June 2026)

A long `expect`/action timeout is **capped by the test-level timeout**. I bumped a
`createPosts()` wait to `expect(...).toBeVisible({ timeout: 240000 })` but the test
kept dying at 90s — because `test.slow()` only gives 3× the 30s default = **90s**,
and the test timeout kills the test before the 240s wait can finish.

```
Error: Test timeout of 90000ms exceeded.
  - Expect "toBeVisible" with timeout 240000ms   ← my wait was 240s
    89 × locator resolved to <span ...>All done!</span> - hidden  ← never got there
```

**Rule:** when one operation legitimately needs N seconds, set BOTH:
```ts
test('slow generation flow', async ({ page }) => {
  test.setTimeout(360000);                 // test budget MUST exceed the sum of waits
  ...
  await expect(success).toBeVisible({ timeout: 240000 });
});
```
The test timeout must be **≥ sum of every long wait in the test + setup buffer**.
`test.slow()` (3×) is often not enough for AI/generation flows — use an explicit
`test.setTimeout(...)`. (And before spending minutes per run on AI ops, see
`expensive-irreversible-ops` — don't re-run to "find" the right timeout.)
