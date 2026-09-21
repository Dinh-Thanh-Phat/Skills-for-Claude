---
name: qa-preflight
description: Kiểm tra môi trường trước khi chạy test — trigger khi user nói "chạy test", "run suite", "test feature X", "bắt đầu test", "run playwright", "maestro test". PHẢI chạy trước bất kỳ test execution nào.
tags: [qa, pre-flight, environment, playwright, maestro, mobile]
---

# QA Pre-flight — Kiểm Tra Môi Trường Trước Khi Test

> **Rule P0:** Không chạy test khi chưa xác nhận môi trường. Mọi fail do môi trường đều lãng phí thời gian và tạo noise trong results.

> **Rule P0 #2 — check file TRƯỚC KHI hỏi credentials hoặc nói "không chạy được".** Tái diễn:
> project đã từng chạy được (có creds, có element map, có kết quả run trước) nhưng khi retest lại
> hỏi lại từ đầu hoặc báo blocked — trong khi thông tin nằm sẵn trên đĩa. TRƯỚC khi hỏi user hoặc
> báo "thiếu X":
> 1. `qa-session-start` → tra project trong registry (`~/.claude/shared-context/registry.md`) +
>    đọc `knowledge/[slug].md` nếu có.
> 2. Nếu không có trong registry: grep thẳng project dir cho `ACCOUNTS.md`, `README.md`,
>    `credentials/`, `.env`, `ELEMENT_MAP*.md`, `*_run_*.log`/`execution_results*.json` — các file
>    này thường ĐÃ có creds/state từ lần chạy trước.
> 3. Chỉ hỏi user hoặc báo blocked SAU KHI đã tìm và không thấy gì — không hỏi trước khi tìm.

---

## Khi nào trigger

- User nói "chạy test", "run suite", "run playwright", "npx playwright test..."
- User nói "test feature X" theo nghĩa thực thi (không phải viết)
- User nói "bắt đầu test session", "maestro test", "run flow"
- Trước khi debug test fail (để loại trừ env factor trước)

**Không trigger khi:** viết test cases, review code, generate manual test cases

---

## Quy trình Pre-flight

### Bước 1 — Xác định test type

| Test type | Factors quan trọng |
|---|---|
| Playwright E2E (web) | URL, auth, headless/headed, test data, feature flags |
| Maestro mobile | Device connected, ADB authorized, app installed, version |
| API tests | API key, endpoint URL, rate limits, mock vs real |
| Chatbot pipeline | LLM API key, model version, doc source |

---

### Bước 2 — Checklist theo loại

#### Playwright E2E

```
□ Environment URL
  - Staging hay Production?
  - URL accessible? (staging có bị down không?)
  - Đúng branch/deploy chưa? (feature có trên staging chưa?)

□ Authentication
  - Test account còn valid không? (password chưa đổi?)
  - Session/cookie hết hạn chưa?
  - OTP/2FA có cần bypass không? → xem otp-untestable-flows

□ Test Data
  - Cần seed data gì trước khi chạy?
  - Data từ lần chạy trước có còn tồn tại không? (cleanup chưa?)
  - Unique ID generation cần thiết không?

□ Browser Mode
  - Headed (thấy browser) hay headless?
  - Local hay CI pipeline?
  - Viewport size quan trọng không? (responsive test)

□ Feature Flags
  - Feature đang test có flag nào không?
  - Flag đang ON/OFF trên staging?

□ Network
  - External API có mock không, hay dùng real API?
  - VPN cần thiết không?
  - Rate limit có ảnh hưởng không khi chạy nhiều test?
```

#### Maestro Mobile

```
□ Device
  - Real device hay emulator/simulator?
  - ADB connected? (adb devices)
  - ADB authorized? (không phải "unauthorized")

□ App
  - App đã install chưa? Đúng version chưa?
  - Package name đúng không? (staging vs prod)
  - App có cần clear state không?

□ Maestro
  - Maestro CLI version up to date?
  - Flow file path đúng không?
  - MAESTRO_DRIVER_STARTUP_TIMEOUT đặt chưa?

□ Network
  - Device và máy tính cùng network không? (wireless ADB)
  - Port 5037 available không?

□ Perf gate (⚠️ P0, xem "MANDATORY gate" đầu skill `maestro-mobile` — bắt buộc nếu > ~5 flow hoặc > 1 account)
  - Đã harvest element 1 LẦN trước khi viết flow chưa? (không dump xen kẽ khi viết) → maestro-element-harvest
  - Flow đã group theo auth state (1 login/session, KHÔNG launchApp+clearState mỗi flow) chưa? → maestro-auth-state-strategy
  - Nếu re-run vì có case fail: chỉ re-run ĐÚNG case đó, không re-run cả section/suite
```

#### API / Chatbot Pipeline

```
□ API Keys
  - Key còn valid không? (chưa expired, chưa revoke)
  - Key đúng environment chưa? (dev key vs prod key)

□ Endpoints
  - Base URL đúng không?
  - Model version đúng không? (chatbot: model đời mới hơn/mắc hơn vs đời rẻ hơn config trong .env)

□ Rate Limits
  - Số lượng test cases có vượt rate limit không?
  - Cần delay giữa các calls không?
```

---

### Bước 3 — Template hỏi user (nếu thiếu thông tin)

Khi bất kỳ item nào trong checklist chưa rõ, hỏi theo template này — **gộp thành 1 lần hỏi, không hỏi từng cái**:

```
Trước khi chạy test, tôi cần xác nhận một số thứ:

**Môi trường:**
- Chạy trên staging hay production?
- URL staging là gì? (hoặc vẫn dùng URL cũ: [URL nếu biết])

**Auth:**
- Test account: [account nếu biết] — password còn dùng được không?
- Cần OTP/2FA bypass không?

**Test data:**
- Cần seed data gì trước khi chạy không?

**Mode:**
- Chạy headed (thấy browser) hay headless?

Nếu tất cả vẫn như lần trước → confirm "ok" là đủ.
```

---

### Bước 4 — Environment factor warning

> **Rule:** Nếu sau 2 lần thử check env mà vẫn chưa resolve được (device không connect, URL không response, auth fail) → **DỪNG ngay, invoke `ask-when-stuck`**. Không tự thử lần 3.

Sau khi thu thập thông tin, **PHẢI báo user** về các factors có thể ảnh hưởng results:

```
⚠️ Lưu ý môi trường trước khi chạy:
- Headless mode: một số UI interactions behave khác headed
- Staging server: cold start có thể làm slow tests (~30s đầu)
- Real API: rate limit có thể cause flaky tests nếu chạy parallel
- [factor cụ thể khác nếu có]

Bạn muốn tiếp tục không?
```

---

## Khi nào skip pre-flight

- Unit tests / vitest tests (no external deps)
- Pure code review / test case generation (không chạy thật)
- Chạy lại đúng test đã fail vừa xong (env đã verified)
- User confirm "env ok, proceed"

---

## Cross-references

- **ask-when-stuck** — nếu env check bị block (device không connect, URL không response) sau 2 lần thử → hỏi user ngay
- **otp-untestable-flows** — xử lý OTP/2FA trong auth scenarios
- **test-data-lifecycle** — cleanup strategy sau khi test xong
- **playwright-diagnosis-first** — khi test fail, diagnose env factor trước khi debug code
