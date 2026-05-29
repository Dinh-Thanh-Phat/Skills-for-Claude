---
name: delivery-scheduler
description: Lên lịch giao hàng tối ưu — gom đơn cùng khu vực, ưu tiên đơn gấp, phân tài xế theo tuyến, export bảng giao hàng cho từng xe
origin: PT
tools: aggregate_excel_data, filter_and_retrieve, create_pivot_table, validate_data
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Delivery Scheduler Skill — Lên Lịch Giao Hàng

Skill hỗ trợ bộ phận vận hành / dispatcher lên lịch giao hàng hiệu quả — gom đơn cùng tuyến, ưu tiên theo deadline, phân tài xế hợp lý, xuất bảng lộ trình cho từng xe.

---

## When to Activate

- User nói "lên lịch giao hàng", "sắp xếp giao hàng", "phân công tài xế"
- User nói "gom đơn cùng quận", "đơn cùng tuyến đường"
- User nói "đơn nào giao trước", "ưu tiên giao hàng"
- User nói "tài xế nào giao khu vực nào", "chia tuyến cho xe"
- User nói "bảng giao hàng ngày mai", "lịch chạy xe hôm nay"
- User kéo thả file đơn hàng cần giao vào chat

---

## Bối Cảnh Thực Tế

Mỗi sáng, bộ phận vận hành cần:
1. Xem đơn cần giao hôm nay
2. Gom đơn cùng khu vực vào 1 chuyến
3. Ưu tiên đơn khách yêu cầu giao buổi sáng
4. Phân công tài xế phù hợp
5. Export bảng lộ trình cho từng xe

---

## Bước 1 — Lọc Đơn Cần Giao Hôm Nay

**Tool:** `filter_and_retrieve`

```json
{
  "filters": [
    {"column": "ngay_giao_du_kien", "op": "eq", "value": "today"},
    {"column": "trang_thai", "op": "in", "value": ["cho_giao", "da_xuat_kho"]}
  ],
  "sort_by": "gio_giao_yeu_cau",
  "select_columns": ["ma_don", "ten_khach", "dia_chi", "quan_huyen", "tinh_thanh", "so_dien_thoai", "trong_luong", "gio_giao_yeu_cau", "ghi_chu"]
}
```

---

## Bước 2 — Phân Tích Theo Khu Vực

**Tool:** `create_pivot_table`

```json
{
  "index": ["quan_huyen"],
  "values": ["so_don", "tong_trong_luong"],
  "aggfunc": {"so_don": "count", "tong_trong_luong": "sum"},
  "add_totals": true
}
```

Xác định khu vực nào có nhiều đơn → ưu tiên điều xe đến đó trước.

---

## Bước 3 — Gom Đơn Theo Tuyến

**Tool:** `aggregate_excel_data`

```json
{
  "key_columns": ["tuyen_giao", "tai_xe_phu_trach"],
  "count_cols": ["ma_don"],
  "sum_cols": ["tong_trong_luong", "gia_tri_don"]
}
```

**Tuyến giao mẫu (tùy định nghĩa của từng công ty):**
- Tuyến Bắc: Hoàn Kiếm, Ba Đình, Tây Hồ
- Tuyến Nam: Thanh Xuân, Hà Đông, Hoàng Mai
- Tuyến Đông: Long Biên, Gia Lâm, Đông Anh

---

## Bước 4 — Ưu Tiên Đơn Gấp

**Tool:** `filter_and_retrieve`

Đơn yêu cầu giao buổi sáng (trước 12h):
```json
{
  "filters": [
    {"column": "gio_giao_yeu_cau", "op": "lt", "value": "12:00"},
    {"column": "ngay_giao_du_kien", "op": "eq", "value": "today"}
  ],
  "sort_by": "gio_giao_yeu_cau"
}
```

Đơn VIP / khách Gold+:
```json
{
  "filters": [
    {"column": "hang_khach_hang", "op": "in", "value": ["Gold", "Platinum"]}
  ]
}
```

---

## Bước 5 — Validate Trước Khi Phân Công

**Tool:** `validate_data`

```json
{
  "required_columns": ["ma_don", "ten_khach", "dia_chi", "so_dien_thoai", "tuyen_giao"],
  "not_negative_columns": ["tong_trong_luong"]
}
```

Phát hiện đơn thiếu địa chỉ hoặc SĐT → không thể giao, cần liên hệ khách trước.

---

## Output Bảng Giao Hàng

```
🚚 LỊCH GIAO HÀNG — Thứ 2, 28/04/2026
========================================
Tổng đơn cần giao: 145 đơn
Tổng trọng lượng:  2,340 kg

TUYẾN BẮC — Xe BKS 29A-12345 | Tài xế: Nguyễn Văn X
   10 đơn | 450kg | Khu vực: Hoàn Kiếm, Ba Đình

   STT | Mã đơn | Khách           | Địa chỉ              | SĐT         | Giờ giao | KG
   ----|--------|-----------------|----------------------|-------------|----------|----
   1   | DH0234 | Cty Minh Phát   | 45 Hàng Bài, HK      | 0912345678  | 9:00     | 25
   2   | DH0267 | Shop ABC        | 12 Đinh Tiên Hoàng   | 0987654321  | 10:30    | 15
   ...

TUYẾN NAM — Xe BKS 29B-67890 | Tài xế: Trần Văn Y
   18 đơn | 680kg | Khu vực: Thanh Xuân, Hà Đông

⚠️  ĐƠN THIẾU THÔNG TIN (cần xử lý trước 8h):
   DH0289 — Thiếu số điện thoại khách
   DH0301 — Địa chỉ không rõ ràng

📎 Export: lich_giao_hang_28042026_[tuyen].xlsx
```

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| Đơn không vào tuyến nào | Địa chỉ không có quận/huyện | Validate địa chỉ có đủ quận trước |
| Xe quá tải | Không check tổng trọng lượng | Thêm điều kiện lọc `tong_trong_luong <= tai_trong_xe` |
| Đơn giao trùng | 1 đơn assign 2 xe | Validate `ma_don` unique trong bảng phân công |


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
