---
name: maestro-real-ios-device
description: |
  Run Maestro YAML flows on real (physical) iOS devices using the community
  maestro-runner tool (devicelab-dev). Use when testing on physical iPhones or iPads,
  not simulators; when parallel real-device runs are needed; or when BrowserStack / cloud
  device labs are unavailable. As of 2026 maestro-runner also covers Android/Web/React
  Native/Flutter/Expo as a single cross-platform runner — use this skill too when asked
  about maestro-runner on those platforms. Triggers on: "real iOS device maestro", "physical
  device maestro", "maestro iPhone", "maestro runner", "maestro-runner", "devicelab maestro",
  "maestro real device", "maestro-runner react native", "maestro-runner flutter",
  "maestro-runner hierarchy", "maestro-runner addMedia", "maestro-runner assertScreenshot",
  "maestro-runner dark mode", "maestro-runner lint", "maestro-runner setDarkMode",
  "maestro-runner retry-failed", "maestro-runner record", "maestro-runner assertVisible count",
  "maestro-runner dragAndDrop", "maestro-runner step-delay", "maestro-runner addMedia document",
  "maestro-runner regex case sensitive", "maestro-runner window-size", "maestro-runner npm".
---

# Maestro on Real iOS Devices (maestro-runner)

Maestro's official CLI does **not** support real iOS devices — only simulators and Android
emulators/devices. The community tool **maestro-runner** (by DeviceLab) fills that gap.

Existing YAML flows work as-is; no syntax changes required.

## Installation

```bash
# macOS — install maestro-runner via Homebrew
brew install devicelab-dev/tap/maestro-runner

# Or download binary from GitHub releases
# https://github.com/devicelab-dev/maestro-runner/releases
```

Requires:
- Xcode + Command Line Tools installed
- Device trusted and unlocked, connected via USB
- Device has a valid Developer provisioning profile (same as running Xcode tests)

## Running Tests on a Real iPhone/iPad

```bash
# List connected devices
maestro-runner devices

# Run a single flow on connected iOS device
maestro-runner test flow.yaml --device <UDID>

# Run entire flows/ folder
maestro-runner test flows/ --device <UDID>

# Run with env vars
maestro-runner test flow.yaml --device <UDID> --env USER_EMAIL=qa@example.com

# JUnit output for CI
maestro-runner test flows/ --device <UDID> --format junit --output results.xml
```

## Parallel Testing on Multiple Real Devices

```bash
# Run the same suite on two devices simultaneously
maestro-runner test flows/ \
  --device <UDID_1> \
  --device <UDID_2>
```

maestro-runner resolves the hardcoded single-port limitation in the original
`maestro-ios-device` tool, so two+ devices can run concurrently.

## How It Works (internals)

maestro-runner builds and installs an XCTest runner bundle on the physical device
and uses automatic port forwarding to relay commands — the same mechanism Xcode uses
for on-device testing. It is a single binary (no JVM), making startup ~3.6× faster
and memory use ~14× lower than the older `maestro-ios-device` wrapper.

## CI/CD — GitHub Actions with a Self-Hosted Mac Runner

Physical device testing requires a Mac machine with the device attached.
Use a self-hosted runner:

```yaml
# .github/workflows/ios-real-device.yml
name: iOS Real Device Tests

on: [pull_request]

jobs:
  maestro-real-device:
    runs-on: self-hosted   # must be a Mac with iPhone connected
    steps:
      - uses: actions/checkout@v4

      - name: Install maestro-runner
        run: brew install devicelab-dev/tap/maestro-runner

      - name: Run flows
        run: |
          UDID=$(maestro-runner devices --json | jq -r '.[0].udid')
          maestro-runner test flows/ \
            --device "$UDID" \
            --format junit \
            --output test-results.xml \
            --env APP_ID=${{ env.APP_BUNDLE_ID }}

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: maestro-results
          path: test-results.xml
```

## Comparison: Simulators vs Real Devices

| Factor | Simulator | Real device (maestro-runner) |
|---|---|---|
| Biometrics | Simulated only | Real Face ID / Touch ID |
| Network | Shared Mac network | Cell / real WiFi |
| Push notifications | Limited | Full (APNs) |
| Hardware sensors | Mocked | Actual gyro, camera, GPS |
| Setup | Zero (auto-boot) | USB + provisioning |
| Parallel on CI | Spin up N simulators | Need N physical devices |

## 2026: maestro-runner Has Outgrown "iOS-Only" (v1.1.15–1.1.19)

As of mid-2026, maestro-runner (v1.1.19, July 1) is a full cross-platform Maestro-compatible
runner — **"Fast UI test automation for Android, iOS, Web, React Native, Flutter & Expo"** —
not just an iOS real-device gap-filler. The caveat below about using `maestro-mobile` for
Android real devices still holds (standard Maestro + ADB works fine there), but maestro-runner
is now a legitimate single-binary alternative across *all* those platforms, with:

- **Dynamic work-queue parallelism** — devices pull from a shared queue rather than static
  sharding, so faster devices automatically pick up more tests (`maestro-runner test flows/ --device <UDID_1> --device <UDID_2> ...`
  scales this way with no per-device test-count balancing needed).
- **Configurable timeouts** at both levels: `--wait-for-idle-timeout 0` to disable device-idle
  waiting entirely, plus per-flow config (`commandTimeout: 10000`, `waitForIdleTimeout: 3000`)
  for flows with known-slow steps.
- **Smart element finding for React Native (testIDs) and Flutter (semantics)** — reduces the
  brittle-selector problem those frameworks are notorious for in Maestro/Appium alike; also
  recognizes RN container testIDs via a descendant-visibility fallback on iOS.
- **Web support** with Playwright-style actionability gates on `tapOn` (element must be enabled,
  not `pointer-events: none`, etc.) and auto-surfaced, color-coded browser console errors in
  flow reports.

## v1.1.20 → v1.1.22: New Commands (July–August 2026)

Three releases since the v1.1.19 baseline above added testing-relevant capability, not just bug fixes:

- **`hierarchy` subcommand (v1.1.22)** — dumps the current on-device view hierarchy as normalized JSON,
  the same tree Maestro itself uses for selector matching, across all drivers (real iOS, Android,
  Web, React Native, Flutter). Use it for selector discovery/debugging instead of guessing from a
  screenshot:
  ```bash
  maestro-runner hierarchy --device <UDID>              # full tree
  maestro-runner hierarchy --device <UDID> --compact     # flat listing
  maestro-runner hierarchy --device <UDID> --find "Add to Cart"   # filter by substring
  ```
- **`addMedia` on all platforms (v1.1.22)** — injects photos/videos into the device gallery for
  flows that test upload pickers; on **real iOS devices** this now works via PhotoKit, which stock
  Maestro/simulators cannot do (simulators can only seed media at boot, not mid-flow on hardware).
- **`swipe` distance parameter (v1.1.22)** — a centered, fixed-length gesture instead of the default
  edge-to-edge travel, for flows where a full-screen swipe overshoots the target.
- **`swipe: from: <selector>` with `duration:` (v1.1.20)** — selector-anchored swipes derive their
  start coordinates from an element's bounds and honor a `duration:` across all drivers (this is
  maestro-runner's own implementation; it predates and is separate from core Maestro's later
  element-relative-`point` swipe support already documented in `maestro-mobile`).
- **`assertScreenshot` (v1.1.21)** — maestro-runner ships its own visual-regression implementation
  (Go stdlib pixel diff, no new dependencies) producing highlighted `*__diff.png` images on failure,
  auto-creating a baseline on first run, and re-baselining via `--update-screenshots`. Same YAML
  shape as core Maestro's `assertScreenshot` (documented in `maestro-visual-testing`), but it's a
  separate reimplementation — diff output and thresholding behavior may not match core Maestro
  pixel-for-pixel, so don't assume baselines are interchangeable between the two.
- **Step-level `platform:` conditions (v1.1.21)** — restrict a single step to a platform; it's
  *skipped*, not failed, on other platforms — useful for cross-platform flows (Web/RN/Flutter) with
  one or two platform-specific steps instead of forking the whole flow file.
- **App crash reporting (v1.1.21)** — Android detects the app dying mid-flow and pulls the logcat
  crash cause when available, instead of the flow just timing out on the next step with no signal.

## v1.1.23: Dark Mode, `lint`, Latency Metrics (August 2026)

- **Dark mode control** — four new commands: `setDarkMode: dark` (or `light`, or `{enabled: true}`),
  `toggleDarkMode`, `assertDarkMode`, `assertLightMode`. Android drives this via `cmd uimode night`;
  iOS simulators via `simctl ui appearance`; **physical iOS devices and Web return an explicit error**
  instead of a silent no-op, since neither can be toggled programmatically.
- **`lint` subcommand** — parses flow files and reports YAML/syntax errors without a connected device
  or simulator:
  ```bash
  maestro-runner lint flows/
  ```
  Use it as a fast pre-commit/CI gate before the much slower device-backed `test` run.
- **`hierarchy --screenshot <path>`** — captures a screenshot from the same session that produced the
  view-hierarchy dump (the `hierarchy` subcommand itself shipped in v1.1.22, above), so the
  selector-discovery JSON and its visual reference come from one atomic capture instead of two calls
  that could race against a changing screen.
- **Per-step latency in `report.json`** — each flow's report now carries a `stepLatency` block with
  `p50`/`p95`/`max`/`mean` timings and the slowest command type, so you can profile which step is
  dragging out a flow instead of only seeing total duration.
- **`point:` on `swipe: from:`** — pick where inside a scrollable element the gesture starts:
  ```yaml
  - swipe:
      from: {id: editor-input, point: "20%, 50%"}
      direction: DOWN
      distance: 0.4
  ```

Notable fixes in this release: `point:` was previously silently ignored on `doubleTapOn`/`longPressOn`
(now honored); `distance:` was ignored on `swipe: from:` (now honored); taps could land on an
on-screen keyboard and still report success (an occlusion guard now checks after all input steps and
fails instead); DeviceLab swipes were inconsistent run-to-run because they shelled out to
`adb shell input swipe` — now routed through the on-device agent for consistent distance (re-record
any DeviceLab swipe-distance screenshot baselines, since this changes actual swipe distance).

## v1.1.24: `--retry-failed`, `--record`, `assertVisible: count:` (August 2026)

- **`--retry-failed`** — re-runs only the flows that failed in the previous run, reading the last
  report under the same `--output` directory (flattened or timestamped layout). A run that was cut
  short counts its unfinished flows as failed too, so nothing is silently dropped from the retry set.
  A clean previous run exits `0` without touching a device; if none of the previous failures are in
  the current flow selection, the run errors instead of silently running nothing:
  ```bash
  maestro-runner test --output ./reports flows/                 # 2 of 40 fail
  maestro-runner test --output ./reports --retry-failed flows/  # runs just those 2
  ```
- **`--record`** — saves a screen recording of every flow into its report assets, played inline in
  the HTML report. Android records on-device via `screenrecord` (3-minute clip cap per flow) and pulls
  the file to the host; iOS simulators record host-side via `simctl`. Physical iOS, Web, and Appium
  drivers aren't supported — the run warns once and continues without recording.
- **`assertVisible` with `count:`** — asserts a selector matches exactly N visible elements; fewer or
  more both fail, and the error reports the count actually observed. Runs through the same
  multi-match machinery `index:` selection already uses, so count semantics stay consistent across
  drivers. Supports `${VAR}`; rejects `count: 0` (use `assertNotVisible` instead) and cannot be
  combined with `index:`:
  ```yaml
  - assertVisible:
      css: .cart-item
      count: 3
  ```
- **Dark mode now covers Web and physical iOS** — `setDarkMode`/`toggleDarkMode`/`assertDarkMode`/
  `assertLightMode` (v1.1.23, above) now also work on the browser driver, emulated via CDP's
  `prefers-color-scheme` (heads-up: headless Chromium defaults to dark, so set an explicit mode before
  asserting), and on `--driver devicelab_ios` via `XCUIDevice.appearance` (iOS 15+), which works on
  real hardware and replaces the simulator-only `simctl` path from v1.1.23; the set is read back and
  the step fails if it didn't take effect.
- **App build number in reports** — reports now show the build behind the version (`versionCode` on
  Android, `CFBundleVersion` on iOS) alongside it, e.g. `v1.16.0 (10009107)`, in `report.json`, the
  HTML header/title, and Allure's environment.

Notable fixes: flow text reaching the device shell is now shell-quoted (an apostrophe in
`openBrowser: "https://example.com/s?q=it's"` was a device-side shell parse error, and `addMedia`
paths with spaces silently registered nothing — fixed across all six call sites on the Android
drivers); WDA `inputText` no longer rejects React Native fields whose accessibility tree merges the
`TextInput` into its parent container (the v1.1.23 focus gate required an active element, which React
Native never reports in this case — it now also accepts a visible keyboard as evidence, and falls
back to tap-and-type on a failed send-keys); iOS text-entry verification now polls for keystrokes to
commit instead of one-shot re-reading, which could previously report text that hadn't landed yet;
`startRecording` on real Android devices now detaches from the adb shell session so a backgrounded
`screenrecord` survives instead of dying with it; Web runs no longer misreport their driver as
`uiautomator2` in reports (now correctly `cdp`).

## v1.1.25: `dragAndDrop`, `--step-delay`, JUnit Failure Artifacts (August 2026)

- **`dragAndDrop`** — long-press an element (or point) and drag it to another, for reorder UIs.
  `from:`/`to:` each take a selector or a `point:`; `holdDuration` (ms, default 1000) is the press
  before movement, `duration` (ms, default 1000) the movement itself. Works on every driver
  (UIAutomator2, DeviceLab Android's `input draganddrop`, WDA, DeviceLab iOS, web CDP mouse
  sequence, Appium):
  ```yaml
  - dragAndDrop:
      from:
        id: "item-3"
      to:
        point: "50%, 20%"
      holdDuration: 800
  ```
  Heads-up for web: pages using native HTML5 `draggable` ignore synthetic mouse events by design —
  only mouse/touch/pointer-event drag implementations work.
- **`--step-delay <ms>`** — pace a pause between top-level steps, for demos and apps whose
  animations outrun the assertions. Also `MAESTRO_STEP_DELAY` env var, and per-flow `stepDelay:`.
- **JUnit `properties:` and failure artifacts** — a flow's `properties:` map now lands as
  `<property>` entries on its JUnit testcase, so flows can carry test-tracking IDs (e.g. `testID:
  Test-1234`) into CI. Failed testcases attach the failing step's screenshot and any `--record`
  video via the `[[ATTACHMENT|path]]` convention Jenkins-style tooling reads; a green run attaches
  only the video.
- **Negation globs in `config.yaml`** — a `flows:` pattern prefixed with `!` subtracts files an
  earlier pattern selected, so a workspace can take everything and carve out fixtures:
  `flows: ["**", "!fixtures/**"]`.
- **DeviceLab iOS now targets the app actually on screen** — a step with no `appId` used to
  activate the runner's own placeholder host app instead (XCUITest's public API can't address "the
  app in front"), blanking whatever was being tested. It now resolves the frontmost app through
  active-application PIDs and targets it directly, falling back to the host app only when that
  fails.

**Fix worth knowing about — `scrollUntilVisible` was accepting a sliver as "visible".** Every
driver previously stopped scrolling on any 1px viewport overlap, and the documented
`visibilityPercentage` option was parsed but never wired to anything. It's now a real check —
fully visible by default, honoring `visibilityPercentage` when set — so a flow that relied on a
tiny corner of an element counting as "found" may now scroll one step further than before; re-run
flows using `scrollUntilVisible` after upgrading. The same release also fixed four stacked causes
that made Flutter apps largely undrivable on the DeviceLab iOS driver (missing coordinate-tap
support, timeout leakage into XCUITest calls, scrolls releasing mid-motion); the driver went from
9/19 to 17/19 on the project's Flutter issue-repro suite, ahead of WDA-with-fallback at 14/19.

## v1.1.26: npm Distribution, Stricter Selectors — Breaking (September 2026)

> ⚠️ **Two selector behavior changes can make an existing flow start failing on upgrade — this is
> intentional, not a regression.** Both close a gap where the selector matched more loosely than
> what the flow actually asked for:
>
> - **Regex selectors are now case-sensitive.** Every regex was previously compiled with the
>   case-insensitive flag, so `^SIGN OUT$` matched both "Sign out" and "SIGN OUT" and page order
>   decided which got tapped. Plain (non-regex) text selectors are unaffected — still
>   case-insensitive. Add `(?i)` explicitly to opt back into insensitivity:
>   ```yaml
>   - tapOn: "^SIGN OUT$"          # now matches only the uppercase button
>   - tapOn: "(?i)^sign out$"      # opt back in
>   ```
> - **A selector naming both `id:` and `text:` must match one element carrying both.** Previously
>   the two were queried separately and whichever matched first won — so an author-intended AND
>   silently behaved as an OR, matching an element with the right id but unrelated text:
>   ```yaml
>   - assertVisible:
>       id: "cart-button"
>       text: "Checkout"          # now both must be true of the same element
>   ```
> Re-run any suite that relies on multi-field selectors or regex text matching after upgrading —
> a previously-passing flow may now correctly fail on a selector that was never as specific as it
> looked.

- **npm distribution** — `npx maestro-runner test flows/`, or `npm install --save-dev
  maestro-runner` to pin it in a React Native/Expo project's own `package.json`. No postinstall
  network fetch — the binary is an ordinary optional dependency npm resolves by `os`/`cpu` — so it
  installs offline, behind a proxy, or in CI that blocks postinstall network access.
- **`--window-size <WxH>`** (env `MAESTRO_WINDOW_SIZE`) — sets the web driver's browser viewport,
  so one suite can assert against phone/tablet/desktop breakpoints: `maestro-runner --platform web
  --window-size 390x844 test flows/`.
- **`--new-command-timeout <seconds>`** — raises `appium:newCommandTimeout` on the Appium session;
  matters for cloud `--parallel` runs where early-created sessions idle through serial
  pre-creation and get reaped at the server default, failing the first flow with `invalid session
  id`.
- Tap-then-validate ordering was inverted (a tap fired before the off-screen/occlusion guard
  checked it, so a rejected tap on DeviceLab Android had already hit — and often navigated via — a
  bottom tab bar underneath); taps are now validated against the resolved point *before* injection,
  and a covering window (keyboard, system/permission dialog) is now named in the failure instead of
  a bare geometry check.

## v1.1.27: Document Uploads, Password-Redaction Fix (September 2026)

> ⚠️ **If login flows started failing right after upgrading to 1.1.26, this is the fix.**
> `inputText` with a selector (e.g. `inputText: {text: "user@example.com", id: "email"}`) silently
> stopped matching its target field in 1.1.26 — the input value and the selector shared an
> internal field, so the text-to-type got reused as a text *predicate*, demanding a field whose
> hint equaled the typed value. Since that pattern usually lives in a shared login sub-flow, whole
> suites went red on their first step. Fixed in 1.1.27; no flow-file changes needed.

- **`addMedia` accepts documents** — PDF, Word, Excel, PowerPoint, plus txt/csv/rtf/json/zip,
  alongside the photos/videos it already handled, for exercising a document-upload picker:
  ```yaml
  - addMedia:
      - assets/contract.pdf
  - tapOn: "Attach a file"        # opens the system document picker
  - tapOn: "contract.pdf"
  ```
  Platform ceiling to know about: works on Android (seeds `Download/`, which the system document
  picker reads directly) and the iOS **simulator** ("On My iPhone" storage); a **physical iPhone
  refuses** — Apple exposes no path into Files storage from outside the app, and PhotoKit (used for
  photos/videos) doesn't cover documents.
- **Password values no longer leak into reports/logs.** A step inside a `runFlow` — where login
  sub-flows live — was described *after* variable expansion, so `inputText: ${PASSWORD}` appeared
  as the literal password in `flow-*.json`, `report.html`, the console, and the driver's request
  log. Steps are now described pre-expansion and the send-keys request body is redacted in the
  driver log too. **Worth an explicit check on any suite whose CI artifacts (HTML reports, JUnit
  attachments) are retained or shared** — a report generated before this fix may already contain a
  plaintext credential.
- Text selectors now match Android's `error` attribute (a Compose field whose only visible content
  is its validation-error text can now be matched by that text on UIAutomator2/Appium) — relevant
  to `form-validation-testing`.
- `speed:` on `scroll`/`scrollUntilVisible` is now honored on every driver (previously parsed and
  silently ignored, so flows always got a driver's hardcoded swipe duration regardless of what the
  YAML said).
- The `value:` spelling of `setAirplaneMode`/`setDarkMode` (Maestro's own map form, `{value:
  enabled, ...}`) was being silently read as *disabled* — a flow written against core Maestro's
  YAML and run under maestro-runner would flip the setting the wrong way with no error. Both
  spellings now work; an unrecognized value is a parse error instead of a silent wrong result.

## Key Caveats

- **Unofficial** — not affiliated with mobile.dev or the Maestro project.
- iOS provisioning profile must cover the test device UDID (free dev cert is fine for 1 device).
- The Maestro team has not committed a timeline for official real-device support.
- Android real devices already work with standard Maestro + ADB (`maestro-mobile`) too — but
  maestro-runner's own Android driver (UIAutomator2) also supports physical Android devices
  directly, so it's a valid single-tool choice for Android+iOS+Web mixed suites.

## Sources

- https://github.com/devicelab-dev/maestro-runner
- https://raw.githubusercontent.com/devicelab-dev/maestro-runner/main/CHANGELOG.md
- https://github.com/devicelab-dev/maestro-ios-device
- https://blog.devicelab.dev/went-in-to-support-maestro-for-physical-devices-came-out-with-even-more/
- https://news.ycombinator.com/item?id=46232126
