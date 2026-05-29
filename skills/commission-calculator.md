---
name: commission-calculator
description: Tính hoa hồng nhân viên sale theo tier doanh số — áp đúng bảng hoa hồng, trừ đơn hủy/trả, export phiếu lương hoa hồng cuối tháng
origin: PT
tools: vlookup_operation, aggregate_excel_data, filter_and_retrieve, validate_data
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Commission Calculator Skill — Tính Hoa Hồng Nhân Viên

Skill hỗ trợ HR / kế toán tính hoa hồng nhân viên sale cuối tháng — tự động áp bảng hoa hồng theo tier doanh số, trừ đơn hủy, xử lý chia hoa hồng khi 2 NV cùng phụ trách.

---

## When to Activate

- User nói "tính hoa hồng", "tính commission", "hoa hồng tháng này"
- User nói "nhân viên được bao nhiêu tiền", "lương commission cuối tháng"
- User nói "ai đạt tier nào", "tier hoa hồng tháng này"
- User nói "trừ đơn hủy khỏi hoa hồng", "đơn trả ảnh hưởng hoa hồng"
- User nói "chia hoa hồng 2 người cùng bán"
- User kéo thả file doanh số tháng để tính commission

---

## Bối Cảnh Thực Tế

Cuối tháng, HR/kế toán phải:
1. Tổng hợp doanh số từng NV
2. Xác định tier hoa hồng đạt được
3. Trừ đơn hủy / đơn trả hàng
4. Tính số tiền hoa hồng thực nhận
5. Export phiếu cho từng NV

Làm thủ công trên Excel tốn 2-3 giờ, hay bị sai vì công thức phức tạp.

---

## Bước 1 — Tổng Hợp Doanh Số Từng NV

**Tool:** `aggregate_excel_data`

```json
{
  "key_columns": ["ma_nhan_vien", "ten_nhan_vien"],
  "sum_cols": ["thanh_tien", "so_luong"],
  "count_cols": ["ma_don_hang"],
  "filters": [
    {"column": "trang_thai", "op": "eq", "value": "hoan_thanh"}
  ]
}
```

Chỉ tính đơn hàng `hoan_thanh` — loại trừ đơn hủy / đơn đang xử lý.

---

## Bước 2 — Áp Bảng Hoa Hồng Theo Tier

**Tool:** `vlookup_operation`

Tra tier hoa hồng theo doanh số tháng:

```json
{
  "join_key": "doanh_so_thang",
  "lookup_columns": ["tier", "phan_tram_hoa_hong", "thuong_them"]
}
```

Lookup: `bang_hoa_hong.xlsx`

**Bảng hoa hồng mẫu:**

| Tier | Doanh số | Hoa hồng | Thưởng thêm |
|---|---|---|---|
| Bronze | < 100M | 2% | 0 |
| Silver | 100M – 200M | 3% | 2,000,000 |
| Gold | 200M – 500M | 5% | 5,000,000 |
| Platinum | > 500M | 7% | 15,000,000 |

Claude tính:
- `hoa_hong_co_ban = doanh_so_thuc × phan_tram`
- `tong_hoa_hong = hoa_hong_co_ban + thuong_them`

---

## Bước 3 — Trừ Đơn Hủy / Trả Hàng

**Tool:** `filter_and_retrieve`

Lấy danh sách đơn hủy trong tháng:
```json
{
  "filters": [
    {"column": "trang_thai", "op": "in", "value": ["huy", "tra_hang"]},
    {"column": "thang", "op": "eq", "value": "2026-04"}
  ],
  "select_columns": ["ma_nhan_vien", "thanh_tien", "ly_do"]
}
```

Sau đó group by NV và trừ vào doanh số:
- `doanh_so_thuc = doanh_so_gross - doanh_so_huy`
- Nếu doanh_so_thuc < ngưỡng tier → hạ tier xuống

---

## Bước 4 — Xử Lý Chia Hoa Hồng (2 NV Cùng Phụ Trách)

**Tool:** `filter_and_retrieve`

Lọc đơn có cột `nhan_vien_phu` không trống:
```json
{
  "filters": [
    {"column": "nhan_vien_phu", "op": "ne", "value": ""}
  ],
  "select_columns": ["ma_don_hang", "thanh_tien", "nhan_vien_chinh", "nhan_vien_phu", "ty_le_chia"]
}
```

Áp tỷ lệ chia (mặc định 70/30 nếu không ghi):
- `hoa_hong_chinh = hoa_hong × ty_le_chinh`
- `hoa_hong_phu = hoa_hong × ty_le_phu`

---

## Bước 5 — Validate Kết Quả Trước Khi Export

**Tool:** `validate_data`

```json
{
  "not_negative_columns": ["tong_hoa_hong", "doanh_so_thuc"],
  "required_columns": ["ma_nhan_vien", "ten_nhan_vien", "doanh_so_thuc", "tier", "tong_hoa_hong"]
}
```

---

## Output Phiếu Hoa Hồng

```
💰 HOA HỒNG THÁNG 04/2026
===========================
Tổng NV tính hoa hồng: 18 người
Tổng hoa hồng chi trả: 245,000,000 VND

🏆 BẢNG HOA HỒNG TỪNG NV:

NV          | DS Gross   | Đơn hủy | DS Thực   | Tier     | HH%  | HH cơ bản | Thưởng  | TỔNG HH
------------|------------|---------|-----------|----------|------|-----------|---------|----------
Nguyễn A    | 520,000,000| 0       | 520,000,000| Platinum| 7%   | 36,400,000| 15,000,000| 51,400,000
Trần B      | 185,000,000| 20,000,000| 165,000,000| Silver | 3%   | 4,950,000 | 2,000,000| 6,950,000
Lê C        | 95,000,000 | 0       | 95,000,000 | Bronze  | 2%   | 1,900,000 | 0       | 1,900,000

📊 PHÂN PHỐI TIER:
   Platinum: 2 NV
   Gold:     5 NV
   Silver:   8 NV
   Bronze:   3 NV

📎 Export: hoa_hong_thang4_2026.xlsx (1 sheet/NV)
```

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| NV bị sai tier | Chưa trừ đơn hủy | Luôn trừ đơn hủy trước khi áp tier |
| Tổng không khớp với kế toán | Đơn VAT vs không VAT | Xác định tính trên doanh thu trước hay sau VAT |
| NV mới không có trong bảng | Bảng hoa hồng chưa cập nhật | Thêm NV mới vào `bang_hoa_hong.xlsx` |
| Chia hoa hồng không đủ 100% | Tỷ lệ chia ghi sai | Validate tổng tỷ lệ chia = 100% |


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
