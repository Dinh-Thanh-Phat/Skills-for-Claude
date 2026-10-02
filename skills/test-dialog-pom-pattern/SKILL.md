---
name: test-dialog-pom-pattern
description: Proper dialog handling in POM - avoid dialog handler conflicts, centralize dialog logic
type: skill
---

# Dialog Handling in Page Object Model

## Problem
Dialog handlers registered in both test code AND POM methods conflict, causing "Cannot accept dialog which is already handled!" errors.

## Root Cause
Playwright's `page.once('dialog')` or `waitForEvent('dialog')` can only be handled once per dialog. If both test and POM register handlers, the second one throws.

---

## ✅ CORRECT PATTERN: POM Owns Dialogs

### Step 1: Dialog Logic Lives ONLY in POM

**File: `pages/AdminPage.ts`**
```ts
export class AdminPage {
  constructor(private page: Page) {}

  async deleteUser(email: string) {
    // POM handles dialog internally.
    // ⚠️ Native dialogs BLOCK the page: click() does not resolve until the dialog is
    // handled. Never `await Promise.all([waitForEvent('dialog'), click()])` and accept
    // afterwards — that deadlocks until timeout (playwright.dev/docs/dialogs).
    // Register the handler BEFORE the click instead:
    this.page.once('dialog', (dialog) => dialog.accept());  // Accept or dismiss based on action
    await this.page.getByRole('row').filter({ hasText: email })
      .getByRole('button', { name: /delete|remove/i })
      .click();
    // Wait for the real outcome, not networkidle (DISCOURAGED in Playwright docs)
    await expect(this.page.getByRole('row').filter({ hasText: email })).toHaveCount(0);
  }

  async deleteContact(name: string) {
    // Variant when you need the Dialog object (e.g. to assert its message):
    const dialogPromise = this.page.waitForEvent('dialog');
    const clickPromise = this.page.getByText(name)
      .locator('..')  // Parent card
      .getByRole('button', { name: /delete/i })
      .click();
    const dialog = await dialogPromise;
    await dialog.accept();   // unblocks the page
    await clickPromise;      // click resolves only after the dialog was handled
  }
}
```

### Step 2: Test Code Does NOT Handle Dialogs

**File: `tests/admin/delete-operations.spec.ts`**
```ts
test('DEL-001: Delete user → confirmation appears', async ({ page }) => {
  const admin = new AdminPage(page);
  
  // Create test user
  await admin.gotoUsers();
  await admin.addUser({
    name: 'Test User',
    email: 'test@example.com',
    password: 'Pass123@',
  });

  // Call POM method — it handles dialog internally
  await admin.deleteUser('test@example.com');  // ← NO dialog handler here!
  
  // Verify deletion
  await admin.gotoUsers();
  // Web-first, retrying assertion (isVisible() ignores `timeout` and never waits)
  await expect(page.getByRole('heading', { name: /users/i })).toBeVisible(); // list really loaded
  await expect(page.getByText('test@example.com')).toHaveCount(0);
});
```

**❌ WRONG (test code also handles dialog):**
```ts
test('DEL-001: Delete user', async ({ page }) => {
  const admin = new AdminPage(page);
  
  // This causes conflict!
  page.once('dialog', (dialog) => dialog.accept());  // ← CONFLICT!
  await admin.deleteUser('test@example.com');  // ← POM also handles dialog
});
```

---

## Pattern Reference

### For Single-Step Dialogs (click → dialog appears)

```ts
async deleteItem(button: Locator) {
  // Handler registered BEFORE the click — the dialog blocks the click until handled
  this.page.once('dialog', (dialog) => dialog.accept());  // or .dismiss()
  await button.click();
}
```

### For Multi-Step Dialogs (fill form in dialog)

```ts
async confirmAction(confirmText: string) {
  const [dialog] = await Promise.all([
    this.page.waitForEvent('dialog'),
    this.page.getByRole('button', { name: /confirm|delete/i }).click(),
  ]);
  
  // Verify dialog message
  expect(dialog.message()).toContain('Are you sure');
  await dialog.accept();
}
```

### For Dialogs Without Auto-Dismiss

```ts
async handleAuthDialog(username: string, password: string) {
  const dialog = await this.page.waitForEvent('dialog');
  
  // Fill credentials if dialog has input
  if (dialog.type === 'prompt') {
    await dialog.accept(username);
  } else {
    await dialog.accept();
  }
}
```

---

## Conflict Resolution Checklist

- [ ] Dialog handling code lives **ONLY in POM**, never in tests
- [ ] Test code calls POM method, not direct dialog handlers
- [ ] Each POM action that triggers dialog uses `Promise.all([waitForEvent, click])`
- [ ] No `page.once('dialog')` in test code
- [ ] No `page.on('dialog')` listeners outside POM
- [ ] POM method name makes dialog expectation clear: `deleteUser()`, `confirmAction()`, etc.

## Error Message Decoder

| Error | Cause | Fix |
|-------|-------|-----|
| `"Cannot accept dialog which is already handled"` | Both test + POM handle dialog | Remove handler from test |
| `"Cannot handle dialog, another handler was already registered"` | `page.on()` + `waitForEvent()` | Use only one approach |
| `"Dialog was closed"` | Dialog dismissed before handler could accept | Ensure handler registered BEFORE click |
| `"Timeout waiting for event 'dialog'"` | No dialog appeared | Check selector, verify action triggers dialog |

## Modal Dialog Components (NOT native — React/Vue/Radix)

Patterns above cover **native** `window.alert/confirm/prompt`. Modal components (HTML `<dialog>`,
Headless UI, Radix AlertDialog) are just DOM — `page.waitForEvent('dialog')` will NOT fire.

```ts
async deleteUser(email: string) {
  await this.page.getByRole('button', { name: /delete/i })
    .filter({ hasText: email }).click();
  const modal = this.page.getByRole('dialog');
  await expect(modal).toBeVisible();
  await modal.getByRole('button', { name: /confirm|yes/i }).click();
  await expect(modal).toBeHidden();
}
```

## `addLocatorHandler` for Unexpected Modals

```ts
// Auto-dismiss any cookie banner that pops up mid-test
await page.addLocatorHandler(
  page.getByRole('dialog', { name: /cookies?/i }),
  async (modal) => { await modal.getByRole('button', { name: /accept/i }).click(); }
);
```

## References

- [Playwright Dialog API](https://playwright.dev/docs/dialogs)
- [Page Object Model Guide](https://playwright.dev/docs/pom)
- [Dialog Handling Best Practices](https://www.browserstack.com/guide/page-object-model-with-playwright)
- [POM with Dialog Components](https://testomat.io/blog/page-object-model-pattern-javascript-with-playwright/)
