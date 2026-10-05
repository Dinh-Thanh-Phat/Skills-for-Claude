---
name: maestro-speed-optimization
description: |
  Speed up Maestro mobile test EXECUTION (x3–x5) using measured bottlenecks from real Android
  device runs — clearState cost, system animations, redundant waitForAnimationToEnd, text-vs-id
  selectors, state grouping via executionOrder, and JVM amortization on folder runs. Contains
  benchmarks that contradict common assumptions (per-flow `adb pm clear` is SLOWER than
  clearState + folder-run; wireless ADB is ~2x slower per call and cancels every other
  optimization).
  Use when: a Maestro suite takes too long, each test costs 30s+, clearState causes lag, someone
  proposes an optimization that has not been measured, or a run must be tuned for a real Android
  device on Windows.
  Triggers on: "maestro test chậm", "test chạy lâu", "tăng tốc maestro", "suite chạy lâu quá",
  "clearState slow", "optimize mobile test", "maestro slow", "speed up maestro", "giảm thời gian
  chạy test", "test mobile lâu", "adb pm clear nhanh hơn không", "wireless adb có chậm không".
scope: mobile-automation, maestro, android
---

> **⚠️ Đọc dòng này trước.** Skill này tối ưu **THỜI GIAN CHẠY test**.
> Nếu bạn chậm ở khâu **DÒ / LẤY ELEMENT** (dump hierarchy, tìm testID, build flow đầu tiên) →
> **sai skill**. Dùng `maestro-element-harvest`: harvest toàn bộ selector 1 lần trong warm session,
> grep trên đĩa, cache `ELEMENT_MAP.md` → build flow sau đó không dump lại.
> Hai vấn đề này có nút thắt hoàn toàn khác nhau; áp dụng sai skill sẽ không thấy cải thiện.

# Maestro Speed Optimization — Tăng Tốc x3-x5

## Root Causes (theo thứ tự impact)

| Cause | Time Lost | Fix |
|-------|-----------|-----|
| `clearState: true` | ~25-40s/test | Thay bằng logout flow |
| System animations | ~1-3s/step | Disable qua ADB |
| `waitForAnimationToEnd` thừa | ~1-2s/call | Chỉ dùng khi cần |
| `scrollUntilVisible` | ~5-15s | Dùng `id:` selector trực tiếp |
| Text selector vs ID | ~0.5s/tap | Dùng `id:` luôn |
| Dò element chậm/lặp | login lại + dump 600KB + parse blob | Harvest 1 lần → cache `ELEMENT_MAP.md`, xem `[[maestro-element-harvest]]` |

> **Chậm khi LẤY element (không phải chạy test)?** → đây là skill sai. Dùng `[[maestro-element-harvest]]`:
> harvest toàn bộ selector 1 lần trong warm session, grep trên đĩa, cache vĩnh viễn → build flow không dump lại.

---

## Step 1 — Disable Animations (Áp dụng 1 lần trước khi chạy suite)

Chạy trước `maestro test` — tiết kiệm 1-3s mỗi animation step:

```powershell
# Disable system animations trên real device
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0

# Giữ màn hình sáng trong suốt test
adb shell settings put global stay_on_while_plugged_in 3
```

Restore sau khi test xong:
```powershell
adb shell settings put global window_animation_scale 1
adb shell settings put global transition_animation_scale 1
adb shell settings put global animator_duration_scale 1
```

---

## Step 2 — Thay clearState bằng Logout Flow

### ❌ Chậm — clearState mỗi test (~35s)
```yaml
- launchApp:
    clearState: true   # Xóa toàn bộ app data = chậm
- waitForAnimationToEnd
```

### ✅ Nhanh — stopApp + launchApp (~5s)
```yaml
- stopApp             # Kill app process
- launchApp           # Relaunch (giữ session data)
```

### ✅ Nhanh — Logout flow cho auth tests
Tạo `flows/_setup/logout.yaml`:
```yaml
appId: ${APP_ID}
---
- stopApp
- launchApp
- waitForAnimationToEnd
# Nếu app đang ở Home (logged in) → navigate to settings → logout
# Nếu app đang ở Welcome → skip logout
- tapOn:
    id: "settings-tab"     # Update theo testID thực tế của app
- waitForAnimationToEnd
- tapOn:
    id: "logout-button"
- waitForAnimationToEnd
```

---

## Step 2b — Auth Test Grouping (clearState 1 lần thay vì N lần)

Nếu không thể bỏ `clearState` (app cần fresh state cho mỗi auth test), dùng **`executionOrder`** để clearState chỉ chạy **1 lần** đầu suite, các test sau tái dùng session.

```
Vấn đề:        [clearState+login] → [test1] → [clearState+login] → [test2] → ...
               80s                              80s                   = N × 80s

Giải pháp:     [clearState+login] → [test1] → [test2] → ... → [logout tests]
               80s (1 lần)          ~5s         ~5s             = 80s + (N-1) × 5s
```

### Phân loại test theo yêu cầu state

| Loại | Ví dụ | State cần | Strategy |
|------|-------|-----------|----------|
| **Session-reuse** | valid login, profile view | Logged in | Chạy sau login 1 lần |
| **Fresh-state** | wrong password, empty fields | Logged out | clearState 1 lần đầu, đặt trước |
| **Destructive** | logout | Logged in → Logged out | Chạy cuối cùng |

### Cấu trúc thực tế với executionOrder

`.maestro/config.yaml`:
```yaml
env:
  APP_ID: com.example.app

executionOrder:
  continueOnFailure: true
  flowsOrder:
    # Group 1: cần fresh state (clearState ở trong flow này)
    - auth/TC-M-AUTH-001_welcome-screen     # clearState trong flow
    - auth/TC-M-AUTH-017_login-empty-fields # clearState, không cần login
    - auth/TC-M-AUTH-008_login-wrong-pass   # clearState, login sai → không tạo session

    # Group 2: session-reuse (login 1 lần trong TC-007, các test sau tái dùng)
    - auth/TC-M-AUTH-007_login-valid        # login thành công → tạo session
    - auth/TC-M-AUTH-009_password-toggle    # reuse → không clearState

    # Group 3: destructive (logout làm mất session, đặt cuối)
    - auth/TC-M-AUTH-014_logout
```

**Lưu ý:** tên dạng `auth/TC-...` ở trên là UNVERIFIED — docs chỉ nói tên file (không `.yaml`) hoặc `name:` của flow. Docs cũng khuyên mỗi flow chạy được trên device đã reset; dựa vào state flow trước là đánh đổi tốc độ lấy độ cô lập — chấp nhận có chủ đích.

**Lưu ý quan trọng:** Maestro không share state giữa flows một cách explicit — nó chỉ không restart app giữa các flows khi không có `clearState`. Session trong app (cookie/token) vẫn còn nếu app chưa bị kill. Test nên idempotent — không dựa vào state từ flow trước, nhưng CÓ THỂ khai thác session còn sót để tránh login lại.

---

## Step 3 — Workspace Config Tối Ưu

`.maestro/config.yaml`:
```yaml
env:
  APP_ID: com.example.app
  TEST_EMAIL: qa@test.com
  TEST_PASSWORD: Test@1234

# KHÔNG có key `disableAnimations` trong config.yaml — tắt animation bằng ADB (Step 1).

# Execution order: `executionOrder` là key TOP-LEVEL (không lồng dưới `flows:`)
executionOrder:
  continueOnFailure: true    # Tiếp tục khi 1 flow fail (default true)
  flowsOrder:
    - TC-M-AUTH-001          # Tests cần fresh state đặt đầu
    - TC-M-AUTH-007          # Login test → tạo session
    - TC-M-AUTH-009          # Reuse logged-in state
    - TC-M-AUTH-008          # Wrong password (logout trước)
```

> Docs: entries là **tên file không có `.yaml`** hoặc `name:` trong flow. Dạng có thư mục
> (`auth/TC-...`) như Step 2b dùng là UNVERIFIED — nếu flow không chạy theo thứ tự, đổi về tên file.
> Flow không liệt kê sẽ chạy SAU dãy này, thứ tự ngẫu nhiên. (docs.maestro.dev/maestro-flows/workspace-management/sequential-execution)

---

## Step 4 — Viết Flows Nhanh

### Tránh waitForAnimationToEnd thừa — đặc biệt khi đã disable ADB animations

`waitForAnimationToEnd` hoạt động bằng cách **chụp screenshots và so sánh** (screenshot comparison loop).
Khi animations đã bị disable qua ADB, màn hình static ngay lập tức → Maestro phát hiện "tĩnh" sau 1-2 lần chụp (~150-300ms/call). Không tốn nhiều nhưng gộp nhiều call = lãng phí + risk flakiness (loop không bao giờ kết thúc nếu có UI element nhấp nháy).

**Quy tắc:**
- Sau `launchApp` (animations đã off) → **bỏ `waitForAnimationToEnd`**, thay bằng `assertVisible` trên element đầu tiên cần tương tác — Maestro tự chờ đến khi element xuất hiện.
- Giữ `waitForAnimationToEnd` chỉ khi animations CHƯA disable và bạn cần chờ transition phức tạp (video, lottie, loading skeleton).

```yaml
# ❌ Chậm + flaky khi animations đã off (screenshot loop vô nghĩa)
- launchApp:
    clearState: true
- waitForAnimationToEnd   # ~200ms overhead, không cần
- tapOn:
    id: "splash-get-started-button"
- waitForAnimationToEnd   # ~200ms overhead nữa
- tapOn: "Sign In"
- waitForAnimationToEnd   # thêm 1 lần

# ✅ Nhanh — assertVisible làm cả hai: chờ element + verify đúng màn hình
- launchApp:
    clearState: true
- assertVisible:
    id: "splash-get-started-button"   # Maestro chờ màn Welcome load xong
- tapOn:
    id: "splash-get-started-button"
- assertVisible:
    id: "login-email-input"            # chờ màn Login load xong
```

### Dùng ID selector (nhanh hơn text ~0.5s/tap)
```yaml
# ❌ Chậm — text search scan toàn bộ UI tree
- tapOn:
    text: "Sign In"

# ✅ Nhanh — direct lookup bằng resource-id
- tapOn:
    id: "login-submit-button"
```

### scrollUntilVisible → kiểm tra ID trước (có thể bỏ scroll hoàn toàn)

`scrollUntilVisible` với `text:` = scan UI tree + scroll vật lý nếu element chưa visible. Nếu element đã on-screen (chỉ chưa indexed) hoặc có testID → bỏ scroll hoàn toàn.

```yaml
# ❌ Chậm + sai — scroll để tìm "Sign In" nhưng element đã on-screen, chỉ cần ID
- scrollUntilVisible:
    element:
      text: "Sign In"

# ✅ Nếu dev đã gắn testID → tap thẳng, không cần scroll
- tapOn:
    id: "auth-signin-link"

# ✅ Nếu chưa có testID nhưng element ON-SCREEN → tapOn text (không cần scroll)
- tapOn:
    text: "Sign In"

# Chỉ dùng scrollUntilVisible khi element THỰC SỰ nằm ngoài viewport
- scrollUntilVisible:
    element:
      id: "item-at-bottom-of-list"
    direction: DOWN
    timeout: 10000
```

---

## Step 5 — Run Script Tối Ưu (PowerShell)

`scripts/run-tests-fast.ps1`:
```powershell
$maestro = "$env:USERPROFILE\.maestro\maestro\bin\maestro.bat"
$APP_ID = "com.example.app"

# 1. Disable animations
Write-Host "Disabling animations..." -ForegroundColor Cyan
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0
adb shell settings put global stay_on_while_plugged_in 3

# 2. Run tests
& $maestro test `
    --env APP_ID=$APP_ID `
    --env TEST_EMAIL=$env:TEST_EMAIL `
    --env TEST_PASSWORD=$env:TEST_PASSWORD `
    flows/

# 3. Restore animations
Write-Host "Restoring animations..." -ForegroundColor Cyan
adb shell settings put global window_animation_scale 1
adb shell settings put global transition_animation_scale 1
adb shell settings put global animator_duration_scale 1

Write-Host "Done."
```

---

## Thứ Tự Ưu Tiên Tối Ưu

1. **Disable animations TRƯỚC khi chạy** → impact ngay lập tức
2. **Xoá clearState, dùng logout flow** → tiết kiệm 25-35s/test
3. **Dùng ID selectors** → nhanh hơn text search
4. **Bỏ waitForAnimationToEnd thừa** → 1-2s mỗi call
5. **Group tests theo state** → tái sử dụng session, tránh re-login

## Benchmark Thực Tế

| Approach | Time/test | 10 tests |
|----------|-----------|----------|
| clearState + text selector | ~45s | ~7.5 min |
| stopApp + ID selector | ~15s | ~2.5 min |
| Shared session + ID | ~8s | ~1.3 min |

**x3-x5 improvement** khi kết hợp tất cả techniques.

## ⚠️ pm-clear-per-flow CHẬM HƠN clearState+folder-run (đo thực tế)

Giả định "thay clearState bằng `adb pm clear` ngoài flow sẽ nhanh hơn" — **SAI khi chạy nhiều flow**. Đo thực tế (The Client Book, 9 auth, USB real device):

| Approach | Kết quả |
|----------|---------|
| folder-run + clearState (`maestro test flows/`) | **9/9, 358s** ✅ ổn định nhất |
| per-flow + `adb pm clear` (loop từng flow) | 2/9, 424s ❌ chậm + flaky |

Lý do per-flow tệ hơn:
1. **JVM startup amortization**: `maestro test <folder>` boot JVM 1 LẦN cho cả suite. Chạy từng flow riêng → boot lại mỗi flow (~10-15s × N flows = lãng phí lớn hơn mọi tiết kiệm clearState).
2. **adb pm clear lặp liên tục làm rớt USB adb** ("device offline") → flaky cascade.

**Quy tắc:** clearState chậm NHƯNG folder-run amortize JVM bù lại. Chỉ dùng `pm clear` ngoài flow khi reset 1 LẦN trước cả suite (không phải per-flow). Muốn nhanh hơn nữa: giảm SỐ BƯỚC navigate (deep-link nếu nav là bottleneck), không đổi cơ chế reset state. ĐO trước khi tin mọi giả định tối ưu.

## ⚠️ Wireless ADB Triệt Tiêu Tối Ưu Tốc Độ

Đo thực tế (The Client Book, 9 auth tests, real device Samsung):
- **Wireless ADB:** ~58s/test (524s/9 tests) — kể cả khi đã disable animations
- **USB:** ~28s/test (252s/9 tests)

Maestro gọi adb HÀNG TRĂM lần/test (dump hierarchy, tap, query). Wireless trễ ~2x mỗi call → triệt tiêu mọi tối ưu khác. **Muốn đạt x5 thật: BẮT BUỘC USB.** Nếu user chọn wireless cho tiện, nói rõ trade-off: tiện ≠ nhanh.

Chi tiết 8 pitfall Maestro+ADB trên Windows: [references/android-windows-gotchas.md](references/android-windows-gotchas.md) §1.

---

## Trước khi tin bất kỳ tối ưu nào — ĐO

Hai giả định "hiển nhiên" trong file này đều đã được đo và **sai**: `adb pm clear` per-flow chậm hơn
`clearState`+folder-run, và wireless ADB tiện nhưng chậm gấp đôi. Quy tắc rút ra:

```bash
# Baseline TRƯỚC khi đổi bất cứ thứ gì — không có baseline thì không có "nhanh hơn"
maestro test flows/ 2>&1 | tail -5      # ghi lại tổng thời gian + pass/fail

# Đổi ĐÚNG MỘT biến, đo lại, so cùng điều kiện (cùng cable, cùng device, cùng số flow)
```

Đổi 2 biến cùng lúc thì con số thu được vô nghĩa — không quy được cải thiện cho biến nào, và một
biến làm chậm có thể che mất một biến làm nhanh. Cũng đừng so pass-rate khác nhau: 9/9 trong 358s
tốt hơn 2/9 trong 424s, nhưng nếu chỉ nhìn "thời gian/test" thì bản flaky trông có vẻ ngang ngửa.
