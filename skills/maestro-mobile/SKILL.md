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

## Quick Start

```bash
# Install
curl -Ls "https://get.maestro.mobile.dev" | bash

# Run a flow
maestro test flow.yaml

# Run with environment variables (for cross-platform)
maestro test --env APP_ID=com.example.app login-flow.yaml

# Run entire folder
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

# Precise swipe (coordinates)
- swipe:
    start: { x: 50%, y: 80% }
    end: { x: 50%, y: 20% }

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
