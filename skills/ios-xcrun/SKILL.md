---
name: ios-xcrun
description: |
  iOS simulator and device management via xcrun simctl. Use this skill when:
  managing iOS simulators (create, boot, shutdown, delete), installing/launching iOS apps,
  capturing screenshots or recording video from simulators, streaming logs, testing deep links,
  simulating push notifications, managing permissions, overriding status bar, setting up CI for
  iOS, or debugging iOS app behavior from the command line.

  Trigger on: "xcrun", "simctl", "iOS simulator", "boot simulator", "install iOS app",
  "iOS screenshot", "iOS logs", "simulator video", "iOS deep link test", "push notification test",
  "iOS CI setup", "simulator management", or any iOS device/simulator command-line task.
---

# iOS xcrun simctl

`xcrun simctl` is the command-line interface to iOS Simulator. It controls every aspect of
simulator lifecycle — from creation to teardown — and is essential for CI and scripted testing.

Always use `xcrun simctl` (not just `simctl`) so Xcode version resolution happens automatically.

## Quick Reference

```bash
# List everything
xcrun simctl list                          # all runtimes, devices, pairs
xcrun simctl list devices                  # just devices
xcrun simctl list devices available        # only available (not unavailable)
xcrun simctl list runtimes                 # installed iOS versions

# Target: use UDID or "booted" (any booted device)
xcrun simctl <command> booted <args>
xcrun simctl <command> <UDID> <args>
```

## Simulator Lifecycle

### Find & Boot

```bash
# Get UDID of a specific simulator
xcrun simctl list devices | grep "iPhone 15 Pro"
# → iPhone 15 Pro (ABCD-1234-...) (Shutdown)

# Boot by UDID
xcrun simctl boot ABCD-1234-...

# Boot by name (alternative, less reliable)
xcrun simctl boot "iPhone 15 Pro"

# Make the window visible
open -a Simulator          # Xcode ≤ 26 only
# Xcode 27: Simulator.app is replaced by DeviceHub.app (Contents/Applications/DeviceHub.app,
# bundle id com.apple.dt.Devices) — `open -a Simulator` fails. See `ios-27-test-gotchas` §1.
# simctl itself still works headless; you don't need the window for CI.

# Wait until booted (for CI scripts)
xcrun simctl bootstatus ABCD-1234-... -b
```

### Shutdown & Cleanup

```bash
xcrun simctl shutdown booted          # shutdown active device
xcrun simctl shutdown all             # shutdown all devices
xcrun simctl erase booted             # wipe to factory (keeps simulator)
xcrun simctl erase all                # wipe all simulators

# Delete unavailable simulators (safe cleanup)
xcrun simctl delete unavailable
```

### Create & Delete

```bash
# Create simulator (name, device type, runtime)
xcrun simctl create "My Test iPhone" "iPhone 15 Pro" "iOS-17-4"

# List device types (for create command)
xcrun simctl list devicetypes

# List runtimes (for create command)
xcrun simctl list runtimes

# Delete specific simulator
xcrun simctl delete ABCD-1234-...
```

## App Management

```bash
# Install .app bundle
xcrun simctl install booted /path/to/MyApp.app

# Launch app (returns PID)
xcrun simctl launch booted com.example.myapp

# Launch with env vars (useful for feature flags) — prefix with SIMCTL_CHILD_; simctl strips the
# prefix and passes FEATURE_FLAG=true to the app. (Anything after the bundle id is argv, NOT env.)
# UNVERIFIED this session (from memory of `xcrun simctl help launch`) — confirm locally.
SIMCTL_CHILD_FEATURE_FLAG=true xcrun simctl launch booted com.example.myapp

# Launch and capture stdout/stderr
xcrun simctl launch --console booted com.example.myapp

# Terminate (graceful)
xcrun simctl terminate booted com.example.myapp

# Uninstall
xcrun simctl uninstall booted com.example.myapp

# Check if installed
xcrun simctl listapps booted | grep "com.example"
```

## Screenshots & Video

```bash
# Screenshot (PNG, TIFF, BMP, GIF, JPEG supported)
xcrun simctl io booted screenshot screenshot.png
xcrun simctl io booted screenshot --type=jpeg screenshot.jpg

# Video recording (starts immediately, Ctrl+C to stop)
xcrun simctl io booted recordVideo recording.mp4

# Record with specific codec
xcrun simctl io booted recordVideo --codec=h264 recording.mp4

# Record to specific format
xcrun simctl io booted recordVideo --type=mp4 recording.mp4

# Non-interactive recording (for CI — kill process to stop)
xcrun simctl io booted recordVideo recording.mp4 &
RECORD_PID=$!
# ... run tests ...
kill $RECORD_PID
```

## Logs

```bash
# Stream all logs (verbose)
xcrun simctl spawn booted log stream

# Filter by subsystem (your app's bundle ID prefix)
xcrun simctl spawn booted log stream \
  --predicate 'subsystem == "com.example.myapp"'

# Filter by category
xcrun simctl spawn booted log stream \
  --predicate 'subsystem CONTAINS "example" AND category == "network"'

# Filter by log level
xcrun simctl spawn booted log stream \
  --level debug \
  --predicate 'subsystem == "com.example.myapp"'

# Collect logs for a time range (after the fact)
xcrun simctl spawn booted log collect \
  --start "2025-01-01 00:00:00" \
  --output app-logs.logarchive

# Show crash logs
xcrun simctl spawn booted log show \
  --predicate 'eventType == "crash"' \
  --last 1h

# Get app container path (useful for reading files the app wrote)
xcrun simctl get_app_container booted com.example.myapp
```

## Deep Links & URLs

```bash
# Open URL / deep link
xcrun simctl openurl booted "https://example.com"
xcrun simctl openurl booted "myapp://product/123"

# Test universal links (requires app installed)
xcrun simctl openurl booted "https://example.com/products/123"
```

## Push Notifications

```bash
# Send push notification (simulator only)
# Create payload.json first:
cat > /tmp/push.json << 'EOF'
{
  "aps": {
    "alert": {
      "title": "Test Notification",
      "body": "This is a test push"
    },
    "badge": 1,
    "sound": "default"
  },
  "custom_data": "value"
}
EOF

xcrun simctl push booted com.example.myapp /tmp/push.json

# Or pipe directly
echo '{"aps":{"alert":"Hello"}}' | xcrun simctl push booted com.example.myapp -
```

## Status Bar Overrides (for consistent screenshots)

```bash
# Perfect status bar for screenshots/demos
xcrun simctl status_bar booted override \
  --time "9:41" \
  --batteryState charged \
  --batteryLevel 100 \
  --wifiBars 3 \
  --cellularBars 4 \
  --cellularMode active

# Clear overrides
xcrun simctl status_bar booted clear
```

## Permissions

```bash
# Grant permission
xcrun simctl privacy booted grant camera com.example.myapp
xcrun simctl privacy booted grant photos com.example.myapp
xcrun simctl privacy booted grant location-always com.example.myapp
xcrun simctl privacy booted grant microphone com.example.myapp
xcrun simctl privacy booted grant contacts com.example.myapp

# Revoke permission
xcrun simctl privacy booted revoke camera com.example.myapp

# Reset all permissions for app (forces re-prompt)
xcrun simctl privacy booted reset all com.example.myapp

# Service names CHANGE between Xcode versions — always check the real list first:
xcrun simctl help privacy
# Known-valid on Xcode 27 (third-party PR conorluddy/ios-simulator-skill#99): all, contacts-limited,
#   location-always, photos-add, media-library (NOT `medialibrary`/`mediaLibrary`); `health`/`keyboard` rejected.
# UNVERIFIED — may be rejected: camera, notifications, location-when-in-use, faceid, speech, usertracking.
# A rejected service fails with NSPOSIXErrorDomain code=1 — don't swallow it.
```

## Media & Files

```bash
# Add photo to Photos library
xcrun simctl addmedia booted /path/to/photo.jpg

# Add multiple photos
xcrun simctl addmedia booted photo1.jpg photo2.png video.mp4

# Get app's data container path
xcrun simctl get_app_container booted com.example.myapp data
# → /Users/.../CoreSimulator/Devices/UDID/data/Containers/Data/...

# Read a file from app's container
APP_DATA=$(xcrun simctl get_app_container booted com.example.myapp data)
cat "$APP_DATA/Documents/myfile.json"
```

## Environment & Keychain

```bash
# Get environment variable from running app
xcrun simctl getenv booted HOME

# Add SSL certificate (for MITM proxies in testing)
xcrun simctl keychain booted add-root-cert /path/to/cert.pem

# Reset keychain
xcrun simctl keychain booted reset
```

## CI/CD Patterns

### GitHub Actions (iOS)

```yaml
# .github/workflows/ios-tests.yml
jobs:
  test:
    runs-on: macos-14      # Always specify macOS version for Xcode stability
    steps:
      - uses: actions/checkout@v4

      - name: Select Xcode
        run: sudo xcode-select -s /Applications/Xcode_15.4.app

      - name: Create & Boot Simulator
        run: |
          UDID=$(xcrun simctl create "CI-iPhone" "iPhone 15 Pro" "iOS-17-4")
          xcrun simctl boot $UDID
          xcrun simctl bootstatus $UDID -b
          echo "SIMULATOR_UDID=$UDID" >> $GITHUB_ENV

      - name: Install App
        run: xcrun simctl install $SIMULATOR_UDID DerivedData/Build/Products/Debug-iphonesimulator/MyApp.app

      - name: Run Tests
        run: xcodebuild test -scheme MyApp -destination "id=$SIMULATOR_UDID"

      - name: Capture Screenshot on Failure
        if: failure()
        run: xcrun simctl io $SIMULATOR_UDID screenshot failure-screenshot.png

      - name: Upload Screenshot
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: failure-screenshots
          path: failure-screenshot.png
```

### Parallel Simulators

```bash
# Create multiple simulators for parallel test runs
for i in 1 2 3 4; do
  xcrun simctl create "CI-iPhone-$i" "iPhone 15" "iOS-17-4" &
done
wait

# List their UDIDs
xcrun simctl list devices | grep "CI-iPhone"
```

## Physical Devices — `xcrun devicectl` (Xcode 15+)

For real iPhones/iPads, `simctl` does NOT work — use `devicectl`:

```bash
# List paired devices
xcrun devicectl list devices

# Install on real device by UDID
xcrun devicectl device install app --device <UDID> /path/to/MyApp.app

# Launch on real device
xcrun devicectl device process launch --device <UDID> com.example.myapp

# Take screenshot from real device — subcommand is `device capture screenshot` (Xcode 26.6+/27 per a
# third-party reference; exact flags UNVERIFIED — check `xcrun devicectl device capture --help`)
xcrun devicectl device capture screenshot --device <UDID> ...

# Stream logs (real device) — `devicectl device log stream` is UNVERIFIED and likely does NOT exist
# (reports say log streaming was missing/renamed in Xcode 26). Check `xcrun devicectl help` before scripting it.

# Pair a device for the first time (after enabling Developer Mode on iOS 16+)
xcrun devicectl manage pair --device <UDID>
```

Real devices need:
- Developer Mode enabled (Settings → Privacy & Security → Developer Mode)
- App signed with a profile that includes the device's UDID

## Network Conditioner (Throttle Real Network for Tests)

```bash
# Install Network Link Conditioner (one-time, on macOS host; ships in "Additional Tools for Xcode" — path UNVERIFIED)
open /Applications/Xcode.app/Contents/Applications/Network\ Link\ Conditioner.prefPane
```

Toggle profiles (3G, Edge, …) from the System Settings pane. There is **no `nlc` CLI** — don't script
`sudo nlc start/stop`. For deterministic slow-network tests prefer a mock server delay
(`maestro-network-mocking`, WireMock `fixedDelayMilliseconds`).

Simulators inherit host network conditions.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Unable to boot device in current state: Booted` | Already running | Skip boot, use `booted` |
| `No devices are booted` | Nothing running | `xcrun simctl boot <UDID>` |
| `Device not eligible for install` | Wrong runtime/arch | Check app's supported archs match simulator |
| App installs but won't launch | Missing Info.plist key or entitlement | Check Xcode build settings for simulator |
| `recordVideo` produces corrupt file | Process killed too fast | Add `sleep 1` before killing recording PID |
| Simulator extremely slow in CI | Full animation speed | Add `defaults write com.apple.iphonesimulator SlowMotionAnimation NO` |
| `simctl list` shows `(unavailable)` | Runtime not installed | Download via Xcode → Settings → Platforms |

## Script: Cấp Quyền Tự Động Trước Khi Maestro Chạy

Chạy script này **trước** `maestro test` để grant toàn bộ permissions, tránh dialog bất ngờ
làm vỡ flow. Script idempotent — chạy nhiều lần không gây lỗi.

```bash
#!/bin/bash
# scripts/ios-grant-permissions.sh
# Usage: ./ios-grant-permissions.sh com.example.myapp [UDID]
# UDID optional — mặc định dùng "booted"
set -e

BUNDLE_ID="${1:?Usage: $0 <bundle-id> [simulator-udid]}"
TARGET="${2:-booted}"

echo "▶ Granting permissions for $BUNDLE_ID on simulator: $TARGET"

grant() {
  local service=$1
  xcrun simctl privacy "$TARGET" grant "$service" "$BUNDLE_ID" 2>/dev/null \
    && echo "  ✓ $service" \
    || echo "  ⚠ $service (skipped — app not installed yet or service unavailable)"
}

# Core permissions cần cho testing — tên service PHẢI khớp `xcrun simctl help privacy` của Xcode đang dùng.
# Các tên dưới: location-always / media-library đã xác nhận trên Xcode 27 (PR #99 bên thứ 3);
# những tên còn lại UNVERIFIED → script in ⚠ nếu bị từ chối, không giả ✓.
grant location-always        # GPS / location services
grant photos
grant microphone
grant contacts
grant calendar
grant reminders
grant motion                 # accelerometer / motion data
grant media-library          # Apple Music library (KHÔNG phải `medialibrary`)
# notifications / camera / speech: simctl privacy có thể không hỗ trợ — UNVERIFIED; với Maestro dùng
# `launchApp: permissions:` thay thế.

echo ""
echo "▶ Xong. Dòng nào ⚠ = service đó KHÔNG được grant — xử lý trước khi tin flow không gặp permission dialog."
echo ""
echo "Lưu ý: Nếu app chưa install thì một số permissions sẽ được grant sau khi install."
echo "Chạy lại script này sau khi install nếu cần."
```

### Tích hợp vào CI workflow

```bash
# Thứ tự đúng trong CI script:
# 1. Boot simulator
UDID=$(xcrun simctl create "CI-iPhone" "iPhone 15 Pro" "iOS-17-4")
xcrun simctl boot $UDID
xcrun simctl bootstatus $UDID -b

# 2. Install app
xcrun simctl install $UDID build/MyApp.app

# 3. Grant permissions (PHẢI sau khi install)
./scripts/ios-grant-permissions.sh com.example.myapp $UDID

# 4. Chạy Maestro tests
maestro test --env APP_ID=com.example.myapp flows/
```

### Grant từng permission thủ công

```bash
# Location (2 loại — grant cả hai để chắc)
xcrun simctl privacy booted grant location-always com.example.myapp
xcrun simctl privacy booted grant location-when-in-use com.example.myapp

# Notifications — quan trọng cho test push notification flow
xcrun simctl privacy booted grant notifications com.example.myapp

# Reset permissions để test lại flow request permission từ đầu
xcrun simctl privacy booted reset all com.example.myapp
```

---

## Script: Chuẩn Bị Simulator (Create + Boot + Permissions)

```bash
#!/bin/bash
# scripts/prepare-ios-sim.sh
# Usage: ./prepare-ios-sim.sh
# Tạo fresh simulator, boot, grant permissions, install app
set -e

DEVICE_NAME="${CI_JOB_ID:-Test-iPhone}"    # unique name trên CI
DEVICE_TYPE="iPhone 15 Pro"
RUNTIME="iOS-17-4"
BUNDLE_ID="${BUNDLE_ID:-com.example.myapp}"
APP_PATH="${APP_PATH:-build/MyApp.app}"

echo "▶ Cleaning up old test simulators..."
xcrun simctl delete "$DEVICE_NAME" 2>/dev/null || true

echo "▶ Creating simulator: $DEVICE_NAME ($DEVICE_TYPE, $RUNTIME)"
UDID=$(xcrun simctl create "$DEVICE_NAME" "$DEVICE_TYPE" "$RUNTIME")
echo "  UDID: $UDID"

echo "▶ Booting..."
xcrun simctl boot $UDID
xcrun simctl bootstatus $UDID -b

echo "▶ Configuring status bar (for consistent screenshots)..."
xcrun simctl status_bar $UDID override \
  --time "9:41" --batteryState charged --batteryLevel 100 \
  --wifiBars 3 --cellularBars 4

echo "▶ Disabling slow animations..."
defaults write com.apple.iphonesimulator SlowMotionAnimation -bool NO 2>/dev/null || true

echo "▶ Installing app: $APP_PATH"
xcrun simctl install $UDID "$APP_PATH"

echo "▶ Granting permissions..."
# Run `xcrun simctl help privacy` for the valid names on YOUR Xcode. Report failures honestly —
# printing ✓ unconditionally hides rejected services (fail-loud).
for service in location-always photos microphone contacts; do
  if xcrun simctl privacy $UDID grant $service $BUNDLE_ID; then
    echo "  ✓ $service"
  else
    echo "  ✗ $service REJECTED (invalid name on this Xcode, or app not installed)" >&2
  fi
done

echo ""
echo "✅ Simulator ready: $UDID"
echo $UDID > /tmp/test-simulator-udid
export SIMULATOR_UDID=$UDID
```

---

## Script: Cleanup Sau Khi Test Kết Thúc

Cleanup đảm bảo CI worker không bị nghẽn simulator/process từ job trước.
Chạy trong `finally` hoặc `after_script` của CI.

```bash
#!/bin/bash
# scripts/ios-cleanup.sh
# Usage: ./ios-cleanup.sh [UDID]
# Nếu không có UDID, đọc từ /tmp/test-simulator-udid
set -e

UDID="${1:-$(cat /tmp/test-simulator-udid 2>/dev/null)}"

if [ -z "$UDID" ]; then
  echo "⚠ Không tìm thấy UDID. Cleanup tất cả booted simulators..."
  xcrun simctl shutdown all 2>/dev/null || true
  echo "✅ Shutdown all simulators"
  exit 0
fi

echo "▶ Cleanup simulator: $UDID"

# 1. Terminate app (graceful)
BUNDLE_ID="${BUNDLE_ID:-}"
if [ -n "$BUNDLE_ID" ]; then
  echo "  Terminating $BUNDLE_ID..."
  xcrun simctl terminate $UDID $BUNDLE_ID 2>/dev/null || true
fi

# 2. Collect logs trước khi shutdown (artifact CI)
LOG_DIR="${CI_ARTIFACTS_DIR:-./test-artifacts}/ios-logs"
mkdir -p "$LOG_DIR"
xcrun simctl spawn $UDID log collect \
  --output "$LOG_DIR/simulator-$UDID.logarchive" 2>/dev/null || true
echo "  Logs saved to $LOG_DIR"

# 3. Shutdown simulator
echo "  Shutting down..."
xcrun simctl shutdown $UDID 2>/dev/null || true

# 4. Xóa simulator (giải phóng disk — chỉ làm trên CI, không làm local)
if [ "${CI:-}" = "true" ]; then
  echo "  Deleting simulator (CI mode)..."
  xcrun simctl delete $UDID 2>/dev/null || true
  echo "  Deleted: $UDID"
fi

# 5. Cleanup temp files
rm -f /tmp/test-simulator-udid
rm -f /tmp/maestro-*.pid 2>/dev/null || true

# 6. Kill orphan Simulator processes nếu còn
if [ "${CI:-}" = "true" ]; then
  pkill -f "Simulator" 2>/dev/null || true
fi

echo "✅ iOS cleanup hoàn tất"
```

### Tích hợp vào GitHub Actions

```yaml
# .github/workflows/ios-maestro.yml
jobs:
  test:
    runs-on: macos-14
    steps:
      - uses: actions/checkout@v4

      - name: Prepare Simulator
        run: |
          export BUNDLE_ID="com.example.myapp"
          export APP_PATH="build/MyApp.app"
          ./scripts/prepare-ios-sim.sh
          # UDID được lưu vào /tmp/test-simulator-udid

      - name: Run Maestro
        run: |
          export SIM_UDID=$(cat /tmp/test-simulator-udid)
          maestro test --retry-on-failure 2 flows/

      - name: Cleanup (always runs)
        if: always()                    # chạy dù test pass hay fail
        run: |
          export BUNDLE_ID="com.example.myapp"
          ./scripts/ios-cleanup.sh

      - name: Upload Test Artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ios-test-artifacts
          path: test-artifacts/
```

---

## Toolchain-version gate

Running on **iOS 26 with Xcode 26.x**? Read `ios-26-test-gotchas` before debugging any
element-not-found failure. Xcode 26.1/26.2 break the accessibility tree on iOS 26+ (`No matches
found for Descendants matching type TabBar`), nav-bar `UIBarButtonItem` accessibility IDs stop
being exposed, and Accessibility Inspector renders an empty hierarchy. None of these are fixable
by rewriting selectors — pin the environment first:

```bash
xcodebuild -version && sw_vers && xcrun simctl list runtimes
```

Simulator won't boot after a macOS upgrade:

```bash
xcrun simctl runtime dyld_shared_cache update --all
```
