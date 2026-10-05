---
name: skill-discovery
description: Hiển thị menu skills khi user hỏi vague — "Claude làm được gì?", "có skill nào cho X không?", "không biết bắt đầu từ đâu"
origin: PT
---

# Skill Discovery — QA Edition

## When to Activate

- User hỏi "Claude có thể làm gì?", "bạn giúp được gì?", "có những tính năng gì?"
- User hỏi "có skill nào cho X không?"
- User nói "không biết bắt đầu từ đâu"
- Đầu session mới — user chưa rõ mình cần làm gì

> **Note cho Claude:** Skill này dành cho user. Nếu user đã nói rõ task QA cụ thể, invoke `qa-router` thay vì skill này.

---

## Response Template

Tôi có thể hỗ trợ các mảng QA sau. Chỉ cần nói tự nhiên — không cần nhớ tên lệnh:

---

## 🧪 Mảng 1 — Web Testing (Playwright)

| Việc cần làm | Ví dụ câu hỏi |
|---|---|
| Viết test cases (manual trước) | "Viết test cases cho trang login" / "Test form đăng ký" |
| Coverage tối đa từ scope + Figma | "Đảm bảo coverage toàn bộ, có scope doc và Figma" |
| Debug test fail / flaky | "Test này lúc pass lúc fail" / "Tại sao test fail?" |
| Tổng hợp gap coverage | "Có test nào còn thiếu không?" / "Quét lại test suite" |
| Cross-module verify | "Test gửi email phải check Campaign History" |
| Upload ảnh / file trong test | "Upload logo trong CMS test" |
| Visual regression | "Snapshot trang chủ, so sánh khi UI thay đổi" |
| Accessibility | "Kiểm tra a11y / WCAG cho dashboard" |
| Regression / smoke trước release | "Release được chưa?" / "Chạy smoke test trước deploy" |
| Test tay tìm bug (exploratory) | "Explore feature này giúp mình, tìm bug" |
| Test plan / ước lượng effort | "Lập test plan cho sprint này" / "Test này mất bao lâu?" |
| Đánh giá UX / workflow | "Feature chạy đúng nhưng bất tiện, đánh giá giúp" |

---

## 📱 Mảng 2 — Mobile Testing

| Việc cần làm | Ví dụ câu hỏi |
|---|---|
| Maestro YAML flow | "Viết test login cho app iOS+Android" |
| iOS simulator | "Tạo simulator iPhone 15, install app" |
| Android + ADB | "Cài APK + grant permissions trước khi test" |
| Lấy hết selector app 1 lần | "Dò element chậm quá" / "Lấy element map cho module này" |
| Tăng tốc suite Maestro | "Suite mobile chạy lâu quá" / "Chạy song song nhiều device" |
| Lỗi sau khi nâng OS/SDK | "Từ khi lên Android 17 / iOS 27 test bị lỗi" |

---

## 🤖 Mảng 3 — Chatbot / AI Testing

| Việc cần làm | Ví dụ câu hỏi |
|---|---|
| Test chatbot accuracy | "Test chatbot này với 50 câu hỏi từ file docs" |
| OCR PDF scan | "Đọc text từ PDF scan / ảnh" |
| Sửa instruction / KB của bot | "Bot trả lời sai, sửa prompt giúp" / "Bot gửi sai ảnh sản phẩm" |
| Hallucination / red-team / guardrail | "Bot có bịa thông tin không?" / "Thử tấn công prompt injection" |
| Đánh giá AI agent | "Agent gọi tool có đúng thứ tự không?" / "Eval RAG pipeline" |

---

## 📊 Mảng 4 — Quản Lý & Báo Cáo

| Việc cần làm | Ví dụ câu hỏi |
|---|---|
| Bug report + log Odoo | "Viết bug report cho lỗi vừa tìm" / "Log bug lên Odoo" |
| Xuất kết quả test | "Báo cáo kết quả test" / "Xuất excel test cases" |
| Kết thúc session test | "Xong hôm nay, tổng kết lại" / "Hôm nay test được gì" |

---

## Gợi Ý Thêm

Nếu user vẫn không rõ, hỏi thêm:

> "Hôm nay bạn đang ở bước nào — viết test cases, chạy test, debug fail, hay tổng kết?"

---

## Lưu Ý

- KHÔNG liệt kê tên file skill (user không cần biết)
- KHÔNG hỏi "bạn muốn dùng skill nào?" — user không biết skill là gì
- Trả lời bằng ví dụ câu hỏi thực tế để user nhận ra ngay mình cần cái nào
- Khi user đã xác định task → invoke `qa-router` để route đúng skill
