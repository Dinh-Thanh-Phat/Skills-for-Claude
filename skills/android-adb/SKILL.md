---
name: android-adb
description: |
  Android device and emulator management via adb (Android Debug Bridge). Use this skill when:
  managing Android emulators/physical devices, installing/uninstalling APKs, capturing logcat for
  debugging, taking screenshots or recording screen, simulating input (taps, swipes, text),
  managing app permissions, port forwarding for debugging, running shell commands on device,
  setting up Android CI/CD, clearing app data, or troubleshooting Android test environments.

  Trigger on: "adb", "Android emulator", "install APK", "adb logcat", "adb shell", "avd",
  "Android device", "adb devices", "screencap", "screenrecord", "am start", "pm clear",
  "adb forward", "Android CI", "adb install", or any Android command-line device management task.
---

# Android adb (Android Debug Bridge)

ADB is the primary tool for interacting with Android devices and emulators from the command line.
It bridges your machine to Android's Linux-based shell, enabling app management, debugging,
input simulation, and full device control.

## Setup & Connection

```bash
# Verify adb is available
adb version
# Platform-tools latest: 37.0.1 (July 2026). AVOID 36.0.1 — it truncated the last character of
# files pushed/pulled on Windows (fixed in 36.0.2). Source: developer.android.com/tools/releases/platform-tools

# List connected devices/emulators
adb devices
adb devices -l    # with details (model, product, transport)

# Target a specific device when multiple are connected
adb -s emulator-5554 install app.apk
adb -s R3CNT06XXXX shell

# Wireless debugging (Android 11+)
adb pair <ip>:<port>        # pair first
adb connect <ip>:<port>     # then connect
adb disconnect <ip>:<port>  # disconnect

# Wait for device (useful in CI before running commands)
adb wait-for-device
```

## Emulator Management

```bash
# List available AVDs (Android Virtual Devices)
emulator -list-avds

# Start emulator (headless for CI)
emulator -avd Pixel_6_API_33 -no-window -no-audio -no-boot-anim &

# Wait for emulator to fully boot
# (wait-for-device returns when adbd is up, NOT when Android finished booting — poll the prop on the host)
adb wait-for-device
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do sleep 2; done

# Get emulator serial (when multiple)
adb devices | grep emulator | awk '{print $1}'

# Kill emulator
adb emu kill
# Or:
adb -s emulator-5554 emu kill

# Snapshot (save/restore state — critical for CI speed)
adb emu avd snapshot save clean-state
adb emu avd snapshot load clean-state
```

## App Management

```bash
# Install APK
adb install app.apk
adb install -r app.apk              # replace/reinstall (keeps data)
adb install -t app.apk              # allow test APK
adb install -d app.apk              # allow version downgrade
adb install --instant app.apk       # install as Instant App

# Install to specific location — legacy; `-s` (SD card) behaviour on current adb is UNVERIFIED, avoid
# adb install -s app.apk

# Uninstall
adb uninstall com.example.app
adb uninstall -k com.example.app    # keep data & cache

# Check if installed
adb shell pm list packages | grep com.example

# Get APK path on device
adb shell pm path com.example.app

# Pull APK from device
adb pull $(adb shell pm path com.example.app | cut -d: -f2) ./extracted.apk
```

## App Control (Activity Manager)

```bash
# Launch app (main activity)
adb shell am start -n com.example.app/.MainActivity

# Launch with action & data (deep link)
adb shell am start \
  -a android.intent.action.VIEW \
  -d "myapp://product/123" \
  com.example.app

# Launch with extra data
adb shell am start \
  -n com.example.app/.MainActivity \
  --es feature_flag "new_checkout" \
  --ez debug_mode true

# Force stop (hard kill)
adb shell am force-stop com.example.app

# Clear app data (fresh state)
adb shell pm clear com.example.app

# Kill background processes
adb shell am kill com.example.app

# Broadcast intent (test event receivers)
adb shell am broadcast -a com.example.app.SYNC_NOW
```

## Input Simulation

```bash
# Tap at coordinates
adb shell input tap 540 960

# Swipe (x1 y1 x2 y2 duration_ms)
adb shell input swipe 540 1500 540 500 300     # scroll up
adb shell input swipe 100 960 900 960 200      # swipe right

# Long press
adb shell input swipe 540 960 540 960 1000     # 1 second press

# Type text
adb shell input text "Hello World"
adb shell input text "user%40example.com"      # @ must be URL-encoded

# Key events
adb shell input keyevent KEYCODE_BACK          # back button
adb shell input keyevent KEYCODE_HOME          # home button
adb shell input keyevent KEYCODE_ENTER         # enter
adb shell input keyevent KEYCODE_POWER         # power button
adb shell input keyevent 4                     # back (numeric)
adb shell input keyevent 66                    # enter (numeric)
adb shell input keyevent 26                    # power (numeric)
adb shell input keyevent 82                    # menu

# Drag (requires API 18+)
adb shell input draganddrop 200 400 600 400 1000

# Multi-touch not directly supported — use Monkey or UIAutomator for that
```

## Logcat (Debugging)

```bash
# Stream all logs
adb logcat

# With timestamps
adb logcat -v time
adb logcat -v threadtime    # thread ID + timestamp

# Filter by tag:level
adb logcat MyApp:D *:S      # MyApp at Debug, silence everything else
adb logcat *:E              # errors from all tags

# Filter by package (API 21+)
adb logcat --pid=$(adb shell pidof -s com.example.app)

# Clear log buffer before test
adb logcat -c

# Dump current buffer to file
adb logcat -d > logcat-$(date +%s).txt

# Save ongoing logs to file
adb logcat -v time > test-run.log &
LOG_PID=$!
# ... run tests ...
kill $LOG_PID

# Filter with grep
adb logcat | grep -E "MyApp|FATAL|ANR|OutOfMemory"

# Readable crash filter
adb logcat -v time AndroidRuntime:E FATAL:E *:S
```

## Screenshots & Screen Recording

```bash
# Screenshot
adb shell screencap /sdcard/screenshot.png
adb pull /sdcard/screenshot.png ./screenshot.png
adb shell rm /sdcard/screenshot.png

# One-liner screenshot (no residue on device)
adb exec-out screencap -p > screenshot.png

# Screen recording (stops on Ctrl+C or after 180s)
adb shell screenrecord /sdcard/recording.mp4
adb pull /sdcard/recording.mp4 ./recording.mp4

# Recording with options
# --time-limit is in seconds (max 180). Never put a comment after a trailing "\" —
# it breaks the line continuation and the command ends early.
adb shell screenrecord \
  --size 1080x1920 \
  --bit-rate 4000000 \
  --time-limit 30 \
  /sdcard/recording.mp4

# Non-interactive recording for CI
adb shell screenrecord /sdcard/recording.mp4 &
RECORD_PID=$!
# ... run tests ...
adb shell kill $RECORD_PID   # stop recording on device
sleep 1
adb pull /sdcard/recording.mp4
```

## File Operations

```bash
# Push file to device
adb push localfile.txt /sdcard/localfile.txt
adb push ./test-data/ /sdcard/test-data/

# Pull file from device
adb pull /sdcard/Downloads/file.txt ./
adb pull /data/data/com.example.app/databases/ ./databases/   # requires root

# List files
adb shell ls /sdcard/

# Run shell commands
adb shell cat /proc/meminfo
adb shell df -h /data
```

## Permissions

```bash
# Grant permission (API 23+, no dialog)
adb shell pm grant com.example.app android.permission.CAMERA
adb shell pm grant com.example.app android.permission.READ_CONTACTS
adb shell pm grant com.example.app android.permission.ACCESS_FINE_LOCATION

# Revoke permission
adb shell pm revoke com.example.app android.permission.CAMERA

# List all granted permissions
adb shell dumpsys package com.example.app | grep "permission"

# Common permissions for testing
BUNDLE=com.example.app
adb shell pm grant $BUNDLE android.permission.CAMERA
adb shell pm grant $BUNDLE android.permission.RECORD_AUDIO
adb shell pm grant $BUNDLE android.permission.READ_EXTERNAL_STORAGE
adb shell pm grant $BUNDLE android.permission.WRITE_EXTERNAL_STORAGE
adb shell pm grant $BUNDLE android.permission.ACCESS_FINE_LOCATION
adb shell pm grant $BUNDLE android.permission.READ_CONTACTS
adb shell pm grant $BUNDLE android.permission.POST_NOTIFICATIONS
```

## Port Forwarding (Debugging / Proxy)

```bash
# Forward: device port → host port (device connects to host services)
adb forward tcp:8080 tcp:8080         # device:8080 → localhost:8080

# Reverse: host port → device port (host reaches device services)
adb reverse tcp:3000 tcp:3000         # localhost:3000 → device:3000

# List forwards
adb forward --list
adb reverse --list

# Remove forwards
adb forward --remove tcp:8080
adb forward --remove-all

# Proxy for network inspection (Charles, mitmproxy)
adb shell settings put global http_proxy 192.168.1.100:8888
adb shell settings put global http_proxy :0    # clear proxy
```

## System Settings (Disable Animations for Tests)

```bash
# Disable animations — critical for reliable UI testing
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0

# Re-enable
adb shell settings put global window_animation_scale 1
adb shell settings put global transition_animation_scale 1
adb shell settings put global animator_duration_scale 1

# Keep screen on during testing
adb shell settings put global stay_on_while_plugged_in 3

# Disable auto-rotate
adb shell settings put system accelerometer_rotation 0
```

## Device Info

```bash
# OS version
adb shell getprop ro.build.version.release     # e.g., "13"
adb shell getprop ro.build.version.sdk         # e.g., "33"

# Device model
adb shell getprop ro.product.model

# Screen size
adb shell wm size

# Screen density
adb shell wm density

# Battery status
adb shell dumpsys battery

# Memory info
adb shell dumpsys meminfo com.example.app

# CPU usage
adb shell top -n 1 | grep com.example
```

## CI/CD Integration

### GitHub Actions (Android Emulator)

```yaml
# .github/workflows/android-tests.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Enable KVM (emulator acceleration)
        run: |
          echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
          sudo udevadm control --reload-rules
          sudo udevadm trigger --name-match=kvm

      - name: Run Android Tests
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 33
          target: google_apis
          arch: x86_64
          profile: pixel_6
          disable-animations: true
          script: |
            adb wait-for-device
            adb install app/build/outputs/apk/debug/app-debug.apk
            ./gradlew connectedAndroidTest

      - name: Screenshot on Failure
        if: failure()
        run: adb exec-out screencap -p > failure.png

      - name: Upload Artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-artifacts
          path: |
            failure.png
            app/build/reports/
```

### Parallel Emulators

```bash
# Start multiple emulators on different ports
emulator -avd Pixel_6_API_33 -port 5554 -no-window &
emulator -avd Pixel_7_API_34 -port 5556 -no-window &

# Run on specific emulator
adb -s emulator-5554 shell am instrument ...
adb -s emulator-5556 shell am instrument ...
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `device unauthorized` | USB debugging not approved | Tap "Allow" on device, or `adb kill-server && adb start-server` |
| `adb: command not found` | Not in PATH | Add `$ANDROID_HOME/platform-tools` to PATH |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Old version installed | `adb uninstall com.example.app` then reinstall |
| `INSTALL_FAILED_INSUFFICIENT_STORAGE` | Device full | `adb shell pm clear com.example.app` or use emulator with more space |
| App crashes immediately | Missing permission or network | Check `adb logcat -v time AndroidRuntime:E *:S` |
| `adb shell am start` - no effect | Activity name wrong | `adb shell pm dump com.example.app \| grep activity` |
| Emulator very slow | No KVM / hardware accel | Linux: enable KVM. Windows: enable **Windows Hypervisor Platform (WHPX)** — HAXM is gone, and the Android Emulator hypervisor driver (AEHD) is sunset 2026-12-31 (developer.android.com/studio/run/emulator-acceleration) |
| Wireless ADB drops often | Network instability | Prefer USB for reliability; `adb reconnect` to recover |

## Script: Cấp Quyền Tự Động Trước Khi Maestro Chạy

Chạy script này **sau khi install APK** và **trước** `maestro test` để grant toàn bộ permissions,
tránh dialog permission bất ngờ làm vỡ Maestro flow.

```bash
#!/bin/bash
# scripts/android-grant-permissions.sh
# Usage: ./android-grant-permissions.sh com.example.app [device-serial]
set -e

BUNDLE_ID="${1:?Usage: $0 <package-name> [device-serial]}"
DEVICE="${2:-}"
ADB_CMD="adb${DEVICE:+ -s $DEVICE}"

echo "▶ Granting permissions for $BUNDLE_ID"

grant() {
  local permission=$1
  $ADB_CMD shell pm grant "$BUNDLE_ID" "$permission" 2>/dev/null \
    && echo "  ✓ $permission" \
    || echo "  ⚠ $permission (skipped — chưa khai báo trong Manifest hoặc API không hỗ trợ)"
}

# Location
grant android.permission.ACCESS_FINE_LOCATION
grant android.permission.ACCESS_COARSE_LOCATION
grant android.permission.ACCESS_BACKGROUND_LOCATION   # Android 10+

# Notifications (Android 13+)
grant android.permission.POST_NOTIFICATIONS

# Media & Storage
grant android.permission.CAMERA
grant android.permission.RECORD_AUDIO
grant android.permission.READ_MEDIA_IMAGES            # Android 13+
grant android.permission.READ_MEDIA_VIDEO             # Android 13+
grant android.permission.READ_EXTERNAL_STORAGE        # Android <13
grant android.permission.WRITE_EXTERNAL_STORAGE       # Android <13

# Contacts & Calendar
grant android.permission.READ_CONTACTS
grant android.permission.WRITE_CONTACTS
grant android.permission.READ_CALENDAR
grant android.permission.WRITE_CALENDAR

# Phone & SMS
grant android.permission.READ_PHONE_STATE
grant android.permission.CALL_PHONE

echo ""
echo "✅ Permissions granted. Maestro sẽ không gặp permission dialog."
echo ""

# Verify: kiểm tra một số permissions quan trọng
echo "▶ Verifying critical permissions..."
GRANTED=$($ADB_CMD shell dumpsys package "$BUNDLE_ID" | grep -c "granted=true" || true)
echo "  Tổng permissions đã granted: $GRANTED"
```

### Tích hợp vào CI workflow

```bash
# Thứ tự đúng trong CI:
# 1. Start emulator và chờ boot
emulator -avd Pixel_6_API_33 -no-window -no-audio &
adb wait-for-device
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null)" = "1" ]; do sleep 2; done

# 2. Install APK
adb install -r build/app-debug.apk

# 3. Grant permissions (PHẢI sau install — app cần có trong package manager)
./scripts/android-grant-permissions.sh com.example.app

# 4. Chạy Maestro
# KHÔNG có flag `--retry-on-failure` (Maestro 2.11.0 `maestro test --help`). Retry đặt TRONG flow,
# chỉ bọc bước hay chập chờn:  - retry: { maxRetries: 2, commands: [ ... ] }   (maxRetries 0–3)
maestro test flows/
```

---

## Script: Chuẩn Bị Android Đầy Đủ (Boot + Config + Permissions + Install)

```bash
#!/bin/bash
# scripts/prepare-android.sh
# Usage: BUNDLE_ID=com.example.app APK_PATH=build/app.apk ./prepare-android.sh
set -e

BUNDLE_ID="${BUNDLE_ID:-com.example.app}"
APK_PATH="${APK_PATH:-build/app-debug.apk}"
DEVICE="${ADB_DEVICE:-}"
ADB_CMD="adb${DEVICE:+ -s $DEVICE}"

echo "▶ Waiting for device..."
$ADB_CMD wait-for-device
until [ "$($ADB_CMD shell getprop sys.boot_completed 2>/dev/null)" = "1" ]; do
  sleep 2
done
echo "  Device ready: $($ADB_CMD shell getprop ro.product.model)"

echo "▶ Disabling animations (critical for UI test stability)..."
$ADB_CMD shell settings put global window_animation_scale 0
$ADB_CMD shell settings put global transition_animation_scale 0
$ADB_CMD shell settings put global animator_duration_scale 0

echo "▶ Configuring device for testing..."
$ADB_CMD shell settings put global stay_on_while_plugged_in 3     # keep screen on
$ADB_CMD shell settings put system accelerometer_rotation 0        # disable auto-rotate
$ADB_CMD shell settings put secure location_mode 3                 # GPS on (High accuracy)

echo "▶ Installing: $APK_PATH"
$ADB_CMD install -r "$APK_PATH"
echo "  Installed: $BUNDLE_ID"

echo "▶ Granting permissions..."
grant_permission() {
  $ADB_CMD shell pm grant "$BUNDLE_ID" "$1" 2>/dev/null && echo "  ✓ $1" || echo "  ⚠ $1"
}

grant_permission android.permission.ACCESS_FINE_LOCATION
grant_permission android.permission.ACCESS_COARSE_LOCATION
grant_permission android.permission.POST_NOTIFICATIONS
grant_permission android.permission.CAMERA
grant_permission android.permission.RECORD_AUDIO
grant_permission android.permission.READ_CONTACTS
grant_permission android.permission.READ_MEDIA_IMAGES
grant_permission android.permission.READ_EXTERNAL_STORAGE

echo ""
echo "✅ Android device ready for testing"
echo "   Package: $BUNDLE_ID"
echo "   Device:  $($ADB_CMD shell getprop ro.product.model) (API $($ADB_CMD shell getprop ro.build.version.sdk))"
```

---

## Script: Cleanup Sau Khi Test Kết Thúc

Cleanup ngăn emulator/process orphan tích tụ trên CI worker, tránh OOM và port conflict.
Chạy trong `finally` hoặc `after_script` block của CI.

```bash
#!/bin/bash
# scripts/android-cleanup.sh
# Usage: BUNDLE_ID=com.example.app ./android-cleanup.sh [device-serial]
set -e

BUNDLE_ID="${BUNDLE_ID:-com.example.app}"
DEVICE="${1:-}"
ADB_CMD="adb${DEVICE:+ -s $DEVICE}"

echo "▶ Android cleanup started..."

# 1. Force stop app (giải phóng memory)
echo "  Stopping app: $BUNDLE_ID"
$ADB_CMD shell am force-stop "$BUNDLE_ID" 2>/dev/null || true

# 2. Re-enable animations (nếu chạy trên real device — không để lại trạng thái tắt animations)
if [ "$CI" != "true" ]; then
  echo "  Re-enabling animations (local device)..."
  $ADB_CMD shell settings put global window_animation_scale 1
  $ADB_CMD shell settings put global transition_animation_scale 1
  $ADB_CMD shell settings put global animator_duration_scale 1
fi

# 3. Pull artifacts trước khi xóa
ARTIFACT_DIR="${CI_ARTIFACTS_DIR:-./test-artifacts}/android"
mkdir -p "$ARTIFACT_DIR"

# Kéo logcat dump nếu có
if $ADB_CMD shell ls /sdcard/logcat.txt >/dev/null 2>&1; then
  $ADB_CMD pull /sdcard/logcat.txt "$ARTIFACT_DIR/" 2>/dev/null || true
  echo "  Logcat pulled to $ARTIFACT_DIR/"
fi

# Kéo screenshots/videos còn lại
$ADB_CMD pull /sdcard/maestro-recording.mp4 "$ARTIFACT_DIR/" 2>/dev/null || true

# 4. Xóa test artifacts khỏi device
$ADB_CMD shell rm -f /sdcard/logcat.txt /sdcard/screenshot*.png /sdcard/maestro-*.mp4 \
  2>/dev/null || true

# 5. Clear app data (optional — comment out nếu muốn giữ state cho debug)
# $ADB_CMD shell pm clear "$BUNDLE_ID" 2>/dev/null || true

# 6. Remove port forwards
$ADB_CMD forward --remove-all 2>/dev/null || true
$ADB_CMD reverse --remove-all 2>/dev/null || true

# 7. Tắt emulator (chỉ trên CI)
if [ "${CI:-}" = "true" ]; then
  echo "  Shutting down emulator..."
  $ADB_CMD emu kill 2>/dev/null || true

  # Chờ emulator tắt hoàn toàn
  sleep 3

  # Kill orphan emulator processes
  pkill -f "qemu-system" 2>/dev/null || true
  pkill -f "emulator64" 2>/dev/null || true
  pkill -f "emulator-" 2>/dev/null || true

  # ADB server không cần thiết nữa — restart để clear state
  adb kill-server 2>/dev/null || true
fi

echo "✅ Android cleanup hoàn tất"
```

### Tích hợp vào GitHub Actions

```yaml
# .github/workflows/android-maestro.yml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      BUNDLE_ID: com.example.app
      APK_PATH: app/build/outputs/apk/debug/app-debug.apk

    steps:
      - uses: actions/checkout@v4

      - name: Enable KVM
        run: |
          echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
          sudo udevadm control --reload-rules && sudo udevadm trigger --name-match=kvm

      - name: Build APK
        run: ./gradlew assembleDebug

      - name: Prepare Android & Run Tests
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 33
          arch: x86_64
          profile: pixel_6
          disable-animations: true
          script: |
            ./scripts/prepare-android.sh
            maestro test --format junit --output results.xml flows/   # no --retry-on-failure flag exists; use the `retry:` flow command

      - name: Cleanup (always)
        if: always()
        run: ./scripts/android-cleanup.sh

      - name: Upload Artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: android-test-artifacts
          path: |
            results.xml
            test-artifacts/android/
```

## Logcat Wrapper for CI

```bash
#!/bin/bash
# scripts/capture-logcat.sh
# Usage: ./capture-logcat.sh com.example.app output.log
BUNDLE=$1
OUTPUT=${2:-logcat.log}

adb logcat -c                                      # clear buffer
adb logcat -v time > "$OUTPUT" &                   # start capture
echo $! > /tmp/logcat-pid

echo "Logcat started (PID: $(cat /tmp/logcat-pid))"
echo "Stop with: kill \$(cat /tmp/logcat-pid)"

# Filter on the fly for quick CI output
adb logcat -v time \
  "$BUNDLE":D \
  AndroidRuntime:E \
  FATAL:E \
  ANRManager:E \
  *:S
```

---

## Platform-version gate

If the app under test targets **API 36 (Android 16)** — or is being tested on an API 36 device —
run `android-16-qa-gate` before sign-off. Android 16 removes the edge-to-edge opt-out, stops
dispatching `onBackPressed()`/`KEYCODE_BACK`, and ignores orientation locks on ≥600dp screens.
These are runtime-only regressions with no build error, so an adb smoke run will not surface them.

```bash
adb shell getprop ro.build.version.sdk          # device API level
adb shell dumpsys package <pkg> | grep -i targetSdk   # what the app targets
```

Both must be 36+ for those behaviour changes to activate — otherwise a "pass" is a false pass.

If the device or `targetSdk` is **API 37 (Android 17**, stable 2026-06-16) → also run `android-17-qa-gate`.
A suite green on API 36 says nothing about API 37 (and Maestro needs CLI ≥ 2.11.0 to `start-device`
an API 37 emulator).
