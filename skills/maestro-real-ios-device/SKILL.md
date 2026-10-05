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
  "maestro real device", "maestro-runner react native", "maestro-runner flutter".
---

# Maestro on Real iOS Devices (maestro-runner)

Maestro's official CLI does **not** support real iOS devices — only simulators and Android
emulators/devices. The community tool **maestro-runner** (by DeviceLab) fills that gap.

Existing YAML flows *mostly* work as-is — but see the **v1.1.28 breaking changes** below
(whole-value selector matching, `-e` parsing) before assuming an old flow is compatible.

> **Official CLI 2.11.0+ (29 Sep 2026):** `maestro` no longer lists physical iPhones in its device
> list, and `maestro test` against one fails immediately with *"Physical iOS devices are not yet
> supported"*. If you see that error, it's not a provisioning/USB problem — switch to maestro-runner.
> Before 2.11.0 the phone could appear as a target and then hang or fail obscurely mid-run.

## Installation

```bash
curl -fsSL https://open.devicelab.dev/install/maestro-runner | bash   # macOS/Linux
npx maestro-runner test flows/                                         # or via npm (1.1.26+)
maestro-runner doctor      # checks Xcode, team ID vs keychain certs
maestro-runner devices     # lists connected iPhones (not-ready ones show the reason)
```

> The older `brew install devicelab-dev/tap/maestro-runner` is not mentioned in the README or any
> 1.1.20–1.1.28 release note — unverified; prefer the curl/npm installs above.

Requires:
- Xcode + Command Line Tools, iOS 15+ on the device
- Device unlocked, trusted, **Developer Mode** on, connected via USB
- An Apple **team ID** passed as `--team-id` — on first run the agent is re-signed for your team and
  cached in `~/.maestro-runner/cache/devicelab-ios-agent/device-signed/`

## Running Tests on a Real iPhone/iPad

Global flags go **before** the subcommand (README form):

```bash
# Default driver (1.1.28+) = DeviceLab
maestro-runner --platform ios --driver devicelab --team-id <TEAM_ID> \
  --device <UDID> --app-file MyApp.app test flows/

# Fallback to the pre-1.1.28 WebDriverAgent driver
maestro-runner --platform ios --driver wda --team-id <TEAM_ID> --device <UDID> test flows/

# Env vars: ONE variable per -e (1.1.28); bare `-e NAME` reads it from the shell
maestro-runner test -e USER_EMAIL=qa@example.com -e API_TOKEN flows/

# Useful run flags (1.1.24–1.1.25)
maestro-runner test --retry-failed --video on-failure flows/
```

## ⚠️ v1.1.28 Breaking Changes (1 Oct 2026)

- **Default driver = DeviceLab** on Android and iOS (simulator + real device). Pin `--driver wda`
  / `--driver uiautomator2` to keep pre-1.1.28 behaviour; old DeviceLab iOS = `--driver devicelab-legacy`.
- **Text/id selectors match the WHOLE value** (case-insensitive). Substring matching needs a regex:
  `tapOn: ".*Open.*"`, `id: ".*login.*"`. (WDA driver keeps old matching.) Regexes are
  case-insensitive again (1.1.26 had made them case-sensitive).
- **`index:` beyond the match count → no element** (used to silently fall back to the first match).
- **`-e A=1,B=2` is ONE variable** (`A` = `1,B=2`); use separate `-e` flags.
- **Element swipes travel further** — centre → 10%/90% of the screen.
- **Real-iPhone DeviceLab limits:** no `clearKeychain`, `setPermissions`, `setLocation`, `addMedia`,
  clipboard, or screen recording.
- New: `${DEVICE_UDID}` in every flow; `wait: <ms>` step (**runner-only — a flow using it fails on
  official Maestro**); `require()` in `runScript` (CommonJS); `--app-file` accepts an http(s) URL
  (+ `--app-file-sha256`); `--disable-animations`.

### Earlier 1.1.2x additions worth knowing
- 1.1.26: `id:` + `text:` in one selector must match ONE element having both; Windows CRLF flows parse.
- 1.1.25: `doctor`, `devices --json`, `lint --json`, `runShell` step, `dragAndDrop`, `--video`,
  `--step-delay`; `scrollUntilVisible` now waits for the element to be FULLY visible.
- 1.1.24: `--retry-failed`, `--record`, `assertVisible: count:`; dark mode on physical iPhones.
- 1.1.23: `lint`, `hierarchy --screenshot`, `point:` on `swipe: from:`. Tapping an element covered
  by the keyboard now FAILS — add `hideKeyboard`.
- 1.1.21: `assertScreenshot` + `--update-screenshots`, step-level `platform:` condition.

## Parallel Testing on Multiple Real Devices

```bash
# README-documented form
maestro-runner test --parallel 2 flows/
```

> Repeating `--device <UDID_1> --device <UDID_2>` appeared in older write-ups; the current README
> documents `--parallel N` instead — unverified whether repeated `--device` still works.

maestro-runner resolves the hardcoded single-port limitation in the original
`maestro-ios-device` tool, so two+ devices can run concurrently.

## How It Works (internals)

With the DeviceLab driver (default since 1.1.28), maestro-runner ships a **prebuilt** iOS agent,
re-signs it for your `--team-id` on first run, caches it, and talks to it over usbmux. The WDA
driver instead builds/installs a WebDriverAgent XCTest bundle like Xcode does. It is a single binary (no JVM), making startup ~3.6× faster
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
          UDID=$(maestro-runner devices --json | jq -r '.[0].udid')   # JSON shape unverified — check once
          maestro-runner --platform ios --team-id "${{ secrets.APPLE_TEAM_ID }}" \
            --device "$UDID" test \
            -e APP_ID=${{ env.APP_BUNDLE_ID }} \
            --output test-results \
            flows/

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: maestro-results
          path: test-results/
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

## Key Caveats

- **Unofficial** — not affiliated with mobile.dev or the Maestro project.
- iOS provisioning profile must cover the test device UDID (free dev cert is fine for 1 device).
- The Maestro team has not committed a timeline for official real-device support.
- Android real devices already work with standard Maestro + ADB (`maestro-mobile`) too — but
  maestro-runner's own Android driver (UIAutomator2) also supports physical Android devices
  directly, so it's a valid single-tool choice for Android+iOS+Web mixed suites.

## Sources

- https://github.com/devicelab-dev/maestro-runner
- https://api.github.com/repos/devicelab-dev/maestro-runner/releases (v1.1.20–v1.1.28 notes, read 2026-10-02)
- https://raw.githubusercontent.com/devicelab-dev/maestro-runner/main/README.md
- https://raw.githubusercontent.com/devicelab-dev/maestro-runner/main/CHANGELOG.md
- https://github.com/devicelab-dev/maestro-ios-device
- https://blog.devicelab.dev/went-in-to-support-maestro-for-physical-devices-came-out-with-even-more/
- https://news.ycombinator.com/item?id=46232126
