---
name: chatbot-platform-config-audit
description: Use BEFORE editing any chatbot instruction or knowledge base — dumps every platform-level toggle/select/model setting first, so symptoms owned by the platform layer are not chased through prompt edits. Includes InCard Agentic specifics (wizard steps, do_not_go_beyond_instructions, save = Next).
---

# Kiểm kê cấu hình platform TRƯỚC khi sửa prompt hay KB

## Vì sao bắt buộc

Ngày 8/8/2026 tôi đốt gần trọn một phiên để đuổi chuỗi
`"Tôi không tìm thấy thông tin này trong tài liệu được cung cấp."`
qua **5 bản instruction và 4 bản KB**. Nguồn thật của nó là một **công tắc**:

```
do_not_go_beyond_instructions = true
```

Tệ hơn: điều này **đã được ghi lại** từ bot 276 trong `lesson_platform-guard-outranks-prompt`, nhưng bot 291 là bot **mới** nên tôi không nghĩ tới. Bot mới trên cùng platform **thừa hưởng cùng bộ guard** — kiểm kê ở lúc tạo bot, không phải lúc debug.

## Quy trình

1. **Dump toàn bộ** trước khi sửa dòng nào. Đừng đọc bằng mắt qua UI — lấy bằng script, lưu ra file, để còn `diff` về sau.
2. Ghi lại **cả những công tắc trông vô hại**. `show_citations`, `enable_image_reply`, `language`, `ai_model` đều đổi hình dạng câu trả lời.
3. Chỉ khi bảng này sạch mới được kết luận "lỗi nằm ở instruction".

Script mẫu (Playwright, sau khi đã vào đúng bước Configure):

```js
await p.evaluate(() => ({
  congTac: [...document.querySelectorAll('input[type="checkbox"]')]
    .map((c) => ({ name: c.name, bat: c.checked })),
  chon: [...document.querySelectorAll('select')]
    .map((s) => ({ name: s.name, gt: s.value, chu: s.selectedOptions[0]?.textContent.trim() })),
  radio: [...document.querySelectorAll('input[type="radio"]')]
    .filter((r) => r.checked).map((r) => ({ name: r.name, gt: r.value })),
}));
```

## Triệu chứng → nghi can

| Triệu chứng | Nghi can đầu tiên |
|---|---|
| Một câu từ chối **giống hệt từng ký tự**, không đổi dù xoá khỏi instruction | `do_not_go_beyond_instructions` |
| Câu trả lời kèm tên file / trích nguồn mà instruction không yêu cầu | `show_citations` |
| Bot gửi ảnh sai hoặc tự gắn ảnh | `enable_image_reply` + cấu hình Google Drive (ảnh chọn theo **tên file**) |
| Bot nhớ tên khách giữa các phiên test → nhiễu kết quả đo | `customer_memory_enabled` |
| Trả lời sai ngôn ngữ, hoặc chèn tiếng Anh | `language` (`auto` vs `vi`) |
| Chất lượng đổi hẳn mà chẳng ai sửa gì | `ai_model` = "Default (global setting)" — admin đổi global là bot đổi theo |
| Có lượt bot trả lời như người thật | `interaction_type` ≠ `Only AI` |

## Test phân biệt guard vs. retrieval vs. prompt (2 lượt, rẻ)

Hỏi **cùng một nội dung** theo hai cách:
- bằng **tên đầy đủ** của bản ghi trong KB;
- bằng **cách gọi tắt** của khách.

| Kết quả | Kết luận |
|---|---|
| Cả hai đều ra chuỗi cố định | guard hoặc thiếu dữ liệu — **không** sửa prompt |
| Tên đầy đủ đúng, gọi tắt chặn | **retrieval khớp theo tên bản ghi** — sửa ở lớp dữ liệu/retrieval |
| Cả hai trả lời được, chỉ sai hình dạng | đúng là việc của instruction |

## InCard Agentic — chi tiết đã trả giá

- Wizard: `1 Configure · 2 Customize · 3 Train · 4 Embed · 5 Channel`.
  Menu **"Customize" mở bước 2**. Ô `instructions` nằm ở **bước 1**, mở bằng menu **"Edit"**. Bấm nhầm từng làm mở **form tạo bot mới** với ô instructions rỗng — suýt lưu đè.
- **Lưu = bấm "Next"**, không có nút Save.
- Trang giữ **nhiều** `textarea[name="instructions"]` (mỗi bot một wizard) và **nhiều** nút `Next`. Luôn lọc theo `isVisible()` **và** đối chiếu nội dung mở đầu trước khi ghi.
- Sau khi lưu: **mở lại từ dashboard và đọc ngược từ server**, so từng ký tự. Đừng tin ô nhập.
- Train → tab **Text**: **xoá bản cũ trước khi nạp bản mới**. Train chồng KHÔNG thay thế — đã gây một sản phẩm hai giá, model né bằng cách hỏi ngược khách.
- Đóng file KB trong editor trước khi train — editor đã từng ghi đè file trên đĩa bằng bản cũ.

## Ghi lại

Lưu bảng kiểm kê vào `~/.claude/shared-context/knowledge/[project].md` ngay lần đầu, kèm ngày. Lần sau chỉ cần `diff`.

Liên quan: `chatbot-instruction-authoring`, `verify-the-instrument-before-the-finding`, `diagnosis-before-fixing`.
