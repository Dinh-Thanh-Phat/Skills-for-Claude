# TetherTails Portal (Admin web — Playwright)

## Quick Snapshot
- **Stack**: Playwright + TypeScript, `automation/` folder
- **Disk**: `D:\HK8\Learning\DQ\TetherTails\TetherTails_Portal`
- **NOT a git repo** — companion to the `tethertails` mobile app project (shared parent folder).

## State/creds already on disk — check before asking
`PORTAL_LIVE_INVENTORY.md`, `execution_results_202608*.json` (prior run results), `automation/`
(Playwright specs + likely `.auth/` storage state). Check these before re-asking for portal
credentials or re-running a scenario already recorded as pass/fail in an execution_results file.

## Known rule
🚨 **PROD — never delete/edit existing real data**, only edit test data you created yourself
([[feedback_tethertails-portal-no-delete-no-edit-existing]]).

## Verification protocol
Two-pass: verify API-only then UI-only separately + reload, cross-check — catches optimistic-UI
lies ([[feedback_two-pass-api-then-ui-separately]]).

## Last Session
- **Date**: 2026-08-29 (last file touch)
- **Did**: Household/subscription QA (`19_household.md`, `18b_subscriptions_portal.md`), found
  SUB-011/HH-004 (app member sees shared pets bug, screenshots attached).
- **Next step**: check `99_OPEN_ITEMS_AND_QUESTIONS.md` for what's still open.
