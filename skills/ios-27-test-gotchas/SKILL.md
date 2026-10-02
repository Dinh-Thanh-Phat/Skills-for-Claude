---
name: ios-27-test-gotchas
description: |
  Version-specific breakages when running iOS UI tests (XCUITest / Appium / Maestro) with Xcode 27.x
  and iOS 27 — where a suite that passed on Xcode 26 fails because of the toolchain or driver, not the
  app. Covers Simulator.app being replaced by Device Hub (Maestro Studio "Streaming failed", Appium
  simulator launch failure), WebDriverAgent refusing to build (IPHONEOS_DEPLOYMENT_TARGET < 15),
  preinstalled WDA dying after ~20 s, xcodebuild spawning a 10-minute simctl diagnose after a failed
  driver session, clipboard/pasteboard reads failing on iOS 27 simulators, keyboard flicker during
  send_keys, and iOS 27 hit-testing changes (keyboard-covered buttons, duplicated SwiftUI a11y elements).
  Use when: anything iOS-automation broke right after installing Xcode 27 / iOS 27 runtimes / macOS 27.
  Triggers on: "iOS 27", "Xcode 27", "Xcode 27.1", "Xcode 27.2", "Device Hub", "DeviceHub.app",
  "Simulator.app cannot be opened", "Streaming failed", "IPHONEOS_DEPLOYMENT_TARGET", "WebDriverAgent
  build failed Xcode 27", "preinstalled WDA", "usePreinstalledWDA", "Code=10300", "simctl diagnose",
  "collect-test-diagnostics", "DeviceUnreachableException", "get_clipboard iOS 27", "keyboard flicker
  send_keys", "SimulatorKit", "idb HID", "unhittable iOS 27", "test iOS 27 fail",
  "maestro studio không stream sau update Xcode", "WDA không build được Xcode 27",
  "lên Xcode 27 test hỏng".
---

# iOS 27 / Xcode 27.x Test Gotchas

> **Why this skill exists:** Xcode 27 changed the *plumbing* under every iOS automation tool —
> the Simulator GUI app, the minimum deployment target, how XCTest runners are launched, and
> diagnostics defaults. These failures look like flaky infra ("driver won't start", "streaming
> failed", "device unreachable") but most are deterministic with a known fix.
> For the iOS 26 accessibility-tree defects (Xcode 26.1/26.2) see `ios-26-test-gotchas`.
> Researched 2026-10-02 from Apple release notes + Appium/WDA/Maestro issue trackers.

## Pin the environment first

```bash
xcodebuild -version            # 27.0 = 27A266a ; 27.1 / 27.2 are betas as of 2026-10
xcrun simctl list runtimes
sw_vers                        # Xcode 27 requires macOS Tahoe 26.6+, Apple silicon only
appium driver list --installed # xcuitest driver version matters (see §2, §3)
maestro --version
```

Change ONE of {Xcode, iOS runtime, driver version} at a time. iOS 27 devices/simulators also work
with **Xcode 26** (Appium tracker) — keeping an Xcode 26.5 runner separates "iOS 27 broke it" from
"Xcode 27 broke it".

---

## 1. Simulator.app is gone — replaced by Device Hub

**Symptom (Maestro Studio):** connects to simulator + driver, then preview shows **"Streaming failed"**;
log: `The application /Applications/Xcode.app/Contents/Developer/Applications/Simulator.app cannot be opened ... there is no such file.`
**Symptom (Appium):** simulator launch fails because Simulator.app is unavailable.

**Cause:** Xcode 27 ships `Contents/Applications/DeviceHub.app` (bundle id `com.apple.dt.Devices`)
instead of `Contents/Developer/Applications/Simulator.app`. Tools hard-coding the old path break.
Maestro CLI flow runs still work — only Studio's screen streaming breaks.

**Fix / workaround:**
- Appium: `appium:isHeadless: true` (simulator needs no GUI window) — or use Xcode 26.
- Maestro Studio: open issue as of 2026-09; a symlink restores the app partially but streaming stays unstable:
  ```bash
  sudo ln -s "/Applications/Xcode.app/Contents/Applications/DeviceHub.app" \
             "/Applications/Xcode.app/Contents/Developer/Applications/Simulator.app"
  ```
- Inspect elements with Appium Inspector or `maestro hierarchy` until Studio is fixed.

**Device Hub side-effects that bite UI tests** (Xcode 27 release notes):
- Parallel testing: simulators running tests may be **invisible in Device Hub** while still running (176809181).
- Mouse clicks in Device Hub synthesize a `direct` finger touch **plus** scroll/transform pointer events
  physical devices don't emit — **manual repro in Device Hub ≠ device behaviour** (48372360).
- iPad simulators on iOS 27.0: "Toggle Software Keyboard" menu item doesn't work (178432770).
- Xcode 27.2 beta: Device → Simulate Memory Warning broken; cloning a 27.2 simulator can fail on file
  permissions (188407822); a re-installed runtime can show unavailable → `killall -9 com.apple.CoreSimulator.CoreSimulatorService` (187950199).
- Xcode 27.1 beta: initial Simulator launch can take **several minutes** (187708500) — raise only the
  *first-boot* timeout in CI, not every step timeout.

## 2. WebDriverAgent won't build — deployment target

**Error:**
`The iOS deployment target 'IPHONEOS_DEPLOYMENT_TARGET' is set to 13.0, but the range of supported deployment target versions is 15.0 to 27.0.x (in target 'WebDriverAgentRunner')`
(maestro-runner variant: `Xcode 27.0 requires IPHONEOS_DEPLOYMENT_TARGET to be at least 15.0` — bundled WDA targets 12.0.)

**Fix:** upgrade to an Appium xcuitest driver / WDA that bumps the target to 15 (WebDriverAgent#1152,
appium-xcuitest-driver#2865). maestro-runner: open as of 2026-09-15 — workaround is editing the bundled
WDA's `IPHONEOS_DEPLOYMENT_TARGET` to 15.0.

**Device-matrix consequence:** Xcode 27 supports on-device debugging only for **iOS 17+** (Xcode 26: iOS 15+).
Devices on iOS 15/16 need an Xcode 26 runner.

## 3. Preinstalled WDA dies after ~20 s (real devices)

**Symptom:** with `appium:usePreinstalledWDA: true`, WDA launches, stays ~20 s, exits;
`Failed to start the preinstalled WebDriverAgent in 60000 ms ... the device might be locked`; port 8100
refuses. Seen on iOS 18 and iOS 26 devices right after upgrading the Mac to Xcode 27. Appium-managed
(non-preinstalled) WDA is unaffected.

**Fix:** appium-xcuitest-driver **≥ 12.13.1** (PR #2980 passes `ActivateSuspended: true`).

**Related, still open:** launching preinstalled WDA via `xcrun devicectl device process launch` on an
**iOS 26.7** device with the Xcode 27 DDI fails with
`XCTest Code=10300, Failed to background test runner within 30.0s` — works on iOS 27.0, so it's an
OS × DDI combination (appium-xcuitest-driver#2985). Repro on two iOS versions before calling it a WDA bug.

## 4. Failed Maestro driver session → 10-minute `simctl diagnose`

**Symptom:** `maestro.DeviceUnreachableException: Device became unreachable during viewHierarchy`, XCTest
log `Restarting after unexpected exit, crash, or test timeout`, then the Mac crawls and parallel runs time out.

**Cause:** since Xcode 26, `xcodebuild -collect-test-diagnostics` defaults to `on-failure`. Maestro
(2.10.0) doesn't pass the flag, so every failed driver session spawns a simulator sysdiagnose that can
run up to 10 minutes. Reproduced on Xcode 27.0 / iOS 27.0 / macOS 27.0 (Maestro#3633).

**Workaround (until Maestro passes `-collect-test-diagnostics never`):** in CI, watch for
`simctl diagnose` processes whose parent is `xcodebuild` and kill them — only for simulator UDIDs your
job owns. For your own `xcodebuild test` invocations pass `-collect-test-diagnostics never` explicitly.

## 5. Clipboard reads fail on iOS 27 simulators (Appium)

**Symptom:** `driver.get_clipboard()` unreliable on iOS 27 / 27.1 simulators (xcuitest driver 12.13.1);
WDA now needs the **"Paste from Other Apps"** permission. `mobile: getPasteboard` works, but simulator
pasteboards sync with the macOS clipboard, so **parallel simulators contaminate each other**
(`appium:simulatorPasteboardAutomaticSync: off` did not help the reporter). Open as of 2026-09-29.

**Do:** run clipboard tests serially (not sharded); assert the pasted value in the app UI instead of
reading the pasteboard back; mark the case environment-dependent in the report.

## 6. Keyboard dismisses/reappears during `send_keys` (iOS 27 real devices)

`/wda/keys` typing makes the keyboard collapse and reopen mid-input on iOS 27 real devices (not iOS 26).
WDA#1258 closed *not planned* — expect no WDA fix. If text arrives incomplete, type into the focused
element (`element.send_keys`) or set the value, then assert the final field value — don't add
retries around keystrokes.

## 7. iOS 27 hit-testing / accessibility-element changes — THIN evidence (single app repos)

Reported in individual app repos, not by Apple or tool maintainers. Treat as *hypotheses to check*,
not confirmed platform rules.

| Symptom on iOS 27 | Reported cause / fix | Source |
|---|---|---|
| Tap on the visible part of a button half-covered by the keyboard does nothing (iPhone) | Dismiss keyboard, wait for it to go, re-read the frame, then tap | StockPilot#199, MagicMobile#49 |
| Coordinate tap in a button's padding no longer hits it | Tap the label/element itself, not padded coordinates | MagicMobile#49 |
| Same SwiftUI card found several times by queries | Child views repeated the parent's label/id/actions — make the row one a11y element (`.accessibilityElement(children: .combine)`), app-side | MagicMobile#49 |
| Visible buttons `isHittable == false`, coordinate taps work | Transparent overlay/marker views overlap sibling leaves — app-side fix | paceprompt-ios#176 |
| Custom-scheme deep link shows **"Open in <App>?"** prompt, flow times out | Tap "Open" after `openLink` / `simctl openurl` | StockPilot#199 |
| idb taps fail: `SimulatorKit is required for HID interactions` | Xcode 27 removed SimulatorKit.framework — needs idb-companion ≥ 1.5 | StockPilot#199 |

Diagnose like iOS 26: same build passes on iOS 26.x, fails on iOS 27 → platform change. Route app-side
fixes to dev; don't paper over them with coordinate taps.

## 8. Useful Xcode 27 additions for testers

- Test Plan **app-crash severity during UI tests**: off / warning / failure (default) / fatal (168107814).
- `XCUIVoiceOverService`: drive VoiceOver from UI tests and assert focus + spoken output (175858549).
- Launch-test template with `runsForEachTargetApplicationUIConfiguration` covers orientation ×
  localization × appearance (168770106).
- `simctl reboot` / `devicectl` reboot of a simulator (172303413).
- XCTest assertion inside Swift Testing (or the reverse) now raises a warning runtime issue (170335449).
- Fixed in 27.0: Accessibility Inspector couldn't inspect simulator elements (179033881 — a 27-beta bug,
  NOT the Xcode 26.1/26.2 tree collapse). Known in 27.2 beta: VoiceOver / AX Inspector can't read an
  **iPhone Duo** in Device Hub (187148389).

## Post-upgrade checklist (Xcode 26 → 27)

- [ ] macOS Tahoe 26.6+ and Apple silicon on every CI runner
- [ ] Drop iOS 15/16 devices from the Xcode 27 matrix (or keep an Xcode 26 runner)
- [ ] Appium xcuitest driver ≥ 12.13.1; WDA deployment target 15
- [ ] Appium on simulators: `isHeadless: true` unless your driver handles Device Hub
- [ ] Maestro Studio streaming: expect failure — inspect via CLI / Appium Inspector
- [ ] `-collect-test-diagnostics never` on your own xcodebuild runs; watchdog for `simctl diagnose`
- [ ] Clipboard tests serial only; keyboard-entry tests assert the final value
- [ ] Control run: one known-good flow on iOS 26.x vs iOS 27, same build

## Anti-patterns

| Anti-pattern | Do instead |
|---|---|
| Retrying "Streaming failed" / WDA start timeouts | Deterministic (§1–§3) — fix the version |
| Raising every timeout because first boot is slow | Raise only the first-boot wait (27.1 known issue) |
| Repro'ing touch bugs by clicking in Device Hub | Device Hub injects pointer events devices don't — use a device or XCUITest |
| Coordinate-tap workaround for unhittable elements | App-side a11y fix; coordinates hide the defect |
| Sharding clipboard tests across simulators | Pasteboards sync via macOS — run serially |

## Related skills
`ios-26-test-gotchas`, `ios-xcrun`, `maestro-real-ios-device`, `maestro-studio`, `bug-repro-isolation`, `timeout-discipline`

## Sources
- https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes (read via the .json data endpoint) — macOS Tahoe 26.6+, on-device iOS 17+, Device Hub notes, testing features, AX Inspector fix, prebuilt dyld cache
- https://developer.apple.com/documentation/xcode-release-notes/xcode-27_1-release-notes — initial Simulator launch takes minutes
- https://developer.apple.com/documentation/xcode-release-notes/xcode-27_2-release-notes — clone permission bug, CoreSimulatorService workaround, memory-warning menu, iPhone Duo AX
- https://github.com/appium/appium/issues/22368 — Xcode 27 support tracker
- https://github.com/appium/appium-xcuitest-driver/issues/2978 + /pull/2980 — preinstalled WDA dies, fixed 12.13.1
- https://github.com/appium/appium-xcuitest-driver/issues/2985 — Code=10300 iOS 26.7 + Xcode 27 DDI
- https://github.com/appium/appium-xcuitest-driver/issues/2998 — get_clipboard on iOS 27 simulators
- https://github.com/appium/WebDriverAgent/issues/1258 — keyboard flicker on send_keys
- https://github.com/mobile-dev-inc/Maestro/issues/3606 — Simulator.app → DeviceHub.app, Studio streaming
- https://github.com/mobile-dev-inc/maestro-studio/issues/86 — Streaming Failed on macOS 27 beta
- https://github.com/mobile-dev-inc/Maestro/issues/3633 — collect-test-diagnostics / simctl diagnose
- https://github.com/devicelab-dev/maestro-runner/issues/170 — WDA deployment target with maestro-runner
- https://github.com/Branden574/StockPilot/pull/199, https://github.com/ineedsomesleep5/MagicMobile/pull/49, https://github.com/syamaner/paceprompt-ios/pull/176 — single-repo hit-testing / a11y observations
