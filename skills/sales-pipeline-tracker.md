---
name: sales-pipeline-tracker
description: Theo dõi cơ hội bán hàng từ lead đến chốt deal — tỷ lệ chuyển đổi từng bước, dự báo doanh thu, phát hiện deal bị stale
origin: PT
tools: aggregate_excel_data, filter_and_retrieve, create_pivot_table, validate_data
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Sales Pipeline Tracker Skill — Theo Dõi Pipeline Bán Hàng

Skill hỗ trợ sale manager theo dõi toàn bộ phễu bán hàng — từ lúc tiếp xúc khách đến khi chốt đơn — phát hiện bottleneck, dự báo doanh thu tháng tới.

---

## When to Activate

- User nói "pipeline", "phễu bán hàng", "cơ hội đang xử lý"
- User nói "deal nào sắp chốt", "forecast tháng này bao nhiêu"
- User nói "tỷ lệ chuyển đổi", "conversion rate từng bước"
- User nói "deal nào bị tắc", "cơ hội bị bỏ quên", "stale deal"
- User nói "nhân viên nào có pipeline mạnh nhất"
- User kéo thả file theo dõi cơ hội vào chat

---

## Bối Cảnh Thực Tế

Pipeline sale thường qua các giai đoạn:
```
Lead → Qualified → Demo/Gặp → Báo giá → Đàm phán → Chốt Deal / Lost
```

Vấn đề phổ biến:
- Deal mắc kẹt ở một giai đoạn quá lâu mà không ai biết
- Forecast doanh thu không chính xác vì không tính xác suất
- Sale tập trung vào deal nhỏ, bỏ deal lớn đang chờ

---

## Phân Tích 1 — Tổng Quan Pipeline Hiện Tại

**Tool:** `create_pivot_table`

```json
{
  "index": ["giai_doan"],
  "values": ["so_deal", "gia_tri_du_kien"],
  "aggfunc": {"so_deal": "count", "gia_tri_du_kien": "sum"},
  "add_totals": true
}
```

**Output:**

| Giai đoạn | Số deal | Giá trị (VND) |
|---|---|---|
| Lead | 45 | 4.5B |
| Qualified | 28 | 3.2B |
| Demo/Gặp | 18 | 2.8B |
| Báo giá | 12 | 2.1B |
| Đàm phán | 8 | 1.8B |
| **Tổng pipeline** | **111** | **14.4B** |

---

## Phân Tích 2 — Dự Báo Doanh Thu (Weighted Forecast)

Claude tính xác suất chốt theo giai đoạn:

| Giai đoạn | Xác suất chốt |
|---|---|
| Lead | 10% |
| Qualified | 20% |
| Demo/Gặp | 40% |
| Báo giá | 60% |
| Đàm phán | 80% |

`doanh_thu_du_bao = gia_tri_du_kien × xac_suat_chot`

**Tool:** `aggregate_excel_data`

```json
{
  "key_columns": ["giai_doan", "nhan_vien_phu_trach"],
  "sum_cols": ["gia_tri_du_kien", "doanh_thu_du_bao"]
}
```

---

## Phân Tích 3 — Deal Bị Stale (Tắc Quá Lâu)

**Tool:** `filter_and_retrieve`

Deal không có cập nhật > 14 ngày:
```json
{
  "filters": [
    {"column": "ngay_cap_nhat_cuoi", "op": "lt", "value": "today-14"},
    {"column": "trang_thai", "op": "ne", "value": "won"},
    {"column": "trang_thai", "op": "ne", "value": "lost"}
  ],
  "sort_by": "gia_tri_du_kien",
  "select_columns": ["ten_khach", "giai_doan", "gia_tri_du_kien", "nhan_vien", "ngay_cap_nhat_cuoi", "so_ngay_tac"]
}
```

---

## Phân Tích 4 — Tỷ Lệ Chuyển Đổi Từng Bước

**Tool:** `aggregate_excel_data`

Tính số deal đi qua từng giai đoạn trong tháng:
```json
{
  "key_columns": ["giai_doan", "thang"],
  "count_cols": ["ma_deal"]
}
```

Claude tính:
- `Lead → Qualified = Qualified / Lead × 100%`
- `Qualified → Demo = Demo / Qualified × 100%`
- `Demo → Báo giá = Báo giá / Demo × 100%`
- `Báo giá → Chốt = Won / Báo giá × 100%`

---

## Phân Tích 5 — Pipeline Theo Nhân Viên

**Tool:** `create_pivot_table`

```json
{
  "index": ["nhan_vien_phu_trach"],
  "columns": ["giai_doan"],
  "values": ["gia_tri_du_kien"],
  "aggfunc": "sum"
}
```

Phát hiện: Nhân viên nào pipeline yếu, nhân viên nào cần hỗ trợ chốt deal.

---

## Output Báo Cáo Pipeline

```
📊 PIPELINE BÁN HÀNG — Tuần 18/2026
=====================================
Tổng pipeline: 111 deals — 14.4B VND
Dự báo chốt tháng này: 3.2B VND (22% pipeline)

⚡ GIAI ĐOẠN CÓ NHIỀU DEAL NHẤT:
   Báo giá: 12 deals — 2.1B VND (ready to close!)

🔴 DEAL BỊ STALE (> 14 ngày không cập nhật): 8 deals
   Deal lớn nhất bị tắc: Cty ABC — 450M — giai đoạn Đàm phán
   → Sale Nguyễn Văn A cần follow-up ngay

📈 TỶ LỆ CHUYỂN ĐỔI THÁNG NÀY:
   Lead → Qualified: 62% (↑ vs tháng trước 54%)
   Báo giá → Chốt: 41% (↓ vs tháng trước 48%)

🏆 TOP PIPELINE (theo giá trị):
   1. Trần Thị B — 4.2B pipeline — 1.1B dự báo
   2. Lê Văn C   — 3.8B pipeline — 0.9B dự báo

📎 Chi tiết: pipeline_tuan18.xlsx
```

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| Forecast quá cao | Không áp xác suất theo giai đoạn | Áp weighted forecast |
| Deal stale không phát hiện | Cột ngày không cập nhật | Nhắc NV cập nhật pipeline mỗi tuần |
| Pipeline bị trùng | Một deal 2 NV cùng track | Dùng `validate_data` kiểm tra mã deal trùng |


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
