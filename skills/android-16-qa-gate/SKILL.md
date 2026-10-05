---
name: android-16-qa-gate
description: |
  QA regression gate for apps bumping targetSdk to 36 (Android 16). Android 16 REMOVES several
  opt-outs that apps silently relied on — the app still compiles and installs, but layouts clip
  under system bars, back gestures stop firing onBackPressed(), and portrait-locked screens
  suddenly rotate on tablets. These are runtime-only regressions: no build error warns you.
  Use when: an app raises targetSdk/compileSdk to 36, a release is tested on an Android 16 device
  or emulator (API 36), a tester reports "content hidden behind status bar / navigation bar",
  "back button does nothing", "app rotates even though it's locked to portrait", or a Play Console
  pre-launch report flags Android 16 issues.
  Triggers on: "Android 16", "API 36", "targetSdk 36", "targetSdkVersion 36", "edge-to-edge",
  "predictive back", "16 KB page size", "windowOptOutEdgeToEdgeEnforcement", "test Android 16",
  "app rotates on tablet", "content behind status bar", "back gesture not working",
  "nội dung bị che status bar", "back không hoạt động", "test Android 16".
---

# Android 16 (API 36) QA Gate

> **Why this skill exists:** Android 16's biggest QA risks are *removed opt-outs*, not new APIs.
> The app builds fine and installs fine. The defects only appear at runtime, only on API 36
> devices, and only once `targetSdk = 36`. A suite that passes on API 35 tells you nothing.

## Gate rule

Treat the `targetSdk 36` bump as its own **regression milestone**, not a build chore.
Do not sign off a targetSdk-36 release until every section below has a run result.

**Precondition — the changes below only activate when BOTH are true:**
1. App manifest/gradle declares `targetSdk 36` (or higher), **and**
2. Test device/emulator runs Android 16 (API 36+).

Verify both before trusting any "pass":

```bash
# 1. What the app targets (read from the installed APK)
adb shell dumpsys package <pkg> | grep -i targetSdk

# 2. What the device runs — must be 36+
adb shell getprop ro.build.version.sdk
adb shell getprop ro.build.version.release
```

> ⚠️ If either is below 36, your test is a **false pass**. Record which pair you tested on in the
> report — "passed on Android 16" is meaningless without the targetSdk value.

---

## 1. Edge-to-edge — opt-out is GONE (highest risk)

`android:windowOptOutEdgeToEdgeEnforcement` is deprecated **and disabled** on Android 16 devices.
Apps that used it to keep the old inset behaviour now draw under the status bar and navigation bar.

**Nuance that causes false passes:** the opt-out still works on **Android 15 devices** even when
the app targets 36. So the same APK looks correct on an API 35 emulator and broken on API 36.
You must test on API 36.

### What to test

Every screen where content can reach a screen edge. Prioritise these, since a clipped control here
blocks the flow entirely:

| Screen | Failure that blocks release |
|---|---|
| Login / OTP | Submit button under the nav bar → cannot log in |
| Payment / checkout | Confirm button unreachable |
| Forms with a bottom CTA | Save hidden behind gesture bar |
| Full-screen media / camera | Controls under status bar |
| Bottom sheets & dialogs | Last row unreachable |
| Lists with sticky footers | Footer overlaps gesture area |

### Checks per screen

- Top content is not under the status bar (clock/battery overlapping text).
- Bottom CTA is fully **tappable**, not merely visible — tap it, don't just screenshot it.
- Scroll to the very bottom: the last item must clear the gesture bar.
- Repeat with **3-button navigation** and **gesture navigation** — the inset heights differ.

```bash
# Force navigation mode to test both (values vary by OEM; check what exists first)
adb shell cmd overlay list | grep -i navbar
adb shell cmd overlay enable com.android.internal.systemui.navbar.threebutton
adb shell cmd overlay enable com.android.internal.systemui.navbar.gestural
```

> **Verify visually, at native resolution.** An inset bug is a *visual* defect — a passing
> `isDisplayed()` assertion says nothing about whether the button sits under the nav bar.
> Take a screenshot and look at it.

---

## 2. Predictive back — `onBackPressed()` stops firing

For apps targeting 36 on Android 16+, predictive back animations are on by default, and as a
consequence:

- `onBackPressed()` is **not called**
- `KeyEvent.KEYCODE_BACK` is **not dispatched**

Any screen whose unsaved-changes prompt, wizard step-back, or custom exit logic hangs off those
hooks silently does nothing — or worse, exits the screen and drops user input.

**Opt-out still exists (temporarily):** `android:enableOnBackInvokedCallback="false"` on
`<application>` or per `<activity>`. If the team set this, note it as **deferred work**, not a fix —
record it in the report.

### What to test

- Multi-step wizards / forms: back must return to the previous step, not exit the flow.
- Unsaved-changes confirmation dialogs: must still appear on back.
- Modal screens and bottom sheets: back dismisses the modal, not the whole activity.
- Nested navigation (tab → detail → sub-detail): back unwinds one level at a time.
- **Predictive preview:** swipe back slowly and hold — the peek animation must show the correct
  destination, then releasing must actually land there. Cancelling the swipe must stay put.
- **3-button nav:** on Android 16, long-pressing back also triggers the predictive animation for
  migrated apps — check it does not double-navigate.

**Data-loss check (mandatory, not optional):** enter data → press back → confirm the app either
prompts or preserves the input. A back handler that silently stopped firing is a data-loss bug,
and it will not be caught by any assertion that only checks which screen is shown.

```bash
# Send back from adb (note: on API 36 this may be swallowed for targetSdk-36 apps —
# that is exactly the behaviour you are testing for)
adb shell input keyevent KEYCODE_BACK
```

> Because the key event may not be dispatched at all, **do not rely on `adb input keyevent` alone**
> to validate back behaviour. Use a real gesture swipe in the automation flow, and treat an adb-only
> pass as unverified.

---

## 3. Orientation / resizability ignored on large screens (≥600dp)

On displays with smallest width ≥ 600 dp, Android 16 **ignores** all of:

- `android:screenOrientation`
- `android:resizableActivity`
- `android:minAspectRatio` / `android:maxAspectRatio`
- `setRequestedOrientation()` / `getRequestedOrientation()`

A phone-only app that always assumed portrait will now rotate and resize on tablets and foldables.

**Opt-out (temporary, dies at API 37):**
`android.window.PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY`. Games (via `android:appCategory`)
are exempt. Screens under 600 dp are unaffected.

### What to test — on a ≥600dp device/emulator only

- Rotate portrait ⇄ landscape on every primary screen; check no clipped/overlapping layout.
- **State survives rotation:** form input, scroll position, selected tab, open dialog, in-flight
  upload. Rotation destroys and recreates the activity — this is where state bugs surface.
- Multi-window / split-screen: resize the window and check the layout reflows.
- Foldable fold/unfold transitions if in scope.

```bash
# Create an API 36 tablet AVD to test this at all (a phone AVD will NOT reproduce it)
avdmanager create avd -n tablet_api36 -k "system-images;android-36;google_apis;x86_64" \
  -d "pixel_tablet"

# Confirm the screen really is >=600dp
adb shell wm size
adb shell wm density
# smallestWidthDp = min(width,height) / (density/160)

# Force rotation
adb shell settings put system accelerometer_rotation 0
adb shell settings put system user_rotation 1   # 0=portrait 1=90 2=180 3=270
```

> A phone-sized emulator cannot reproduce this class of bug. If no ≥600dp device was tested,
> report this section as **NOT COVERED**, not as passing.

---

## 4. 16 KB memory page size (native libraries)

Devices with 16 KB pages reject native `.so` libraries not aligned for them — the app can crash on
launch or when the feature loading that library is first used. This hits apps with NDK code *and*
apps whose third-party SDKs ship native libs, which is the common case teams miss.

```bash
# Is the device using 16 KB pages?
adb shell getconf PAGE_SIZE     # 16384 = 16 KB, 4096 = 4 KB

# Audit alignment of every native lib in the APK
unzip -l app.apk | grep '\.so$'
# Then per lib (needs Android NDK llvm-readelf):
llvm-readelf -l lib/arm64-v8a/libfoo.so | grep -A1 LOAD
# Align must be 2**14 (16384) — 2**12 (4096) is the failure case
```

Test the **crash-prone path**, not just launch: features backed by native code (camera/ML/video/
crypto/maps/analytics SDKs) must each be exercised on a 16 KB device.

---

## 5. Health & fitness permissions (only if the app reads body sensors)

`BODY_SENSORS` / `BODY_SENSORS_BACKGROUND` are replaced by granular health permissions:

| Old | New |
|---|---|
| `BODY_SENSORS` | `READ_HEART_RATE` |
| `BODY_SENSORS_BACKGROUND` | `READ_HEALTH_DATA_IN_BACKGROUND` |

No opt-out. Mobile apps must also declare an activity that shows the privacy policy.

Test grant, deny, and revoke-while-running for each new permission — plus the app's behaviour when
the permission is denied (it must degrade gracefully, not crash).

```bash
adb shell pm grant  <pkg> android.permission.READ_HEART_RATE
adb shell pm revoke <pkg> android.permission.READ_HEART_RATE
adb shell dumpsys package <pkg> | grep -A40 "runtime permissions"
```

---

## 6. Local network access (enforcement is coming — test early)

Access to the local network moves behind a runtime permission (`NEARBY_WIFI_DEVICES`). Currently
opt-in, so it will **not** fail by default — you must enable the compat flag to see the future
behaviour. Relevant for apps doing local device discovery, casting, printing, or LAN API calls.

```bash
adb shell am compat enable RESTRICT_LOCAL_NETWORK <pkg>
adb reboot
# ... test discovery/casting/LAN features ...
adb shell am compat disable RESTRICT_LOCAL_NETWORK <pkg>
```

---

## 7. Lower-risk changes — confirm only if relevant

| Change | Test only if | Opt-out |
|---|---|---|
| `elegantTextHeight` ignored | App renders Arabic / Lao / Myanmar / Tamil / Tibetan text | None — check line heights don't clip |
| `scheduleAtFixedRate()` runs at most one missed execution | App has periodic background work | Compat flag `STPE_SKIP_MULTIPLE_MISSED_PERIODIC_TASKS` |
| `MediaStore#getVersion()` now per-app | App parses that version string | None |
| Safer Intents (`intentMatchingFlags`) | Team opted in explicitly | Opt-in only, not default |
| Photo picker pre-selects app-owned photos | App uses photo picker | None — verify selection UX |

---

## Coverage matrix to fill before sign-off

Do not report the gate as passed with blanks. `N/A` is a valid result **with a reason**;
an empty cell is not.

| # | Area | Device (model / API) | targetSdk verified | Nav mode | Result | Evidence |
|---|---|---|---|---|---|---|
| 1 | Edge-to-edge — top insets | | | gesture / 3-button | | screenshot |
| 2 | Edge-to-edge — bottom CTA tappable | | | gesture / 3-button | | screenshot |
| 3 | Predictive back — wizard/back stack | | | | | video |
| 4 | Predictive back — unsaved-data prompt | | | | | video |
| 5 | Rotation on ≥600dp + state retention | | | | | screenshot |
| 6 | Multi-window resize | | | | | screenshot |
| 7 | 16 KB page size — native paths | | | | | logcat |
| 8 | Health permissions grant/deny/revoke | | | | | logcat |
| 9 | Local network under compat flag | | | | | logcat |

---

## Anti-patterns

| Anti-pattern | Why it fails | Do instead |
|---|---|---|
| Testing on an API 35 emulator | Edge-to-edge opt-out still honoured there → false pass | Test on API 36+ |
| Bumping targetSdk without re-running the suite | No build error is produced; defects are runtime-only | Treat the bump as a regression milestone |
| Asserting `isDisplayed()` for inset bugs | An element under the nav bar is still "displayed" | Tap it; screenshot at native resolution |
| Validating back only via `adb input keyevent` | The key event may not be dispatched at all on API 36 | Use a real gesture swipe |
| Testing rotation on a phone AVD | <600dp is unaffected by the change | Use a ≥600dp tablet/foldable AVD |
| Treating an opt-out flag as a fix | `enableOnBackInvokedCallback=false` and the resizability property both expire | Log as deferred work with the expiry (API 37) |
| Reporting "Android 16 passed" | Meaningless without the targetSdk pair | Record device API **and** app targetSdk |

## Related skills

- `android-17-qa-gate` — next gate: targetSdk 37 turns several of these opt-ins into defaults (local-network permission, SMS OTP delay, CT, resizability opt-out removed)
- `android-adb` — the adb command surface used throughout this gate
- `responsive-viewport-testing` — rotation / multi-window layout assertions
- `maestro-mobile` — encoding these checks as repeatable flows
- `state-ripple-verify` — rotation destroys and recreates the activity; verify downstream state
- `qa-bug-report` / `bug-repro-isolation` — isolate device API vs targetSdk before blaming a change

## Sources
- https://developer.android.com/about/versions/16/behavior-changes-16 — behaviour changes for apps targeting API 36: `windowOptOutEdgeToEdgeEnforcement` deprecated+disabled, predictive back default (`onBackPressed()` not called, `KEYCODE_BACK` not dispatched) with temporary `enableOnBackInvokedCallback` opt-out, orientation/resizability/aspect-ratio ignored at ≥600dp with `PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY` opt-out expiring at API 37, `BODY_SENSORS` → `READ_HEART_RATE`, `RESTRICT_LOCAL_NETWORK` compat flag, `elegantTextHeight`, `scheduleAtFixedRate()`, MediaStore version, Safer Intents
- https://developer.android.com/about/versions/16/behavior-changes-all — changes affecting all apps regardless of targetSdk
