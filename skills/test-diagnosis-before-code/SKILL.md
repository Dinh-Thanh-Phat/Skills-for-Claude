---
name: test-diagnosis-before-code
description: Diagnose app behavior before writing tests - understand UI, data flow, error handling, then code
type: skill
---

# Test Diagnosis Before Coding

## Rule
**Never write a test for a feature you haven't manually verified works.**

This prevents writing tests for broken features, tests that depend on unreliable state, or tests that check the wrong thing.

---

## The 4-Step Diagnosis Protocol

### Step 1: Feature Walkthrough (Manual Testing)

**Goal:** Verify the happy path works end-to-end

**Checklist:**
- [ ] Navigate to the feature
- [ ] Try the primary action (create, delete, export, import)
- [ ] Verify success state (button changes, data appears, download triggers)
- [ ] Open DevTools → check network requests, console errors
- [ ] Check response data (was it persisted? Did API work?)

**Example: CSV Export**
```
1. Go to /admin/ports
2. Click "Export CSV" button
3. Check: Download dialog appears?
4. Check: File has correct headers + data?
5. DevTools → check Network tab for export API call
6. If API returns error → don't write test yet, report bug
```

### Step 2: State Persistence Check

**Goal:** Verify data persists after create/update/delete

**Checklist:**
- [ ] Create/update item
- [ ] Refresh page
- [ ] Item still visible?
- [ ] Clear browser cache
- [ ] Item STILL visible?
- [ ] If not → data is not actually persisting (bug)

**Example: User Creation**
```
1. Create user "Test User" via admin form
2. User appears in list
3. Refresh page (F5)
4. User STILL in list?
   - YES → can write test
   - NO → user creation only in UI cache (bug) → report it
5. Clear storage (DevTools → Application → Clear site data)
6. Reload → user still there?
```

### Step 3: Error Handling Check

**Goal:** Understand what happens when things go wrong

**Checklist:**
- [ ] What happens on invalid input? (validation message? toast? page reload?)
- [ ] What happens on network timeout? (error message? retry button? just hang?)
- [ ] What happens on duplicate? (duplicate allowed? merge? error?)
- [ ] What happens on permission denied? (404? 403? error message?)

**Example: CSV Import**
```
1. Try importing empty CSV (header only)
   - Message? Toast? Silent skip? → document behavior
2. Try importing with typo in headers
   - Does UI detect? Does it proceed anyway? → document behavior
3. Try importing duplicate port name
   - Merge? Skip? Error message? → document behavior
4. Record exact UI response for each case
```

### Step 4: Edge Cases & Boundaries

**Goal:** Find what breaks the feature

**Checklist:**
- [ ] Special characters in data (Vietnamese, emoji, quotes)
- [ ] Very long values (100+ chars, 1000 chars)
- [ ] Very large files (10MB CSV, 100 rows)
- [ ] Concurrent actions (delete while editing, import while exporting)
- [ ] Missing permissions (as guest, as limited user)

**Example: File Upload**
```
1. Upload file with special name: "tệp-tài-liệu (v1.0).pdf"
   - Name preserved or sanitized?
2. Upload large file (100MB)
   - Works? Timeout? Progress bar?
3. Upload while another upload is pending
   - Queue? Override? Error?
```

---

## Diagnosis Checklist Template

Create this for EVERY feature before writing tests:

```markdown
# Feature: [Feature Name]
## Status: [Not Started / In Progress / Ready to Test]

### Step 1: Happy Path
- [ ] Primary action works (create/delete/export/import)
- [ ] Success feedback visible (button state, message, download)
- [ ] Network request visible in DevTools
- [ ] Response is valid/expected

### Step 2: State Persistence
- [ ] Data visible after action
- [ ] Data persists after page refresh
- [ ] Data persists after cache clear
- [ ] Data visible to other users (if applicable)

### Step 3: Error Handling
- Invalid input: [behavior]
- Network timeout: [behavior]
- Duplicate data: [behavior]
- Permission denied: [behavior]

### Step 4: Edge Cases
- Special characters: [works/breaks]
- Large values: [works/breaks]
- Concurrent actions: [works/breaks]
- Missing permissions: [works/breaks]

### Known Issues
- [Issue 1]
- [Issue 2]

### Test Strategy
- Tests can focus on: [what's proven to work]
- Tests to fail-lock: [what's broken → `test.fail(true, 'BUG-xxx')`, see `skip-vs-fail`]
- Tests to hold back: [what's flaky — diagnose first, don't automate yet]
- Tests need mock: [external services]
```

---

## When Diagnosis Reveals Problems

### Problem: Feature Doesn't Work

```
Diagnosis: "Delete user button doesn't work"
→ Report bug with reproduction steps (get a BUG-ID)
→ Write the test asserting the EXPECTED behavior, locked with
  test.fail(true, 'BUG-xxx: delete user button does nothing')
→ When dev fixes, the run reports "expected to fail but passed" → remove test.fail
```
Never `test.skip` a known bug — canonical policy: `skip-vs-fail`.

### Problem: Feature Works But Flaky

```
Diagnosis: "Port import sometimes doesn't show on list"
→ Don't write test (it will be flaky)
→ Investigate: timing? cache? API response?
→ Propose fix: add loading indicator? delay? refresh?
→ Test AFTER fix is verified
```

### Problem: Feature Needs Data Setup

```
Diagnosis: "Delete test only works if user is already admin"
→ Your test needs setup
→ Add beforeEach() that grants admin role
→ Don't hard-code to existing admin user
```

---

## Diagnosis vs. Testing

| Phase | Activity | Outcome |
|-------|----------|---------|
| **Diagnosis** | Manual + DevTools | "Feature works / is broken / is flaky" |
| **Test Planning** | "What can we automate?" | "Tests X, Y, Z; skip W, V, U" |
| **Test Coding** | Write assertions | Automated verification |
| **Test Debugging** | "Why did test fail?" | Root cause (app bug vs. test bug) |

---

## Diagnosis For Special Feature Types

**Responsive / visual feature:**
- Native-resolution viewport screenshot at each breakpoint (375 / 768 / 1280) and VIEW IT
- Do NOT trust downscaled full-page thumbnails (see `feedback_visual-bug-native-screenshot-only`)

**Real-time / WebSocket feature:**
- DevTools → Network → WS tab — observe frames during manual test
- If frames absent → feature broken server-side, don't write test
- Test reconnect: kill network, restore → UI recovers?

**Cross-tab / multi-user feature:**
- Open 2 windows; action in tab 1; verify tab 2 updates
- Propagation >5s = UX bug; file bug first

**Feature behind feature flag:**
- Confirm flag value in test env BEFORE writing (flag off → test always fails)
- Get toggle mechanism from dev (env var, admin UI, API)

## Red Flags (Stop, Diagnose First)

- [ ] Test expects data that you haven't manually verified persists
- [ ] Test skips because "app doesn't support this yet"
- [ ] Test relies on timing (setTimeout) instead of waiting
- [ ] Test passes randomly (flaky after diagnosis)
- [ ] Test only works in specific order (state dependency)
- [ ] Dialog/message not appearing in your test (works in manual testing)

## Tools for Diagnosis

| Tool | Use For |
|------|---------|
| **Browser DevTools** | Network requests, console errors, storage |
| **Playwright Trace** | Record test execution, replay failures |
| **Video Recording** | See UI updates in slow motion |
| **Inspector Mode** | Find stable selectors |
| **Page Source** | Understand form structure, data attributes |

## References

- [Playwright Debugging Guide](https://testdino.com/blog/playwright-debugging-guide/)
- [Running & Debugging Tests](https://playwright.dev/docs/running-tests)
- [Playwright Trace Viewer](https://playwright.dev/docs/trace-viewer)
- [Diagnosis Best Practices](https://betterstack.com/community/guides/testing/avoid-flaky-playwright-tests/)
