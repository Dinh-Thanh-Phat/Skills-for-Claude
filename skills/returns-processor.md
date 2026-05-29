---
name: returns-processor
description: Xử lý đơn trả hàng — tính hoàn tiền, cập nhật tồn kho, phân tích lý do trả để cải thiện chất lượng sản phẩm/dịch vụ
origin: PT
tools: vlookup_operation, filter_and_retrieve, aggregate_excel_data, validate_data
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Returns Processor Skill — Xử Lý Đơn Trả Hàng

Skill hỗ trợ bộ phận vận hành / kế toán xử lý đơn trả hàng — tính số tiền hoàn lại, đối chiếu với kho, phân tích lý do trả để báo cáo ban quản lý.

---

## When to Activate

- User nói "đơn trả hàng", "return order", "hoàn hàng", "đổi trả"
- User nói "tính tiền hoàn cho khách", "refund bao nhiêu"
- User nói "kho nhận lại được bao nhiêu", "hàng trả về có nhập kho không"
- User nói "lý do trả hàng nhiều nhất là gì", "sản phẩm nào bị trả nhiều"
- User nói "tỷ lệ trả hàng tháng này", "return rate"
- User kéo thả file đơn trả hàng vào chat

---

## Bối Cảnh Thực Tế

Đơn trả hàng phức tạp vì liên quan nhiều bộ phận:
- **Kho:** Nhận hàng trở lại, kiểm tra chất lượng, nhập kho
- **Kế toán:** Tính tiền hoàn, ghi giảm doanh thu
- **Sale:** Trừ doanh số, ảnh hưởng hoa hồng
- **Sản phẩm/QC:** Phân tích lý do để cải thiện

---

## Bước 1 — Validate Đơn Trả

**Tool:** `validate_data`

```json
{
  "required_columns": ["ma_don_tra", "ma_don_goc", "ma_khach_hang", "ngay_tra", "ly_do_tra", "san_pham_tra", "so_luong_tra"],
  "not_negative_columns": ["so_luong_tra"],
  "date_columns": ["ngay_tra", "ngay_don_goc"]
}
```

---

## Bước 2 — Đối Chiếu Với Đơn Gốc

**Tool:** `vlookup_operation`

Tra thông tin đơn gốc để tính tiền hoàn:
```json
{
  "join_key": "ma_don_goc",
  "lookup_columns": ["ngay_dat_goc", "don_gia_ban", "thanh_tien_goc", "trang_thai_thanh_toan"]
}
```

Main: file đơn trả hàng  
Lookup: file đơn hàng gốc

Claude tính:
- `tien_hoan = so_luong_tra × don_gia_ban`
- Nếu trả một phần: `tien_hoan = (so_luong_tra / so_luong_goc) × thanh_tien_goc`

---

## Bước 3 — Phân Loại Hoàn Tiền

**Tool:** `filter_and_retrieve`

**Hoàn tiền 100%** (lỗi của công ty):
```json
{
  "filters": [
    {"column": "ly_do_tra", "op": "in", "value": ["loi_san_pham", "giao_sai_hang", "hang_hong_khi_nhan"]}
  ]
}
```

**Hoàn tiền 70%** (khách đổi ý, không lỗi công ty):
```json
{
  "filters": [
    {"column": "ly_do_tra", "op": "in", "value": ["khong_can_nua", "dat_nham", "doi_y"]}
  ]
}
```

**Không hoàn** (quá thời hạn đổi trả):
```json
{
  "filters": [
    {"column": "so_ngay_tu_mua", "op": "gt", "value": 30}
  ]
}
```

---

## Bước 4 — Tổng Hợp Theo Lý Do Trả

**Tool:** `create_pivot_table`

```json
{
  "index": ["ly_do_tra"],
  "values": ["so_don_tra", "tong_tien_hoan", "so_luong_san_pham"],
  "aggfunc": {"so_don_tra": "count", "tong_tien_hoan": "sum"}
}
```

---

## Bước 5 — Sản Phẩm Bị Trả Nhiều Nhất

**Tool:** `aggregate_excel_data`

```json
{
  "key_columns": ["ma_san_pham", "ten_san_pham"],
  "sum_cols": ["so_luong_tra", "tien_hoan"],
  "count_cols": ["ma_don_tra"]
}
```

Sau đó sort_by để lấy top 10 SP bị trả nhiều.

---

## Output Báo Cáo Đơn Trả

```
📦 BÁO CÁO ĐƠN TRẢ HÀNG — Tháng 04/2026
==========================================
Tổng đơn trả: 87 đơn
Tổng tiền hoàn: 342,000,000 VND
Return rate: 87/1,240 = 7.0% (↑ vs tháng 3: 5.8%)

📊 LÝ DO TRẢ:
   Lỗi sản phẩm:       35 đơn (40%) — Hoàn 100%: 156M
   Giao sai hàng:      22 đơn (25%) — Hoàn 100%: 98M
   Khách đổi ý:        18 đơn (21%) — Hoàn 70%: 63M
   Hàng hỏng khi giao:  8 đơn (9%)  — Hoàn 100%: 22M
   Quá hạn đổi trả:     4 đơn (5%)  — Không hoàn

⚠️  CẢNH BÁO: Return rate tháng này 7% > ngưỡng 5%
   → Cần review QC quy trình đóng gói và xuất hàng

🔴 SP BỊ TRẢ NHIỀU NHẤT:
   1. SP089 - Giày da: 12 đơn trả (lý do: lỗi đế)
   2. SP045 - Áo khoác: 8 đơn (lý do: sai size)

📎 Chi tiết: don_tra_thang4.xlsx
```

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| Không tìm thấy đơn gốc | Mã đơn format khác | Normalize mã đơn trước khi join |
| Tiền hoàn > tiền đơn gốc | Nhập sai số lượng trả | Validate `so_luong_tra <= so_luong_goc` |
| Return rate cao bất thường | Gộp cả đơn đổi size | Tách "đổi hàng" vs "trả hàng" trong cột lý do |


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
