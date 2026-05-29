---
name: quote-builder
description: Tạo báo giá từ bảng giá chính thức + thông tin khách hàng — tự động tính discount tier, thuế, tổng tiền, export file báo giá chuẩn
origin: PT
tools: vlookup_operation, filter_and_retrieve, smart_fill, validate_data
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Quote Builder Skill — Tạo Báo Giá

Skill hỗ trợ nhân viên sale tạo báo giá nhanh từ bảng giá chính thức, tự động tra discount theo hạng khách hàng, tính thuế VAT, và export file báo giá sạch gửi khách.

---

## When to Activate

- User nói "tạo báo giá", "làm quote", "lập báo giá cho khách"
- User nói "tra giá sản phẩm", "áp giá đúng cho khách này"
- User nói "khách này được giảm bao nhiêu %", "discount tier của khách"
- User nói "xuất file báo giá", "gửi quote cho khách"
- User kéo thả file danh sách sản phẩm cần báo giá + bảng giá vào chat

---

## Bối Cảnh Thực Tế

Nhân viên sale mỗi ngày cần tạo 5-20 báo giá:
- Tra bảng giá đúng phiên bản
- Áp discount đúng tier khách (Silver/Gold/Platinum)
- Tính VAT 10%
- Format file đẹp để gửi khách

Làm thủ công tốn 15-30 phút/báo giá. Skill này rút xuống còn 2-3 phút.

---

## Bước 1 — Tra Giá Sản Phẩm

**Tool:** `vlookup_operation`

File chứa danh sách SP cần báo giá:
```json
{
  "join_key": "ma_san_pham",
  "lookup_columns": ["ten_san_pham", "gia_niem_yet", "don_vi_tinh", "mo_ta"]
}
```

Main: danh sách SP khách yêu cầu  
Lookup: `bang_gia_chinh_thuc.xlsx`

---

## Bước 2 — Áp Discount Theo Tier Khách

**Tool:** `vlookup_operation`

Tra hạng khách hàng:
```json
{
  "join_key": "ma_khach_hang",
  "lookup_columns": ["hang_khach_hang", "discount_phan_tram", "han_muc_gia_dac_biet"]
}
```

Lookup: `phan_loai_khach_hang.xlsx`

**Bảng discount mẫu:**

| Hạng | Discount | Điều kiện |
|---|---|---|
| Standard | 0% | Đơn < 10M |
| Silver | 5% | Đơn 10M–50M |
| Gold | 10% | Đơn 50M–200M |
| Platinum | 15% | Đơn > 200M |

Claude tính:
- `gia_sau_discount = gia_niem_yet × (1 - discount%)`
- `thanh_tien = so_luong × gia_sau_discount`
- `vat = thanh_tien × 10%`
- `tong_cong = thanh_tien + vat`

---

## Bước 3 — Validate Báo Giá

**Tool:** `validate_data`

```json
{
  "required_columns": ["ma_san_pham", "ten_san_pham", "so_luong", "gia_niem_yet", "gia_sau_discount"],
  "not_negative_columns": ["so_luong", "gia_sau_discount"],
  "numeric_columns": ["so_luong", "gia_niem_yet", "discount_phan_tram"]
}
```

---

## Output Báo Giá Chuẩn

```
📋 BÁO GIÁ — [Tên khách hàng]
Ngày:     27/04/2026
Hiệu lực: 30 ngày
Hạng KH:  Gold (discount 10%)

STT | Mã SP  | Sản phẩm       | SL  | Đơn giá    | Discount | Thành tiền
----|--------|----------------|-----|------------|----------|------------
1   | SP001  | Áo sơ mi trắng | 100 | 250,000    | 10%      | 22,500,000
2   | SP002  | Quần tây đen   | 50  | 400,000    | 10%      | 18,000,000
----|--------|----------------|-----|------------|----------|------------
                              Tổng chưa VAT:            40,500,000
                              VAT 10%:                   4,050,000
                              TỔNG CỘNG:                44,550,000

📎 Export: bao_gia_[ten_kh]_[ngay].xlsx
```

---

## Các Trường Hợp Đặc Biệt

**Giá đặc biệt theo đơn lớn:**
```json
{
  "filters": [
    {"column": "tong_don", "op": "gt", "value": 500000000}
  ]
}
```
→ Flag để sale manager duyệt giá thêm

**Sản phẩm hết hàng / ngừng kinh doanh:**
```json
{
  "filters": [
    {"column": "trang_thai", "op": "eq", "value": "active"}
  ]
}
```
→ Chỉ báo giá SP đang active

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| Giá sai phiên bản | Dùng bảng giá cũ | Luôn dùng file có ngày mới nhất |
| Discount không đúng | Sai hạng khách | Check lại `phan_loai_khach_hang.xlsx` |
| SP không có trong bảng giá | SP mới chưa cập nhật | Báo admin thêm vào bảng giá |
| VAT tính sai | Một số SP không chịu VAT | Check cột `chiu_vat` trong bảng giá |


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
