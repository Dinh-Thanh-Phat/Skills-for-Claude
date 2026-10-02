---
name: maestro-mobile
description: |
  Complete Maestro mobile test automation skill for iOS and Android. Use this skill when:
  writing Maestro YAML test flows, debugging flaky Maestro tests, setting up Maestro on CI/CD
  (GitHub Actions, GitLab CI), integrating with Maestro Cloud or BrowserStack, handling timing/
  animation issues, composing flows with runFlow, using conditional logic, writing cross-platform
  tests, or any mobile E2E automation task with Maestro.

  Trigger on: "maestro test", "write mobile test", "maestro flow", "maestro yaml", "mobile E2E",
  "maestro cloud", "flaky mobile test", "maestro CI", "test iOS and Android", maestro run,
  maestro record, or when someone needs to automate mobile app interactions.
---

# Maestro Mobile Testing

Maestro is a declarative YAML framework for mobile E2E testing — no WebDriver, no complex setup.
One YAML file runs on both iOS and Android. Built-in retry tolerance makes it far less flaky than
Appium for most use cases.

## 🚦 MANDATORY gate — do this BEFORE writing/running ANY flow, on ANY project

This is not optional background reading. Skipping it is what made both TetherTails and Soundwise
slow — evidence, not theory:

- **TetherTails** (measured 2026-09-21 by grep, NOT assumed): only 5 of 82 flows do
  `launchApp: {clearState: true}` + OTP-login `runFlow` (all in `flows/petmgmt/`, the delete/edit
  flows that need a different account); the other 56 already use `clearState: false` = warm session.
  So the suite's flow design was mostly fine — the recurring slowness there came from element
  discovery and whole-suite reruns, not from per-flow login. clearState+login is still a ~30-40s tax
  per flow that uses it, so don't add more of them.
- **Soundwise**: element discovery was done as 338 separate `adb shell uiautomator dump` + `pull`
  round-trips, one screen at a time, instead of one `maestro hierarchy`/Studio harvest pass — and
  failing sections got **re-run whole** (3×, 3×, 2×) instead of retesting only the failed IDs.

Both projects hit exactly the failure modes these skills already exist to prevent. The fix isn't
"remember better" — it's **stop and do these 4 checks before the first flow/dump of any new
suite**, on every project, no exception:

| # | Do this first | Detail below |
|---|---|---|
| 0 | `ls`/glob `flows/**/*.yaml` for an existing flow covering this scenario — extend/reuse it | ↓ |
| 1 | For a module with no `ELEMENT_MAP_<module>.md` yet: one pass, nav + full hierarchy dump together, per screen. Reuse the saved map forever after — never re-dump a mapped screen "to be safe" | ↓ |
| 2 | Group flows by auth state — one login/session via `runFlow` attach, not `launchApp+clearState` per flow | ↓ |
| 3 | A failure → rerun only that flow/ID, never the whole suite/section | ↓ |
| 4 | Never `maestro test flows/<folder>` across MULTIPLE modules/accounts in one invocation — see below | ↓ |

0. **Check for already-saved flows FIRST, across sessions — not just within one.** TetherTails:
   user asked "have you saved the automation script so next time you just run it" **3 separate
   times** across different sessions (24-Aug, 27-Aug, 03-Sep) — meaning flows kept getting
   re-authored/re-discovered from scratch instead of being found and reused. Before writing ANY new
   flow: `ls`/glob the project's flows directory (e.g. `app-automation/flows/**/*.yaml`,
   `*/automation/`) for one that already covers the scenario. Extend/re-run it; only author new when
   nothing already exists. This is a session-to-session persistence check, distinct from #1 below
   (which is about not re-discovering elements *within* one session).
1. **Onboarding a module you haven't harvested yet (check per-MODULE, not per-project — a project
   having `ELEMENT_MAP_A.md` says nothing about whether module B is covered): one single pass that
   does navigation + FULL element harvest together, not two separate passes.** Walk every screen/tab
   of that module once; at each screen, before moving on, dump the FULL hierarchy right there
   (`maestro hierarchy` or Studio Inspector) — don't just note the nav path and move on. **Why merge
   them:** the expensive part is getting to that screen (login/navigate, ~30-40s), not the dump itself
   (near-zero marginal cost once you're already there) — so harvesting every element on every screen
   you naturally pass through costs almost nothing extra over just mapping navigation, and skipping it
   means paying full login/navigate again later just to get the elements you skipped. This does NOT
   mean recursively chasing every possible modal/edge-state/permission×tier combination — that
   requires deliberately engineering a state, which IS expensive; only harvest what you land on
   naturally while walking the module's main flows.

   **Two different outputs go to two different places — don't conflate them:**
   - Element/selector data → `ELEMENT_MAP_<module>.md` in the project's automation folder (project-
     local; this is what flows are authored from).
   - Any business-logic quirk you notice along the way (permission behavior, env facts like "staging
     doesn't charge money," anything a human would otherwise have to re-explain) → append it to
     `knowledge/[slug].md` (`~/.claude/shared-context/knowledge/`), NOT into the ELEMENT_MAP file —
     that's the file `qa-session-start` actually reads at the top of a session; a quirk buried only in
     an ELEMENT_MAP is invisible to that lookup and gets re-asked later (see the registry/knowledge
     gap fixed earlier — don't recreate a second, undiscoverable copy of that same problem).

   **The ELEMENT_MAP output MUST be reused on every future run — never re-harvested from scratch.**
   Before writing or running ANY flow for a module, on ANY session — including a brand new session
   days later — `ls`/glob for that module's `ELEMENT_MAP*.md`/`*AUTOMATION_MAP*.md` FIRST and read it;
   only dump again if the specific element you need genuinely isn't in it (UI changed, or that screen
   wasn't covered in the original pass). Re-harvesting an already-mapped screen "just to be safe"
   every run is exactly the waste this gate exists to prevent — trust the saved file until it's proven
   stale (an element it documents no longer matches).
2. **Group flows by auth state before writing them** — `maestro-auth-state-strategy`. One login per
   account/session, chain everything that account needs via `runFlow` attach (no `launchApp`/
   `clearState`) instead of a fresh login per flow. If you're about to write a flow that starts with
   `launchApp: {clearState: true}` + a login `runFlow`, stop and check whether it can instead attach
   to an already-logged-in session.
3. **Never re-run a whole suite/section to retest a few failures** — `feedback_test-rerun-discipline`
   / canary pattern. Re-run only the specific failed IDs/flows; a full-section rerun to confirm 2
   fixed cases wastes the same login+navigate cost as the original run, times however many cases
   already passed.
4. **Never `maestro test flows/<folder>` across multiple modules/accounts in one invocation.**
   Measured on TetherTails (2026-09-22): batching all 8 remaining modules (57 flows) as 8 sequential
   `maestro test flows/<module>` folder-runs produced 49 "FAILED" results that were almost entirely
   **not real** — traced via screenshot + `maestro hierarchy` to two mechanical causes:
   - Folder-mode drops each flow's `-e` params (`${PET_NAME}` etc.) — any flow with no env default
     taps on an empty string and fails. Confirmed on ~14 flows.
   - **Account-bleed**: one flow inside the batch did its own `clearState:true` + login to a
     *different* account; every subsequent flow in the batch that assumed `clearState:false`
     (continue with whatever session is already active — correct in isolation) silently inherited
     the wrong account, so fixed seed-pet names the flow author wrote for *that* flow's specific
     account weren't visible under the one actually logged in. This is exactly what step #2 above
     (group by auth state) exists to prevent, and folder-batching across modules violates it even
     though each individual flow is written correctly.
   Rule: run flows individually with their required `-e` params, or batch ONLY flows already
   verified to share both (a) no unmet env requirement and (b) the same required logged-in account.
   A 49-failure result from a mixed-module folder run is a methodology signal, not a bug report —
   verify the actually-logged-in account (`maestro hierarchy` → look for the account-name label) and
   check for missing `-e` before reporting any of it as an app defect.

If a task looks like it'll produce more than ~5 flows or touch more than 1 account, this gate is not
skippable — say explicitly which of the 5 you applied before starting.

## Tap says COMPLETED but nothing changed / "element not found" right after launch — check for an overlay FIRST

Measured on TetherTails (2026-09-21): 0/3 pass -> 3/3 after one fix. A cold-start **announcement/promo
overlay** appeared 1-3s AFTER `launchApp` returned and covered the tab bar. `tapOn` reported COMPLETED
(Maestro tapped the right bounds — the overlay swallowed it), and a later `assertVisible` failed.
Upgrading Maestro did not help; the selector was never the problem. Diagnose in this order, don't
retry-loop:
1. Screenshot at t=1s/3s/10s after `adb shell am force-stop <pkg>` + launch — look at what is actually
   on screen (a popup that is still there at 10s is not an animation).
2. Isolate the tool: `adb shell input tap <x> <y>` on the same spot. If that works, the app and the
   target are fine and something is covering/swallowing Maestro's tap.
3. Fix with ONE reusable helper (`_setup/dismiss-popups.yaml`) called right after `launchApp` (or after
   login when the popup only shows post-login): `extendedWaitUntil visible: <overlay label>, optional`
   (it arrives late), then `runFlow: when: visible: <overlay label>` -> tap its close by point. Key the
   guard on the overlay's own semantic label found via `maestro hierarchy` (e.g. a View labelled
   "Announcements"), not on decorative text like a badge ("PROMO" vs "UPDATE" differ per announcement),
   and confirm that label appears on no normal screen so the guarded tap can never hit real UI.

## Quick Start

```bash
# Install
curl -Ls "https://get.maestro.mobile.dev" | bash

# Run a flow
maestro test flow.yaml

# Run with environment variables (for cross-platform)
maestro test --env APP_ID=com.example.app login-flow.yaml

# Run entire folder — ONLY when every flow in it needs no missing -e param AND shares the same
# required logged-in account. See gate #4 above before doing this across modules.
maestro test flows/

# Record a new flow interactively
maestro record flow.yaml
```

## YAML Anatomy

```yaml
# flows/login.yaml
appId: com.example.app          # required — bundle ID (iOS) or package (Android)
---
- launchApp                     # fresh launch, clears state
- tapOn: "Email"                # tap element by text or accessibility ID
- inputText: "user@example.com"
- tapOn: "Password"
- inputText: "secret123"
- tapOn: "Login"
- assertVisible: "Welcome"      # hard assertion — fails immediately if not found
```

## launchApp & Permissions

Permission dialogs are the most common cause of "the flow worked yesterday" failures — a single
unhandled OS prompt blocks every subsequent step. Decide permissions at launch instead of tapping
system dialogs:

```yaml
- launchApp:
    appId: "com.example.app"
    clearState: true            # wipe app data — fresh user every run
    clearKeychain: true         # iOS: also drop stored credentials
    stopApp: false              # skip the kill+restart when you only need a foreground
    permissions:
      all: deny                 # deny everything, then grant what the flow needs
      notifications: allow
      android.permission.ACCESS_FINE_LOCATION: allow
    arguments:
      featureFlagX: true        # passed to the app at launch
```

Values are `allow`, `deny`, or `unset`. `all` sets a baseline that the more specific keys override.

**Test the denied path too.** `all: deny` is the more valuable default: it exercises what users who
refuse permissions actually see. A suite that only ever grants everything never covers the
permission-denied branch — and that branch is where crashes hide.

### Variables in permission values (Maestro 2.8.0+)

```yaml
env:
  LOCATION_PERM: deny
---
- launchApp:
    appId: "com.example.app"
    permissions:
      android.permission.ACCESS_FINE_LOCATION: ${LOCATION_PERM}
```

This lets one flow cover both branches from CI instead of duplicating the file — run it twice with
`LOCATION_PERM=allow` and `LOCATION_PERM=deny`.

> `clearState: true` also clears the login session. If a flow assumes a logged-in user, either log
> in inside the flow or omit `clearState` — see the auth-state grouping strategy in the
> `maestro-auth-state-strategy` notes rather than paying a full login on every flow.

## Element Selection (Priority Order)

Use the most stable selector available, in this order:

| Selector | Example | Notes |
|----------|---------|-------|
| `id:` | `id: login-btn` | Best — accessibility ID, survives text changes |
| `text:` | `text: Login` | OK for unique text, breaks with i18n |
| `label:` | `label: "Submit form"` | iOS accessibilityLabel / Android contentDescription |
| `contains:` | `contains: "Welcome"` | Partial text match |
| Below/above/leftOf/rightOf | `below: "Email"` | Relative positioning |

```yaml
# Prefer accessibility IDs for stability
- tapOn:
    id: "login-button"

# Use contains for dynamic text
- assertVisible:
    text: "Order #"
    contains: true

# Relative positioning for unlabeled elements
- tapOn:
    below: "Email"
    above: "Login"
```

## Full Command Reference

See [references/commands.md](references/commands.md) for the complete command list.
Key commands: `tapOn`, `inputText`, `scrollUntilVisible`, `swipe`, `assertVisible`,
`assertNotVisible`, `waitForAnimationToEnd`, `runFlow`, `condition`, `repeat`, `takeScreenshot`.

## Handling Flakiness (Most Common Pain Points)

### 1. Animations — Always the Culprit

```yaml
# ❌ Bad: taps during animation
- tapOn: "Confirm"

# ✓ Good: wait for UI to settle
- waitForAnimationToEnd
- tapOn: "Confirm"

# ✓ Also good: waitForAnimationToEnd with timeout (ms)
- waitForAnimationToEnd:
    timeout: 3000
```

### 2. Smart Retry Logic cho Network Flakiness

Maestro auto-retry ~5s mặc định. Mạng chậm hoặc staging API không ổn định cần chiến lược rõ ràng hơn.

**Tầng 1 — CLI retry (đơn giản nhất, áp dụng cả flow)**

```bash
# Retry toàn bộ flow khi thất bại (tối đa 2 lần)
maestro test --retry-on-failure 2 flows/

# Hoặc trong CI script
maestro test --retry-on-failure 2 --format junit --output results.xml flows/
```

**Tầng 2 — Assertion timeout (chờ API response cụ thể)**

```yaml
# Tăng timeout cho màn hình cần API call chậm
- assertVisible:
    id: "dashboard__content"
    timeout: 20000          # 20s cho slow staging API

# Chờ loading indicator BIẾN MẤT trước khi tương tác
- assertNotVisible:
    id: "loading-spinner"
    timeout: 15000
- tapOn:
    id: "checkout__confirm-button"
```

**Tầng 3 — Conditional retry pattern (retry từng bước)**

```yaml
# Pattern: thử tap, nếu thất bại thì refresh và thử lại
- repeat:
    while:
      notVisible:
        id: "orders__list-item"
    maxRepeat: 3
    commands:
      - tapOn:
          id: "orders__refresh-button"
      - waitForAnimationToEnd
      - assertVisible:
          id: "loading-spinner"
          visible: false
          timeout: 8000
```

**Tầng 4 — Network error recovery (xử lý "No connection" dialog)**

```yaml
# Xử lý lỗi mạng ngay trong flow — không để test fail vì dialog bất ngờ
- condition:
    visible: "No internet connection"
  if:
    - tapOn: "Retry"
    - waitForAnimationToEnd:
        timeout: 5000
  # Tiếp tục flow bình thường sau khi retry

# Pattern hoàn chỉnh cho flow quan trọng
- tapOn:
    id: "payment__submit-button"
- condition:
    visible: "Connection error"
  if:
    - takeScreenshot: "network-error-occurred"
    - tapOn: "Try Again"
    - assertVisible:
        id: "payment__success-confirmation"
        timeout: 20000
  else:
    - assertVisible:
        id: "payment__success-confirmation"
        timeout: 10000
```

**Tầng 5 — Flaky test detection (chạy nhiều lần để xác định)**

```bash
# Chạy 5 lần để phát hiện test flaky (pass rate < 100% = vấn đề)
for i in {1..5}; do
  maestro test flows/checkout.yaml --format junit \
    --output "results-run-$i.xml" && echo "Run $i: PASS" || echo "Run $i: FAIL"
done
```

**Config file cho retry mặc định**

```yaml
# .maestro/config.yaml — áp dụng cho tất cả flows trong project
env:
  APP_ID: com.example.app
  # Timeout mặc định cho assertion (ms) — tăng nếu staging API chậm
  MAESTRO_DRIVER_STARTUP_TIMEOUT: 60000
```

### 3. Keyboards Blocking Elements

```yaml
- tapOn: "Username"
- inputText: "user@test.com"
- hideKeyboard          # dismiss before tapping next element
- tapOn: "Next"
```

### 4. Conditional / Optional Elements (e.g., Permission Dialogs)

```yaml
- condition:
    visible: "Allow"    # iOS permission prompt
  if:
    - tapOn: "Allow"
  else:
    - takeScreenshot: "no-prompt-appeared"
```

## Expo / React Native: testID Cross-Platform

Expo và React Native dùng prop `testID` để gắn ID cho elements. Đây là cách duy nhất đảm bảo
selector nhất quán giữa iOS và Android trong Maestro.

### Cách testID hoạt động trên từng platform

| Platform | testID map sang | Maestro selector |
|----------|----------------|------------------|
| iOS | `accessibilityIdentifier` | `id: "my-button"` |
| Android | `resource-id` (dạng `com.example.app:id/my-button`) | `id: "my-button"` |

Maestro tự normalize resource-id — chỉ cần dùng phần cuối, không cần package prefix.

### Gắn testID đúng cách trong Expo

```tsx
// ✓ Đúng — testID trực tiếp trên native element
<TouchableOpacity testID="login-button" onPress={handleLogin}>
  <Text>Login</Text>
</TouchableOpacity>

// ✓ Đúng — trên Text, TextInput, View
<TextInput testID="email-input" placeholder="Email" />
<Text testID="welcome-message">Welcome!</Text>

// ❌ Sai — testID trên custom component không forward prop
<MyButton testID="login-button" />    // bị mất nếu MyButton không forward testID
```

```tsx
// Fix cho custom components — forward testID đến native element bên trong
interface MyButtonProps {
  testID?: string;
  onPress: () => void;
  label: string;
}

const MyButton = ({ testID, onPress, label }: MyButtonProps) => (
  <TouchableOpacity testID={testID} onPress={onPress}>
    <Text>{label}</Text>
  </TouchableOpacity>
);
```

### Naming Convention cho testID

Dùng kebab-case, mô tả vị trí + loại element:

```
screen-name__element-description
auth__login-button
auth__email-input
checkout__confirm-order-button
cart__item-count-badge
profile__avatar-image
```

### Dùng trong Maestro

```yaml
# ✓ Luôn dùng id: thay vì text: cho stability
- tapOn:
    id: "auth__login-button"

- assertVisible:
    id: "checkout__confirm-order-button"

- inputText: "user@test.com"
  element:
    id: "auth__email-input"
```

### Kiểm tra testID trên device

```bash
# iOS — xem accessibility tree (Maestro Inspector)
maestro studio

# Android — dump UI hierarchy
adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml
# Tìm resource-id trong file XML

# iOS — xem trong Accessibility Inspector (Xcode)
# Xcode → Open Developer Tool → Accessibility Inspector
```

> Xem chi tiết và troubleshooting tại [references/expo-testids.md](references/expo-testids.md)

---

## Cross-Platform Tests

Same YAML, different appId. Pass at runtime:

```bash
# iOS
maestro test --env APP_ID=com.example.app --env PLATFORM=ios flows/

# Android
maestro test --env APP_ID=com.example.app --env PLATFORM=android flows/
```

```yaml
# flows/login.yaml — uses env var for appId
appId: ${APP_ID}
---
- launchApp
- tapOn: "Login"
```

Platform-specific branches when needed:

```yaml
- condition:
    platform: iOS
  if:
    - tapOn: "Allow Notifications"   # iOS only dialog
```

## Flow Composition (Reusability)

Break flows into small, focused pieces. Each flow = one user intent.

```yaml
# flows/_setup/login.yaml — reusable login helper
appId: ${APP_ID}
---
- launchApp
- tapOn:
    id: email-input
- inputText: ${USER_EMAIL}
- tapOn:
    id: password-input
- inputText: ${USER_PASSWORD}
- tapOn:
    id: login-btn
- assertVisible: "Dashboard"
```

```yaml
# flows/checkout.yaml — imports login
appId: ${APP_ID}
---
- runFlow:
    file: _setup/login.yaml
    env:
      USER_EMAIL: test@example.com
      USER_PASSWORD: secret
- tapOn: "Shop"
- scrollUntilVisible:
    element:
      text: "Add to Cart"
- tapOn: "Add to Cart"
- assertVisible: "Cart (1)"
```

## Gestures

```yaml
# Swipe directions
- swipe:
    direction: UP        # UP / DOWN / LEFT / RIGHT
    duration: 500        # ms, default 400

# Swipe anchored to an element (PREFERRED — survives layout changes)
- swipe:
    from:
      id: "feeditem_identifier"
    direction: LEFT

# Swipe from a specific point INSIDE an element (Maestro 2.8.0+)
- swipe:
    from:
      text: "Desired card text"
      point: "50%, 85%"    # % of the ELEMENT's own bounds, not the screen
    direction: LEFT
# Omit `point` and the swipe starts from the element's CENTER.
# Absolute pixel offsets from the element's top-left also work: point: "25, 75"

# Precise swipe (screen coordinates) — brittle across devices, last resort
- swipe:
    start: 90%, 50%
    end: 10%, 50%

# Long press
- longPressOn: "Delete"

# Double tap
- doubleTapOn: "Image"

# Scroll to bottom
- scroll:
    direction: DOWN

# Drag
- drag:
    start: { x: 100, y: 400 }
    end: { x: 300, y: 400 }
```

### Choosing a swipe form

Prefer in this order — each step down trades reliability for control:

1. `direction` alone — whole-screen scroll
2. `from: <selector>` — anchored to an element, survives layout shifts
3. `from: <selector>` + `point` — anchored *and* precise (2.8.0+)
4. `start`/`end` screen coordinates — **last resort**, breaks on any other screen size

> **2.11.0 breaking:** `start`/`end` are valid ONLY directly under `swipe` (and `drag`). Putting
> them inside an element selector — e.g. `tapOn: { start: "50%,50%" }` or under `from:` — used to be
> **silently ignored** (the tap hit the element centre or the wrong place and the flow still
> "passed"); it is now a hard error. If an old flow starts failing on parse after upgrading, grep
> it: `grep -rnE "^\s+(start|end):" flows/` and check each hit's parent is `swipe`/`drag`.

**When `point` is the fix.** Element-anchored swipes start at the element's center. That silently
fails when the center sits on top of something that swallows the gesture — a nested scroll view, an
embedded map, an image carousel inside a card, or a button. The classic symptom is a swipe-to-delete
or carousel test that "does nothing" while the selector clearly matched. Before 2.8.0 the only
escape was screen coordinates; now anchor to the element and move the start point into a dead zone:

```yaml
# Swipe-to-delete on a card whose centre hosts a nested carousel
- swipe:
    from:
      id: "order-card"
      point: "50%, 90%"   # bottom strip of the card — below the carousel
    direction: LEFT
```

> Don't reach for `point` first. If a plain `from:` swipe works, adding a point only makes the flow
> sensitive to the element's internal layout.

## Scripts (JavaScript for Dynamic Logic)

```yaml
- runScript:
    file: scripts/generate-email.js
    env:
      PREFIX: "qa"
    outputVars:
      EMAIL: result.email
      TIMESTAMP: result.timestamp
- inputText: ${EMAIL}
```

```javascript
// scripts/generate-email.js
var timestamp = Date.now();
output.email = params.PREFIX + '-' + timestamp + '@test.com';
output.timestamp = timestamp;
```

## Repeat / Loops

```yaml
# Run 5 times
- repeat:
    times: 5
    commands:
      - tapOn: "Next"
      - waitForAnimationToEnd

# Repeat while condition
- repeat:
    while:
      notVisible: "End of List"
    commands:
      - scroll:
          direction: DOWN
```

## Screenshots & Artifacts

```yaml
- takeScreenshot: "before-checkout"    # saves to test-artifacts/
- startRecording
- tapOn: "Checkout"
- stopRecording                         # saves video
```

### Automatic Per-Step Screenshots + Failure Hierarchy (2.7.0)

You no longer need explicit `takeScreenshot` calls just to debug a failure: as of CLI 2.7.0,
Maestro captures a screenshot **before every step automatically**, and on a failing step it also
captures the full view hierarchy alongside that screenshot — so a CI failure gives you the exact
visual + element-tree state at the point of failure without adding instrumentation to the flow.
The output bundle itself was also revamped into a leaner, flat structure with a manifest
(`readable step names`, device logs, and crash/ANR reports all in one place) instead of the older
nested-per-flow layout — worth knowing if you have tooling that parses the artifacts directory
structure directly, since paths changed.

Android also gained **native (SIGSEGV) crash detection** in 2.7.0 — previously Maestro only
detected JVM-level crashes, so a native-library segfault (common in apps with native/NDK code,
e.g. video/camera/ML SDKs) could silently kill the app under test without Maestro surfacing it as
a crash in the report. Explicit `takeScreenshot`/`startRecording` calls are still worth keeping
for narrative bug-repro captures (e.g. a specific before/after pair to attach to a bug report) —
the automatic per-step capture is for *debugging why a step failed*, not for producing a curated
artifact set.

## CI/CD Integration

See [references/ci-cd.md](references/ci-cd.md) for full GitHub Actions and GitLab CI examples.

### GitHub Actions (minimal)

```yaml
- name: Run Maestro tests
  uses: mobile-dev-inc/maestro-github-action@v1
  with:
    api-key: ${{ secrets.MAESTRO_CLOUD_API_KEY }}
    app-file: app.apk          # or app.app for iOS
    flows-dir: flows/
```

### Local CI (no cloud)

```yaml
# .github/workflows/maestro.yml
- name: Install Maestro
  run: curl -Ls "https://get.maestro.mobile.dev" | bash

- name: Boot Android Emulator
  uses: reactivecircus/android-emulator-runner@v2
  with:
    api-level: 33
    script: maestro test flows/

- name: Run Tests
  run: |
    maestro test --format junit --output test-results.xml flows/
```

## Directory Structure (Recommended)

```
mobile-tests/
├── flows/
│   ├── _setup/
│   │   ├── login.yaml        # reusable helpers (prefix _ to exclude from direct run)
│   │   └── seed-data.yaml
│   ├── auth/
│   │   ├── login.yaml
│   │   └── forgot-password.yaml
│   ├── checkout/
│   │   └── full-checkout.yaml
│   └── smoke.yaml            # quick health check
├── scripts/
│   └── generate-data.js
└── .maestro/
    └── config.yaml           # default env vars
```

```yaml
# .maestro/config.yaml
env:
  APP_ID: com.example.app
  API_URL: https://staging.api.example.com
```

## Common Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Element not found: "Login"` | Text changed or animation in progress | Add `waitForAnimationToEnd`, use `id:` selector |
| Tap hits wrong element | Multiple matches | Combine selectors: `text: + below:` |
| Test passes locally, fails CI | Emulator slower on CI | Increase `timeout:` on assertions |
| Keyboard covers element | Soft keyboard showing | Add `hideKeyboard` before next tap |
| App relaunches mid-flow | `launchApp` in runFlow resets | Use `clearState` instead of `launchApp` in sub-flows |
| Video recording empty | Stopped too early | Add `waitForAnimationToEnd` before `stopRecording` |
| `uiautomator dump` returns near-empty tree | React Native / Expo renders to canvas — no native testIDs | Use `maestro hierarchy` (a11y tree, shows RN `testID`→`id`), not adb uiautomator |
| `assertVisible: "X"` fails though "X" is on screen | Maestro matches the element's **whole** text; node is e.g. "First Last" not "Last" | Use regex for substring: `assertVisible: ".*X.*"` |
| Assert/tap matches the search box, not the result | Typing into a search input makes the box **echo** your text → it matches your selector | Target the result relatively: `text: "X"` + `below: { id: search-input }` — never assert the bare typed text |
| `device offline` / `unauthorized` mid-run | USB drops when screen locks (esp. Samsung) | `adb reconnect && adb wait-for-device`; `stay_on_while_plugged_in 3`; keep phone unlocked |
| System autofill dialog (Samsung Pass / Google) blocks login | OS offers to save creds, steals focus after typing password | Disable before run: `adb shell settings put secure autofill_service null` (restore after) |

### ⚠️ Verify the OUTCOME, not just the tap (fail-loud)

A login flow that only types + taps Submit + `takeScreenshot` **passes even when login fails** —
the taps "complete" regardless, hiding broken auth (wrong creds, backend change). Assert the
post-action state was actually reached:

```yaml
- tapOn: { id: login-submit-button }
# ❌ shallow: just a screenshot → green even on "Invalid credentials"
# ✓ fail-loud: prove you reached Home
- assertVisible: "HELLO"      # a Home text / testID / tab
- assertVisible: "CRM"
```

Put this in the **shared login helper** so every flow that logs in fails loudly when auth breaks.
Same rule for create/edit/delete — assert the record actually appears/changes, don't trust that the
tap "worked". Cross-ref `outcome-verification`, `soft-assertion-ban`.

## Maestro AI Commands (`assertWithAI`, `extractTextWithAI`)

Maestro 1.40+ ships AI commands that read the screen with an LLM. Use when traditional
selectors can't reach the element (canvas, custom-drawn UI, dynamic text):

```yaml
- assertWithAI: "The order confirmation page is visible with order number"
- extractTextWithAI:
    prompt: "Extract the order number from the confirmation"
    outputVariable: ORDER_NUMBER
```

**Use sparingly** — AI calls are slow (2-5s) and incur cost. Prefer testID/role first;
fall back to AI only when no stable selector exists.

## Speed Optimisation (vs `waitForAnimationToEnd`)

Per `reference_maestro-speed-optimization` memory — Maestro speeds up 3-5× when:
1. Disable animations via adb BEFORE launching tests (see `android-adb` script)
2. **Skip `waitForAnimationToEnd`** if animations are off (it does nothing then, but adds tiny overhead)
3. Use **`id:` selectors** (resource-id) over text — text-matching is slower
4. Skip `clearState` if not needed — uninstall/reinstall is overkill

Apply animation-disable globally: `adb shell settings put global window_animation_scale 0`.

## Deep-Link Verification

After `openLink:`, verify the destination — don't trust that the link "fired":
```yaml
- openLink: "myapp://product/123"
- assertVisible:
    id: "product__detail-screen"
    timeout: 10000
- assertVisible:
    text: "Product 123"
```

## Biometric / Fingerprint Mock

```bash
# Android — auth-success via adb broadcast
adb shell am broadcast -a com.android.internal.intent.action.FINGERPRINT_AUTH_SUCCEEDED

# iOS Simulator — simulate Face ID success
xcrun simctl spawn booted notifyutil -p com.apple.LocalAuthentication.evaluation.success
```

(Test infra setup — verify with the dev/SRE team for your actual app.)

## Validate Flow Syntax Before Running (`maestro check-syntax`)

Lint a flow's YAML without booting a device or app — catches typos/indentation errors in seconds, useful as a pre-commit hook or a fast first CI step before the slower device-backed `maestro test` run:

```bash
maestro check-syntax flows/checkout.yaml
maestro check-syntax flows/          # whole directory
```

```yaml
# .github/workflows/maestro.yml
- name: Lint Maestro flows
  run: maestro check-syntax flows/    # fails fast on bad YAML, before spinning up an emulator
- name: Run Maestro tests
  run: maestro test flows/
```

## More CLI Utility Commands & Flags (1.39–1.40)

Also uncovered by any existing Maestro skill:

> **Discontinued in 2.7.0:** `maestro chat` was removed — the CLI now points users at Maestro MCP
> (see the `maestro-viewer` skill) for the same "ask an agent about a failing flow" workflow,
> since an MCP-connected coding agent can inspect the live hierarchy and fix selectors directly
> instead of a terminal-only chat loop. Kept below for historical/pre-2.7.0 reference.

```bash
# Interactive AI chat for building/debugging a flow from the terminal, no editor round-trip
maestro chat
maestro chat --ask="why does this flow fail on the login step?"

# Reinstall the xctestrunner driver before this run — fixes stale-driver flakiness on iOS
# without a manual `maestro cleanup` + reinstall dance
maestro test --reinstall-driver flows/ios/

# Target a specific iOS minor version / device model instead of "whatever booted simulator"
maestro test --device-os "17.4" --device-model "iPhone 15" flows/

# Shrink hierarchy JSON output by dropping empty fields (useful when piping to an LLM/agent)
maestro hierarchy --compact
```

```yaml
# MAESTRO_FILENAME — built-in env var exposing the current flow's filename inside the flow itself
# Useful for tagging screenshots/artifacts with the source file without hardcoding it per flow
- takeScreenshot: "${MAESTRO_FILENAME}-before-checkout"
```

## Parallel Local iOS Simulator Runs (2.6.0)

Before CLI 2.6.0, running multiple `maestro test` processes against different iOS simulators
on the same machine was unreliable — concurrent local runs would intermittently collide on driver
ports and session state. 2.6.0 fixes this with per-device session tracking, cross-process file
locking, and a port-availability check, plus a new flag to pin the driver port explicitly when
you need deterministic port assignment (e.g. matching a CI matrix or a firewall rule):

```bash
# Run two local iOS suites in parallel without them fighting over the same xctestrunner driver port
maestro test --driver-host-port 9080 flows/ios/suite-a/ &
maestro test --driver-host-port 9081 flows/ios/suite-b/ &
wait
```

This is distinct from the `--shards` distribution model above — `--shards` splits one flow set
across N devices for a single `maestro test` invocation, while this fix targets running several
independent `maestro test` processes (e.g. different suites, different CI jobs) against local iOS
simulators at the same time.

## Dark Mode Testing (2.9.0)

"One of the most requested authoring features since 2023" — a flow can now switch appearance
mid-run and assert both themes without a separate flow/device profile per mode. Works on iOS,
Android, and Web:

```yaml
- setDarkMode: enabled     # or: disabled
- assertVisible: "Settings"
- assertDarkMode           # fails the flow if the device isn't actually in dark mode right now
- toggleDarkMode           # flips whichever mode is currently active
- assertLightMode
```

**2.11.0 tightened the value:** `setDarkMode` and `setAirplaneMode` accept **only** `enabled` /
`disabled` — `true`/`false`/`on`/`off` that older flows might carry now fail validation. They also
finally honour `optional: true` (before 2.11.0 the flag was ignored and a platform that couldn't
switch theme failed the whole flow):

```yaml
- setDarkMode:
    value: enabled
    optional: true     # 2.11.0+: skip instead of fail where the platform can't switch
```

**Measured 2026-10-02 (CLI 2.11.0, Samsung A51 / One UI, Settings app):** `assertDarkMode` passes
as soon as the *system* setting flips — it does NOT prove the app has re-rendered. Android recreates
the activity on the uiMode change, and a `takeScreenshot` straight after `setDarkMode` captured a
blank white screen while `assertDarkMode` was green. Always follow a theme switch with a wait on
real content before asserting/screenshotting visuals:

```yaml
- setDarkMode: enabled
- assertDarkMode
- extendedWaitUntil:          # activity recreation — wait for real content
    visible: "Connections"
    timeout: 10000
- takeScreenshot: "dark"
```

Same trap after `launchApp` on a real device: the first screenshot can still show the previous
foreground app. Gate it on an `extendedWaitUntil` too.

Use this instead of the old workaround of duplicating a flow per theme or pre-setting device
appearance outside Maestro (`adb shell cmd uimode night yes` / simulator defaults) — those still
work but can't switch *within* a running flow to catch state that only breaks on the transition
(e.g. a chart re-render, a cached-color flash).

## Targeting a Specific Android System Image (2.10.0)

`--device-os` (on `maestro cloud` and `maestro start-device`) now accepts a full system-image path,
not just a bare API level — lets you pin the exact image (Play Store vs AOSP variant, specific ABI)
instead of whatever the version-shaped value resolves to:

```bash
# Old form — still works unchanged, resolves to Maestro's default image for that API level
maestro cloud --device-os "android-34" flows/

# New in 2.10.0 — full path: system-images;<api-level>;<tag>;<abi>
maestro cloud --device-os "system-images;android-34;google_apis_playstore;arm64-v8a" flows/
maestro start-device --device-os "system-images;android-34;google_apis_playstore;arm64-v8a"
```

Maestro Cloud supports API levels 29/30/31/33/34/35/36, tags `google_apis` or
`google_apis_playstore`, ABI `arm64-v8a`. Locally, any image `sdkmanager` can install is fair game
(downloaded on demand). `--android-api-level`/`--ios-version`/`--os-version` still work but now emit
a deprecation warning — migrate to `--device-os`.

**Android 17 / API 37 (2.11.0):** `maestro start-device --device-os android-37` works; API 37 ships
minor-versioned 16 KB page-size system images, which Maestro now resolves. If the derived image
isn't installed, the error names the exact `--device-os` string to pass — copy it rather than guessing.

## Anti-Patterns to Avoid

```yaml
# ❌ Don't use sleep — Maestro auto-waits
- sleep: 3000

# ✓ Instead — assert what you're waiting for
- assertVisible:
    text: "Loading..."
    visible: false    # wait for loading to disappear

# ❌ Don't select by index — fragile
- tapOn:
    text: "Button"
    index: 2

# ✓ Use unique IDs
- tapOn:
    id: "confirm-delete-btn"

# ❌ Don't hardcode test data in shared flows
- inputText: "real-user@company.com"

# ✓ Use environment variables
- inputText: ${TEST_EMAIL}
```

## Version timeline (CLI)

| Version | Date | What it added that changes how you write flows |
|---|---|---|
| **2.11.0** | 29 Sep 2026 | Android 17 (API 37) in `start-device`; physical iPhones no longer listed — runs fail early "Physical iOS devices are not yet supported"; `setDarkMode`/`setAirplaneMode` accept ONLY `enabled`/`disabled` + honour `optional: true`; `start`/`end` inside element selectors now REJECTED (was silently ignored); recording `metadata.startedAtEpochMs` in artifact manifest; Windows fix for `maestro cloud` + `runFlow` with complex paths |
| 2.10.0 | 9 Sep 2026 | `--device-os` accepts full `system-images;<api>;<tag>;<abi>` path (not just bare API level); legacy `--android-api-level`/`--ios-version`/`--os-version` now deprecated |
| 2.9.0 | 31 Aug 2026 | `setDarkMode`/`toggleDarkMode`/`assertDarkMode`/`assertLightMode` — switch + assert theme mid-run (iOS/Android/Web) |
| 2.8.0 | 6 Aug 2026 | `point` inside a `from:` selector for swipes; variables/JS expressions in `permissions` values and in `thresholdPercentage`; Cloud upload + report fixes |
| 2.7.0 | 27 Jul 2026 | Redesigned per-flow debug bundle for AI-agent debugging of failing Cloud runs; automatic per-step screenshots + failure hierarchy; leaner artifacts; Android native SIGSEGV crash detection; `maestro chat` discontinued |
| 2.6.1 | 12 Jun 2026 | Fixes |
| 2.6.0 | 25 May 2026 | Maestro Viewer + built-in MCP server; parallel local iOS simulator fix; `--driver-host-port`; cleaner output |
| 2.5.x | Apr 2026 | Android 15/16 support, new Pixel 9 device profiles |

Check what you actually have before assuming a feature exists — a flow using `point` fails to parse
on 2.7.x:

```bash
maestro --version
maestro check-syntax flows/            # catches unsupported keys before a device run
```

## Sources
- https://github.com/mobile-dev-inc/maestro/blob/main/CHANGELOG.md#2110 — CLI 2.11.0 (29 Sep 2026): Android 17/API 37, physical iOS rejected early, setDarkMode/setAirplaneMode value + optional, start/end rejected in selectors, recording startedAtEpochMs, Windows cloud runFlow path fix
- https://maestro.dev/blog/maestro-cli-2-10-0 — CLI 2.10.0 (9 Sep 2026): full system-image path for `--device-os`, legacy flags deprecated
- https://maestro.dev/blog/maestro-cli-2-9-0 — CLI 2.9.0 (31 Aug 2026): dark mode commands, iOS/Android/Web
- https://docs.maestro.dev/reference/commands-available/setdarkmode — `setDarkMode: enabled | disabled`
- https://maestro.dev/blog — CLI 2.8.0 (6 Aug 2026): swipe from any point inside an element, variables in permissions and screenshot thresholds, Cloud upload/report reliability fixes; CLI 2.7.0 (27 Jul 2026): debug failing Cloud runs with your AI agent
- https://docs.maestro.dev/reference/commands-available/swipe — `from.point` accepts `"50%, 85%"` (relative to the element's own bounds) or `"25, 75"` (pixel offset from its top-left); omitted → swipe starts at element centre; `direction` cannot be combined with `start`/`end`
- https://github.com/mobile-dev-inc/maestro/blob/main/CHANGELOG.md — `maestro check-syntax`, `maestro chat`, `--reinstall-driver`, `--device-os`/`--device-model`, `--compact`, `MAESTRO_FILENAME` (1.39.0–1.40.0); parallel local iOS simulator fix + `--driver-host-port` (2.6.0); automatic per-step screenshots + failure hierarchy, leaner artifact bundle, Android native SIGSEGV crash detection, `maestro chat` discontinued (2.7.0)
- https://maestro.dev/blog/maestro-cli-v2-6-0 — Maestro CLI 2.6.0 release notes
- https://docs.maestro.dev/
