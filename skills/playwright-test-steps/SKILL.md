---
name: playwright-test-steps
description: Use Playwright's test.step() to structure tests into named, nestable groups that show up in the HTML report and Trace Viewer — including the box option (collapse helper internals in stack traces), the per-step timeout option, and step.skip() to disable an in-progress step. Use when a test's failure trace is hard to read, when a helper function's internal call stack pollutes error messages, or when a Page Object method should read as one report line instead of ten raw actions. Triggers on: "playwright test.step", "test step timeout", "step.skip", "boxed steps playwright", "box: true", "playwright report step", "structure playwright test", "group test actions".
---

# Playwright Test Steps

`test.step(title, body, options?)` runs `body` and records it as a named, collapsible group in the HTML report and Trace Viewer's Action Timeline. It changes **presentation and failure-location**, not test behavior — the same actions run in the same order either way.

## 1. Basic usage — one report line per user-journey phase

```typescript
test('checkout completes', async ({ page }) => {
  await test.step('add item to cart', async () => {
    await page.goto('/products/42');
    await page.getByRole('button', { name: 'Add to cart' }).click();
  });

  await test.step('fill shipping details', async () => {
    await page.getByLabel('Address').fill('123 Main St');
    await page.getByLabel('City').fill('Springfield');
  });

  await test.step('submit payment', async () => {
    await page.getByRole('button', { name: 'Pay now' }).click();
    await expect(page.getByText('Order confirmed')).toBeVisible();
  });
});
```

Failure output points straight at "submit payment" instead of forcing you to scan raw action logs. Steps **nest** — wrap steps inside steps to mirror a multi-phase journey (e.g. `'checkout' > 'submit payment' > 'retry after decline'`).

`test.step()` returns whatever the callback returns, so it composes with data setup: `const orderId = await test.step('create order via API', async () => { ... return id; });`

## 2. `box: true` — hide helper internals from stack traces

Default `box` is `false`. When a step is **boxed**, an error thrown *inside* the step's implementation is reported at the **step's call site**, not at the line deep inside the helper. Use this for Page Object / helper methods so failures point at the test line that called the helper, not at internal locator plumbing.

```typescript
// page-objects/checkout-page.ts
class CheckoutPage {
  async submitPayment(card: string) {
    return test.step('submit payment', async () => {
      await this.page.getByLabel('Card number').fill(card);
      await this.page.getByRole('button', { name: 'Pay now' }).click();
    }, { box: true });
  }
}
```

If `fill()` throws inside `submitPayment`, the reported error location is the call to `checkoutPage.submitPayment(card)` in the test — not the `fill()` line buried inside the class. Without `box: true`, the same failure would show the full internal stack, forcing you to jump into the Page Object to find what actually happened.

Fixtures support the same option: `{ box: true }` hides all of a fixture's internal steps from the report; `{ box: 'self' }` hides only the fixture's own step but still shows steps *inside* the fixture body.

## 3. `timeout` option — bound a single step independently of the test timeout

```typescript
await test.step('wait for async export to finish', async () => {
  await expect(page.getByText('Export ready')).toBeVisible();
}, { timeout: 10_000 });
```

Defaults to `0` (no step-level timeout — only the overall test timeout applies). Set an explicit `timeout` when one phase of a long test (e.g. a slow background job) needs its own budget so a hang there fails fast and points at the right step, instead of burning the whole test's timeout before failing generically.

## 4. `step.skip()` — disable one step without skipping the whole test

The step callback receives a `step` argument; call `step.skip()` to bail out of just that step while the rest of the test continues:

```typescript
await test.step('verify legacy banner (flaky, tracked in JIRA-4821)', async (step) => {
  if (isMobile) {
    step.skip(true, 'banner not rendered on mobile layouts');
    return;
  }
  await expect(page.getByRole('banner')).toBeVisible();
});
```

Prefer this over commenting out a step or wrapping it in an `if` with no annotation — `step.skip()` marks the step as skipped in the report (with your reason string) instead of silently omitting it, so the skip is visible and searchable in CI history.

## 5. TypeScript decorator pattern for Page Object methods

For POM classes with many methods, wrapping each one manually in `test.step()` gets repetitive. A class-method decorator applies it automatically:

```typescript
function step(target: Function, context: ClassMethodDecoratorContext) {
  return function replacementMethod(this: any, ...args: any[]) {
    const name = `${this.constructor.name}.${String(context.name)}`;
    return test.step(name, () => target.call(this, ...args), { box: true });
  };
}

class LoginPage {
  constructor(private page: Page) {}

  @step
  async signIn(user: string, pass: string) {
    await this.page.getByLabel('Username').fill(user);
    await this.page.getByLabel('Password').fill(pass);
    await this.page.getByRole('button', { name: 'Sign in' }).click();
  }
}
```

Every decorated method reports as `LoginPage.signIn` in the HTML report and Trace Viewer, boxed by default, with zero per-method boilerplate. Requires TS 5.0+ decorator syntax (`"target": "ES2022"` or later in `tsconfig.json`).

## Decision table

| Need | Use |
|---|---|
| Group related actions under one report/trace label | `test.step(title, body)` |
| Hide a helper's internal call stack from error output | `{ box: true }` |
| Hide a fixture's internal steps but keep the fixture body's own steps visible | `{ box: 'self' }` on the fixture |
| Fail fast on one slow phase without inflating the whole test's timeout | `{ timeout: ms }` |
| Conditionally skip one step, with a visible reason | `step.skip(condition, reason)` |
| Auto-step every Page Object method without manual wrapping | class-method decorator (§5) |

Not a substitute for `test.step.skip()` at the top level or `test.skip()` — those skip declaration-time; `step.skip()` inside a running step is for conditional, runtime skip decisions.

## Sources
- https://raw.githubusercontent.com/microsoft/playwright/v1.61.0/docs/src/test-api/class-test.md (Added in: v1.10 for `test.step()`, v1.50 for `timeout` option and `step.skip()`)
- https://github.com/microsoft/playwright/issues/33475 (timeout option for test.step)
- https://github.com/microsoft/playwright/issues/19332 (step.skip feature request/implementation)
- https://timdeschryver.dev/blog/keep-your-playwright-tests-structured-with-steps
- https://learn.microsoft.com/en-us/samples/microsoft/playwright-examples/boxed-steps/
- https://qaskills.sh/blog/playwright-test-step-annotations-guide
