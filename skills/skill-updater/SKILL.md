---
name: skill-updater
description: Khi user phản hồi xử lý sai hoặc yêu cầu tạo skill mới — tự detect skill liên quan, sửa theo feedback, hoặc tạo skill mới từ mô tả của user
origin: PT
---

# Skill Updater — Tự Detect, Cập Nhật & Tạo Mới Skills

Hai chế độ:
- **Sửa skill cũ:** User mô tả kết quả sai → Claude tự detect skill liên quan → đề xuất sửa
- **Tạo skill mới:** User mô tả nhu cầu mới → Claude tạo skill mới → lưu vào `~/.claude/skills/`

---

## Phân Biệt 2 Chế Độ

| Dấu hiệu | Chế độ |
|---|---|
| "Lúc nãy làm sai", "phải làm khác đi", "lần sau khi X thì Y" | **Sửa skill cũ** |
| "Tôi cần xử lý...", "có thể làm được... không", "tạo thêm skill" | **Tạo skill mới** |

---

## CHẾ ĐỘ 1 — Sửa Skill Cũ (Feedback)

---

## When to Activate

- User mô tả kết quả sai: "lúc nãy nó làm A nhưng phải làm B mới đúng"
- User chỉnh lại output: "báo giá thiếu cột VAT", "report không có ranking"
- User nói "lần sau khi tôi nói X thì phải làm Y"
- User nói "xử lý kiểu đó không đúng với trường hợp của tôi"
- User nói "phải hỏi tôi thêm thông tin trước khi làm"
- Bất kỳ feedback nào về cách Claude xử lý một task Excel/sale/vận hành

---

## Bước 1 — Detect Skill Liên Quan

Đọc lại context conversation để xác định task vừa thực hiện là gì.

**KHÔNG dùng bảng skill gõ cứng** — thư viện có ~170+ skill và thay đổi hằng ngày (routine `daily-skill-evolution`). Discover bằng lệnh:

```bash
# 1. Danh sách skill LOADABLE (dạng thư mục)
ls ~/.claude/skills
# 2. Tìm theo keyword của task trong name/description/triggers
grep -il "<keyword>" ~/.claude/skills/*/SKILL.md
grep -i -A1 "^description:" ~/.claude/skills/*/SKILL.md | grep -i "<keyword>"
```

Ưu tiên skill có `description`/`triggers` khớp nhất với task vừa làm. Với task QA, đối chiếu thêm bảng route trong `qa-router` (entry point).

> ⚠️ **13 file business phẳng ở gốc** (`quote-builder.md`, `price-list-manager.md`, `customer-segmentation.md`,
> `sales-pipeline-tracker.md`, `commission-calculator.md`, `returns-processor.md`, `reorder-suggester.md`,
> `delivery-scheduler.md`, `contract-tracker.md`, `order-aggregation.md`, `order-verification.md`,
> `order-reconciliation.md`, `order-reporting.md`) **hiện KHÔNG được Claude Code load** — Claude Code chỉ load
> `<name>/SKILL.md`. Nếu feedback liên quan tới chúng: báo user rằng file đó không tự kích hoạt, và hỏi có muốn
> chuyển sang dạng `<name>/SKILL.md` không (user quyết định, không tự chuyển).

Nếu không chắc, hỏi user:
> "Vấn đề bạn gặp xảy ra khi đang làm gì (task nào, bước nào)?"

---

## Bước 2 — Hiểu Vấn Đề Cụ Thể

Phân tích feedback của user để xác định loại lỗi:

| Loại feedback | Phần skill cần sửa |
|---|---|
| "Lần sau khi tôi nói X thì mới kích hoạt" | `When to Activate` — thêm trigger |
| "Không xử lý được trường hợp X" | Thêm case/bước mới vào workflow |
| "Output thiếu Y / format sai" | Sửa phần `Output` |
| "Hỏi tôi thêm thông tin trước khi làm" | Thêm bước clarification vào đầu workflow |
| "Đừng giả định X, hỏi tôi trước" | Thêm vào phần lưu ý hoặc bước đầu |
| "Gặp lỗi Z chưa biết xử lý" | Thêm vào bảng `Lỗi Thường Gặp` |

---

## Bước 3 — Đọc Skill Hiện Tại

**Convention loadable duy nhất:** `~/.claude/skills/[skill-name]\SKILL.md` (+ `references/` tuỳ chọn).

File phẳng `~/.claude/skills/[skill-name].md` (13 file business cũ) vẫn đọc/sửa được, nhưng **không được
Claude Code load** — sửa chúng không thay đổi hành vi. Khi sửa một file phẳng, nhắc user điều này.

Thử folder trước (`[name]/SKILL.md`); nếu không có thì thử file (`[name].md`).
Dùng Read tool để đọc toàn bộ nội dung skill được detect ở Bước 1.

---

## Bước 4 — Đề Xuất Thay Đổi (LUÔN HỎI TRƯỚC)

Trình bày rõ trước khi sửa:

```
🔍 Tôi detect vấn đề này liên quan đến skill: [skill-name]

Vấn đề: [mô tả vấn đề user gặp]
Chỗ cần sửa: [tên phần trong skill]

Thay đổi đề xuất:
  TRƯỚC: [nội dung hiện tại]
  SAU:   [nội dung sau khi sửa]

Sửa theo feedback này không?
```

---

## Bước 5 — Update File Sau Khi User Xác Nhận

Sửa file ở đúng convention đã detect ở Bước 3:
- Folder skill: `~/.claude/skills/[skill-name]\SKILL.md`
- Single-file skill: `~/.claude/skills/[skill-name].md`

Cho business skills (PT — chỉ máy maintainer, bỏ qua nếu không có), backup vào: `D:\HK8\Learning\DQ\PT\skills\[skill-name].md`
(QA skills không cần backup — chỉ lưu ở `~/.claude/skills/`.)

### Bước 5b — Gate "người khác pull về dùng được ngay" (áp cho CẢ sửa lẫn tạo mới)

Skill dùng chung được hook đồng bộ đẩy lên repo Skills-for-Claude, nơi người khác cài bằng `setup.ps1`/`setup.sh`.
Lỗi máy maintainer KHÔNG thấy (Windows không phân biệt hoa/thường, đường dẫn của mình luôn tồn tại), nên
phải kiểm chủ động trước khi coi là xong:

| Kiểm | Vì sao (đã xảy ra 2026-10-05) |
|---|---|
| File tên đúng `SKILL.md` (hoa) | 4 skill tên `skill.md` → Mac/Linux không load |
| UTF-8 **không BOM**, dòng 1 là `---` | 19 skill có BOM → front-matter hỏng, KHÔNG load kể cả trên máy mình suốt nhiều tháng |
| Front-matter có `name` + `description` | description là thứ Claude dùng để chọn skill |
| Không đường dẫn cứng `C:\Users\<me>`, `D:\HK8...` | dùng `~/...`, `os.path.expanduser`, hoặc biến môi trường |
| Không nhắc skill cá nhân như thể bắt buộc | ghi "(nếu đã cài)" — máy người khác không có odoo-*/incard-* |
| Skill gắn tài khoản/dự án riêng | thêm tên vào `PERSONAL` trong `~/.claude/hooks/sync-skills-repo.py`, nếu không sẽ bị đẩy lên |
| Cần công cụ/API key mới | thêm dòng vào `docs/REQUIREMENTS.md` của repo |

Chạy trong repo: `python tools/check_skills.py --catalog` → phải `0 problem(s)`, commit cả `SKILLS.md`.
**Sửa bằng Bash/Python script KHÔNG kích hoạt hook** → sau đó phải `diff -rq --strip-trailing-cr` rồi sync + push tay
(chỉ skill testing/QA; skill không chắc → hỏi user). Đổi cấu trúc repo/installer → cài thử vào HOME giả
(`HOME=<tmp> USERPROFILE=<tmp> python install.py --skip-plugins`) từ một bản clone mới trước khi báo xong.

---

## Bước 6 — Ghi Log

Append vào `~/.claude/skills/_update-log.md`:

```markdown
## [skill-name] — [ngày]
- **Feedback:** [user nói gì]
- **Sửa chỗ:** [phần đã thay đổi]
- **Thay đổi:** [tóm tắt nội dung sửa]
```

---

## Ví Dụ Thực Tế

**User:** "Lúc nãy tạo báo giá xong nhưng không có dòng tổng cộng bằng chữ, lần sau phải có"

→ Claude detect: task "tạo báo giá" → skill `quote-builder`  
→ Loại lỗi: thiếu format trong Output  
→ Đề xuất: thêm dòng "Bằng chữ: [số tiền viết bằng chữ]" vào template Output  
→ User OK → sửa file → ghi log

---

**User:** "Khi tôi gộp file đơn mà có cột tên nhân viên viết hoa viết thường lẫn lộn thì bị tách ra 2 người khác nhau"

→ Claude detect: "gộp file đơn" → skill `order-aggregation`  
→ Loại lỗi: chưa có bước normalize tên trước khi gộp  
→ Đề xuất: thêm bước dùng `fuzzy_match` normalize tên NV trước bước aggregate  
→ User OK → sửa → ghi log

---

## CHẾ ĐỘ 2 — Tạo Skill Mới

### Khi Nào Tạo Mới

Khi user mô tả nhu cầu chưa có skill nào cover:
- "Tôi cần xử lý bảng chấm công, tính tăng ca..."
- "Có thể làm báo cáo công nợ theo nhà cung cấp không?"
- "Tạo thêm skill để xử lý X"

### Bước 1 — Hỏi Làm Rõ (nếu cần)

Nếu mô tả còn chung chung, hỏi thêm:
> - "Dữ liệu đầu vào là file gì? Có những cột nào?"
> - "Output mong muốn trông như thế nào?"
> - "Hay gặp vấn đề gì nhất khi làm thủ công?"

### Bước 1b — Kiểm Tra Skill Đã Tồn Tại (LUÔN LÀM TRƯỚC KHI TẠO MỚI)

So sánh mô tả của user với **toàn bộ** skill hiện có — discover, không dùng danh sách gõ cứng:

```bash
ls ~/.claude/skills                                   # tên thư mục = skill loadable
ls ~/.claude/skills/*.md                              # file phẳng (KHÔNG loadable, xem cảnh báo ở Bước 1)
grep -il "<keyword>" ~/.claude/skills/*/SKILL.md      # skill có nhắc keyword
grep -h "^description:" ~/.claude/skills/*/SKILL.md | grep -i "<keyword>"   # overlap description/trigger
```

Dùng 2-3 keyword chính từ yêu cầu (cả tiếng Việt lẫn tiếng Anh). Skill nào khớp → đọc `SKILL.md` để ước lượng overlap.

**Nếu overlap > 50%:** Đề xuất mở rộng skill cũ:
> "Skill [tên] đã xử lý việc này một phần. Tôi có thể thêm trường hợp [X] vào skill đó thay vì tạo skill mới — như vậy gọn hơn. Bạn có đồng ý không?"

**Nếu overlap < 50% hoặc user muốn tạo mới:** Tiếp tục Bước 2.

### Bước 2 — Đặt Tên Skill

Tên **thư mục** kebab-case: `~/.claude/skills/<kebab-name>\SKILL.md`  
Ví dụ: `timesheet-processor/SKILL.md`, `supplier-payable/SKILL.md`, `inventory-tracker/SKILL.md`

> ⚠️ **KHÔNG tạo file `.md` phẳng ở gốc `skills/`** (vd `timesheet-processor.md`). Claude Code chỉ load skill dạng
> `<name>/SKILL.md` — file phẳng tồn tại trên đĩa nhưng không bao giờ kích hoạt (13 file business cũ đang bị như vậy).
> Tên thư mục phải trùng `name:` trong frontmatter và không trùng thư mục đã có (`ls` để kiểm tra).

### Bước 3 — Tạo File Skill

Dùng cấu trúc chuẩn:

```markdown
---
name: [skill-name]            # = tên thư mục
description: [mô tả 1 dòng — "Use when … Triggers on: …"]
triggers:
  - "[cụm từ kích hoạt 1]"
  - "[cụm từ kích hoạt 2]"
scope: [global | tên project]
origin: PT
tools: [tools MCP cần dùng — chỉ ghi nếu thật sự dùng]
---

# [Tên Skill]

## When to Activate
[trigger phrases]

## Bối Cảnh Thực Tế
[vấn đề thực tế skill này giải quyết]

## Workflow
[các bước xử lý với tool params cụ thể]

## Output
[format kết quả mẫu]

## Lỗi Thường Gặp
[bảng lỗi + giải pháp]
```

### Bước 4 — Lưu Vào 2 Nơi

- `~/.claude/skills/[skill-name]/SKILL.md` — để Claude dùng ngay (dạng thư mục, loadable)
- `D:\HK8\Learning\DQ\PT\skills\[skill-name]\SKILL.md` — bản backup (chỉ máy maintainer)

Sau khi tạo: cập nhật `capabilities.md` (theo CLAUDE.md Self-Update), và nếu là skill QA → thêm 1 dòng route vào `qa-router`.
Rồi chạy gate **Bước 5b** (SKILL.md hoa, không BOM, không đường dẫn cứng, skill riêng → `PERSONAL`).

### Bước 5 — Ghi Log

```markdown
## [skill-name] — [ngày] — MỚI TẠO
- **Yêu cầu:** [user mô tả gì]
- **Skill:** [tên file]
- **Tools:** [tools dùng]
```

### Ví Dụ

**User:** "Tôi cần tính tăng ca cho công nhân, mỗi ngày chấm vào giờ, giờ tăng ca tính 1.5x, cuối tháng ra bảng lương"

→ Claude hỏi thêm: "File chấm công có cột giờ vào/ra không? Hay chỉ có tổng giờ?"  
→ User trả lời → Claude tạo `timesheet-processor/SKILL.md`  
→ Lưu vào cả 2 nơi → ghi log → thông báo có thể dùng ngay
