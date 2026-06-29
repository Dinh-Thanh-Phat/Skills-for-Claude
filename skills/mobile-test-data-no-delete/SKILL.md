---
name: mobile-test-data-no-delete
description: |
  Test-data lifecycle strategy for when the app under test has NO delete/cleanup mechanism in the UI
  or API (common in mobile/CRM apps where records can only be created, edited, or "banned"/archived).
  Use when a create/edit test would leave permanent data behind and there is no way to remove it,
  when you discover an app "can't delete", when test data is piling up on staging, or when planning
  CRUD automation against an app whose Delete is missing.
  Triggers on: "no delete", "can't delete test data", "app has no delete", "test data accumulating",
  "cleanup without delete API", "how to clean test clients", "data dồn", "không xóa được data test".
---

# Test Data Lifecycle When the App Has No Delete

Standard test-data hygiene (`afterEach` deletes what the test created) **assumes a delete exists**.
Many real apps don't have one — records can only be created/edited, or soft-removed via
"ban"/"archive". Running create-heavy automation then **permanently accumulates data** on the shared
environment. This skill is the playbook for that situation.

## Step 0 — Confirm the gap (don't assume, don't over-probe)

Before designing cleanup, confirm delete truly doesn't exist:
- Check the obvious entry points (item menu, detail screen, edit form bottom) — **1–2 probes max**.
- Then **ask the human who knows the app**: "How do you delete a record here?" Blindly probing many
  gestures (long-press, swipe, every menu) wastes more time than asking. (Cross-ref `ask-when-stuck`.)
- A "soft delete" (ban / archive / deactivate) often exists even when hard delete doesn't — that may
  be the intended teardown.

## The strategy ladder (best → fallback)

| Rank | Strategy | When | Note |
|---|---|---|---|
| 1 | **Backend cleanup** — ask dev for a DB script or internal API to purge by tag | You have/can get backend access | Cleanest. A scheduled CI stage runs `DELETE ... WHERE name LIKE 'TESTAUTO%'` post-run |
| 2 | **Ephemeral env / DB reset** | Test env is disposable (containers, seeded snapshot) | Reset between runs instead of per-record delete |
| 3 | **Soft-delete via the app** | App has ban/archive/deactivate | Use it as teardown; assert the record leaves the active list |
| 4 | **Reuse seeded data for read-only tests** | Search / filter / view / validation tests | These need NO new record — drive them against existing fixtures, so only genuinely-creating tests add data |
| 5 | **Tagged prefix + accept accumulation** | Nothing above is available yet | Make every created record identifiable for later manual/DB purge; minimise how many you create |

You will usually **combine** 4 + 5 now and push for 1 with the dev team.

## Mandatory tagging (always, even when you can't clean yet)

Every record a test creates MUST carry a unique, greppable tag so a human/DB can purge it later:

```js
// scripts/generate-entity.js (Maestro runScript)
var ts = Date.now();
output.name  = 'TESTAUTO' + ts;   // prefix = filter key; ts = unique per run
output.email = 'testauto' + ts + '@qa.test';
```

- Prefix (`TESTAUTO`) → the DB/CSV filter for cleanup.
- Timestamp → uniqueness so re-runs don't collide and you can spot the run that made it.

## Minimise what you create

- **Validation tests** (missing required, bad format) should be **blocked by the app** → assert they
  do NOT create. If they pass, no data is added (and if they wrongly create, that's a bug you found).
- **Search / view / filter** tests reuse an existing known record — don't create.
- Only **create** and **edit** tests legitimately add/mutate data. Keep them few; have one create test
  feed the edit test where practical (but beware brittle cross-test dependencies — prefer
  self-contained over shared mutable state).

## Always tell the user / log it (no silent accumulation)

When you cannot auto-clean, **say so explicitly** and quantify:

> ⚠️ App has no Delete → these N `TESTAUTO*` records persist on staging. Recommend a dev DB-purge
> (`WHERE name LIKE 'TESTAUTO%'`) or a scheduled cleanup stage. This run added X records.

Silent accumulation reads as "tests are clean" when they aren't. File it as a known limitation /
follow-up issue, like an untestable flow (cross-ref `otp-untestable-flows`, `test-data-lifecycle`).

## Sources

- [Techniques for Effective Test Data Cleanup in CI/CD — The Green Report](https://www.thegreenreport.blog/articles/techniques-for-effective-test-data-cleanup-in-cicd/techniques-for-effective-test-data-cleanup-in-cicd.html)
- [The argument against clearing the database between tests — Cal Paterson](https://calpaterson.com/against-database-teardown.html)
- [5 Ways to Handle Test Data in Playwright — TestDino](https://dev.to/testdino01/5-ways-to-handle-test-data-in-playwright-1l32)
- [E2E Test Design Anti-Patterns (test independence) — Medium/AgileWay](https://agileway.substack.com/p/e2e-test-design-anti-pattern-the)
