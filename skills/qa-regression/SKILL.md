---
name: qa-regression
description: Manage and execute regression testing, smoke tests, and release readiness checks. Use when asked to do "regression testing", "smoke test", "sanity check", "release testing", "pre-deploy checklist", "is this safe to release", "test before release", or after a significant code change. Analyzes git diff to identify regression risk.
---

# QA Regression Testing Skill

You are a **Senior QA Engineer** running regression and release-readiness testing.

## Types of Testing

| Type | When | Coverage | Duration |
|------|------|---------|---------|
| **Smoke Test** | After every deploy | Core flows only | 5-15 min |
| **Sanity Test** | After a bug fix | Changed area + direct neighbors | 15-30 min |
| **Regression Test** | Before release | All critical paths | 1-4 hours |
| **Full Regression** | Major release | Everything | Day(s) |

---

## Step 1: Analyze What Changed

Before running any tests, read the changes:
1. Run `git diff main...HEAD` to see what changed
2. Identify impacted areas (which features, which files)
3. Map changes to risk:

| Change Type | Regression Risk |
|-------------|----------------|
| Database schema change | HIGH — check all data reads/writes |
| Auth / permissions change | HIGH — check access control everywhere |
| Shared utility/helper change | HIGH — check all callers |
| API contract change | HIGH — check all consumers |
| UI-only change (styling) | LOW — visual check only |
| New feature (isolated) | MEDIUM — check new feature + integration points |
| Bug fix | MEDIUM — check fix works + no new bugs introduced |
| Dependency upgrade | HIGH — check all areas that use the dependency |

---

## Smoke Test Checklist

Run after every deploy. Should take < 15 minutes.

```markdown
## Smoke Test — [date] [env]

### Core Flows
- [ ] App loads without console errors
- [ ] User can log in with valid credentials
- [ ] User can log out
- [ ] Main navigation works (all top-level pages load)
- [ ] Most critical user action works (e.g., create record, submit form)
- [ ] API health check returns 200

### Result: PASS / FAIL
- Failures: [list any failures]
- Decision: DEPLOY / ROLLBACK
```

---

## Regression Test Suite Template

```markdown
## Regression Test Run — [version/PR] — [date]

**Environment:** [staging / prod]
**Triggered by:** [PR #, deploy, change description]
**Tester:** QA
**Estimated time:** [X hours]

---

### High Risk Areas (test all)
Based on changes in this PR/release:
- [Area 1 — reason it's high risk]
- [Area 2]

### Test Execution

#### Authentication & Authorization
- [ ] Login (valid credentials)
- [ ] Login (invalid credentials — correct error shown)
- [ ] Logout
- [ ] Access protected page without auth → redirect to login
- [ ] Role-based access (user cannot access admin pages)
- [ ] Password reset flow

#### Core User Flows
- [ ] [Main feature 1] — happy path
- [ ] [Main feature 1] — error path
- [ ] [Main feature 2] — happy path
- [ ] [Main feature 2] — error path

#### Data Integrity
- [ ] Create operation persists correctly
- [ ] Update operation saves changes correctly
- [ ] Delete operation removes data (or soft-deletes correctly)
- [ ] List/search shows correct data
- [ ] No data leakage between users/accounts

#### Integrations
- [ ] [External API 1] integration works
- [ ] [Webhook] fires on expected events
- [ ] [Email] notifications sent correctly

#### Performance
- [ ] Page load < 3s on standard connection
- [ ] No memory leaks (check browser DevTools)
- [ ] API responses < 500ms

#### Cross-Browser (if applicable)
- [ ] Chrome — latest
- [ ] Firefox — latest
- [ ] Safari — latest
- [ ] Mobile Safari (iPhone)
- [ ] Chrome Android

---

### Results Summary

| Area | Tests Run | Pass | Fail | Skip |
|------|----------|------|------|------|
| Auth | X | X | X | X |
| Core Flows | X | X | X | X |
| Total | | | | |

### Bugs Found
| ID | Title | Severity | Status |
|----|-------|---------|--------|
| BUG-001 | ... | P2 | Open |

### Release Decision
- [ ] **GO** — all P1 tests pass, no blocker bugs
- [ ] **GO WITH CONDITIONS** — [list conditions]
- [ ] **NO-GO** — [list blocking issues]

**Sign-off:** QA — [date]
```

---

## Risk-Based Regression Prioritization

When time is short, prioritize by:

**Always test (no matter what):**
1. Login / Logout / Auth
2. The primary user action (what the app is FOR)
3. Payment / financial flows (if applicable)
4. Data persistence (create/edit/delete)

**Test if time allows:**
5. Secondary features
6. Admin functions
7. Edge cases

**Automate first:**
- Smoke tests (run on every deploy via CI)
- Auth flows (login/logout/access control)
- CRUD operations on main entities
- Critical business flows

---

## Auto-Map `git diff` → Spec Files to Run

Reduce regression run time by only running specs affected by the changed files:

```bash
# 1. Get changed files
CHANGED=$(git diff main...HEAD --name-only)

# 2. Map source → spec (project-specific convention)
for f in $CHANGED; do
  case "$f" in
    src/auth/*)          SPECS="$SPECS tests/auth/" ;;
    src/dashboard/*)     SPECS="$SPECS tests/dashboard/" ;;
    src/components/*)    SPECS="$SPECS tests/components/" ;;
    src/api/*)           SPECS="$SPECS tests/api/" ;;
    *)                   AFFECTS_ALL=1 ;;
  esac
done

# 3. If a shared utility changed → run full suite
if [ -n "$AFFECTS_ALL" ]; then
  npx playwright test
else
  npx playwright test $SPECS
fi
```

Playwright 1.46+ has `--only-changed=main` for this automatically.

## Automation Coverage Gap Analysis

Ask this regularly:
- What manual tests am I running every sprint? → Automate those first
- What bugs escaped to prod recently? → Add regression tests for those
- What takes the longest to test manually? → Automate for speed

Track automation coverage:
```
Total critical test cases: N
Automated: M (M/N = X%)
Manual only: N-M
Target: 80% automation coverage for P1 tests
```

---

## Release Readiness Checklist

Before signing off on a release:

**Code Quality:**
- [ ] All automated tests passing in CI
- [ ] No known P0/P1 bugs open
- [ ] New feature tests written and passing
- [ ] Code reviewed and merged

**QA Sign-off:**
- [ ] Smoke test passed on staging
- [ ] Regression test completed
- [ ] New features tested against acceptance criteria
- [ ] Performance acceptable
- [ ] Security checks done (if auth/data changes)

**Deployment:**
- [ ] Rollback plan documented
- [ ] Feature flags configured (if applicable)
- [ ] Monitoring/alerts in place
- [ ] Team notified of release time
