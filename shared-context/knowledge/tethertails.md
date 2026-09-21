# TetherTails (App — Maestro mobile)

## Quick Snapshot
- **Stack**: Maestro (Android, `com.tethertails.tethertails.stg`, staging, device 192.168.1.11)
- **Disk**: `D:\HK8\Learning\DQ\TetherTails\app-automation`
- **NOT a git repo** — deliverables live on disk only.

## Credentials — ALREADY ON DISK, don't ask, read `app-automation/ACCOUNTS.md` first
Login = phone (+65) + static test OTP `418` + last-3-digits-of-phone (no SMS). Full account table
(Care+/Care/Free tiers, phone/OTP pairs) is in `ACCOUNTS.md` in that folder — read it before asking
the user for credentials or claiming login is blocked.

## Existing element maps / flow inventory — don't re-harvest from scratch
`ELEMENT_MAP_PETMGMT.md`, `ELEMENT_MAP_SUBA.md`, `LOSTPET_AUTOMATION_MAP.md`,
`PETMGMT_AUTOMATION_MAP.md`, `SUBA_AUTOMATION_MAP.md`, `CALENDAR_AUTOMATION_MAP.md` — element/flow
maps already harvested for their respective modules. Check these before re-dumping the UI.
`MATRIX_RESULTS.md` = tier×permission matrix results already run.

## ⚠️ P0 — Generated automation flows ARE saved on disk. Run/extend them, don't rewrite from scratch.
User asked this 3 separate times across sessions (24-Aug, 27-Aug, 03-Sep — "có lưu script auto lại
để những lần sau chạy cho nhanh k, chứ mỗi lần cứ dò lại rất mất thời gian") — meaning it was never
durably fixed. The `.yaml` flows ARE persisted: `app-automation/flows/**/*.yaml` (mobile, Maestro)
and `TetherTails_Portal/automation/` (portal, Playwright). At the start of ANY TetherTails/Portal
task: `ls`/glob the relevant flows dir FIRST and check whether a flow for the target scenario
already exists — extend or re-run it (`maestro test flows/x.yaml`) instead of authoring a fresh one
or re-discovering selectors. Only write a new flow when nothing already covers the scenario.

## Staging environment facts (told to Claude, not previously written down anywhere — 18-Sep)
- **Staging billing does NOT actually charge money** — safe to run real purchase/upgrade/downgrade
  IAP flows on staging without worrying about real charges.
- **Multi-account testing needs a second ACCOUNT (login), not a second physical device.** Use
  `switch-account.yaml` / a second phone+OTP pair from `ACCOUNTS.md`, not a second device/emulator.
- **Destructive/RPC operations CAN be performed on staging.** This is a staging-specific allowance —
  it does NOT apply to the TetherTails Portal PROD no-delete/no-edit rule
  ([[feedback_tethertails-portal-no-delete-no-edit-existing]]), which is about the Portal's
  production data specifically, not the mobile app's staging environment.

## Unverified — needs reconfirm before treating as fact
- Voice notes may be visible only to the household member who added them, with other roles
  (including Full/Owner) unable to see them — mentioned once (25-Aug) but not yet re-verified or
  cross-checked against `reference_tethertails-permission-model.md`'s CRUD×role matrix, which
  documents role-based CRUD but not creator-only visibility for voice notes specifically.

## Known findings
- View-tier household member gets Edit/Delete + a functional (but server-blocked) Save form on the
  medical Weight Log — client affordance leak, locked in `permissions/view-capabilities.yaml`
  (asserts the bug present, so it FAILS when fixed).

## Live check 2026-09-21 (Galaxy A51 SM_A515F, Android 13) — RESOLVED, read this before touching flows
- **Root cause of "tap COMPLETED but nothing happens" / "Tap on Pets failed" after cold start:** an
  in-app **Announcements overlay** (badge "UPDATE"/"PROMO", title, Next, X) appears 1-3s after
  `launchApp` returns and covers the tab bar + avatar. Found by screenshotting at t=1/3/10s after
  `force-stop` + launch (popup still there at 10s). `adb input tap` on the same coords worked, so app
  and selector were fine.
- **Fix (done):** `flows/_setup/dismiss-popups.yaml` rewritten: waits up to 3s (optional) for a View
  labelled `Announcements`, taps its X by point `85%,24%` (X has no accessibilityText), plus the legacy
  PROMO block. The old helper only matched "PROMO" and tapped 89%,18%, so it missed this popup type.
  Every cold-starting flow now calls it: 55/82 (26 added; for the 5 clearState+login flows it is
  inserted AFTER login, because the popup shows post-login). Canary went 0/3 -> 3/3; `check_bell` ok;
  `maestro check-syntax` 0 failures on all flows. Backups: `_backup/flows_before_appid_20260921`,
  `_backup/flows_before_popup_20260921`.
- **appId standardized to `.stg`** in all 82 flows + `.maestro/config.yaml` (36 were prod id; only the
  stg app is installed). Note the popup content ("Lee test") is a portal test announcement; new
  announcements may change the X position -> if a flow stalls right after launch, screenshot first.
- **Maestro upgraded 2.5.1 -> 2.10.0** on this machine (old copy: `~/.maestro/maestro_2.5.1_backup`).
  Upgrade did NOT fix the flake (it was the popup) but the skills now match the CLI.
- Device was logged in as **QC HH Free3 Phat (70000036)** at check time.

## Perf lesson (2026-09-21) — read before writing/running more flows
CORRECTED 2026-09-21 (earlier text here said 23/23, which was wrong): only 5/82 flows (all in
`flows/petmgmt/`, delete/edit flows) run `launchApp:{clearState:true}` + full OTP login per
flow. The other 56 use `clearState:false` (warm session), so per-flow login was NOT the main cause
of the slowness seen here — element discovery and whole-suite reruns were. See the "MANDATORY gate"
at the top of the `maestro-mobile` skill before adding more flows to this project.

## Last Session
- **Date**: 2026-09-12 (last file touch)
- **Did**: petmgmt matrix (create/edit/delete/cancel flows), member move-to-memory, household delete
  flows.
- **Next step**: unclear — resume from `00_COVERAGE_MATRIX.md`/`99_OPEN_ITEMS_AND_QUESTIONS.md` in
  the parent `TetherTails/` folder for what's still open.
