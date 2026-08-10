---
name: chatbot-instruction-authoring
description: Use when writing, repairing, or reviewing the system instruction of a RAG sales/support chatbot (InCard Agentic, Yasaka, Dify, any "instructions + trained docs" platform). Enforces conflict-review before editing, complete fallback coverage, escape hatches for mandatory slots, and section routing.
---

# Viết instruction cho chatbot RAG bán hàng

Rút từ phiên NARENCA (InCard Agentic, bot 276 + 291) 6–10/8/2026. Mỗi luật sinh từ một lỗi
đã đo, phần lớn là **lỗi của tôi**, được chính user chỉ ra.

---

## LUẬT 1 — SỬA bằng cách VIẾT LẠI, không bao giờ bằng cách THÊM VÀO

**Đây là lỗi tốn kém nhất của cả phiên.** Tôi vá từng lỗi bằng cách chèn thêm một mục vào cuối
instruction, không lần nào đọc lại toàn bộ để xem mục mới có **mâu thuẫn** với mục cũ không.
Instruction phình **6.064 → 15.905 ký tự qua ~10 vòng**, và bot chạy *tệ đi*, không tốt lên.

Các mâu thuẫn tôi tự tạo ra rồi tự đi đuổi hàng giờ:

| Mục A nói | Mục B nói | Bot làm gì |
|---|---|---|
| §11 "khi bí thì dùng câu dự phòng này" | §7,§8,§9,§9b "cấm dùng câu dự phòng" | không còn đường hợp lệ → rơi về mặc định platform |
| §10 "không chắc thì đừng nêu tên" | §9b "cấm từ chối, phải so sánh hai bên" | bịa sản phẩm thứ hai cho cân |
| §7 "phải nói rõ lấy ví dụ từ mẫu nào" | §10 "chỉ nêu tên khi đọc thấy dòng ###" | bịa "Quả Địa Cầu Tự Xoay – 25cm" |

**Quy trình bắt buộc mỗi lần sửa:**
1. **Đọc lại TOÀN BỘ** instruction hiện tại trước khi gõ chữ nào.
2. Liệt kê mọi mục **nhắc tới cùng hành vi** với chỗ sắp sửa (từ chối, hỏi lại khách, nêu tên,
   nêu giá, gửi link). Đây là các ứng viên mâu thuẫn.
3. Sửa **tại chỗ** trong các mục đó. Chỉ tạo mục mới khi thực sự là hành vi chưa từng có.
4. **Bảng đối chiếu cuối:** mỗi mục CẤM một hành vi → chỉ ra mục nào cung cấp hành vi thay thế.
   Ô nào trống là một lỗ hổng, và ở chế độ tuân thủ nghiêm thì lỗ hổng = lỗi.
5. Độ dài không tăng thì tốt. Instruction dài ra sau một bản vá là **dấu hiệu** vá sai chỗ.

Bản user viết lại rất tốt chính vì nó **gom** chứ không thêm: mọi mục cấm từ chối đều trỏ về
đúng một catalogue `§11b`, thay vì mỗi mục tự chế một câu.

---

## LUẬT 2 — Instruction phải PHỦ KÍN, vì bot không được phép ứng biến

Nếu platform có cờ kiểu `do_not_go_beyond_instructions` (InCard) / strict mode / "chỉ trả lời
theo tài liệu" và cờ đó **BẬT**, thì bot **tuân thủ tuyệt đối** instruction. Đây là chế độ nên
dùng cho bot bán hàng — nhưng nó **khuếch đại** chất lượng instruction theo cả hai chiều:

- Instruction đầy đủ, không mâu thuẫn → bot làm rất sát, câu mẫu viết sao ra vậy.
- Instruction có lỗ hổng → bot **không tự nghĩ ra lối thoát**, nó rơi về câu mặc định của
  platform (`"Tôi không tìm thấy thông tin này trong tài liệu được cung cấp."`).

Chuỗi mặc định đó **không phải guard đè lên prompt**. Nó là **triệu chứng của lỗ hổng**.
Tôi đã kết luận sai theo hướng ngược lại và đốt nhiều vòng vô ích. Cách vá đúng là **viết câu mẫu
tường minh cho đúng tình huống đang rơi**, không phải đi cấm chuỗi đó.

→ Thấy câu mặc định của platform: **hỏi "instruction thiếu câu mẫu cho tình huống nào?"**, đừng
hỏi "làm sao chặn chuỗi này".

---

## LUẬT 3 — Một CATALOGUE câu dự phòng theo tình huống, không phải một câu

Một câu dự phòng duy nhất luôn dẫn tới Luật 1: các mục khác buộc phải cấm nó, và cấm xong là hở.

```
§11b — chọn đúng một tình huống:
(a) khách nêu tên sản phẩm không tra được   → xin đường kính hoặc ảnh
(b) so sánh, chỉ mở được một bên            → trình bày bên đó + hỏi nhu cầu
(c) so sánh, không mở được bên nào          → nêu 3 trục khác biệt + hỏi 1 câu
(d) câu hỏi khái niệm mà chưa mở được mục   → hẹn xác nhận + hỏi mục đích dùng
(e) phong thuỷ sâu (hướng, tuổi, mệnh)      → nói thẳng chưa có + chuyển sang vị trí trưng bày
(f) danh sách mà chưa chắc duyệt hết        → nêu phần đọc được + hẹn rà lại
(g) ngoài phạm vi (ship, VAT, bảo hành)     → chuyển bộ phận + hotline
```

Ba quy tắc kèm theo, thiếu là hỏng:
- Mỗi câu chỉ hỏi khách **tối đa một** câu hỏi.
- **Không giải thích** vì sao chưa trả lời được.
- **Không xếp chồng** hai câu dự phòng.

Và **mỗi câu phải kết thúc bằng một hướng đi tiếp cho khách**. Từ chối cụt = khách rời đi.

---

## LUẬT 4 — Mọi ô BẮT BUỘC phải có LỐI THOÁT tường minh

Đã vấp **5 lần trong một phiên**, cùng một cơ chế: ép có một trường → không tra được → bịa.

| Ô bắt buộc tôi thêm vào | Model bịa ra |
|---|---|
| "phải gợi ý mẫu thay thế" | tên biến thể không tồn tại |
| "phải kèm link" | 3 tên miền không có thật |
| "từ chối là sai" | 4 sản phẩm ma |
| "nói rõ lấy ví dụ từ mẫu nào" | "Quả Địa Cầu Tự Xoay – 25cm" |
| "so sánh phải nêu song song hai bên" | bịa bên thứ hai cho cân |

Khuôn đúng, đủ **ba** phần trong cùng một chỗ:
1. **Nguồn** — "chép nguyên từ dòng `Giá bán:` của đúng mục đó, không nhớ, không suy, không làm tròn".
2. **Lối thoát** — "không mở được mục nào thì dừng ở câu ngắn, bỏ hẳn phần này".
3. **Xếp hạng lỗi** — "điền số không có trong dữ liệu là lỗi NẶNG HƠN việc trả lời ngắn".

Đánh dấu ô tuỳ chọn ngay trong câu mẫu:
```
{TUỲ CHỌN, chỉ thêm khi đang thực sự đọc được mục ### của một biến thể còn hàng:
 hoặc anh/chị tham khảo giúp em <tên chép nguyên> — giá <giá chép nguyên>, hiện còn hàng ạ.}
```

---

## LUẬT 5 — Luật chống bịa không được biến thành giấy phép im lặng

Phải viết rõ phạm vi + thang xuống cấp:
```
Luật này chi phối việc NÊU TÊN sản phẩm. Nó KHÔNG cho phép bạn im lặng hay từ chối.
1. Trả lời được phần nào thì trả lời phần đó, bỏ phần không chắc.
2. Không nêu được tên cụ thể thì trả lời chung, vẫn phải có nội dung.
3. Không còn gì để nói thì dùng §11b — luôn có một câu hợp lệ để dùng.
```

---

## LUẬT 6 — Cấm HỌ TỪ NGỮ, không cấm một chuỗi

```
Cấm tuyệt đối, trong mọi câu trả lời, kể cả khi từ chối:
- xưng "tôi"
- các chữ: tài liệu, dữ liệu, hệ thống, cơ sở dữ liệu, KB, thông tin được cung cấp,
  ngữ cảnh, không tìm thấy, không có thông tin
```

---

## LUẬT 7 — Ca ở RANH GIỚI phải có tie-breaker bằng cụm từ THẬT của khách

```
"khác nhau thế nào" / "là gì" / "có bền không" / "dùng để làm gì" → §7, trả lời luôn
"có mẫu nào" / "cho xem" / "bao nhiêu tiền"                      → §8, được hỏi lại một câu
```
Hai mục chồng lấn mà không phân định → model chọn ngẫu nhiên → tỉ lệ đúng dao động, và bạn sẽ
tưởng là lỗi dữ liệu.

---

## LUẬT 8 — KHÔNG nhét dữ liệu vào instruction

Instruction chứa **luật**; KB chứa **dữ liệu**. Nhét giá, link, danh sách cỡ, danh sách màu vào
instruction thì catalogue đổi một cái là instruction nói dối, mà không ai nhớ để sửa.

Ca thật: `§11b(a)` liệt kê cứng "10cm, 10.6cm, 16cm, 20cm, 23cm, 30cm" — **thiếu 140mm và 200mm**
của dòng lơ lửng. Khách cầm quả 140mm nghe một danh sách không có cỡ của mình.
→ Trỏ về mục BẢNG TRA NHANH trong KB, đừng liệt kê.

---

## LUẬT 9 — Cần một hành vi phức tạp thì tách FILE TRAIN RIÊNG, đừng phình instruction

Xem `chatbot-kb-file-design`. Tóm tắt: tôi đã cố dạy bot **so sánh sản phẩm** bằng cách nhồi
luật vào instruction (§9b, 5 bước) rồi nhồi bảng tra vào file KB lớn — **thất bại cả hai**
(3/9 lượt, có lượt bịa sản phẩm và giá). Cách đúng là **một file .md train riêng cho so sánh**,
instruction chỉ giữ **một luật nhỏ** trỏ tới nó.

---

## LUẬT 10 — Luật dành cho bot, đừng để bot đọc cho khách

```
Không nhận đơn cho món hết hàng — nhưng đây là luật dành cho bạn,
không viết luật này ra cho khách đọc.
```
Không có câu bảo vệ đó, bot dán nguyên văn nhãn nội bộ vào câu trả lời (đã xảy ra thật:
`"HẾT HÀNG — không chào bán, không nhận đơn"`). Cấm luôn các nhãn kỹ thuật của KB
(`Tình trạng:`, `Giá bán:`, `Phân biệt:`) xuất hiện trong câu trả lời.

---

## LUẬT 11 — Trình bày phải viết ra thành luật

```
Dùng "- " ở đầu dòng, không thụt lề, không dùng •, không lồng nhiều cấp.
Mỗi gạch đầu dòng phải có nội dung NGAY TRÊN CÙNG DÒNG ĐÓ.
Không để dòng trống xen giữa các gạch đầu dòng.
Không đặt dấu ngoặc kép quanh tên sản phẩm, quanh giá.
```

---

## Đo lường

- **N ≥ 8 lượt / ca.** Đã hai lần trong một phiên báo "3/3, xong" rồi phải rút lại.
- **Báo tỉ lệ, không báo pass/fail.**
- **Đổi một lớp mỗi lần** (instruction HOẶC KB HOẶC config).
- **Luôn có nhóm canh regression** — nhóm "hỏi bằng tên đầy đủ sản phẩm" ổn định nhất.
- **Kiểm chứng công cụ chấm TRƯỚC.** Regex giá thiếu cờ `i` từng cho 23 lượt bịa giá lọt qua
  và bị báo là sạch. Danh sách "cụm từ cấm" sai từng khiến tôi chấm **câu trả lời đúng sự thật**
  là bịa (chính sách ship thật của shop). Xem `verify-the-instrument-before-the-finding`.

---

## Checklist review một instruction

**Trước khi sửa**
- [ ] Đã đọc lại toàn bộ bản hiện tại?
- [ ] Đã liệt kê các mục nói về cùng hành vi với chỗ sắp sửa?
- [ ] Sửa tại chỗ thay vì thêm mục mới?

**Sau khi sửa**
- [ ] Mỗi mục CẤM một hành vi đều chỉ ra được mục cung cấp hành vi thay thế?
- [ ] Mỗi ô BẮT BUỘC có nguồn + lối thoát + xếp hạng lỗi?
- [ ] Catalogue dự phòng phủ hết các tình huống bị cấm dùng câu chung?
- [ ] Không có dữ liệu (giá, cỡ, link, danh sách) nằm trong instruction?
- [ ] Hành vi phức tạp đã tách thành file train riêng chưa?
- [ ] Không có luật nội bộ nào có thể bị đọc cho khách?
- [ ] Độ dài KHÔNG tăng, hoặc tăng có lý do nêu được?

Liên quan: `chatbot-kb-file-design`, `chatbot-platform-config-audit`,
`llm-hallucination-detection`, `response-evaluator`.
