---
name: contract-tracker
description: Theo dõi hợp đồng khách hàng — cảnh báo hợp đồng sắp hết hạn, điều khoản thanh toán quá hạn, công nợ lâu chưa thu
origin: PT
tools: filter_and_retrieve, aggregate_excel_data, vlookup_operation, validate_data
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Contract Tracker Skill — Theo Dõi Hợp Đồng

Skill hỗ trợ bộ phận kinh doanh / kế toán theo dõi hợp đồng khách hàng — không để hợp đồng hết hạn mà không gia hạn, không để công nợ tồn đọng quá lâu.

---

## When to Activate

- User nói "hợp đồng sắp hết hạn", "contract expiry", "gia hạn hợp đồng"
- User nói "công nợ quá hạn", "khách nợ lâu chưa trả", "overdue payment"
- User nói "điều khoản thanh toán", "net 30", "khách thanh toán trễ hạn"
- User nói "hợp đồng nào cần gia hạn tháng này"
- User nói "tổng công nợ hiện tại", "aging report"
- User kéo thả file quản lý hợp đồng / công nợ vào chat

---

## Bối Cảnh Thực Tế

Doanh nghiệp B2B thường ký hợp đồng khung với khách lớn:
- Hợp đồng có thời hạn 1 năm, cần gia hạn
- Điều khoản thanh toán: Net 30, Net 60 (trả tiền sau 30/60 ngày)
- Công nợ quá hạn ảnh hưởng dòng tiền của công ty

---

## Case 1 — Hợp Đồng Sắp Hết Hạn

**Tool:** `filter_and_retrieve`

Hợp đồng hết hạn trong 30 ngày tới:
```json
{
  "filters": [
    {"column": "ngay_het_han", "op": "gte", "value": "today"},
    {"column": "ngay_het_han", "op": "lte", "value": "today+30"},
    {"column": "trang_thai", "op": "eq", "value": "active"}
  ],
  "sort_by": "ngay_het_han",
  "select_columns": ["ma_hop_dong", "ten_khach_hang", "ngay_ky", "ngay_het_han", "gia_tri_hop_dong", "nhan_vien_phu_trach", "so_ngay_con_lai"]
}
```

Hợp đồng đã hết hạn nhưng chưa gia hạn:
```json
{
  "filters": [
    {"column": "ngay_het_han", "op": "lt", "value": "today"},
    {"column": "trang_thai", "op": "eq", "value": "active"}
  ]
}
```

---

## Case 2 — Công Nợ Quá Hạn (Aging Report)

**Tool:** `filter_and_retrieve`

**Quá hạn 1–30 ngày:**
```json
{
  "filters": [
    {"column": "so_ngay_qua_han", "op": "gte", "value": 1},
    {"column": "so_ngay_qua_han", "op": "lte", "value": 30}
  ],
  "select_columns": ["ma_khach_hang", "ten_khach_hang", "so_tien_no", "ngay_den_han", "so_ngay_qua_han"]
}
```

**Quá hạn 31–60 ngày (cần escalate):**
```json
{
  "filters": [
    {"column": "so_ngay_qua_han", "op": "gte", "value": 31},
    {"column": "so_ngay_qua_han", "op": "lte", "value": 60}
  ]
}
```

**Quá hạn > 60 ngày (nguy cơ mất nợ):**
```json
{
  "filters": [
    {"column": "so_ngay_qua_han", "op": "gt", "value": 60}
  ],
  "sort_by": "so_tien_no"
}
```

---

## Case 3 — Tổng Hợp Công Nợ Theo Nhóm Tuổi

**Tool:** `aggregate_excel_data`

```json
{
  "key_columns": ["nhom_cong_no"],
  "count_cols": ["ma_khach_hang"],
  "sum_cols": ["so_tien_no"]
}
```

Claude phân nhóm tự động:
- `Chưa đến hạn`
- `1–30 ngày`
- `31–60 ngày`
- `61–90 ngày`
- `> 90 ngày`

---

## Case 4 — Khớp Đơn Hàng Với Điều Khoản Thanh Toán

**Tool:** `vlookup_operation`

Join file đơn hàng với điều khoản thanh toán của từng khách:
```json
{
  "join_key": "ma_khach_hang",
  "lookup_columns": ["dieu_khoan_tt", "so_ngay_net", "han_muc_tin_dung"]
}
```

Tính ngày đến hạn thanh toán:
- `ngay_den_han = ngay_xuat_hoa_don + so_ngay_net`

Lọc đơn sắp đến hạn trong 7 ngày:
```json
{
  "filters": [
    {"column": "ngay_den_han", "op": "gte", "value": "today"},
    {"column": "ngay_den_han", "op": "lte", "value": "today+7"},
    {"column": "trang_thai_tt", "op": "ne", "value": "da_thanh_toan"}
  ]
}
```

---

## Case 5 — Khách Vượt Hạn Mức Tín Dụng

**Tool:** `vlookup_operation`

```json
{
  "join_key": "ma_khach_hang",
  "lookup_columns": ["han_muc_tin_dung"]
}
```

Sau khi join, lọc khách có công nợ > hạn mức:
```json
{
  "filters": [
    {"column": "tong_cong_no", "op": "gt", "value": "han_muc_tin_dung"}
  ],
  "select_columns": ["ten_khach_hang", "tong_cong_no", "han_muc_tin_dung", "vuot_han_muc"]
}
```

**Cảnh báo:** Không duyệt đơn mới cho khách đang vượt hạn mức tín dụng.

---

## Output Báo Cáo Hợp Đồng & Công Nợ

```
📋 BÁO CÁO HỢP ĐỒNG & CÔNG NỢ — 27/04/2026
=============================================

📄 HỢP ĐỒNG SẮP HẾT HẠN (30 ngày tới): 8 hợp đồng
   ⚠️  Cty Minh Phát    — hết hạn 05/05 (còn 8 ngày)  — NV: Trần B
   ⚠️  Cty Hoàng Long   — hết hạn 12/05 (còn 15 ngày) — NV: Lê C
   → Cần liên hệ gia hạn ngay tuần này

💰 TÌNH HÌNH CÔNG NỢ:
   Chưa đến hạn:    2,340,000,000 VND (45 KH)
   Quá hạn 1–30:     780,000,000 VND (18 KH) ⚠️
   Quá hạn 31–60:    340,000,000 VND (8 KH)  🔴
   Quá hạn > 60:     180,000,000 VND (3 KH)  🚨
   TỔNG CÔNG NỢ:   3,640,000,000 VND

🚨 KHÁCH VƯỢT HẠN MỨC TÍN DỤNG: 2 khách
   Cty XYZ: công nợ 850M / hạn mức 500M (+70%)
   → Tạm dừng xuất hàng cho khách này

📅 ĐẾN HẠN THANH TOÁN TUẦN NÀY: 12 đơn — 456M VND
   → Gửi reminder cho khách

📎 Chi tiết: hop_dong_cong_no_27042026.xlsx
```

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| Công nợ không đúng | Chưa cập nhật thanh toán vào file | Sync file thanh toán mới nhất trước khi chạy |
| Hợp đồng hết hạn không cảnh báo | Ngày lưu dạng text | Convert cột ngày sang date format |
| Khách nhiều hợp đồng tính sai | Gộp hết vào 1 dòng | Group by `ma_hop_dong`, không chỉ `ma_khach_hang` |


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
