# Debug Report — [Feature Name]
<!-- Scenario C input template. Fill before invoking playwright-snapshot-parser Step 5. -->

## Failing Test
**File:** [e.g., tests/login.spec.ts]
**Test name:** [e.g., "login with valid credentials → redirects to dashboard"]
**Line number:** [e.g., 42]

---

## Failing Selector
```typescript
// Paste the exact failing locator here
page.getByRole('button', { name: 'Submit' })
```

---

## Error Output
```
// Paste the full Playwright error here
Error: locator.click: Error: strict mode violation: getByRole('button', { name: 'Submit' }) ...
```

---

## Page State When Failure Occurs
**URL:** [e.g., https://app.example.com/login]
**State:** [e.g., "After filling email and password fields"]
**Screenshot path:** [e.g., test-results/login-failure.png  — if available]

---

## When Did It Last Pass?
- [ ] Never passed
- [ ] Passed before [approximate date or commit]
- [ ] Passes locally but fails in CI
- [ ] Flaky — passes sometimes

---

## What Changed Since Last Pass
- [ ] UI update / redesign
- [ ] Text content changed
- [ ] New element added that creates duplicate matches
- [ ] Auth / routing change
- [ ] Unknown

---

## Expected Behavior
[What should happen when the test runs correctly]

---

## Snapshot File (attach after capturing)
**Snapshot path:** data/outputs/snapshots/[feature]-snapshot.txt
