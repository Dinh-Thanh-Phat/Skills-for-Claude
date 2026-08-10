---
name: chatbot-kb-file-design
description: Use when designing or repairing the knowledge base of a RAG chatbot — decide how many .md files to train and what goes in each. Rule: one file per INTENT the bot must serve, not one giant catalogue file. Covers comparison files, lookup tables, retrieval keys, and train-stacking.
---

# Thiết kế file KB cho chatbot RAG

Rút từ NARENCA (InCard Agentic) 6–10/8/2026, sau khi làm hỏng theo đúng hướng ngược lại.

---

## Luật 1 — MỘT FILE cho MỘT Ý ĐỊNH của khách, không phải một file cho cả catalogue

Đây là điểm user chỉ ra sau khi tôi thất bại: tôi cố dạy bot **so sánh sản phẩm** bằng cách
(a) viết luật 5 bước vào instruction, rồi (b) nhồi bảng so sánh vào **file KB lớn 153.000 ký tự**.
**Hỏng cả hai đường** — 3/9 lượt, có lượt bịa hẳn sản phẩm và giá.

Cách đúng:

```
NARENCA_SanPham.md      ← chi tiết từng biến thể (giá, ảnh, link, mô tả)
NARENCA_SoSanh.md       ← file RIÊNG: từng cặp/nhóm hay bị so sánh, viết sẵn đáp án
NARENCA_ChinhSach.md    ← ship, bảo hành, đổi trả, VAT
```

Instruction chỉ cần **một luật nhỏ** trỏ tới file mới:
> Khách nhờ so sánh hai dòng hoặc hai cỡ → đọc tài liệu so sánh trước, trả lời theo đúng cặp
> ghi trong đó. Không có cặp khớp thì dùng §11b(c).

**Vì sao hiệu quả hơn:** truy xuất chỉ lấy vài đoạn cho mỗi truy vấn. Một khối so sánh nằm lẫn
giữa 31 khối sản phẩm gần như không bao giờ được chọn — nó phải cạnh tranh với chính các sản phẩm
mà khách vừa nhắc tên. Tách file thì khối so sánh trở thành **kết quả tự nhiên** của câu hỏi
so sánh.

**Dấu hiệu cần tách file:** bạn đang định viết bước 3, bước 4, bước 5 vào instruction cho một
dạng câu hỏi. Luật nhiều bước = hành vi phức tạp = **thiếu dữ liệu đã soạn sẵn**, không phải
thiếu luật.

---

## Luật 2 — Dữ liệu tổng hợp phải là đáp án ĐÓNG, ĐẾM ĐƯỢC

Đo trên 3 bản bảng tra nhanh:

| Bản | Nội dung | Kết quả |
|---|---|---|
| 1 | bảng giá + danh sách hết hàng + các cỡ | vá được D03, D05, B37; **B27 vẫn 0/5** |
| 2 | thêm khối "gợi ý so sánh" dạng **khuôn điền sẵn** liệt kê nhiều sản phẩm | B27 lên 4/4 nhưng **B37 3/3→1/3, C02 2/3→1/4** |
| 3 | giữ 3 khối đáp án đóng, **bỏ** khối so sánh và khối quà tặng | tốt nhất mọi mặt |

→ Khối tổng hợp được phép chứa: *"Đang hết hàng: A, B, C"*, *"Rẻ nhất: X — 250.000₫"*,
*"Các cỡ đang bán: 10cm, 10.6cm, 16cm, 20cm, 23cm, 30cm, 140mm, 200mm"*.
→ **Không** được chứa khuôn dạng *"Nếu khách hỏi so sánh thì nêu <mẫu A> và <mẫu B>…"* —
model coi đó là mệnh lệnh điền chỗ trống và **bịa ra thứ để điền**.

---

## Luật 3 — Truy xuất khớp theo TÊN bản ghi, không theo dòng `Từ khoá:`

Test quyết định (2 lượt, rẻ): hỏi **cùng một nội dung** bằng **tên đầy đủ của mục `###`** và
bằng **cách gọi tắt của khách**.

- Tên đầy đủ đúng, gọi tắt chặn → **lỗi truy xuất**, không phải thiếu dữ liệu.

Tôi **dự đoán trước** rằng thêm alias vào dòng `Từ khoá:` sẽ vá được, rồi thêm **302 alias**.
Kết quả **K37 0/3 → 0/3, K39 0/3 → 0/3**. Không nhúc nhích. **Dòng `Từ khoá:` không tham gia
truy xuất theo cách tôi nghĩ.**

→ Muốn khách gọi tắt vẫn ra đúng mục thì **đặt cách gọi tắt vào TIÊU ĐỀ `###`** hoặc tách hẳn
một file "cách gọi thông dụng → tên chính thức", chứ không nhét vào một dòng metadata trong thân bài.

---

## Luật 4 — KB không được chứa chữ dành cho người vận hành

Tôi từng chuẩn hoá dòng trạng thái thành `Tình trạng: HẾT HÀNG — không chào bán, không nhận đơn`.
Bot **đọc nguyên văn cho khách**. Mọi chữ trong KB đều có thể bị đọc lên.

→ KB chỉ chứa **sự thật về sản phẩm**. Chỉ dẫn hành vi thuộc về instruction. Nhãn kỹ thuật
(`Tình trạng:`, `Giá bán:`, `Phân biệt:`) phải được instruction cấm xuất hiện trong câu trả lời.

---

## Luật 5 — Train THÊM không phải train THAY THẾ

Nạp file mới mà không xoá bản cũ → **KB giữ cả hai**. Đã gây một sản phẩm hai giá; model né bằng
cách hỏi ngược khách, và tôi tưởng là lỗi instruction, đi vá instruction.

→ Trước khi train: **xoá bản cũ ở tab Text**, train xong thì **grep lại KB** để chắc mỗi sản phẩm
chỉ còn một giá. Grep KB **trước** khi kết luận một lỗi là lỗi prompt.

---

## Luật 6 — An toàn khi sinh/sửa KB bằng script

Ba lỗi thật, đều mất thời gian:

- **`indexOf('### ')` khớp trúng chuỗi nằm trong văn xuôi** của phần mở đầu ("Mỗi mục ### là MỘT
  biến thể riêng…") → sinh ra một khối rác `### là MỘT biến thể riêng`. Lần trước cũng vậy với `![`.
  → Khi tách theo dấu Markdown, **chỉ khớp ở đầu dòng** (`/^### /m`), không khớp giữa dòng.
- **Editor đang mở file ghi đè bản trên đĩa** — 302 alias biến mất, khối rác quay lại.
  → Đóng file trong editor trước khi chạy script, và **so md5 với bản backup** trước khi train.
- **Luôn đếm bất biến trước khi ghi**: số mục `###`, số dòng `Giá bán:`, số dòng `Tình trạng:`.
  Lệch một con số là **không ghi**.

---

## Checklist trước khi train

- [ ] Mỗi ý định của khách có file riêng, hay đang nhồi hết vào một file?
- [ ] Khối tổng hợp là đáp án đóng, không phải khuôn điền sẵn?
- [ ] Cách khách gọi tắt có nằm trong **tiêu đề** mục không?
- [ ] KB có chữ nào dành cho người vận hành không?
- [ ] Đã xoá bản train cũ chưa?
- [ ] Đã đóng file trong editor, đã so md5, đã đếm bất biến chưa?
- [ ] Mỗi sản phẩm chỉ còn đúng một giá? (grep)

Liên quan: `chatbot-instruction-authoring`, `chatbot-platform-config-audit`,
`python-code-gen-safety`.
