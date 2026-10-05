# Soundwise (white-label Android apps — manual/adb QA)

## Quick Snapshot
- **Stack**: manual QA + `adb shell uiautomator dump` (no Maestro flows saved to disk for this project)
- **Disk**: `D:\HK8\Learning\DQ\test\soundwise-audio-android`
- **Odoo**: all bugs logged to project 76 "[Project] Soundwise" (no per-brand project) — see
  [[project_soundwise-whitelabel-qa]] for stages/credentials/brand list.

## State already on disk — check before re-running or re-asking
`00_COVERAGE_MATRIX.md` / `01_EXPANDED_COVERAGE_MATRIX.md` = the test matrix. `matrix_run_*.log`
files = prior run results per section (A/B/C/DEFGH/auth) — check the latest `_v2`/`_v3` log before
re-running a section; only retest IDs that were still failing in the LAST log, not the whole section.
`dumps/` (338 files) = already-harvested UI hierarchy dumps (`.xml` + `.png` pairs) per screen —
check here before re-dumping a screen that's already captured.

## Perf lesson (2026-09-21)
Element discovery here was 338 individual `adb uiautomator dump`+`pull` round-trips instead of a
batched/warm-session harvest, and failing sections got re-run whole (3×/3×/2×) instead of retesting
only the failed IDs. Read the "MANDATORY gate" at the top of the `maestro-mobile` skill before
adding more dumps or re-running sections — same discipline applies even without Maestro YAML flows.

## Persistence testing — cold relaunch required
State-persistence claims (edit saved, download persisted, etc.) must be verified with
`adb shell am force-stop <pkg>` + relaunch, not navigate-away-and-back — see
[[lesson_android-persistence-needs-cold-relaunch]]. A profile-bio "PASS" was retracted to BUG once
a real cold relaunch was used (revert only showed up then).

## AUTH module gotchas (2026-09-22 re-run)
- **New Android notification-permission system dialog appears on cold launch** since ~2026-09,
  not present when `run_matrix_auth_full.py` was first written — script now auto-dismisses it
  ("Allow" tap) inside `ensure_cold_start_at_login()`.
- **`sw_driver.Device()` now supports `ANDROID_SERIAL` env var** (fixes "Multiple devices
  connected" crash when both the wireless-debug and USB session of the same phone show up in
  `adb devices` at once) — set it before running any script if that error appears again.
- **AUTH-09 (Forgot Password) must NEVER submit the reset form against `Support@mysoundwise.com`**
  — user explicitly said (2026-09-22) not to trigger a real password reset on that shared real
  content account. The script now only verifies the external-browser link opens, and does not
  type an email or tap "Send reset email". The full submit+confirmation was verified once
  manually on 2026-09-14 (01_EXPANDED_COVERAGE_MATRIX.md AUTH-09) — treat that as still valid,
  don't re-trigger a real reset email automatically on future runs.
- Chrome's WebView content for `app.mysoundwise.com/password_reset` is **not exposed in the
  uiautomator accessibility tree** (only the URL bar/toolbar show up as native nodes) — any
  future automation of that page needs screenshot-based pixel coordinates, not `find_by_text`.

## Gap-fill pass 2026-09-22 — SET-07/SET-09/NOT-03 closed, GLB-02/03 blocker root-caused
Closed the last genuinely-actionable open items from `00_COVERAGE_MATRIX.md`: Log Out (SET-07),
Show Profile (SET-09), tap-notification-navigates (NOT-03) — all PASS. Also root-caused why
GLB-02/03 (airplane mode) kept getting deferred: the phone's SECOND "device" entry in `adb devices`
(`adb-R58NA3EF0YA-YxSlil._adb-tls-connect._tcp`) looks like it could be a USB cable but is actually
ALSO wireless debugging (mDNS-discovered), not a real USB connection — both `adb` entries share the
same wifi radio and would drop together if wifi/airplane-mode were toggled. **Don't assume a second
`adb devices` entry is a USB safety net without checking** — a real USB serial looks like a bare
alphanumeric string (no `_adb-tls-connect._tcp` suffix, no `ip:port` form). Airplane-mode testing
here still needs an actual USB cable, not just a second `adb devices` row.

## Device state gotchas
- **Locked/dozing device blocks adb input.** Diagnose with `adb shell dumpsys power | grep
  mWakefulness` and `adb shell dumpsys window | grep isKeyguardShowing`; if locked, ask the user to
  physically unlock (adb can't unlock it for you). Mitigate recurrence:
  `adb shell settings put system screen_off_timeout 1800000` (30min) at session start.
- **`uiautomator dump` can return the PREVIOUS screen's stale content** during an active transition
  or while audio is playing, not just missing popups — see the second trigger note in
  [[lesson_uiautomator_diff_misses_popup_windows]]. Cross-check with a screenshot before treating a
  suspicious dump as a finding.

## Deliverable convention — save + verify automation scripts exist
User has asked twice ("Nhớ lưu automation scripts cho full AUTH Module này", later "Đã lưu
automation scripts chưa" for Profile) for each tested module to produce a saved, re-runnable script
(`run_matrix_<module>_full.py` pattern) — confirm it exists via `ls` before reporting a module
"done", don't just describe it as saved.

## Last Session
- **Date**: 2026-09-16 (last file touch)
- **Did**: Expanded coverage matrix; sections A/B/C matrix runs (with retries after fixes).
- **Next step**: check `01_EXPANDED_COVERAGE_MATRIX.md` + latest `matrix_run_*` logs for open items.
