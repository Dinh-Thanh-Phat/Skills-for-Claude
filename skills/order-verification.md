---
name: order-verification
description: Kiểm tra tính hợp lệ của đơn hàng — phát hiện đơn trùng, giá sai, thiếu thông tin, số lượng bất thường, không khớp với bảng giá
origin: PT
tools: validate_data, compare_excel_files, vlookup_operation, fuzzy_match, filter_and_retrieve
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Order Verification Skill — Kiểm Đơn Hàng

Skill hỗ trợ kiểm soát viên / kế toán kiểm tra chất lượng đơn hàng trước khi xử lý. Phát hiện sai sót sớm để tránh xuất hàng nhầm, thanh toán sai, hoặc tranh chấp sau này.

---

## When to Activate

- User nói "kiểm đơn", "soát đơn", "check đơn hàng", "review order"
- User nói "giá có đúng không", "đơn nào bị sai giá", "giá không khớp với bảng giá"
- User nói "đơn trùng", "duplicate order", "nhập 2 lần", "đơn bị lặp"
- User nói "thiếu thông tin", "đơn chưa đủ", "missing field"
- User nói "số lượng bất thường", "đơn quá lớn", "đơn nghi ngờ"
- User nói "kiểm tra trước khi duyệt", "validate trước khi gửi kho"
- User kéo thả file đơn hàng + bảng giá vào chat để cross-check

---

## Bối Cảnh Thực Tế

Trước khi duyệt đơn và gửi kho xuất hàng, bộ phận kiểm soát cần:
1. **Kiểm tra đơn trùng** — cùng đơn nhập 2 lần
2. **Kiểm tra giá** — giá bán có đúng bảng giá không
3. **Kiểm tra thông tin bắt buộc** — tên khách, địa chỉ, SĐT, mã sản phẩm
4. **Kiểm tra số lượng bất thường** — đơn quá lớn so với lịch sử
5. **Kiểm tra discount** — chiết khấu có vượt mức cho phép không

---

## Kiểm Tra 1: Đơn Trùng Lặp

**Tool:** `validate_data`

**Khi nào xảy ra:**
- Nhân viên nhập đơn 2 lần do refresh form
- 2 nhân viên cùng nhập đơn của 1 khách
- Import file 2 lần

**Params:**
```json
{
  "unique_columns": ["ma_don_hang"],
  "required_columns": ["ma_don_hang", "ngay_dat", "ma_khach_hang"]
}
```

**Phát hiện nâng cao — trùng nội dung dù khác mã:**

Đôi khi 2 đơn có mã khác nhau nhưng cùng khách, cùng ngày, cùng sản phẩm → dùng `filter_and_retrieve`:

```json
{
  "filters": [
    {"column": "ngay_dat", "op": "eq", "value": "2024-04-15"},
    {"column": "ma_khach_hang", "op": "eq", "value": "KH001"}
  ]
}
```

Nếu ra 2+ dòng với cùng sản phẩm và số lượng → nghi ngờ trùng.

---

## Kiểm Tra 2: Giá Bán vs Bảng Giá

**Tool:** `vlookup_operation`

**Scenario:** File đơn hàng có cột `don_gia_ban`, cần check với `bang_gia_chinh_thuc.xlsx`.

```json
{
  "join_key": "ma_san_pham",
  "lookup_columns": ["gia_niem_yet", "gia_toi_thieu", "discount_max"]
}
```

Sau khi join, dùng `filter_and_retrieve` để lọc ra các đơn sai giá:

```json
{
  "filters": [
    {"column": "don_gia_ban", "op": "lt", "value": "gia_toi_thieu"}
  ]
}
```

**Output:** Danh sách đơn có giá thấp hơn giá tối thiểu — cần xem xét.

---

## Kiểm Tra 3: Thông Tin Bắt Buộc

**Tool:** `validate_data`

Các trường PHẢI có giá trị trước khi duyệt đơn:

```json
{
  "required_columns": [
    "ma_don_hang",
    "ma_khach_hang",
    "ten_khach_hang",
    "so_dien_thoai",
    "dia_chi_giao_hang",
    "ma_san_pham",
    "so_luong",
    "don_gia_ban",
    "ngay_giao_hang_yeu_cau"
  ]
}
```

**Output mẫu:**
```
❌ Thiếu dia_chi_giao_hang: 23 đơn (DH001, DH005, DH012...)
❌ Thiếu ngay_giao_hang_yeu_cau: 8 đơn
⚠️  so_dien_thoai chứa ký tự lạ: 5 đơn
✅ 1,204/1,240 đơn đầy đủ thông tin
```

---

## Kiểm Tra 4: Số Lượng Bất Thường

**Tool:** `validate_data` + `filter_and_retrieve`

**Phát hiện đơn có số lượng <= 0 hoặc âm:**
```json
{
  "not_negative_columns": ["so_luong", "thanh_tien"],
  "numeric_columns": ["so_luong", "don_gia_ban", "thanh_tien"]
}
```

**Phát hiện đơn vượt mức bất thường** (VD: > 1000 sản phẩm):
```json
{
  "filters": [
    {"column": "so_luong", "op": "gt", "value": 1000}
  ],
  "sort_by": "so_luong",
  "top_n": 20
}
```

**Output:** Top 20 đơn có số lượng lớn nhất — để review thủ công.

---

## Kiểm Tra 5: Chiết Khấu Vượt Mức

**Tool:** `filter_and_retrieve`

Nếu file có cột `chiet_khau_phan_tram`:
```json
{
  "filters": [
    {"column": "chiet_khau_phan_tram", "op": "gt", "value": 30}
  ]
}
```

Các đơn có chiết khấu > 30% cần xem lại — có thể nhân viên nhập sai hoặc cố tình.

---

## Kiểm Tra 6: Ngày Tháng Hợp Lệ

**Tool:** `validate_data`

```json
{
  "date_columns": ["ngay_dat", "ngay_giao_hang_yeu_cau", "ngay_het_han"]
}
```

**Phát hiện:**
- Ngày không hợp lệ (VD: "30/02/2024")
- Ngày giao hàng trước ngày đặt
- Đơn có ngày đặt trong tương lai (nhập sai năm)

---

## Kiểm Tra 7: Mã Khách Hàng Không Tồn Tại

**Tool:** `compare_excel_files`

So sánh cột `ma_khach_hang` trong file đơn với danh sách khách hàng chính thức:

```json
{
  "key_column": "ma_khach_hang"
}
```

Các mã `Added` trong file đơn mà không có trong danh sách KH = mã không hợp lệ.

---

## Kiểm Tra 8: Tên Khách Hàng Không Rõ Ràng

**Tool:** `fuzzy_match`

Phát hiện các tên khách gõ sai chính tả hoặc viết tắt khác nhau:

```json
{
  "match_column_a": "ten_khach_hang",
  "match_column_b": "ten_cong_ty",
  "threshold": 70
}
```

**Ví dụ phát hiện:**
| File đơn | Danh sách KH | Score |
|---|---|---|
| "Cty Minh Phát" | "Công ty TNHH Minh Phát" | 82% |
| "Honda Viêt Nam" | "Honda Việt Nam" | 95% |

---

## Workflow Kiểm Đơn Đầy Đủ

```
1. [validate_data]        → Kiểm trùng mã, thiếu field, số âm, ngày lỗi
2. [vlookup_operation]    → Join bảng giá → phát hiện giá sai
3. [filter_and_retrieve]  → Lọc đơn có discount cao bất thường
4. [filter_and_retrieve]  → Lọc đơn số lượng quá lớn
5. [compare_excel_files]  → Kiểm mã KH vs danh sách chính thức
6. [fuzzy_match]          → Phát hiện tên KH gõ sai
```

---

## Output Báo Cáo Kiểm Đơn

Claude tổng hợp kết quả theo format:

```
📋 BÁO CÁO KIỂM ĐƠN — [Ngày]
================================
Tổng đơn kiểm tra: 1,240

✅ ĐƠN HỢP LỆ: 1,180 đơn (95.2%)

⚠️  CẦN XEM LẠI: 36 đơn
   - Giá thấp hơn bảng giá: 12 đơn
   - Chiết khấu > 30%: 8 đơn
   - Số lượng bất thường (>1000): 4 đơn
   - Tên KH không rõ ràng: 12 đơn

❌ CẦN SỬA NGAY: 24 đơn
   - Thiếu địa chỉ giao hàng: 15 đơn
   - Trùng mã đơn: 5 đơn (DH001, DH003...)
   - Mã KH không tồn tại: 4 đơn

📎 File chi tiết: kiem_don_20240427.xlsx
```

---

## Hành Động Sau Kiểm Tra

| Loại lỗi | Xử lý đề xuất |
|---|---|
| Đơn trùng | Export list, hỏi nhân viên giữ đơn nào |
| Giá sai | Flag cho sale manager review |
| Thiếu thông tin | Gửi lại nhân viên bổ sung |
| KH không tồn tại | Kiểm tra có tạo KH mới chưa |
| Số lượng lớn | Xác nhận lại với khách hàng |
| Discount vượt mức | Cần approval từ manager |

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| Kiểm giá ra sai hết | Tên cột giá khác nhau | Mô tả tên cột thực tế: "cột giá tên là 'Đơn giá'" |
| Không phát hiện trùng | Mã đơn có khoảng trắng thừa | Dữ liệu cần trim trước |
| Fuzzy match quá nhiều false positive | Threshold quá thấp | Tăng lên 85-90 |
| Validate data báo lỗi ngày | File lưu ngày dạng text | Cần convert sang date format trong Excel |


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
