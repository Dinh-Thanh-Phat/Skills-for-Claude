---
name: chatbot-instruction-authoring
description: Use when writing, repairing, or reviewing the system instruction of a RAG sales/support chatbot (InCard Agentic, Yasaka, Dify, any "instructions + trained docs" platform) — covers fallback catalogues, escape hatches for mandatory slots, section routing, and how to avoid prompt edits that cause fabrication.
---

# Viết instruction cho chatbot RAG bán hàng

Rút ra từ ~40 vòng sửa instruction bot NARENCA (InCard Agentic, bot 276 + 291), 6/8/2026.
Mỗi luật dưới đây đều sinh ra từ một lỗi đã đo được, không phải suy đoán.

## Luật 0 — Xác định LỚP trước khi sửa chữ nào

Ba lớp, sửa nhầm lớp là đốt cả buổi:

| Lớp | Sở hữu cái gì | Dấu hiệu |
|---|---|---|
| **Platform config** | chuỗi từ chối cố định, citation, ngôn ngữ, model, guard | câu trả lời **giống hệt từng ký tự** qua nhiều lượt và **không đổi dù xoá hết** khỏi instruction |
| **Retrieval + KB** | bot có mở được mục hay không | hỏi bằng **tên đầy đủ** thì đúng, hỏi **gọi tắt** thì chặn |
| **Instruction** | **hình dạng** câu trả lời khi bot ĐÃ đọc được dữ liệu | nội dung đúng nhưng trình bày sai, hỏi ngược khách, thiếu link/ảnh |

Chạy `chatbot-platform-config-audit` trước. Instruction **không** sửa được lỗi của hai lớp kia — mọi vòng sửa thêm chỉ làm instruction dài ra và sinh lỗi mới.

## Luật 1 — Mọi lệnh CẤM phải kèm hành vi THAY THẾ

Cấm mà không kê thay thế → model tự nghĩ ra một câu nghe êm tai, thường là bịa.

```
SAI:  Không được nói "hết hàng — không chào bán".
ĐÚNG: Không viết luật này ra cho khách. Thay vào đó dùng câu mẫu §6.
```

## Luật 2 — Mọi ô BẮT BUỘC phải có LỐI THOÁT tường minh

Đã vấp **5 lần trong một phiên**, cùng một cơ chế: bắt buộc có một trường → không tra được → bịa.

| Ô bắt buộc tôi thêm vào | Model bịa ra |
|---|---|
| "phải gợi ý mẫu thay thế" | tên biến thể không tồn tại |
| "phải kèm link" | 3 tên miền không có thật |
| "từ chối là sai" | 4 sản phẩm ma |
| "nói rõ lấy ví dụ từ mẫu nào" | "Quả Địa Cầu Tự Xoay – 25cm" (không có) |
| "so sánh phải nêu song song hai bên" | bịa bên thứ hai cho cân |

Khuôn đúng, đủ **ba** phần trong cùng một chỗ:
1. **Nguồn** — "chép nguyên từ dòng `Giá bán:` của đúng mục đó, không nhớ, không suy, không làm tròn".
2. **Lối thoát** — "không mở được mục nào thì dừng ở câu ngắn, bỏ hẳn phần này".
3. **Xếp hạng lỗi** — "điền số không có trong dữ liệu là lỗi NẶNG HƠN việc trả lời ngắn". Không xếp hạng thì model chọn cái nó vừa bị ép.

Đánh dấu ô tuỳ chọn ngay trong câu mẫu:

```
{TUỲ CHỌN, chỉ thêm khi đang thực sự đọc được mục ### của một biến thể còn hàng:
 hoặc anh/chị tham khảo giúp em <tên chép nguyên> — giá <giá chép nguyên>, hiện còn hàng ạ.}
```

## Luật 3 — Một CATALOGUE câu dự phòng, không phải một câu

Một câu dự phòng duy nhất là bẫy: các luật khác đều phải cấm dùng nó ("không dùng câu dự phòng cho §7, §8, §9, §9b"), và khi model rơi vào đúng các ca đó mà vẫn bí thì **không còn câu hợp lệ nào** → nó tự chế, hoặc im, hoặc rơi về chuỗi guard của platform.

Đúng: một mục `§11b` liệt kê câu mẫu **theo tình huống**, mỗi luật khác trỏ tới đúng câu.

```
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
- **Không giải thích** vì sao chưa trả lời được. Khách không cần biết.
- **Không xếp chồng** hai câu dự phòng. Chọn một.

Và: **mỗi câu dự phòng phải kết thúc bằng một hướng đi tiếp cho khách.** Từ chối cụt = khách rời đi.

## Luật 4 — Luật "phải có thật" không được biến thành giấy phép im lặng

Luật chống bịa tên rất dễ bị model đọc thành "không chắc thì đừng nói gì". Phải viết rõ phạm vi của nó và kèm thang xuống cấp:

```
Luật này chi phối việc NÊU TÊN sản phẩm. Nó KHÔNG cho phép bạn im lặng hay từ chối.

Thứ tự ưu tiên khi bí:
1. Trả lời được phần nào thì trả lời phần đó, bỏ phần không chắc.
2. Không nêu được tên cụ thể thì trả lời chung, vẫn phải có nội dung.
3. Không còn gì để nói thì dùng §11 hoặc §11b — luôn có một câu hợp lệ để dùng.
```

## Luật 5 — Cấm HỌ TỪ NGỮ, không cấm một chuỗi

Cấm đúng một câu → model đổi chữ, giữ nguyên cảm giác "shop không nắm được hàng của mình".

```
Cấm tuyệt đối, trong mọi câu trả lời, kể cả khi từ chối:
- xưng "tôi"
- các chữ: tài liệu, dữ liệu, hệ thống, cơ sở dữ liệu, KB, thông tin được cung cấp,
  ngữ cảnh, không tìm thấy, không có thông tin
```

## Luật 6 — Ca ở RANH GIỚI phải có luật phân định riêng

Hai mục instruction chồng lấn → model chọn ngẫu nhiên → tỉ lệ đúng dao động. Viết tie-breaker bằng **cụm từ thật của khách**, không bằng khái niệm:

```
Khách hỏi "khác nhau thế nào", "là gì", "có bền không", "dùng để làm gì"
  → §7, trả lời luôn, không hỏi lại.
Khách hỏi "có mẫu nào", "cho xem", "bao nhiêu tiền"
  → §8, được hỏi lại một câu.
```

## Luật 7 — Hỏi khách một câu thì phải trả lời được câu khách hỏi ngược

Bot hỏi "anh/chị quan tâm cỡ nào" rồi khách hỏi "shop có những cỡ nào" mà bot từ chối → khách bế tắc và rời đi. Mọi câu hỏi ngược khả dĩ đều phải có đáp án đóng trong KB, và instruction phải nói thẳng "tuyệt đối không từ chối câu này".

## Luật 8 — Luật dành cho bot, đừng để bot đọc cho khách

```
Không nhận đơn cho món hết hàng — nhưng đây là luật dành cho bạn,
không viết luật này ra cho khách đọc.
```
Không có câu bảo vệ đó, bot dán nguyên văn nhãn nội bộ vào câu trả lời (đã xảy ra thật: `"HẾT HÀNG — không chào bán, không nhận đơn"`). Cũng cấm luôn các nhãn kỹ thuật của KB (`Tình trạng:`, `Giá bán:`, `Phân biệt:`) xuất hiện trong câu trả lời.

## Luật 9 — Trình bày phải viết ra thành luật, không mặc định

Lỗi format hay gặp: gạch đầu dòng trống rồi mới xuống dòng viết chữ (lồng cấp giả).
```
Dùng "- " ở đầu dòng, không thụt lề, không dùng •, không lồng nhiều cấp.
Mỗi gạch đầu dòng phải có nội dung NGAY TRÊN CÙNG DÒNG ĐÓ.
Không để dòng trống xen giữa các gạch đầu dòng.
```

## Đo lường — luật cứng

- **N ≥ 8 lượt / ca.** Bot RAG dao động rất mạnh. Đã hai lần trong một phiên tôi báo "3/3, sửa xong" rồi phải rút lại khi đo lại. **3 lượt không phân biệt được 50% với 90%.**
- **Báo tỉ lệ, không báo pass/fail.** "K15 1/3" chứ không phải "K15 hỏng".
- **Đổi một lớp mỗi lần.** Sửa instruction VÀ train KB cùng lúc → không quy được nguyên nhân. (Đã vấp: K15 rớt 3/3 → 1/3, không biết do KB hay do dao động.)
- **Luôn chạy lại canh regression** trên nhóm đang tốt. Bản vá cho ca A thường làm rớt ca B. Nhóm "hỏi bằng tên đầy đủ sản phẩm" là canh tốt nhất (ổn định 30/30).
- **Kiểm chứng công cụ chấm trước khi tin kết quả.** Regex thiếu cờ `i` đã làm 23 lượt bịa giá lọt qua và bị báo là sạch. Xem `verify-the-instrument-before-the-finding`.

## Checklist review một instruction

- [ ] Mỗi lệnh CẤM có kèm hành vi thay thế?
- [ ] Mỗi ô BẮT BUỘC có nguồn + lối thoát + xếp hạng lỗi?
- [ ] Có catalogue câu dự phòng theo tình huống, mỗi câu kết thúc bằng hướng đi tiếp?
- [ ] Luật chống bịa có nói rõ "không cho phép im lặng"?
- [ ] Có cấm họ từ ngữ máy móc, không chỉ một chuỗi?
- [ ] Các mục chồng lấn có tie-breaker bằng cụm từ thật?
- [ ] Câu bot hỏi ngược khách đều có đáp án đóng trong KB?
- [ ] Không có luật nội bộ nào có thể bị đọc cho khách?
- [ ] Có luật trình bày (bullet, ngoặc kép, nhãn kỹ thuật)?

Liên quan: `chatbot-platform-config-audit`, `llm-hallucination-detection`, `response-evaluator`, `chatbot-tester`.
