---
name: chatbot-platform-config-audit
description: Use BEFORE editing any chatbot instruction or knowledge base — inventory every platform-level toggle/model setting first, because they change what the instruction is allowed to do. Includes InCard Agentic specifics (strict-adherence flag, wizard steps, save = Next, train-stacking).
---

# Kiểm kê cấu hình platform TRƯỚC khi sửa prompt hay KB

## Vì sao

Ba lớp. Sửa nhầm lớp là đốt cả buổi:

| Lớp | Sở hữu | Sửa ở đâu |
|---|---|---|
| **Config platform** | bot có được ứng biến không, có kèm citation không, model nào, ngôn ngữ nào | dashboard |
| **KB / truy xuất** | bot có mở được mục hay không | file train — xem `chatbot-kb-file-design` |
| **Instruction** | bot **phải làm gì** khi có và khi không có dữ liệu | ô instructions |

Kiểm kê **một lần, bằng script, lưu ra file** để lần sau chỉ cần `diff`.

```js
await p.evaluate(() => ({
  congTac: [...document.querySelectorAll('input[type="checkbox"]')].map((c) => ({ name: c.name, bat: c.checked })),
  chon: [...document.querySelectorAll('select')].map((s) => ({ name: s.name, gt: s.value, chu: s.selectedOptions[0]?.textContent.trim() })),
  radio: [...document.querySelectorAll('input[type="radio"]')].filter((r) => r.checked).map((r) => ({ name: r.name, gt: r.value })),
}));
```

---

## Cờ TUÂN THỦ NGHIÊM — hiểu cho đúng

InCard: `do_not_go_beyond_instructions`. Các platform khác: strict mode, "chỉ trả lời theo tài liệu".

**BẬT = bot tuân thủ tuyệt đối instruction.** Đây là chế độ **nên dùng** cho bot bán hàng.
Nhưng nó **khuếch đại chất lượng instruction theo cả hai chiều**:

| Instruction | Kết quả ở chế độ nghiêm |
|---|---|
| đầy đủ, không mâu thuẫn | bot làm rất sát — viết câu mẫu sao ra vậy |
| có lỗ hổng / có mâu thuẫn | bot **không tự nghĩ ra lối thoát** → rơi về câu mặc định của platform |

> ⚠️ **Sai lầm đã mắc:** thấy chuỗi mặc định `"Tôi không tìm thấy thông tin này trong tài liệu
> được cung cấp."` tôi kết luận đó là **guard đè lên prompt** và đi cấm chuỗi đó qua 5 bản
> instruction — vô ích. Nó là **triệu chứng của lỗ hổng instruction**. User vá bằng cách **viết
> câu mẫu tường minh cho đúng tình huống đang rơi** thì hết ngay.

→ Thấy câu mặc định của platform, hỏi: **"instruction thiếu câu mẫu cho tình huống nào?"**
Đừng hỏi "làm sao chặn chuỗi này".

> ⚠️ Mâu thuẫn với memory `lesson_platform-guard-outranks-prompt` (nói ngược lại: chuỗi ra y hệt
> = guard platform) — cần reconcile.

---

## Triệu chứng → nghi can

| Triệu chứng | Nghi can |
|---|---|
| Rơi về câu từ chối mặc định của platform | **lỗ hổng instruction** ở chế độ nghiêm — bịt bằng câu mẫu, không phải bằng lệnh cấm |
| Bot ứng biến, nói thứ không có trong tài liệu | cờ tuân thủ nghiêm đang **TẮT** |
| Kèm tên file / trích nguồn mà instruction không yêu cầu | `show_citations` |
| Gửi ảnh sai hoặc tự gắn ảnh | `enable_image_reply` + Google Drive (ảnh chọn theo **tên file**) |
| Bot nhớ khách giữa các lượt test → nhiễu số đo | `customer_memory_enabled` |
| Sai ngôn ngữ, chèn tiếng Anh | `language` (`auto` vs `vi`) |
| Chất lượng đổi hẳn mà không ai sửa gì | `ai_model` = "Default (global setting)" — admin đổi global là bot đổi theo |
| Có lượt trả lời như người thật | `interaction_type` ≠ Only AI |

Bot **mới** trên cùng platform **kế thừa cùng bộ cấu hình mặc định**. Kiểm kê lúc **tạo** bot,
đừng đợi lúc debug.

---

## Test 2 lượt: lỗi thuộc lớp nào

Hỏi **cùng một nội dung** bằng **tên đầy đủ bản ghi** và bằng **cách gọi tắt của khách**.

| Kết quả | Lớp có lỗi |
|---|---|
| Tên đầy đủ đúng, gọi tắt chặn | **truy xuất / KB** — xem `chatbot-kb-file-design` |
| Cả hai đều rơi về câu mặc định | **instruction thiếu câu mẫu** cho tình huống đó |
| Cả hai trả lời được, chỉ sai hình dạng | **instruction** — sai luật trình bày |

---

## InCard Agentic — bẫy thao tác đã trả giá

- Wizard: `1 Configure · 2 Customize · 3 Train · 4 Embed · 5 Channel`.
  Menu **"Customize" mở bước 2**. Ô `instructions` ở **bước 1**, mở bằng menu **"Edit"**.
  Bấm nhầm từng mở **form tạo bot mới** với ô instructions rỗng — suýt lưu đè.
- **Lưu = bấm "Next"**, không có nút Save.
- Trang giữ **nhiều** `textarea[name="instructions"]` (mỗi bot một wizard) và **nhiều** nút `Next`.
  Lọc theo `isVisible()` **và** đối chiếu nội dung mở đầu trước khi ghi.
- Sau khi lưu: **mở lại từ dashboard, đọc ngược từ server, so từng ký tự.** Đừng tin ô nhập.
- Train → tab **Text**: **xoá bản cũ trước khi nạp bản mới**. Train chồng KHÔNG thay thế.
- Đóng file KB trong editor trước khi train — editor đã từng ghi đè bản trên đĩa bằng bản cũ.

---

Lưu bảng kiểm kê vào `~/.claude/shared-context/knowledge/[project].md` kèm ngày.

Liên quan: skill `chatbot-instruction-authoring`, `chatbot-kb-file-design`; memory (không phải
skill) `lesson_verify-the-instrument-before-the-finding.md`, `feedback_diagnosis-before-fixing.md`.
