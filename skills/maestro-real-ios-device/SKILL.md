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
  "maestro-runner hierarchy", "maestro-runner addMedia", "maestro-runner assertScreenshot".
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
