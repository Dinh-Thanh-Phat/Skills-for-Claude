---
name: order-reconciliation
description: Đối chiếu đơn hàng với các hệ thống liên quan — đơn vs thanh toán, đơn vs giao hàng, đơn vs kho, đơn vs hóa đơn VAT để tìm chênh lệch
origin: PT
tools: compare_excel_files, vlookup_operation, filter_and_retrieve, validate_data, aggregate_excel_data
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Order Reconciliation Skill — Đối Chiếu Đơn Hàng

Skill hỗ trợ kế toán / kiểm soát nội bộ đối chiếu đơn hàng giữa các bộ phận — phát hiện chênh lệch giữa đơn đặt hàng, phiếu giao hàng, hóa đơn, và thanh toán.

---

## When to Activate

- User nói "đối chiếu", "reconcile", "khớp dữ liệu", "so sánh 2 hệ thống"
- User nói "đơn đặt vs đơn giao có khớp không", "hàng giao có đúng không"
- User nói "đơn nào chưa thanh toán", "công nợ khách hàng"
- User nói "hóa đơn VAT có khớp với đơn hàng không"
- User nói "kho xuất bao nhiêu, đơn ghi bao nhiêu", "stock discrepancy"
- User nói "tháng này có bao nhiêu đơn chưa xử lý", "đơn tồn đọng"
- User kéo thả 2 file từ 2 hệ thống khác nhau để đối chiếu
- User nói "tìm đơn bị rơi", "đơn mất tích", "không tìm thấy trong hệ thống"

---

## Bối Cảnh Thực Tế

Trong doanh nghiệp, dữ liệu đơn hàng tồn tại ở nhiều nơi:
- **Sale** → file đơn đặt hàng (purchase orders)
- **Kho** → phiếu xuất kho (delivery notes)
- **Kế toán** → hóa đơn VAT, phiếu thu
- **Công nợ** → báo cáo thanh toán

Sự chênh lệch giữa các nguồn dẫn đến: xuất hàng sai số lượng, thu tiền thiếu, kê khai VAT sai.

---

## Loại Đối Chiếu

### Loại 1 — Đơn Hàng vs Phiếu Giao Hàng

**Mục tiêu:** Tìm đơn đặt nhưng chưa giao, hoặc giao sai số lượng.

**Tool:** `compare_excel_files`

```json
{
  "key_column": "ma_don_hang"
}
```

File 1: `don_dat_hang.xlsx` (từ Sale)  
File 2: `phieu_giao_hang.xlsx` (từ Kho)

**Kết quả:**
- `Added` (có trong giao, không có trong đặt) → giao hàng không có đơn
- `Deleted` (có trong đặt, không có trong giao) → đơn chưa được giao
- `Modified` (có trong cả 2, giá trị khác nhau) → giao sai số lượng

**Workflow tiếp theo cho "Modified":**

Dùng `filter_and_retrieve` để lấy chi tiết các đơn bị sai:
```json
{
  "filters": [
    {"column": "trang_thai", "op": "eq", "value": "Modified"}
  ],
  "select_columns": ["ma_don_hang", "so_luong_dat", "so_luong_giao", "chenh_lech"]
}
```

---

### Loại 2 — Đơn Hàng vs Thanh Toán / Công Nợ

**Mục tiêu:** Tìm đơn chưa thanh toán, thanh toán thiếu, hoặc thanh toán nhầm.

**Tool:** `vlookup_operation`

```json
{
  "join_key": "ma_don_hang",
  "lookup_columns": ["so_tien_da_thanh_toan", "ngay_thanh_toan", "hinh_thuc_tt"]
}
```

Main: `don_hang.xlsx`  
Lookup: `bang_thanh_toan.xlsx`

Sau khi join, dùng `filter_and_retrieve` để lọc:

```json
{
  "filters": [
    {"column": "so_tien_da_thanh_toan", "op": "lt", "value": "thanh_tien"}
  ]
}
```

**Output:** Danh sách đơn chưa thanh toán đủ + số tiền còn thiếu.

---

### Loại 3 — Đơn Hàng vs Hóa Đơn VAT

**Mục tiêu:** Mỗi đơn hàng có phát sinh hóa đơn VAT chưa? Giá trị có khớp?

**Tool:** `compare_excel_files`

```json
{
  "key_column": "ma_don_hang",
  "compare_columns": ["thanh_tien", "ma_khach_hang"]
}
```

File 1: `don_hang_thang4.xlsx`  
File 2: `hoa_don_vat_thang4.xlsx`

**Phát hiện:**
- Đơn không có hóa đơn VAT → cần xuất HĐ
- Giá trị HĐ ≠ giá trị đơn → sai kê khai

---

### Loại 4 — Đơn Hàng vs Tồn Kho

**Mục tiêu:** Đơn đã duyệt có đủ hàng trong kho xuất không?

**Tool:** `vlookup_operation`

```json
{
  "join_key": "ma_san_pham",
  "lookup_columns": ["ton_kho_hien_tai", "don_vi_tinh"]
}
```

Sau khi join, tính `can_xuat = so_luong_dat - ton_kho`:
```json
{
  "filters": [
    {"column": "ton_kho_hien_tai", "op": "lt", "value": "so_luong_dat"}
  ],
  "select_columns": ["ma_san_pham", "ten_san_pham", "so_luong_dat", "ton_kho_hien_tai"]
}
```

**Output:** Danh sách sản phẩm thiếu hàng → cần mua thêm hoặc thông báo khách.

---

### Loại 5 — Đối Chiếu Theo Tháng / Kỳ

**Mục tiêu:** Tổng doanh thu tháng theo 2 hệ thống có khớp không?

**Tool:** `aggregate_excel_data`

Chạy riêng cho từng file, group theo tháng:
```json
{
  "key_columns": ["thang"],
  "sum_cols": ["thanh_tien"]
}
```

Sau đó `compare_excel_files` để so sánh bảng tổng hợp.

---

## Workflow Đối Chiếu Chuẩn

```
Bước 1: [compare_excel_files]   → Tìm đơn bị mất / thêm giữa 2 hệ thống
Bước 2: [vlookup_operation]     → Join thêm thông tin để phân tích sâu
Bước 3: [filter_and_retrieve]   → Lọc ra các trường hợp chênh lệch cụ thể
Bước 4: [aggregate_excel_data]  → Tính tổng chênh lệch theo kỳ / nhân viên / SP
Bước 5: [validate_data]         → Kiểm tra kết quả đối chiếu không có lỗi logic
```

---

## Template Câu Hỏi Đối Chiếu

**Đơn vs Giao hàng:**
> "Đây là file đơn đặt hàng và file phiếu xuất kho tháng 4. Cột mã đơn là 'so_don'. Kiểm tra đơn nào chưa xuất kho, và đơn nào xuất sai số lượng."

**Đơn vs Thanh toán:**
> "File đơn hàng và file sao kê ngân hàng. Tìm đơn chưa có tiền về, và đơn có tiền về nhưng không có đơn."

**Đơn vs Hóa đơn:**
> "Tháng 3 có 450 đơn hàng nhưng chỉ xuất 440 hóa đơn. Hóa đơn nào bị thiếu?"

---

## Output Báo Cáo Đối Chiếu

```
📋 ĐỐI CHIẾU ĐƠN HÀNG vs PHIẾU GIAO HÀNG — Tháng 04/2024
============================================================
Đơn đặt hàng:    1,450 đơn   |  Tổng: 2,340,000,000 VND
Phiếu giao hàng: 1,423 đơn   |  Tổng: 2,298,500,000 VND
Chênh lệch:         27 đơn   |        41,500,000 VND

PHÂN TÍCH:
❌ 15 đơn đặt CHƯA giao:     DH0234, DH0267, DH0289...
❌ 8  đơn giao KHÔNG có đơn: PN0145, PN0167...
⚠️  4  đơn giao SAI số lượng: DH0312 (đặt 100, giao 80)

📎 Chi tiết: doi_chieu_thang4.xlsx
```

---

## Các Chỉ Số Đối Chiếu Quan Trọng

| Chỉ số | Công thức | Ngưỡng cảnh báo |
|---|---|---|
| Tỷ lệ khớp | (Đơn khớp / Tổng đơn) × 100% | < 95% cần điều tra |
| Chênh lệch giá trị | Tổng đơn - Tổng thanh toán | > 5% tổng doanh thu |
| Đơn tồn đọng > 30 ngày | Count(ngay_dat < today - 30) | > 10 đơn = vấn đề |
| HĐ thiếu | Đơn - HĐ VAT | > 0 = vi phạm quy trình |

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| Không khớp dù cùng đơn | Mã đơn format khác ("DH001" vs "001") | Yêu cầu normalize key trước |
| Chênh lệch tất cả đơn | Đơn vị tiền tệ khác (VND vs USD) | Convert về cùng đơn vị |
| Tìm thấy nhiều chênh lệch giả | Ngày tháng format khác | Chuẩn hóa ngày trước khi so sánh |
| File kho có nhiều sheet | Mỗi kho 1 sheet | Xử lý từng sheet rồi gộp |


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
