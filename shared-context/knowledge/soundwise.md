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
