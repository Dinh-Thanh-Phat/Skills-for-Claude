# Test Case Deliverable Format — CHUẨN MẶC ĐỊNH

> **Nguồn gốc:** format này được user xác nhận "khá tốt" sau khi dùng cho TetherTails (697 cases, 2 spec PDF, 05-08-2026).
> **Áp dụng:** MỌI lần viết bộ test cases từ spec/PRD/scope doc. Không cần user yêu cầu lại.

---

## Nguyên tắc số 1 — Markdown là nguồn sự thật, Excel được SINH RA từ nó

**KHÔNG BAO GIỜ gõ test case hai lần.** Viết case trong markdown, rồi chạy script parse ra Excel.

```
spec/PRD  →  markdown (13 file module)  →  [script parse]  →  Excel (1 sheet/module)
                      ▲                                              │
                      └──────── sửa ở đây, chạy lại script ──────────┘
```

Lý do: nếu gõ tay vào cả markdown và Excel, hai bản sẽ lệch nhau ngay lần sửa đầu tiên. Người đọc không biết tin bản nào.

---

## PHẦN 1 — Cấu trúc thư mục deliverable

```
<output-dir>/
├── README.md                          ← điều hướng + 3 điều quan trọng nhất + phát hiện đáng chú ý
├── 00_COVERAGE_MATRIX.md              ← source inventory, feature→case map, 8-category gap, ripple map, wave
├── 01_<module>.md                     ← test cases module 1
├── 02_<module>.md
├── …
├── 99_OPEN_ITEMS_AND_QUESTIONS.md     ← spec gaps, mâu thuẫn, câu hỏi cho PO, điều kiện môi trường
├── export_test_cases.py               ← script parse markdown → Excel
└── <Project>_TestCases_manual_YYYYMMDD.xlsx
```

Tên file module: `NN_snake_case_module_name.md`, số thứ tự khớp số section của spec.

### `README.md` phải có

1. Nguồn (tên file spec + version + ngày)
2. Trạng thái rõ ràng: `✅ Manual xong — ⏸ automation CHƯA viết, chờ review`
3. Bảng "đọc theo thứ tự này"
4. Bảng file × số case
5. Mô tả file Excel (sheet nào, cột nào, cách lọc)
6. **"3 điều quan trọng nhất cần biết trước khi dùng"** — blocker môi trường, case BLOCKED, phát hiện rủi ro
7. Bảng phát hiện 🔴/🟠 xếp theo rủi ro
8. Nguyên tắc đã áp dụng khi viết
9. Bước tiếp theo

### `00_COVERAGE_MATRIX.md` phải có

| Mục | Nội dung |
|---|---|
| PHASE 0 Source Inventory | Bảng mọi nguồn đã đọc + ✅/❌. **Nguồn THIẾU phải liệt kê tường minh** (vd "chưa có Figma", "chưa có companion xlsx") |
| PHASE 1 Feature→Case Mapping | Bảng § × module × req count × case count × file |
| Phân bố 8 category | POS/NEG/SEC/EDGE-BOUNDARY/UI/PERF/A11Y/PLAT |
| PHASE 2 Gap Check | Module nào 0 case ở category nào + verdict PASS / ⚠️CONDITIONAL |
| PHASE 3 Checklist | Coverage by source + common gap areas, dùng `[x]` / `[ ]⚠️` |
| **Cross-Module Ripple Map** | Bảng "hành động ở A → phải verify gì ở B" + case ID. **BẮT BUỘC** |
| Ưu tiên chạy (Wave 1–4) | Wave 1 = mọi case critical |
| Điều kiện để execute được | Những gì phải gỡ trước |
| Quy ước ID | Prefix × module |

### `99_OPEN_ITEMS_AND_QUESTIONS.md` phải có

| Mục | Nội dung |
|---|---|
| **A** | Spec đã tự tuyên bố NOT CONFIRMED / TBD → **KHÔNG test, KHÔNG viết Expected** |
| **B** | **MÂU THUẪN giữa các tài liệu** (hoặc giữa 2 chỗ trong cùng 1 tài liệu) — nêu rõ trích dẫn từng bên |
| **C** | Gap spec — spec không định nghĩa. Xếp 🔴 (mất data/pháp lý/store reject) → 🟠 → 🟡 |
| **D** | Điều kiện môi trường bắt buộc × module bị chặn |
| **E** | Thứ tự khuyến nghị gỡ blocker × ai làm × lý do |

---

## PHẦN 2 — Format 1 test case trong markdown

Header bảng, rồi bullet block bên dưới:

```markdown
| ID | Cat | Pri | Title |
|---|---|---|---|
| AUTH-001 | POS | critical | Signup thành công với name + DOB + phone + OTP đúng |

- **Pre:** App cài mới, chưa từng đăng nhập. Số `+6591000001` chưa tồn tại.
- **Steps:** 1) Mở app → Sign up. 2) Name = `Nguyen Test A`. 3) DOB = `01/01/1995`. 4) Submit → nhận OTP. 5) Nhập OTP đúng.
- **Test data:** UUID đọc trực tiếp từ DB, ví dụ `9f1c2d34-...`
- **Expected:** 1) Tài khoản tạo thành công, vào Home Feed. 2) DB: tồn tại 1 record với `uuid` dạng UUID.
- **Ghi chú severity:** Đây là rủi ro consumer-protection, không phải copy nit.
```

### Quy tắc bắt buộc

| Quy tắc | Vì sao |
|---|---|
| **Nhiều case liên tiếp CHIA SẺ 1 bullet block** — parser tự gán cho cả nhóm | Tránh copy-paste 3 lần cho AUTH-003/004/005 cùng logic |
| Steps đánh số `1) 2) 3)` trên cùng 1 dòng | Parser tự tách thành nhiều dòng trong Excel |
| Expected đánh số `1) 2) 3)`, **verifiable**, không được "hoạt động đúng" | "No errors" không kiểm được |
| **Con số phải chính xác** — "quota còn ~400MB", không phải "quota giảm" | "giảm đâu đó" không phát hiện được bug tính sai |
| Pre-condition ghi rõ: app state + data phải có + user role + tier + platform | Người khác phải repro được |
| Test data là giá trị **cụ thể** | "valid email" không chạy được |
| `⛔BLOCKED` ở cột Cat khi spec chưa chốt — **KHÔNG viết Expected** | Viết Expected = QA tự quyết thay PO |
| `⛔ Cần PO xác nhận` trong Expected khi spec có gap | Ghi câu hỏi, không đoán |
| Cross-reference: `- Chi tiết XXX-001` / `- Xem XXX-001` | Không nhân bản case, nhưng vẫn truy vết được requirement |

### Cat và Pri

- **Cat:** `POS` `NEG` `UI` `EDGE` `BOUNDARY` `SEC` `PERF` `A11Y` `PLAT` `⛔BLOCKED`
- **Pri:** `critical` → P0 (auth/mất data/payment/security/PDPA) · `high` → P1 (core CRUD + cross-module) · `medium` → P2 (edge/a11y/perf/platform)

### Cảnh báo môi trường đặt ĐẦU file module

Khi module cần điều kiện đặc biệt, viết blockquote ngay sau header:

```markdown
> ⚠️ **Cảnh báo môi trường trước khi chạy module này:**
> 1. Phần lớn case yêu cầu **chờ tới đúng thời điểm push bắn** — không verify được bằng nhìn UI.
> 2. Case reboot cần **thiết bị thật**, emulator giữ state khác.
> Nếu chưa có → báo trước, đừng chạy rồi kết luận "pass" bằng cách nhìn UI.
```

---

## PHẦN 3 — Format Excel

### Sheet: MỖI MODULE 1 SHEET

- `00_SUMMARY` ở vị trí đầu
- `NN_<Module Name>` cho từng module, tên ≤31 ký tự, strip `[]:*?/\`
- Module có sub-module (vd §2.1–2.8) → **vẫn 1 sheet**, dùng cột `Sub-module` để lọc

### 14 cột

| # | Cột | Ghi chú |
|---|---|---|
| A | ID | |
| B | Module | tên section từ spec |
| C | Sub-module | để lọc trong sheet lớn |
| D | Test Case Description | |
| E | Pre-condition | |
| F | Test Case Procedure | mỗi step 1 dòng |
| G | Test Data | |
| H | Expected Output | |
| I | Actual Result | trống |
| J | **Result** | tô màu |
| K | Test Date | trống |
| L | **Priority** | tô màu |
| M | Category | |
| N | Note | |

Width: `[14, 22, 22, 44, 34, 56, 26, 52, 26, 11, 12, 9, 12, 34]`

### Màu

| Cột | Giá trị | Màu |
|---|---|---|
| Result | PASS | `92D050` xanh |
| Result | FAIL | `FF0000` đỏ + chữ trắng bold |
| Result | PENDING | `FFFF00` vàng |
| Result | BLOCKED | `FFA500` cam |
| Priority | P0 | `FFC7CE` đỏ nhạt |
| Priority | P1 | `FFEB9C` vàng nhạt |
| Priority | P2/P3 | `E2EFDA` xanh nhạt |
| Header | | `1F4E79` + chữ trắng bold |
| Row lẻ/chẵn | | `FFFFFF` / `EBF3FB` |

### Mọi sheet phải có

- `freeze_panes = "A2"`
- `auto_filter` phủ hết vùng data (không chỉ header row)
- `wrap_text=True`, `vertical="top"`
- Row height tính theo độ dài nội dung, cap 300

### Sheet `00_SUMMARY`

- Title merge, nền `1F4E79`
- Bảng: Sheet × Module × Cases × P0 × P1 × P2 × BLOCKED × 9 category
- Dòng TỔNG nền đậm
- **Khối ghi chú cảnh báo** (đỏ) — để người mở file lần đầu KHÔNG tưởng đây là bộ case chạy được ngay:
  1. Toàn bộ PENDING, chưa execute, chưa có automation
  2. Case cam = BLOCKED, spec chưa chốt, xem file 99
  3. Case UI viết theo text spec, chưa có Figma
  4. N điều kiện môi trường phải gỡ trước
  5. Cross-reference chỉ chạy 1 lần ở module gốc
  6. Nghĩa của P0/P1/P2

### 3 loại Expected Output — phải phân loại tường minh, KHÔNG để ô trống im lặng

| Giá trị | Nghĩa |
|---|---|
| Expected đầy đủ | Chạy được |
| `→ Dùng Expected của case được tham chiếu: …` | Cross-ref, chỉ chạy 1 lần ở module gốc |
| `[CẦN BỔ SUNG] Case 1 dòng — Expected chi tiết viết khi có Figma/build.` | Gap thật, không phải sót |
| (trống, Result=BLOCKED) | Cố tình không viết, chờ PO |

---

## PHẦN 4 — Script export

Dùng `scripts/export_testcases_from_md.py` trong skill này. Copy vào output dir thành `export_test_cases.py`, sửa `BASE_DIR` + `PROJECT`.

**Bắt buộc trước khi save/run:**
1. `ast.parse()` validate syntax
2. `get_column_letter(n)`, không dùng `chr(64+n)`
3. `encoding="utf-8"` khi đọc markdown (nội dung tiếng Việt)
4. Chạy xong phải **verify bằng cách load lại file** và spot-check ≥2 case, trong đó ≥1 case thuộc nhóm chia sẻ bullet block (kiểm parser gán đúng)

**Script phải in ra:**
- Số case mỗi sheet
- Danh sách ID BLOCKED
- Số case cross-ref
- Số case `[CẦN BỔ SUNG]` + liệt kê ID

Con số này phải **đối chiếu với con số đã khai trong `00_COVERAGE_MATRIX.md`**. Lệch thì sửa matrix cho khớp thực tế, **không** sửa số cho đẹp.

---

## PHẦN 5 — Kỷ luật khi viết (những gì làm nên chất lượng)

1. **Mọi ràng buộc "server-side" trong spec → 1 case gọi API trực tiếp bypass UI.** Test qua UI không chứng minh được gì. Nếu spec có câu kiểu "a client-only limit is a bug" thì đây là yêu cầu tường minh.
2. **Không test module đơn lẻ ở nơi có ripple.** Lập ripple map trước, mỗi state change verify hết các module consume state đó.
3. **Case cần chờ thời gian thật → ghi rõ phải chờ thật.** Reminder bị cancel, re-bump 3 ngày, streak 7 ngày: nhìn UI không kết luận được.
4. **Case đếm chi phí viết riêng** khi spec nói tới chi phí đơn vị (vd moderation ops/ảnh) — đây là case tiền bạc, không phải case chức năng.
5. **Feature out-of-scope → viết NEG case xác nhận KHÔNG truy cập được** (UI + API).
6. **Gap spec → ⛔ + câu hỏi, không đoán Expected.**
7. **Mâu thuẫn giữa tài liệu → nêu trích dẫn cả 2 bên**, để PO thấy chính xác chỗ vênh.
8. **Đọc spec để tìm rủi ro, không chỉ để liệt kê requirement.** Phần giá trị nhất của deliverable thường là mục C của file 99 — những gì spec KHÔNG nói.

---

## Two-phase rule vẫn áp dụng

Format này là cho **Phase 1 (manual)**. Xuất Excel xong vẫn **DỪNG**, chờ user confirm mới viết automation.
