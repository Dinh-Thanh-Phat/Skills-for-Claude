---
name: maestro-element-harvest
description: Lấy TOÀN BỘ selector (testID/text) của app mobile NHANH trong 1 lần, cache vĩnh viễn — hết cảnh dò element chậm mỗi lần build flow. Use when "lấy element chậm", "dò selector lâu", trước khi build nhiều Maestro flow, hoặc app chưa có element map.
triggers:
  - "lấy element chậm"
  - "dò selector lâu"
  - "harvest element"
  - "element map"
  - "lấy toàn bộ element trước khi chạy"
  - "build nhiều flow maestro"
scope: mobile-automation, maestro, android, ios, element-discovery
---

# Maestro Element Harvest — Lấy Hết Selector 1 Lần, Cache Vĩnh Viễn

## Nguyên tắc gốc (đọc kỹ dòng này)

**Element discovery là chi phí MỘT LẦN.** Cái làm bạn thấy "chậm" là **trả chi phí đó lặp lại**:
re-login mỗi flow, re-dump mỗi màn, re-parse blob JSON vào context. Cách đúng: **harvest 1 lần →
cache ra `ELEMENT_MAP.md` → không bao giờ dump lại.** Từ đó build flow = chi phí dump 0.

> Nếu bạn đang dò element *trong lúc* build flow thứ N → SAI. Harvest hết TRƯỚC, rồi build từ map.

---

## 4 nút thắt tốc độ (đo thực tế, The Client Book / RN Expo)

| Nút thắt | Vì sao chậm | Fix |
|---|---|---|
| **Dump 300–620KB/màn** | `maestro hierarchy` serialize cả a11y tree RN; đọc cả blob vào context = tốn giây + token | Dump ra **file**, `grep` testID trên đĩa — KHÔNG đọc blob vào context |
| **Re-login mỗi lần dò** | `clearState`/login = 30–40s | 1 WARM session: login 1 lần, các dump sau **không launchApp/clearState** |
| **Tap lại nav mỗi màn** | đi Home→tab→sub-screen lặp lại | **Deep link** nhảy thẳng, hoặc chain nhiều dump trong 1 flow |
| **waitForAnimationToEnd × N** | screenshot-loop 200ms+/call | disable animation ADB trước; dùng `assertVisible` thay chờ |

---

## Quy trình harvest (1 warm session → cả app)

### Bước 0 — Chuẩn bị 1 lần
```bash
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0
adb shell settings put secure autofill_service null   # tắt Samsung Pass/autofill chèn dialog
```
⚠️ USB, không wireless — Maestro gọi adb hàng trăm lần/dump, wireless ~2× trễ. Xem `[[maestro-speed-optimization]]`.

### Bước 1 — Login MỘT lần (flow có launchApp)
Chạy `_setup/login.yaml` tới Home. Để app **parked** — đừng kill.

### Bước 2 — Attach-flow chain: nav + dump NHIỀU màn, KHÔNG relaunch
1 flow lấy nhiều màn, mỗi màn 1 dump. Flow **không** có `launchApp`/`clearState` → bám session đang chạy:
```yaml
appId: com.olivia.mobile.staging
---
# màn 1
- tapOn: { id: "tab-crm" }
- runScript: { file: dump.js, env: { NAME: "crm" } }   # hoặc dùng hierarchy CLI (dưới)
# màn 2
- tapOn: { id: "clients-add" }
- runScript: { file: dump.js, env: { NAME: "crm-create" } }
- back
# ... chain tiếp các màn
```
Không có `runScript`? Chạy `maestro hierarchy` giữa các bước nav bằng vòng lặp shell:
```bash
# parked app đang ở Home — nav + dump từng màn, 1 login duy nhất
for pair in "tab-crm crm" "tab-appointments cal" "tab-forms forms" "tab-daily-tasks tasks"; do
  set -- $pair
  # `maestro test -` (đọc flow từ stdin) KHÔNG có trong TestCommand — UNVERIFIED/khả năng fail.
  # Ghi flow tạm ra file rồi chạy:
  cat > /tmp/nav.yaml <<EOF
appId: com.olivia.mobile.staging
---
- tapOn: { id: "$1" }
EOF
  maestro test /tmp/nav.yaml
  maestro hierarchy --compact > "dumps/$2.json"    # --compact bỏ giá trị rỗng → file nhỏ hơn; dump ra ĐĨA
done
```
Lưu ý: mỗi `maestro test` boot lại JVM (~10–15s) — vòng lặp này chậm hơn attach-flow chain ở trên;
dùng khi không có cách dump trong flow. Từ 2.6.0 `maestro hierarchy` chỉ in JSON.

### Bước 3 — Trích selector TRÊN ĐĨA (không đọc blob vào context)
```bash
# testID (RN) → land ở resource-id; + text/hint labels
grep -rhoE '"resource-id"[: ]+"[^"]+"' dumps/ | sort -u
grep -rhoE '"(text|hintText|accessibilityText)"[: ]+"[^"]+"' dumps/ | sort -u
```
Chỉ khối grep gọn này vào context, KHÔNG phải 600KB JSON.

### Bước 4 — Cache vào `ELEMENT_MAP.md` (artifact bền của project)
Ghi catalog: mỗi module → id chính, input không-testID → placeholder/`below:`, `<uuid>` dynamic →
match bằng `text:`+`below:`. Kèm ngày + build versionCode. **Đây là nguồn build flow — không dump lại.**

---

## Deep link — bỏ luôn bước nav (nhanh nhất)
Nếu app có scheme (vd `olivia://`), nhảy thẳng vào màn cần thay vì tap nav:
```yaml
# flow (YAML) — chỉ chứa lệnh Maestro
- openLink: "olivia://clients/new"   # thẳng tới form, bỏ Home→tab→add
```
```bash
# shell — `maestro hierarchy` là lệnh CLI, KHÔNG đặt trong YAML
maestro hierarchy --compact > dumps/crm-create.json
```
Xem memory `reference_maestro-test-scaling.md` (KHÔNG phải skill; deep-link bỏ nav ~70%).

---

## uiautomator KHÔNG dùng cho React Native
`adb shell uiautomator dump` trả tree gần rỗng cho RN/Expo (render canvas, chỉ thấy native chrome).
**Luôn `maestro hierarchy`** — đúng a11y tree Maestro dùng, testID hiện ra. Container rỗng cả trong
hierarchy (bug Maestro đã biết) → fallback `text:`/relative/screenshot.

---

## Khi nào HỎI thay vì dò
Capability không lộ trong 1–2 probe ("Delete ở đâu?", "flow đặt lịch thế nào?") → **hỏi người biết app**.
Dò mù N cách là nút thắt lớn nhất. Xem skill `[[ask-when-stuck]]`, memory `feedback_maestro-element-discovery-efficiency` (file memory, không phải skill).

---

## Checklist harvest (làm theo đúng thứ tự)
1. [ ] Disable animation + autofill (ADB), USB
2. [ ] Login 1 lần, để app parked
3. [ ] Chain nav+dump nhiều màn trong warm session, dump ra **file**
4. [ ] Deep link cho màn nào có scheme (bỏ nav)
5. [ ] `grep` testID/text trên đĩa — không đọc blob vào context
6. [ ] Ghi `ELEMENT_MAP.md` (id + placeholder + uuid rule + build version)
7. [ ] Build flow TỪ map — không dump lại

## Anti-pattern (từng mắc → đừng lặp)
- ❌ Dò element ngay trước mỗi flow → login lại N lần
- ❌ Đọc cả `hierarchy` 600KB vào context để tìm 1 id
- ❌ `uiautomator dump` cho RN → tree rỗng, tưởng app hỏng
- ❌ Full-suite rerun để verify 1 selector — chạy canary 1 flow thôi

Liên quan: skill `[[maestro-studio]]` (§Element discovery), skill `[[maestro-speed-optimization]]`, memory `reference_maestro-test-scaling.md` (không phải skill).
