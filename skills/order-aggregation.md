---
name: order-aggregation
description: Tổng hợp đơn hàng từ nhiều nhân viên/chi nhánh/sheet vào một file master — phát hiện trùng lặp, bổ sung thông tin còn thiếu, chuẩn hóa định dạng
origin: PT
tools: aggregate_excel_data, smart_fill, fuzzy_match, validate_data, filter_and_retrieve
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Order Aggregation Skill — Tổng Hợp Đơn Hàng

Skill hỗ trợ nhân viên kế toán / sale admin tổng hợp đơn hàng từ nhiều file Excel của từng nhân viên kinh doanh, chi nhánh, hoặc kỳ báo cáo. Toàn bộ xử lý qua MCP Server `excel-tools`.

---

## When to Activate

- User nói "tổng hợp đơn", "gộp đơn hàng từ mấy nhân viên", "merge file đơn"
- User nói "nhân viên A B C mỗi người gửi 1 file, cần gộp lại"
- User nói "thu thập đơn từ các chi nhánh", "hợp nhất dữ liệu bán hàng"
- User nói "tháng này có bao nhiêu đơn tổng cộng", "consolidate orders"
- User kéo thả 3+ file Excel có cùng cấu trúc vào chat
- User nói "chuẩn hóa mã khách hàng", "đồng bộ định dạng ngày tháng"
- User nói "điền thông tin còn thiếu từ file danh sách khách"

---

## Bối Cảnh Thực Tế

Mỗi tuần/tháng, nhân viên sale gửi file đơn hàng riêng lẻ:
- `don_hang_nguyen.xlsx` — NV Nguyễn
- `don_hang_tran.xlsx` — NV Trần
- `don_hang_le.xlsx` — NV Lê
- `cn_hanoi.xlsx`, `cn_hcm.xlsx` — chi nhánh Hà Nội, HCM

Bộ phận kế toán / sale admin cần **gộp tất cả vào 1 file master**, loại trùng, và điền thông tin khách hàng còn thiếu.

---

## Workflow Chuẩn

### Bước 1 — Gộp tất cả file đơn

**Tool:** `aggregate_excel_data`

```
Các file: don_hang_nguyen.xlsx, don_hang_tran.xlsx, don_hang_le.xlsx
Cột khóa chính: ma_don_hang
Cần tổng hợp: so_luong, thanh_tien
```

**Params:**
```json
{
  "key_columns": ["ma_don_hang"],
  "group_by_cols": ["nhan_vien", "ma_khach_hang", "ten_san_pham"],
  "sum_cols": ["so_luong", "thanh_tien"],
  "output_path": "C:/Reports/master_orders.xlsx"
}
```

**Lưu ý:**
- Nếu các file có tên cột khác nhau (VD: "Mã ĐH" vs "ma_don_hang"), dùng tool `smart_fill` để chuẩn hóa trước
- Không set `group_by_cols` nếu chỉ muốn nối thô (append) không tính tổng

---

### Bước 2 — Phát hiện đơn trùng

Sau khi gộp, kiểm tra `ma_don_hang` trùng (cùng đơn bị nhập 2 lần bởi 2 nhân viên).

**Tool:** `validate_data`

```json
{
  "unique_columns": ["ma_don_hang"],
  "required_columns": ["ma_don_hang", "ma_khach_hang", "ngay_dat", "thanh_tien"]
}
```

**Output mẫu:**
```
❌ Duplicate ma_don_hang: DH2024001 (xuất hiện 2 lần)
❌ Missing ma_khach_hang: 5 dòng
✅ Tổng 1,234 đơn — 1,229 hợp lệ
```

---

### Bước 3 — Điền thông tin thiếu từ danh sách khách

Nhiều nhân viên chỉ nhập `ma_khach_hang` mà bỏ trống `ten_khach`, `dia_chi`, `so_dien_thoai`.

**Tool:** `smart_fill`

```json
{
  "join_key": "ma_khach_hang",
  "column_mapping": {
    "ten_khach": "ten_khach_hang",
    "dia_chi": "dia_chi_giao_hang",
    "dien_thoai": "so_dien_thoai"
  }
}
```

Source file: `danh_sach_khach.xlsx`  
Target file: `master_orders.xlsx`

---

### Bước 4 — Khớp tên khách hàng bị gõ sai

Nhân viên khác nhau hay gõ tên khách không đồng nhất: "Cty TNHH Minh Phát" vs "TNHH Minh Phát" vs "Minh Phat".

**Tool:** `fuzzy_match`

```json
{
  "match_column_a": "ten_khach",
  "match_column_b": "ten_cong_ty",
  "threshold": 75
}
```

**Output:** Danh sách cặp có thể là cùng khách, similarity score — để review và merge.

---

## Các Trường Hợp Hay Gặp

### Case 1: File của từng nhân viên có cột khác nhau

| File NV Nguyễn | File NV Trần | File NV Lê |
|---|---|---|
| `Mã ĐH` | `ma_don_hang` | `Order ID` |
| `Khách hàng` | `ten_kh` | `Customer` |
| `Ngày đặt` | `date` | `ngay_dat` |

**Giải pháp:**  
1. Dùng `smart_fill` để chuẩn hóa tên cột (hoặc đổi thủ công trước)  
2. Mô tả với Claude: "File của Nguyễn dùng 'Mã ĐH' thay vì 'ma_don_hang'"  
3. Claude sẽ map và gộp chính xác

---

### Case 2: Gộp theo kỳ — tuần/tháng/quý

```
User: "Gộp đơn hàng 3 tháng gần nhất, mỗi tháng 1 file"
```

1. Kéo thả 3 file tháng 2, 3, 4 vào chat
2. `aggregate_excel_data` gộp thô (không sum, chỉ append)
3. `filter_and_retrieve` lọc theo `ngay_dat` để lấy kỳ cụ thể

---

### Case 3: Gộp file nhiều sheet

Mỗi file có nhiều sheet (VD: sheet "Hà Nội", "HCM", "Đà Nẵng").

**Tool:** `aggregate_excel_data` với param `sheet` chỉ định tên sheet  
Hoặc: Xử lý từng sheet riêng rồi gộp kết quả.

---

### Case 4: Chuẩn hóa mã hàng

Mã hàng bị gõ không đồng nhất: "SP001", "sp001", "SP-001".

**Tool:** `fuzzy_match` với `threshold=90` để phát hiện cặp gần giống.  
Sau đó dùng `smart_fill` để ghi đè cột mã hàng bằng giá trị chuẩn từ bảng giá.

---

## Output

Sau khi hoàn tất aggregation:

```
✅ Tổng hợp thành công:
   - 5 file đầu vào → 1 file master
   - 2,450 đơn hàng
   - Loại 12 đơn trùng
   - Điền thêm thông tin cho 89 khách hàng
   - Output: master_orders.xlsx
```

File output có thêm cột:
- `nguon_file` — file gốc đơn hàng đến từ đâu
- `trang_thai_kiem_tra` — VALID / DUPLICATE / MISSING_INFO

---

## Giao Tiếp Với User

**Khi nhận yêu cầu tổng hợp:**
1. Xác nhận số file và cấu trúc: "Em thấy 3 file. Cột nào là mã đơn hàng?"
2. Hỏi output mong muốn: "Anh/chị cần gộp thô hay tính tổng số lượng/doanh thu?"
3. Hỏi xử lý trùng: "Nếu trùng mã đơn, giữ dòng nào — dòng đầu hay dòng sau?"

**Khi phát hiện vấn đề:**
- Luôn báo cụ thể: "12 đơn trùng mã DH2024001-DH2024012"
- Đề xuất hành động: "Em có thể xóa trùng giữ dòng đầu, hoặc export danh sách trùng để anh/chị review"

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| "Không tìm thấy cột key_column" | Tên cột khác nhau giữa các file | Mô tả tên cột thực tế trong từng file |
| "File không đọc được" | File đang mở trong Excel | Đóng file Excel trên máy rồi thử lại |
| "Kết quả rỗng" | Filter quá chặt | Kiểm tra lại điều kiện lọc |
| Tên khách bị split | Encoding lỗi (tiếng Việt) | Lưu file dạng UTF-8 trước khi kéo thả |


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
