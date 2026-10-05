---
name: maestro-android-windows-gotchas
description: Pitfalls khi chạy Maestro + ADB trên Windows + real device. Use khi setup wireless ADB, gặp path/encoding lỗi, scrollUntilVisible timeout, miss confirm dialog, hoặc Maestro 2.x syntax error.
triggers:
  - "wireless adb không connect"
  - "adb mdns"
  - "scrollUntilVisible timeout"
  - "Unknown Property timeout maestro"
  - "FileNotFoundException maestro report"
  - "sign out không logout được"
  - "maestro flow fail real device"
scope: mobile-automation, maestro, android, windows
---

# Maestro + Android + Windows — Gotchas & Lessons

Tổng hợp lỗi thực tế đã mắc + cách phòng tránh. Đọc TRƯỚC khi setup project mobile mới.

---

## 1. Wireless ADB: Port Pair ≠ Port Connect (Android 11+)

**Lỗi đã mắc:** Pair thành công ở port `34009`, tưởng dùng port đó để `adb connect` → "connection refused". Bảo user rút USB quá sớm.

**Sự thật:** Android 11+ dùng TLS pairing + mDNS, port động (random, KHÔNG phải 5555):
- Màn "Ghép nối bằng mã" → **port pair** (chỉ dùng 1 lần với `adb pair`)
- Màn chính "Địa chỉ IP và cổng" → **port connect** (dùng `adb connect`) — KHÁC port pair

**Cách đúng — không cần hỏi user port connect:**
```powershell
adb pair 192.168.0.7:34009 077926      # port + code từ màn "Ghép nối"
adb mdns services                       # tự tìm port connect thật
# Output: adb-XXXX _adb-tls-connect._tcp  192.168.0.7:45903
adb connect 192.168.0.7:45903           # connect bằng port từ mdns
```

mDNS records: `_adb._tcp`, `_adb-tls-connect._tcp` (connect), `_adb-tls-pairing._tcp` (pair).
Nếu device không hiện trong `adb devices` sau khi rớt → chạy lại `adb mdns services` lấy port mới (port đổi sau mỗi lần toggle wireless debugging).

**Wireless CHẬM hơn USB ~2x** cho Maestro (gọi adb rất nhiều). Real device đo được: wireless ~58s/test, USB ~28s/test. Cảnh báo user trade-off này TRƯỚC khi khuyên rút USB.

---

## 2. Windows: Bash Mangle `/sdcard` Path

**Lỗi đã mắc:** Chạy `adb pull /sdcard/ui.xml` qua Bash tool trên Windows → Git Bash MSYS tự convert `/sdcard` thành `C:/Program Files/Git/sdcard` → "No such file or directory".

**Fix:** Mọi lệnh `adb` có path kiểu Unix (`/sdcard/...`) trên Windows → dùng **PowerShell tool, KHÔNG dùng Bash tool**. Bash chỉ an toàn cho lệnh adb không có Unix path.

---

## 3. Non-ASCII Path Phá Java/Maestro Output

**Lỗi đã mắc:** Project tại `D:\HK8\Learning\DQ\The Client Bọok\` (ký tự "ọ"). Maestro `--output results.xml` → `FileNotFoundException: ...The Client Bá»ok\... (system cannot find path)`. Java encode path bằng cp1252, hỏng ký tự Unicode.

**Fix:** Output của Maestro/Java (JUnit XML, reports) PHẢI ghi ra path **thuần ASCII**:
```powershell
$resultsDir = "D:\HK8\Learning\DQ\test\client-book-mobile"   # ASCII-safe
# KHÔNG: "D:\...\The Client Bọok\test-results"
```
Flow YAML/screenshot Maestro tự xử lý OK; chỉ `--output` (Java FileOutputStream) bị lỗi.

---

## 4. Maestro 2.x: `timeout:` Không Hợp Lệ Trong assertVisible

**Lỗi đã mắc:** Viết `assertVisible: { text: "X", timeout: 8000 }` → `> Unknown Property: timeout` (Maestro 2.5.1).

**Fix:** Maestro auto-wait sẵn. Cần chờ lâu hơn → dùng `extendedWaitUntil`:
```yaml
- extendedWaitUntil:
    visible:
      id: "dashboard"
    timeout: 20000
```
`scrollUntilVisible` thì `timeout:` hợp lệ (default 20000ms).

---

## 5. scrollUntilVisible Trap: Element KHÔNG BAO GIỜ Xuất Hiện

**Lỗi đã mắc:** `login.yaml` chạy `scrollUntilVisible text "Sign In"` ngay trên Welcome screen — nhưng "Sign In" chỉ có SAU khi tap `splash-get-started-button`. → scroll vô vọng ~57s rồi fail. Mỗi test dùng login.yaml fail oan.

**Quy tắc:**
- Trước khi `scrollUntilVisible`, ĐẢM BẢO element CÓ THỂ xuất hiện trên màn hiện tại (đã dump UI verify navigation đúng).
- KHÔNG duplicate logic navigation. Tách `navigate-to-X.yaml` rồi `runFlow` tái dùng — đừng copy-paste rồi thiếu bước.
- Đặt `timeout:` ngắn hơn default cho scroll khi muốn fail nhanh thay vì chờ 20s.

---

## 6. Destructive Action Luôn Có Confirm Dialog — Dump UI Sau Mỗi Bước

**Lỗi đã mắc:** TC logout: tap "Sign Out" rồi assert ngay về login → fail. Thực tế có dialog "Sign out?" với `sign-out-confirm`/`sign-out-cancel` chen giữa.

**Quy tắc:**
- Sau MỌI hành động destructive (logout, delete, reset) → dump UI (`adb shell uiautomator dump`) kiểm tra có dialog/confirm không, ĐỪNG giả định 1 bước.
- Confirm dialog có thể không xuất hiện → bọc `runFlow: when: visible:` để robust:
```yaml
- tapOn: { id: "profile-sign-out" }
- runFlow:
    when: { visible: "Sign out?" }
    commands:
      - tapOn: { id: "sign-out-confirm" }
- assertVisible: { id: "login-email-input" }   # assert state THẬT sau logout (đã verify bằng dump)
```
- Đừng assume màn sau logout = welcome. Verify bằng dump (project này về thẳng login form, không về splash).

---

## 7. Python Print UI Dump → cp1252 UnicodeEncodeError (Windows)

**Lỗi đã mắc:** Parse `ui.xml` rồi `print()` text chứa ký tự private-use (icon font ``) → `UnicodeEncodeError: 'charmap' codec`.

**Fix:** Force UTF-8 stdout đầu script parse XML:
```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

---

## 8. clearState Flaky Trên Real Device

**Lỗi đã mắc:** `launchApp: clearState: true` đôi khi fail `Unable to clear state... pm list packages --user 0` (nhất là khi adb connection drop giữa suite).

**Fix:** Reset qua adb NGOÀI flow, bỏ clearState trong YAML:
```powershell
adb shell pm clear com.example.app   # tin cậy hơn clearState
```
Xem thêm skill `maestro-speed-optimization` (clearState cũng là nguyên nhân chậm #1).

---

## Checklist Setup Project Mobile Mới (Windows + Real Device)

- [ ] Output dir Maestro = ASCII path (không dấu tiếng Việt)
- [ ] adb có Unix path → dùng PowerShell tool, không Bash
- [ ] Wireless: `adb pair` → `adb mdns services` → `adb connect` (port khác nhau)
- [ ] Cảnh báo user wireless chậm ~2x USB trước khi khuyên rút cáp
- [ ] Disable animations trước suite (xem maestro-speed-optimization)
- [ ] Dump UI verify navigation TRƯỚC khi viết scrollUntilVisible
- [ ] Tách navigate-to-X.yaml, runFlow tái dùng — không copy-paste navigation
- [ ] Sau destructive action: dump UI tìm confirm dialog
- [ ] Maestro 2.x: chờ lâu = extendedWaitUntil, không timeout: trong assertVisible
