---
name: ios-26-test-gotchas
description: |
  Version-specific breakages when running iOS UI tests on iOS 26 with Xcode 26.x — where a test
  suite that passed yesterday fails today because of the toolchain, not the app. Covers the
  Xcode 26.1/26.2 accessibility-tree regression ("No matches found for Descendants matching type
  TabBar"), navigation-bar accessibility IDs disappearing on iOS 26, Accessibility Inspector
  showing an empty hierarchy, and the simulator failing to boot after a macOS upgrade.
  Use when: XCUITest/Appium/Maestro flows suddenly cannot find iOS elements after an Xcode or iOS
  upgrade, the element inspector shows an empty or truncated tree, tab bar / nav bar items are
  invisible to automation, or a simulator refuses to boot on first build after updating macOS.
  Triggers on: "iOS 26", "Xcode 26", "Xcode 26.1", "Xcode 26.2", "No matches found for Descendants",
  "TabBar not found", "accessibility identifier missing iOS 26", "Accessibility Inspector empty",
  "view hierarchy empty", "simulator won't boot", "dyld_shared_cache", "liquid glass test",
  "element không tìm thấy sau khi update Xcode", "test iOS 26 fail".
---

# iOS 26 / Xcode 26.x Test Gotchas

> **Why this skill exists:** After an iOS 26 + Xcode 26.x upgrade, element-not-found failures look
> exactly like ordinary flaky-locator failures — so teams spend hours rewriting perfectly good
> selectors. Several of these failures are **toolchain and accessibility-tree defects**, and no
> selector rewrite can fix them. Identify the class of failure before touching test code.

## Diagnose before fixing

Element-not-found on iOS 26 has three very different root causes. Rewriting locators only helps for
the third one.

```
Test can't find an iOS element
        ↓
Did it pass on the SAME app build with an older Xcode / older iOS?
        ↓
   YES ──────────────────────────────► Toolchain or a11y-tree defect (§1–§3)
        │                               Do NOT rewrite selectors.
        NO
        ↓
Is the element visible in the inspector's tree?
        ↓
   NO ───► a11y tree is broken or element lacks an identifier (§2)
   YES ──► ordinary locator problem → normal debugging
```

**Pin the variables first — never change two at once:**

```bash
xcodebuild -version                    # Xcode + build number
xcrun simctl list runtimes             # which iOS runtimes are installed
xcrun simctl list devices booted       # what is actually booted
sw_vers                                # macOS version
```

Record all four in the bug report. "Fails on iOS 26" without the Xcode version is not reproducible —
these defects are specific to Xcode **26.1/26.2** and absent in 26.0.

---

## 1. Xcode 26.1 / 26.2 — accessibility tree collapses on iOS 26+

**Symptom.** UI tests fail *only* on iOS 26+ (simulator **and** real device) under Xcode 26.1 or
26.2. The identical test code and identical app pass under Xcode 26.0 on the same iOS 26 device,
and pass on iOS 18.x under any of those Xcode versions.

**Representative error:**

```
Failed to tap Button (Element at index 1): No matches found for
Descendants matching type TabBar from input {(Application, pid: 1883)}
```

**Blast radius.** Not limited to tab bars — the view hierarchy itself is broken, so navigation
components and arbitrary descendants can disappear from XCTest queries.

**Root cause (important — this is an APP bug the new toolchain exposes, not purely an Xcode bug).**
Custom view implementations that create **cycles in the SwiftUI attributes graph** break the
accessibility tree that both XCUITest and Accessibility Inspector read. The common trigger is a
custom `TabView` doing OS-version-conditional styling — e.g. a `ZStack` branching on the OS version
to apply iOS 26 Liquid Glass effects.

**Fix.** Refactor the custom view to remove the attribute-graph cycle. This is a dev-side change:
route it to the app team, do not attempt to work around it in the test layer.

**Confirming it is this defect and not your locator:**

| Evidence | Meaning |
|---|---|
| Same test passes under Xcode 26.0, fails under 26.1/26.2 | This defect |
| Fails on iOS 26+, passes on iOS 18.x, same Xcode | This defect |
| Accessibility Inspector also shows an empty tree (§3) | This defect — confirmed at the a11y layer |
| Only one specific element is missing, tree otherwise intact | Ordinary locator problem |

> **Report it as a blocker with the environment matrix.** A "flaky test" label here is wrong and
> costs the team days. This blocks the whole suite on the affected screens.

---

## 2. Navigation-bar accessibility IDs invisible on iOS 26

Accessibility identifiers set on `UIBarButtonItem` (navigation-bar buttons) stopped being exposed
on iOS 26, while working correctly on iOS 18.5.

**Impact.** Any flow that taps a nav-bar action — Save, Close, Edit, Done, Back — by identifier
breaks. This is high-traffic: nav-bar buttons terminate most edit and detail flows.

**What to do:**
1. Confirm against iOS 18.x on the same build. Working there and failing on iOS 26 confirms it.
2. Report to the app team — the durable fix is app-side (setting the identifier on the underlying
   custom view, or supplying an accessibility label).
3. Only then consider a test-side fallback (matching by label text), and mark it explicitly as a
   temporary workaround tied to this defect, not as the permanent locator.

> ⚠️ Falling back to label text quietly makes the suite **locale-dependent** and brittle. If you do
> it, log it as tech debt with the defect reference — do not let it silently become the standard.

---

## 3. Accessibility Inspector shows an empty hierarchy

With Xcode 26.2, Accessibility Inspector fails to display the view hierarchy for iOS 26+, though it
worked across all devices and OS versions under Xcode 26.0.

**Use this as a diagnostic instrument, not just an annoyance.** If the Inspector *also* sees
nothing, the accessibility tree is genuinely broken — the problem is not your XCUITest query.

**Verify your instrument before trusting a "no elements" result** (an empty tree is the single most
misleading test output there is — it looks like "the screen is empty" when it means "I cannot see"):

1. Open the Inspector against a **known-good** app/screen on the same simulator.
   - Tree renders → the instrument works; the failure is specific to your app → §1.
   - Tree empty there too → the instrument is broken → switch tools before concluding anything.
2. Cross-check with a second tool that reads the same tree — `maestro studio`, Appium Inspector, or
   `xcrun simctl ui`. Agreement across two independent readers is what makes the finding real.

---

## 4. Simulator fails to boot after a macOS upgrade

**Symptom.** The first build after upgrading macOS fails; the simulator never boots.

**Workaround — refresh the dyld shared cache before booting:**

```bash
xcrun simctl runtime dyld_shared_cache update --all
xcrun simctl boot "iPhone 17 Pro"
xcrun simctl bootstatus <UDID> -b        # wait until fully booted
```

Add this to CI provisioning on any runner whose macOS image was just updated — otherwise the first
pipeline run after an image bump fails for reasons unrelated to the code under test.

Other post-upgrade cleanup, in increasing order of destructiveness:

```bash
xcrun simctl shutdown all
xcrun simctl erase <UDID>              # wipes ONE simulator's data
xcrun simctl delete unavailable        # removes runtimes Xcode can no longer use — safe
```

> `xcrun simctl erase all` wipes **every** simulator's data, including any signed-in state or
> fixtures other suites depend on. Prefer erasing a specific UDID. Check what is booted first.

---

## 5. Toolchain compatibility constraints

| Constraint | Consequence for the test plan |
|---|---|
| Xcode 26 requires macOS Sequoia 15.4+ | CI runner images must be upgraded together with Xcode |
| Xcode 26 supports on-device debugging for iOS 16+ only | Apps built with Xcode 26 will not run on iOS 15 and below — drop those from the device matrix or keep an older Xcode runner |
| iOS UI tests need macOS + Xcode | No supported way to run them on Linux or Windows hosts — a Windows workstation must use a macOS CI runner or a real-device cloud |

---

## 6. Simulator vs real device — what a simulator pass does NOT prove

Simulators are correct for functional flows and CI throughput, but they do not represent real
hardware behaviour. **Never** sign off these on a simulator alone:

| Area | Why the simulator lies |
|---|---|
| Biometrics (Face ID / Touch ID) | Simulated enrolment only; real failure/fallback paths differ. iOS 26 Face ID handling in particular needed tuning for automation |
| Camera / photo capture | Synthetic camera; camera-roll permission alerts differ on iOS 26 |
| Performance / launch time / jank | Runs on host CPU — numbers are meaningless |
| NFC, GPS, cellular, push, background modes | Not faithfully represented |
| Memory pressure, thermal throttling | Absent |

**Tiered approach:** run the bulk of the suite on simulators for speed; run a critical subset on
real devices on a slower cadence. State clearly in the report which tier produced each result.

```bash
# Simulator biometric controls (for the happy path only)
xcrun simctl privacy <UDID> grant  all <bundle-id>
xcrun simctl privacy <UDID> revoke all <bundle-id>
```

---

## Post-upgrade regression checklist

Run this after **any** Xcode or iOS runtime bump, before blaming the test suite:

- [ ] Record `xcodebuild -version`, `sw_vers`, `simctl list runtimes` — pin the environment
- [ ] Re-run one **known-good** flow that passed pre-upgrade (control run — this is what separates
      "toolchain broke" from "our change broke it")
- [ ] Open Accessibility Inspector on a known-good app → is the instrument itself healthy? (§3)
- [ ] Cross-check the tree with a second reader (Maestro Studio / Appium Inspector)
- [ ] Check nav-bar-identifier flows specifically (§2)
- [ ] Check tab-bar / custom-container flows specifically (§1)
- [ ] If failures are iOS-26-only, test the same build on iOS 18.x to confirm the version boundary
- [ ] If failures are Xcode-26.1/26.2-only, test under 26.0 to confirm the toolchain boundary
- [ ] Only after all the above: consider that the app or the test is at fault

---

## Anti-patterns

| Anti-pattern | Why it fails | Do instead |
|---|---|---|
| Rewriting selectors after an Xcode upgrade | The tree is broken; no selector can match a node that isn't exposed | Run the control (§ checklist) first |
| Marking these failures "flaky" and retrying | Deterministic toolchain defects — retries burn CI time and hide a blocker | Report as a blocker with the version matrix |
| Concluding "screen has no elements" from an empty tree | Empty output usually means the reader is broken, not the screen | Verify the instrument on a known-good app |
| Reporting "fails on iOS 26" | Not reproducible — 26.0 vs 26.1/26.2 behave differently | Always include Xcode build + iOS version + device type |
| Permanently switching nav-bar locators to label text | Silently makes the suite locale-dependent | Temporary workaround only, logged as debt |
| Signing off biometrics/camera on a simulator | Those paths are simulated, not real | Run that subset on a real device |
| Changing Xcode and iOS runtime in one step | Cannot attribute the failure to either | Change one variable at a time |

## Related skills

- `ios-xcrun` — the `simctl` command surface used here
- `maestro-real-ios-device` — moving the critical subset onto physical iPhones
- `maestro-studio` / `maestro-element-harvest` — the second independent tree reader used in §3
- `playwright-diagnosis-first` — the general diagnose-before-fixing discipline this follows
- `bug-repro-isolation` — one variable at a time before claiming a cause
- `ask-when-stuck` — stop after 1–2 failed attempts rather than rewriting locators a third time
