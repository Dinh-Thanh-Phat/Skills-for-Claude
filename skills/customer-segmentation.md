---
name: customer-segmentation
description: Phân loại khách hàng theo RFM (Recency, Frequency, Monetary) — xác định khách VIP, khách sắp rời bỏ, khách tiềm năng để tập trung nguồn lực đúng chỗ
origin: PT
tools: aggregate_excel_data, filter_and_retrieve, create_pivot_table, compare_excel_files
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Customer Segmentation Skill — Phân Loại Khách Hàng

Skill hỗ trợ sale manager / marketing phân tích tệp khách hàng, xác định ai cần chăm sóc, ai đang nguội dần, ai có tiềm năng upsell — để phân bổ nguồn lực sale hiệu quả.

---

## When to Activate

- User nói "phân loại khách hàng", "segmentation", "nhóm khách"
- User nói "khách VIP là ai", "khách nào mua nhiều nhất"
- User nói "khách nào đang bỏ bê", "khách lâu không mua", "churn risk"
- User nói "khách nào có tiềm năng upsell", "ai có thể mua thêm"
- User nói "tập trung vào khách nào", "ưu tiên khách nào"
- User kéo thả file lịch sử mua hàng để phân tích

---

## Bối Cảnh Thực Tế

Một công ty thường có 80/20: **20% khách tạo ra 80% doanh thu**. Nhưng sale team thường không biết ai là 20% đó, dẫn đến:
- Lãng phí thời gian chăm khách nhỏ
- Bỏ qua tín hiệu khách lớn sắp rời
- Không biết khách nào đang "nóng" để push deal

---

## Phân Tích RFM

**R** — Recency: Lần cuối mua cách đây bao lâu?  
**F** — Frequency: Mua bao nhiêu lần trong kỳ?  
**M** — Monetary: Tổng tiền đã mua?

### Bước 1 — Tính RFM Cho Từng Khách

**Tool:** `aggregate_excel_data`

```json
{
  "key_columns": ["ma_khach_hang", "ten_khach_hang"],
  "sum_cols": ["thanh_tien"],
  "count_cols": ["ma_don_hang"],
  "max_cols": ["ngay_dat"]
}
```

Kết quả: Mỗi khách có 3 chỉ số:
- `ngay_mua_gan_nhat` (Recency)
- `so_lan_mua` (Frequency)
- `tong_doanh_thu` (Monetary)

---

### Bước 2 — Tính Điểm R, F, M (1-5)

Claude tính tự động dựa trên phân vị:

| Điểm | R (ngày chưa mua) | F (số đơn) | M (doanh thu) |
|---|---|---|---|
| 5 | ≤ 30 ngày | ≥ 20 đơn | Top 20% |
| 4 | 31–60 ngày | 10–19 đơn | Top 21–40% |
| 3 | 61–90 ngày | 5–9 đơn | Top 41–60% |
| 2 | 91–180 ngày | 2–4 đơn | Top 61–80% |
| 1 | > 180 ngày | 1 đơn | Bottom 20% |

---

### Bước 3 — Phân Nhóm Khách Hàng

**Tool:** `filter_and_retrieve`

**Champions (R≥4, F≥4, M≥4) — Khách vàng:**
```json
{
  "filters": [
    {"column": "r_score", "op": "gte", "value": 4},
    {"column": "f_score", "op": "gte", "value": 4},
    {"column": "m_score", "op": "gte", "value": 4}
  ]
}
```

**At Risk (R≤2, F≥3) — Khách từng tốt, đang nguội:**
```json
{
  "filters": [
    {"column": "r_score", "op": "lte", "value": 2},
    {"column": "f_score", "op": "gte", "value": 3}
  ]
}
```

**Lost (R=1, F=1) — Khách đã mất:**
```json
{
  "filters": [
    {"column": "r_score", "op": "eq", "value": 1},
    {"column": "f_score", "op": "eq", "value": 1}
  ]
}
```

**Promising (R≥4, F≤2) — Mới mua, tiềm năng:**
```json
{
  "filters": [
    {"column": "r_score", "op": "gte", "value": 4},
    {"column": "f_score", "op": "lte", "value": 2}
  ]
}
```

---

### Bước 4 — Pivot Tổng Hợp Theo Nhóm

**Tool:** `create_pivot_table`

```json
{
  "index": ["nhom_rfm"],
  "values": ["so_khach", "tong_doanh_thu", "don_hang_trung_binh"],
  "aggfunc": {"so_khach": "count", "tong_doanh_thu": "sum"}
}
```

---

## Output Phân Tích Khách Hàng

```
👥 PHÂN TÍCH KHÁCH HÀNG — Tháng 04/2026
=========================================
Tổng khách hàng phân tích: 850

🏆 CHAMPIONS (mua nhiều, mua gần, tiêu nhiều): 45 KH
   Doanh thu: 3.2B/tháng (52% tổng)
   → Hành động: Tặng quà VIP, ưu tiên CS

⚡ LOYAL (mua thường xuyên): 120 KH
   Doanh thu: 1.8B/tháng (29%)
   → Hành động: Upsell sản phẩm cao cấp

⚠️  AT RISK (từng mua nhiều, nay nguội): 78 KH
   Doanh thu tiềm năng: 900M/tháng
   → Hành động: Sale gọi điện ngay tuần này

🌱 PROMISING (mới mua, tiềm năng): 95 KH
   → Hành động: Nurture, gửi catalogue

💀 LOST (> 6 tháng không mua): 210 KH
   → Hành động: Win-back campaign hoặc bỏ qua

📎 File chi tiết: phan_loai_khach_thang4.xlsx
```

---

## Hành Động Theo Nhóm

| Nhóm | Chiến lược | Ai chịu trách nhiệm |
|---|---|---|
| Champions | Giữ chân, tặng thưởng, xin referral | Sale senior |
| Loyal | Upsell, cross-sell | Sale phụ trách |
| At Risk | Gọi điện hỏi thăm, offer ưu đãi | Sale manager |
| Promising | Gửi thông tin sản phẩm, follow-up | Sale junior |
| Lost | Win-back email/call hoặc archive | Marketing |

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| Khách VIP bị xếp sai nhóm | Dữ liệu chỉ lấy 1 tháng | Lấy tối thiểu 12 tháng lịch sử |
| Quá nhiều nhóm "Lost" | Ngày cutoff quá gần | Điều chỉnh ngưỡng R theo chu kỳ mua ngành |
| Một khách nhiều mã KH | Nhập liệu không nhất quán | Dùng `fuzzy_match` gộp tên trùng |


---

## Khi MCP Không Phản Hồi

| Tool MCP | Thay thế thủ công trong Excel |
|---|---|
| `vlookup_operation` | `=VLOOKUP(key,range,col,0)` hoặc XLOOKUP |
| `filter_and_retrieve` | Data → Filter → tùy chỉnh điều kiện lọc |
| `aggregate_excel_data` | Insert → PivotTable → Sum/Count |
| `create_pivot_table` | Insert → PivotTable |
| `compare_excel_files` | VLOOKUP ngược để tìm dòng Added/Deleted |
| `validate_data` | Conditional Formatting → Highlight Blanks/Duplicates |
| `smart_fill` | `=IFERROR(VLOOKUP(A2,DanhSach!A:Z,2,0),"")` |
| `fuzzy_match` | Power Query → Merge Queries → Approximate Match |

**Kiểm tra MCP server:** `python D:\HK8\Learning\DQ\PT\check_server.py`  
Nếu server down: chạy script trên → tự restart, chờ ~30s rồi thử lại.
