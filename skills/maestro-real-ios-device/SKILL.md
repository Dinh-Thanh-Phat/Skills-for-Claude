---
name: maestro-real-ios-device
description: |
  Run Maestro YAML flows on real (physical) iOS devices using the community
  maestro-runner tool (devicelab-dev). Use when testing on physical iPhones or iPads,
  not simulators; when parallel real-device runs are needed; or when BrowserStack / cloud
  device labs are unavailable. Triggers on: "real iOS device maestro", "physical device
  maestro", "maestro iPhone", "maestro runner", "maestro-runner", "devicelab maestro",
  "maestro real device".
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

## Key Caveats

- **Unofficial** — not affiliated with mobile.dev or the Maestro project.
- iOS provisioning profile must cover the test device UDID (free dev cert is fine for 1 device).
- The Maestro team has not committed a timeline for official real-device support.
- Android real devices already work with standard Maestro + ADB — use `maestro-mobile` for that.

## Sources

- https://github.com/devicelab-dev/maestro-runner
- https://github.com/devicelab-dev/maestro-ios-device
- https://blog.devicelab.dev/went-in-to-support-maestro-for-physical-devices-came-out-with-even-more/
- https://news.ycombinator.com/item?id=46232126
