---
name: android-17-qa-gate
description: |
  QA regression gate for apps bumping targetSdk to 37 (Android 17), and for any app tested on an
  Android 17 / One UI 9 device. Android 17 turns several Android 16 opt-ins into defaults:
  local-network access needs a runtime permission, standard SMS OTPs are withheld from
  SMS-reading apps for 3 hours, Certificate Transparency is enforced, the large-screen
  orientation opt-out is gone, and dynamically loaded native libs must be read-only. The app
  builds and installs fine; failures are runtime-only (timeouts, silent audio, OTP never
  auto-fills, UnsatisfiedLinkError, rotation on Fold inner screen).
  Use when: targetSdk/compileSdk raised to 37, a release is tested on Android 17 / One UI 9
  (Galaxy S26, S25, Z Fold7/8, Z Flip7/8), testers report "OTP không tự điền", "không tìm thấy
  thiết bị trong mạng LAN", "app xoay trên Fold", "mất tiếng khi chạy nền", "TLS/SSL lỗi chỉ
  trên Android 17".
  Triggers on: "Android 17", "API 37", "targetSdk 37", "targetSdkVersion 37", "One UI 9",
  "ACCESS_LOCAL_NETWORK", "local network permission", "SMS OTP delay", "SMS_RECEIVED",
  "Certificate Transparency", "UNIVERSAL_RESIZABLE_BY_DEFAULT", "memory-limiter",
  "background audio hardening", "test Android 17", "OTP không tự điền", "OTP bị trễ",
  "app không kết nối LAN", "app xoay trên Fold", "mất tiếng nền".
---

# Android 17 (API 37) QA Gate

> **Why this skill exists:** Android 16's opt-ins become Android 17's defaults, and most failures
> are *silent* — a TCP timeout, an OTP that never arrives, audio that just doesn't play. No crash,
> no build error. A suite green on API 36 tells you nothing about API 37.
> Android 17 stable: 2026-06-16. Samsung ships it as **One UI 9**. Researched 2026-10-02 from the
> official behaviour-change pages; items marked `[inference]` are reasoned, not documented.

## Gate rule

Treat the `targetSdk 37` bump as its own regression milestone — no sign-off until every section has a
result. **Two kinds of change; record which one each finding belongs to:**

| Kind | Activates when | Sections |
|---|---|---|
| **All apps** | Device runs Android 17, any targetSdk | 2b, 7, 8, 9, 10 |
| **Targeting 37** | Device on 17 **and** `targetSdk ≥ 37` | 1, 2a, 3, 4, 5, 6, 8 (stricter) |

```bash
adb shell dumpsys package <pkg> | grep -i targetSdk     # must be 37 for "targeting" sections
adb shell getprop ro.build.version.sdk                  # must be 37
adb shell getprop ro.build.version.release              # 17
adb shell getconf PAGE_SIZE                             # 16384 = 16 KB device
```

> ⚠️ Testing a targetSdk-36 build on an Android 17 device only covers the "All apps" rows.
> Report the pair — "Android 17 passed" is meaningless without the targetSdk.

---

## 1. Local network access blocked by default (targeting 37) — HIGH RISK

New runtime permission `ACCESS_LOCAL_NETWORK` (group `NEARBY_DEVICES`). Without it: outgoing/incoming
TCP, UDP unicast/multicast/broadcast, mDNS (`.local`), SSDP, raw sockets to LAN addresses all fail.
Exempt: DNS on port 53, system pickers (`NsdManager` + `FLAG_SHOW_PICKER`, Cast Output Switcher).
WebView inherits the host app's permission state.

**Symptom:** TCP → *timeout* (not a permission error); UDP → `EPERM`. If the user already granted
another `NEARBY_DEVICES` permission (e.g. Bluetooth), **no prompt appears** — test fresh install AND
Bluetooth-already-granted state.

Test: device discovery, casting, printing, smart-home, LAN API calls, IP-camera streams.
```bash
adb shell pm revoke <pkg> android.permission.ACCESS_LOCAL_NETWORK   # deny path
adb shell pm grant  <pkg> android.permission.ACCESS_LOCAL_NETWORK   # grant path
adb logcat | grep -iE "EPERM|timeout|LNP"
```
Checks: deny path shows a rationale/error state (not an endless spinner); grant → works without app
restart; revoke while running → degrades without crash.
> [inference] Dev/staging builds loading from a LAN IP (React Native Metro / Expo on
> `192.168.x.x:8081`, staging server on the office LAN) time out at targetSdk 37 until the
> permission is granted — grant it in your setup script before blaming the build.

## 2. SMS OTP withheld for 3 hours

- **2a (targeting 37):** *standard* SMS (not WebOTP / SMS Retriever format) is withheld from the app
  for 3 h — `SMS_RECEIVED_ACTION` not delivered, `Telephony.Sms` provider queries filtered.
- **2b (all apps):** **WebOTP-format** messages withheld 3 h from apps with SMS-read permission that
  are *not* the domain-verified recipient.
- Exempt: default SMS app, companion apps of connected devices, other system-chosen apps.

**Symptom:** OTP auto-fill silently stops; a login test waiting for auto-fill hangs to timeout. The
correct path is SMS Retriever / SMS User Consent API.

Test:
1. Login/register with a real SIM on the Android 17 device; send the OTP in **each** format the
   backend can produce (standard text; SMS Retriever with 11-char app hash; WebOTP `@domain #code`).
2. Expected: Retriever/User-Consent flows still auto-fill; anything relying on `READ_SMS`/`RECEIVE_SMS`
   is a bug at targetSdk 37.
3. Manual-entry fallback must always be reachable (field focusable, keyboard opens).
```bash
adb emu sms send 5551234 "Your code is 123456"   # emulator only; real device needs a real SMS
```
> [inference] An automation helper app that reads OTPs off the device SMS store is subject to the
> same 3 h delay — switch the suite to a backend OTP bypass / fixed test OTP (see `otp-untestable-flows`).

## 3. Large screens — orientation/resize opt-out REMOVED (targeting 37)

On displays with sw ≥ 600dp these are ignored with **no developer opt-out**: `screenOrientation`,
`resizeableActivity`, `minAspectRatio`, `maxAspectRatio`, `setRequestedOrientation()` /
`getRequestedOrientation()`. The Android 16 `PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY` escape
hatch no longer applies. Exempt: games (`android:appCategory`), sw < 600dp, and a *user* opt-in in the
device's aspect-ratio settings.

**Samsung:** Z Fold inner screen and Galaxy Tab hit this (Fold8 ships Android 17). Reset any per-app
aspect-ratio override in Settings first — the user opt-in exemption masks the bug.
```bash
adb shell am compat enable UNIVERSAL_RESIZABLE_BY_DEFAULT <pkg>   # documented test switch
adb shell wm size; adb shell wm density   # sw = min(w,h)/(density/160) — must be ≥600
adb shell settings put system accelerometer_rotation 0
adb shell settings put system user_rotation 1
```
Check: stretched layouts, off-screen components, **camera preview stretched/rotated/cropped**, state lost
on rotation (form input, scroll, open dialog, upload in progress); fold/unfold mid-flow.
> No ≥600dp device tested → report **NOT COVERED**, not passed.

## 4. Certificate Transparency on by default (targeting 37)

`<certificateTransparency>` now defaults to enabled; servers whose certs aren't in CT logs (private /
internal-CA staging servers) fail the TLS handshake. CT is skipped for a `<domain-config>` that trusts
`user` or inline anchors — so a debug build trusting user CAs (Charles/Proxyman) can **pass while the
release build fails**.

Test: **release** build against every backend host (prod, staging, CDN, analytics, payment SDK hosts) on
Android 17 without a proxy; any host failing only here = CT. Per-domain opt-out (`enabled="false"`)
exists — report as a finding, not a fix.

Also targeting 37: **ECH** (`<domainEncryption>`) on by default if the networking library supports it.
[inference] SNI-inspecting corporate firewalls may break TLS — retest on mobile data before filing.

## 5. Native libs loaded via `System.load()` must be read-only (targeting 37)

Writable `.so` → `UnsatisfiedLinkError`. Typical: SDKs that download/unpack native code at runtime
(plugins, anti-tamper, ML runtimes). Test every native-backed feature (camera/ML/video/crypto/maps) on
first use after a clean install.
```bash
adb logcat | grep -E "UnsatisfiedLinkError"
```
16 KB page size still applies (`android-16-qa-gate` §4) — `getconf PAGE_SIZE` must be 16384.

## 6. Background launch, widgets, reflection (targeting 37)

| Change | Symptom | Test |
|---|---|---|
| BAL hardening extended to `IntentSender`; `MODE_BACKGROUND_ACTIVITY_START_ALLOWED` deprecated | Tapping a notification/PendingIntent while app is backgrounded does nothing | Background the app → tap each notification type → screen must open |
| Widget RemoteViews bitmap limit `1.5 × w × h × 4` | `IllegalArgumentException`, crash on widget update | Add every widget size; trigger image-heavy update |
| `static final` fields unmodifiable | `IllegalAccessException` (reflection) / crash (JNI) | Full smoke; grep logcat |
| `setContentCaptureEnabled(false)` no-op → use `FLAG_SECURE` | Sensitive screens visible to on-device AI | Payment/password screens: `adb exec-out screencap -p` should be black if the app expects secure |
| `MessageQueue` lock-free rewrite | Libraries reflecting on MessageQueue internals break | Full smoke; watch SDK crashes |

> [inference] `FLAG_SECURE` screens are also black in Maestro/adb screenshots — expected, not a bug.

## 7. App memory limiter (all apps)

Per-app memory limits based on device RAM. Kill reason `REASON_OTHER`, description contains
`MemoryLimiter:AnonSwap`. Symptom: app "restarts" on return from background during heavy flows.
```bash
adb shell am memory-limiter status
adb shell am memory-limiter manual <pid> 300     # force a low limit (MB) to reproduce
adb shell am memory-limiter manual <pid> none    # restore default
adb shell dumpsys activity exit-info <pkg> | grep -i MemoryLimiter
```
Test long sessions (gallery scroll, video, map, large uploads) on the lowest-RAM Samsung in scope.

## 8. Background audio hardening (all apps; stricter at 37)

Playback, focus requests and volume APIs need a visible activity or a non-`SHORT_SERVICE` foreground
service; at targetSdk 37 that FGS must also have **while-in-use** capability (exception: exact-alarm
permission + `USAGE_ALARM`). **Playback and volume fail silently**; focus returns `AUDIOFOCUS_REQUEST_FAILED`.
```bash
adb shell cmd audio set-enable-hardening enable   # enforce for all apps regardless of target
adb shell cmd audio set-enable-hardening throw    # make violations throw (easier to see)
adb shell dumpsys audio | grep AudioHardening     # full = FGS without WIU, partial = no FGS
adb shell cmd audio set-enable-hardening disable  # cleanup — ALWAYS restore
```
Test: start playback → Home → lock screen → resume from notification; alarms/reminders that start sound
from background. Not affected: visible activity (incl. PiP), VoIP via Telecom.
Audio apps (e.g. Soundwise white-labels) — this section is mandatory.

## 9. Keyboard not restored after rotation (all apps)

If the app doesn't handle the config change, the soft keyboard is **not** re-shown after rotation.
Test: focus a field with keyboard open → rotate → expected per spec.
[inference] Maestro flows that `inputText` right after a rotation may need `tapOn` on the field first.

## 10. Other all-apps changes (only if relevant)

| Change | Test only if |
|---|---|
| Cross-profile loopback traffic blocked | App runs in Work profile / Samsung Secure Folder and talks to localhost in the other profile |
| Keystore limit 50,000 keys (target 37) / 200,000 (others) → `KeyStoreException` | App creates keys per message/session |
| Touchpad pointer capture → relative events | App uses `requestPointerCapture()` |
| Bluetooth auto re-pairing; `ACTION_KEY_MISSING` only after failed re-pair | Companion/BLE apps: unpair in Settings, check recovery |
| RFCOMM `BluetoothSocket.read()` returns `-1` on close (target 37) | Classic BT apps: power off peripheral mid-transfer |
| Passwords fully hidden with external keyboard (target 37) | Samsung DeX / tablet keyboard flows |
| Implicit URI grants for SEND/IMAGE_CAPTURE end in **Android 18** | Share/camera flows — watch `adb logcat \| grep "Please set the grant explicitly"` now |

## 11. Carried over from Android 16 (still check)

- **Edge-to-edge:** no new Android 17 change; opt-out disabled since targetSdk 36 — rerun `android-16-qa-gate` §1.
- **Predictive back:** **not listed** in the Android 17 behaviour-change pages. Whether
  `enableOnBackInvokedCallback="false"` is still honoured at targetSdk 37 is **UNVERIFIED** — if the
  opt-out is in the manifest, test back with a real gesture swipe both ways and log it as deferred work.

---

## Tooling

- **Emulator via Maestro:** Maestro CLI 2.11.0 CHANGELOG says `start-device` supports Android 17
  (API 37) and resolves the minor-versioned 16 KB page-size images, naming the exact `--device-os` to
  use if the derived image isn't installed — e.g. `maestro start-device --platform android --device-os android-37`
  (from changelog; not yet run in this environment — no local SDK emulator as of 2026-10-02).
  **UNVERIFIED** (third-party): API 37.x x86_64 images ship only as `google_apis_ps16k` (16 KB pages) —
  confirm with `adb shell getconf PAGE_SIZE`.
- **Samsung:** Android 17 = **One UI 9**. Preinstalled on Z Fold8/Flip8; stable rollout wide on Galaxy
  S26 late Sep 2026, then S25 series, Z Fold7/Flip7 (~28 Sep), older models Oct 2026. Use a Fold inner
  screen for §3. One UI version getprop key unverified — read Settings > About phone > Software information.

## Coverage matrix

| # | Area | Kind | Device / API | targetSdk | Result | Evidence |
|---|---|---|---|---|---|---|
| 1 | Local network: grant / deny / revoke / pre-granted BT | 37 | | | | logcat |
| 2 | SMS OTP: standard / Retriever / WebOTP + manual fallback | 37 + all | | | | video |
| 3 | Rotation + state on ≥600dp (Fold inner / Tab) | 37 | | | | screenshot |
| 4 | Release build vs every backend host (CT) | 37 | | | | logcat |
| 5 | Native-backed features first use | 37 | | | | logcat |
| 6 | Notification tap from background, widgets | 37 | | | | video |
| 7 | Memory limiter under forced limit | all | | | | exit-info |
| 8 | Background audio with hardening=enable | all | | | | dumpsys audio |
| 9 | Keyboard after rotation | all | | | | screenshot |
| 10 | Edge-to-edge + predictive back recheck | 36+ | | | | screenshot/video |

`N/A` needs a reason. Blank = not done.

## Anti-patterns

| Anti-pattern | Why it fails | Do instead |
|---|---|---|
| Testing a targetSdk-36 build on Android 17 and calling the gate done | Only "all apps" changes fire | Test the targetSdk-37 build |
| Treating a LAN timeout as a backend/network bug | Local-network permission produces timeouts, not errors | Check `ACCESS_LOCAL_NETWORK` state first |
| Debug build behind Charles/Proxyman for TLS checks | User trust anchors switch CT off → false pass | Release build, no proxy |
| Waiting for OTP auto-fill in automation | Standard SMS withheld 3 h at target 37 | Backend OTP bypass / fixed test OTP |
| Background audio "works on my device" | Silent failure | Force `set-enable-hardening enable` |
| Rotation tests on a phone | sw < 600dp is exempt | Fold inner screen / tablet, or mark NOT COVERED |
| Leaving a Samsung per-app aspect-ratio override set | User opt-in exempts the app | Reset to default before §3 |
| Leaving `set-enable-hardening` / `memory-limiter manual` on after testing | Pollutes later runs on a shared device | Restore (`disable` / `none`) in teardown |

## Related skills
`android-16-qa-gate` (baseline, still applies) · `android-adb` · `maestro-mobile` · `otp-untestable-flows` ·
`responsive-viewport-testing` · `state-ripple-verify` · `bug-repro-isolation` · `qa-bug-report`

## Sources
- https://developer.android.com/about/versions/17/behavior-changes-17 — target-37 changes
- https://developer.android.com/about/versions/17/behavior-changes-all — all-apps changes
- https://developer.android.com/about/versions/17/features
- https://developer.android.com/about/versions/17/changes/ff-restrictions-ignored — ignored attrs/APIs, exemptions, `UNIVERSAL_RESIZABLE_BY_DEFAULT`
- https://developer.android.com/about/versions/17/changes/bg-audio — `cmd audio set-enable-hardening`, `AudioHardening` dumpsys
- https://developer.android.com/privacy-and-security/local-network-permission — restricted traffic, symptoms, `pm grant`
- https://developer.android.com/privacy-and-security/security-config — `<certificateTransparency>` defaults + user-anchor rule, `<domainEncryption>`
- https://developer.android.com/about/versions/16/behavior-changes-16 — resizability opt-out expires at API 37
- https://github.com/mobile-dev-inc/maestro/blob/main/CHANGELOG.md#2110 — Android 17 / API 37 in `start-device`
- https://9to5google.com/2026/09/29/samsung-android-17-update-rolling-out-galaxy-s26-s25/ — One UI 9 = Android 17
- https://github.com/knirski/subsloth/pull/394 — (third-party, unverified) API 37.x images only as `google_apis_ps16k`
