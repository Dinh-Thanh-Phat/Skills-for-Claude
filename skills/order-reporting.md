---
name: order-reporting
description: Tạo báo cáo tổng hợp doanh số từ file đơn hàng — doanh thu theo nhân viên, sản phẩm, khu vực, thời gian; ranking; trend phân tích
origin: PT
tools: create_pivot_table, aggregate_excel_data, filter_and_retrieve, compare_excel_files
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Order Reporting Skill — Báo Cáo Đơn Hàng

Skill hỗ trợ sale manager / trưởng phòng kinh doanh tạo báo cáo doanh số từ file đơn hàng mà không cần biết Excel nâng cao. Từ dữ liệu thô → báo cáo trực quan trong vài phút.

---

## When to Activate

- User nói "báo cáo doanh số", "report doanh thu", "tổng kết bán hàng"
- User nói "nhân viên nào bán được nhiều nhất", "top sale", "xếp hạng doanh số"
- User nói "sản phẩm nào bán chạy", "best seller", "hàng tồn chưa bán được"
- User nói "doanh thu theo tháng", "so sánh tháng này vs tháng trước"
- User nói "doanh thu theo khu vực", "chi nhánh nào oke nhất"
- User nói "khách hàng nào đặt nhiều nhất", "top khách hàng"
- User nói "tạo pivot table", "làm bảng tổng hợp", "group by"
- User kéo thả file đơn hàng và nói "làm báo cáo cho tôi"

---

## Bối Cảnh Thực Tế

Cuối tuần/tháng/quý, quản lý cần báo cáo:
- **Sale manager:** Ai bán được bao nhiêu? Sản phẩm nào chạy?
- **Giám đốc kinh doanh:** Doanh thu có tăng trưởng không? Chi nhánh nào yếu?
- **Kế toán:** Tổng doanh thu để đối chiếu với sổ sách
- **Marketing:** Sản phẩm nào cần đẩy mạnh?

---

## Báo Cáo 1: Doanh Thu Theo Nhân Viên

**Tool:** `create_pivot_table`

```json
{
  "index": ["ten_nhan_vien"],
  "values": ["so_luong", "thanh_tien"],
  "aggfunc": "sum",
  "add_totals": true
}
```

**Output:**

| Nhân viên | Số đơn | Tổng doanh thu |
|---|---|---|
| Nguyễn Văn A | 145 | 2,340,000,000 |
| Trần Thị B | 132 | 2,180,000,000 |
| Lê Văn C | 98 | 1,560,000,000 |
| **Tổng** | **375** | **6,080,000,000** |

**Dùng `filter_and_retrieve` để lấy top 5:**
```json
{
  "sort_by": "thanh_tien",
  "top_n": 5
}
```

---

## Báo Cáo 2: Doanh Thu Theo Sản Phẩm

**Tool:** `create_pivot_table`

```json
{
  "index": ["ma_san_pham", "ten_san_pham"],
  "values": ["so_luong", "thanh_tien"],
  "aggfunc": "sum",
  "add_totals": true
}
```

**Thêm cột % đóng góp:**

Claude tính tự động:  
`% = thanh_tien_sp / tong_doanh_thu × 100`

**Output:**

| Sản phẩm | Số lượng | Doanh thu | % Đóng góp |
|---|---|---|---|
| SP001 - Áo sơ mi | 2,340 | 1,170,000,000 | 19.2% |
| SP002 - Quần tây | 1,890 | 945,000,000 | 15.5% |
| SP003 - Giày da | 567 | 850,500,000 | 14.0% |

---

## Báo Cáo 3: Doanh Thu Theo Khu Vực / Chi Nhánh

**Tool:** `create_pivot_table`

```json
{
  "index": ["khu_vuc"],
  "columns": ["thang"],
  "values": ["thanh_tien"],
  "aggfunc": "sum"
}
```

**Output (Pivot 2D — Khu vực × Tháng):**

| Khu vực | Tháng 1 | Tháng 2 | Tháng 3 | Tổng |
|---|---|---|---|---|
| Hà Nội | 1.2B | 1.4B | 1.1B | 3.7B |
| TP.HCM | 1.8B | 1.7B | 2.1B | 5.6B |
| Đà Nẵng | 0.6B | 0.5B | 0.7B | 1.8B |

---

## Báo Cáo 4: Trend Doanh Thu Theo Thời Gian

**Tool:** `aggregate_excel_data`

Group theo tháng:
```json
{
  "key_columns": ["thang", "nam"],
  "sum_cols": ["so_luong", "thanh_tien"],
  "output_path": "C:/Reports/trend_doanh_thu.xlsx"
}
```

**Nếu muốn so sánh cùng kỳ năm trước:**

Lọc năm nay:
```json
{"filters": [{"column": "nam", "op": "eq", "value": 2024}]}
```

Lọc năm trước:
```json
{"filters": [{"column": "nam", "op": "eq", "value": 2023}]}
```

Dùng `compare_excel_files` để tính tăng trưởng.

---

## Báo Cáo 5: Top Khách Hàng

**Tool:** `create_pivot_table`

```json
{
  "index": ["ma_khach_hang", "ten_khach_hang"],
  "values": ["so_don", "thanh_tien"],
  "aggfunc": {"so_don": "count", "thanh_tien": "sum"}
}
```

Sau đó `filter_and_retrieve` lấy top 10:
```json
{
  "sort_by": "thanh_tien",
  "top_n": 10
}
```

---

## Báo Cáo 6: Sản Phẩm Bán Chậm / Tồn Đọng

**Tool:** `filter_and_retrieve`

Lọc sản phẩm có doanh số thấp trong kỳ:
```json
{
  "filters": [
    {"column": "so_luong", "op": "lt", "value": 10}
  ],
  "sort_by": "so_luong"
}
```

**Hoặc:** Lọc sản phẩm không có đơn nào trong 30 ngày qua — cần join với danh sách sản phẩm rồi so sánh.

---

## Báo Cáo 7: Phân Tích Giỏ Hàng Trung Bình

**Tool:** `aggregate_excel_data`

```json
{
  "key_columns": ["ma_khach_hang"],
  "sum_cols": ["thanh_tien"],
  "group_by_cols": ["phan_khuc_khach_hang"]
}
```

Claude tính:
- `AOV (Average Order Value) = tong_doanh_thu / so_don`
- `Frequency = so_don / so_khach`

---

## Báo Cáo 8: So Sánh Mục Tiêu vs Thực Hiện

**Tool:** `vlookup_operation`

```json
{
  "join_key": "ten_nhan_vien",
  "lookup_columns": ["chi_tieu_thang", "chi_tieu_quy"]
}
```

Main: `ket_qua_ban_hang.xlsx`  
Lookup: `chi_tieu_sale.xlsx`

Kết quả join thêm cột:
- `% Hoàn thành = doanh_thu_thuc / chi_tieu × 100`
- `Chênh lệch = doanh_thu_thuc - chi_tieu`

**Output:**

| Nhân viên | Chỉ tiêu | Thực hiện | % Hoàn thành |
|---|---|---|---|
| Nguyễn Văn A | 2,000,000,000 | 2,340,000,000 | ✅ 117% |
| Trần Thị B | 2,500,000,000 | 2,180,000,000 | ⚠️ 87% |
| Lê Văn C | 2,000,000,000 | 1,560,000,000 | ❌ 78% |

---

## Cách Mô Tả Báo Cáo Với Claude

**Cú pháp đơn giản:**
> "Tạo báo cáo doanh thu theo nhân viên từ file này. Cột doanh thu tên là 'Thành tiền', cột nhân viên là 'NV phụ trách'."

**Báo cáo tháng:**
> "Tổng hợp doanh thu 3 tháng Q1. Chia theo từng tháng và từng sản phẩm. Top 10 sản phẩm bán chạy nhất."

**So sánh:**
> "File tháng 3 và tháng 4. So sánh doanh thu từng nhân viên. Ai tăng ai giảm?"

**Báo cáo thực hiện chỉ tiêu:**
> "File kết quả bán hàng tháng này và file chỉ tiêu. Nhân viên nào đạt, ai chưa đạt?"

---

## Format Output Chuẩn

Mọi báo cáo đều được export kèm:
1. **Summary table** — bảng tóm tắt chính
2. **Ranking** — xếp hạng theo metric chính
3. **Highlights** — top 3 cao nhất, bottom 3 thấp nhất
4. **File Excel** — để sếp có thể tự format thêm

**Template output:**

```
📊 BÁO CÁO DOANH SỐ THÁNG 04/2024
=====================================
Tổng doanh thu:  6,080,000,000 VND
Tổng đơn hàng:   1,240 đơn
AOV trung bình:  4,903,226 VND/đơn
vs Tháng trước:  ↑ +8.5%

🏆 TOP NHÂN VIÊN:
1. Nguyễn Văn A — 2.34B (117% chỉ tiêu) ✅
2. Trần Thị B   — 2.18B (87% chỉ tiêu) ⚠️
3. Lê Văn C     — 1.56B (78% chỉ tiêu) ❌

🔥 SẢN PHẨM BÁN CHẠY:
1. SP001 - Áo sơ mi — 2,340 cái — 1.17B
2. SP002 - Quần tây — 1,890 cái — 0.95B

📎 Xuất file: bao_cao_thang4_2024.xlsx
```

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| Pivot không có tháng | Cột ngày lưu dạng text | Convert sang date trong Excel trước |
| Doanh thu hiển thị sai | Có dòng text lẫn trong cột số | Dùng `validate_data` lọc trước |
| Nhân viên bị tách đôi | "Nguyễn A" vs "Nguyen A" | Dùng `fuzzy_match` để gộp |
| Tổng không khớp | Có đơn bị hủy chưa lọc | Lọc `trang_thai = "active"` trước |


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
