---
name: price-list-manager
description: Quản lý bảng giá — so sánh phiên bản cũ vs mới, phát hiện sản phẩm thay đổi giá, áp đúng giá theo khách/khu vực/kênh bán
origin: PT
tools: compare_excel_files, vlookup_operation, filter_and_retrieve, validate_data
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Price List Manager Skill — Quản Lý Bảng Giá

Skill hỗ trợ bộ phận kinh doanh / kế toán quản lý bảng giá nhiều phiên bản, phát hiện thay đổi giá, đảm bảo nhân viên sale dùng đúng giá khi chào hàng.

---

## When to Activate

- User nói "cập nhật bảng giá", "bảng giá mới", "giá đã thay đổi"
- User nói "so sánh bảng giá cũ và mới", "SP nào tăng giá, SP nào giảm"
- User nói "giá theo kênh bán", "giá online vs offline", "giá đại lý vs lẻ"
- User nói "kiểm tra nhân viên báo giá đúng không", "có ai báo giá sai không"
- User kéo thả 2 file bảng giá để so sánh

---

## Bối Cảnh Thực Tế

Bảng giá cập nhật theo tháng/quý. Khi giá mới ban hành:
- Cần thông báo ngay cho sale team
- Cần biết SP nào tăng/giảm/ngừng kinh doanh
- Cần đảm bảo đơn hàng đang chờ duyệt không dùng giá cũ

---

## Case 1 — So Sánh Bảng Giá Cũ vs Mới

**Tool:** `compare_excel_files`

```json
{
  "key_column": "ma_san_pham",
  "compare_columns": ["gia_niem_yet", "gia_si", "trang_thai"]
}
```

File 1: `bang_gia_thang3.xlsx`  
File 2: `bang_gia_thang4.xlsx`

**Output phân loại:**
- `Added` → SP mới ra mắt tháng này
- `Deleted` → SP bị ngừng kinh doanh
- `Modified` → SP thay đổi giá (cần review ngay)

---

## Case 2 — Chi Tiết Sản Phẩm Tăng/Giảm Giá

Sau `compare_excel_files`, dùng `filter_and_retrieve` để phân tích:

**SP tăng giá:**
```json
{
  "filters": [
    {"column": "gia_niem_yet_moi", "op": "gt", "value": "gia_niem_yet_cu"}
  ],
  "sort_by": "chenh_lech_gia",
  "select_columns": ["ma_san_pham", "ten_san_pham", "gia_cu", "gia_moi", "chenh_lech", "phan_tram_tang"]
}
```

**SP giảm giá:**
```json
{
  "filters": [
    {"column": "gia_niem_yet_moi", "op": "lt", "value": "gia_niem_yet_cu"}
  ]
}
```

---

## Case 3 — Áp Giá Theo Kênh Bán / Khu Vực

**Tool:** `vlookup_operation`

Bảng giá có nhiều tier theo kênh:
```json
{
  "join_key": "ma_san_pham",
  "lookup_columns": ["gia_le", "gia_si", "gia_dai_ly", "gia_xuat_khau"]
}
```

Sau khi join, dùng `filter_and_retrieve` để lấy đúng cột giá theo kênh của đơn:
```json
{
  "filters": [
    {"column": "kenh_ban", "op": "eq", "value": "dai_ly"}
  ],
  "select_columns": ["ma_san_pham", "ten_san_pham", "gia_dai_ly"]
}
```

---

## Case 4 — Phát Hiện Đơn Hàng Dùng Giá Cũ

**Tool:** `vlookup_operation`

Join file đơn hàng đang chờ duyệt với bảng giá mới:
```json
{
  "join_key": "ma_san_pham",
  "lookup_columns": ["gia_niem_yet_hien_tai"]
}
```

Sau đó lọc đơn có giá không khớp:
```json
{
  "filters": [
    {"column": "don_gia_ban", "op": "ne", "value": "gia_niem_yet_hien_tai"}
  ]
}
```

**Output:** Danh sách đơn cần cập nhật giá trước khi duyệt.

---

## Case 5 — Validate Bảng Giá Mới

**Tool:** `validate_data`

Trước khi phát hành bảng giá mới:
```json
{
  "required_columns": ["ma_san_pham", "ten_san_pham", "gia_niem_yet", "don_vi_tinh", "trang_thai"],
  "not_negative_columns": ["gia_niem_yet", "gia_si"],
  "unique_columns": ["ma_san_pham"]
}
```

---

## Output Báo Cáo Thay Đổi Giá

```
📊 BÁO CÁO THAY ĐỔI BẢNG GIÁ — Tháng 04/2026
===============================================
Tổng SP trong bảng giá: 1,240

🆕 SP MỚI (thêm vào):    12 sản phẩm
🗑️  SP NGỪNG BÁN:          5 sản phẩm
📈 SP TĂNG GIÁ:           38 sản phẩm  (avg +7.2%)
📉 SP GIẢM GIÁ:           15 sản phẩm  (avg -3.1%)
✅ SP GIỮ NGUYÊN GIÁ:  1,170 sản phẩm

⚠️  TOP 5 SP TĂNG GIÁ MẠNH NHẤT:
1. SP089 - Giày da cao cấp: 850K → 950K (+11.8%)
2. SP045 - Áo khoác da:     1.2M → 1.35M (+12.5%)

📎 Chi tiết: thay_doi_gia_thang4.xlsx
```

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| So sánh ra sai hết | Mã SP format khác nhau | Normalize mã SP (trim, uppercase) |
| Không tìm thấy SP | SP có trong một bảng, không có bảng kia | Xem cột `Added`/`Deleted` |
| Giá 0 hoặc trống | SP mới chưa nhập giá | Dùng `validate_data` phát hiện |


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
