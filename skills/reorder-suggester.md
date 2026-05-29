---
name: reorder-suggester
description: Gợi ý khách hàng sắp cần đặt hàng lại dựa trên chu kỳ mua — tạo danh sách follow-up cho sale, không bỏ lỡ cơ hội tái đơn
origin: PT
tools: aggregate_excel_data, filter_and_retrieve, vlookup_operation, create_pivot_table
mcp_server: https://excel-mcp-server-dawn-star-9929.fly.dev
---

# Reorder Suggester Skill — Gợi Ý Tái Đơn

Skill phân tích lịch sử mua hàng của từng khách, tính chu kỳ mua trung bình, dự đoán khách nào sắp cần đặt lại để sale chủ động liên hệ đúng thời điểm.

---

## When to Activate

- User nói "khách nào sắp cần mua lại", "tái đơn", "reorder"
- User nói "gợi ý khách để follow-up", "ai nên gọi điện tuần này"
- User nói "khách nào hay mua định kỳ", "chu kỳ mua của khách"
- User nói "đừng để khách mua từ đối thủ", "giữ khách quen"
- User nói "danh sách khách cần liên hệ tháng này"
- User kéo thả file lịch sử đơn hàng vào chat

---

## Bối Cảnh Thực Tế

Nhiều ngành hàng có chu kỳ mua định kỳ:
- Văn phòng phẩm: mỗi tháng
- Thực phẩm B2B: mỗi 2 tuần
- Nguyên liệu sản xuất: theo sản lượng
- Đồng phục công ty: mỗi năm

Sale chủ động gọi **đúng lúc** khách sắp hết hàng → win rate cao hơn chờ khách gọi.

---

## Bước 1 — Tính Chu Kỳ Mua Trung Bình

**Tool:** `aggregate_excel_data`

Tính khoảng cách giữa các đơn của từng khách:
```json
{
  "key_columns": ["ma_khach_hang", "ten_khach_hang"],
  "count_cols": ["ma_don_hang"],
  "sum_cols": ["thanh_tien"],
  "max_cols": ["ngay_dat"],
  "min_cols": ["ngay_dat"]
}
```

Claude tính:
- `tong_ngay = ngay_dat_cuoi - ngay_dat_dau`
- `chu_ky_tb = tong_ngay / (so_lan_mua - 1)` (số ngày trung bình giữa 2 đơn)
- `ngay_du_kien_mua_tiep = ngay_mua_cuoi + chu_ky_tb`

---

## Bước 2 — Lọc Khách Sắp Đến Chu Kỳ

**Tool:** `filter_and_retrieve`

Khách sẽ cần mua trong 7 ngày tới:
```json
{
  "filters": [
    {"column": "ngay_du_kien_mua_tiep", "op": "gte", "value": "today"},
    {"column": "ngay_du_kien_mua_tiep", "op": "lte", "value": "today+7"},
    {"column": "so_lan_mua", "op": "gte", "value": 3}
  ],
  "sort_by": "gia_tri_don_tb",
  "select_columns": ["ten_khach_hang", "so_dien_thoai", "nhan_vien_phu_trach", "chu_ky_tb", "ngay_du_kien_mua_tiep", "gia_tri_don_tb", "san_pham_hay_mua"]
}
```

---

## Bước 3 — Khách Đã Qua Chu Kỳ Nhưng Chưa Đặt

**Tool:** `filter_and_retrieve`

Khách trễ hơn chu kỳ > 7 ngày (cần ưu tiên gọi):
```json
{
  "filters": [
    {"column": "ngay_du_kien_mua_tiep", "op": "lt", "value": "today-7"},
    {"column": "so_lan_mua", "op": "gte", "value": 3}
  ],
  "sort_by": "so_ngay_tre",
  "select_columns": ["ten_khach_hang", "so_dien_thoai", "nhan_vien_phu_trach", "so_ngay_tre", "gia_tri_don_tb"]
}
```

---

## Bước 4 — Sản Phẩm Hay Mua Của Từng Khách

**Tool:** `create_pivot_table`

```json
{
  "index": ["ma_khach_hang"],
  "columns": ["ma_san_pham"],
  "values": ["so_luong"],
  "aggfunc": "sum"
}
```

Dùng để sale biết gợi ý đúng sản phẩm khi gọi điện.

---

## Bước 5 — Phân Theo NV Phụ Trách

**Tool:** `aggregate_excel_data`

```json
{
  "key_columns": ["nhan_vien_phu_trach"],
  "count_cols": ["ma_khach_hang"],
  "sum_cols": ["gia_tri_don_tb"]
}
```

Export danh sách riêng cho từng NV sale.

---

## Output Danh Sách Follow-up

```
📞 DANH SÁCH KHÁCH CẦN LIÊN HỆ — Tuần 18/2026
================================================
Tổng: 34 khách cần follow-up tuần này

🔴 ƯU TIÊN CAO — Đã qua chu kỳ > 7 ngày (12 khách):
   KH001 - Cty Minh Phát    | NV: Trần B | Trễ 14 ngày | Đơn TB: 45M
   KH002 - Cty Hoàng Long   | NV: Lê C   | Trễ 10 ngày | Đơn TB: 28M
   → SP hay mua: SP001 (Áo sơ mi), SP002 (Quần tây)

🟡 BÌNH THƯỜNG — Sắp đến chu kỳ (22 khách):
   KH015 - Shop Thời Trang ABC | NV: Nguyễn A | Còn 3 ngày | Đơn TB: 32M
   KH023 - Cty XYZ            | NV: Trần B   | Còn 5 ngày | Đơn TB: 18M

📊 PHÂN BỔ THEO NV:
   Nguyễn A: 14 khách — tổng đơn dự kiến: 420M
   Trần B:   12 khách — tổng đơn dự kiến: 380M
   Lê C:      8 khách — tổng đơn dự kiến: 220M

📎 Export riêng từng NV: follow_up_tuan18_[ten_nv].xlsx
```

---

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| Chu kỳ tính sai | Khách mua 1-2 lần không đủ data | Chỉ tính KH có ≥ 3 đơn |
| Gợi ý sai sản phẩm | SP không còn trong bảng giá | Join với bảng giá để lọc SP active |
| KH theo mùa bị báo sai | Chu kỳ mua theo mùa, không đều | Lọc theo cùng tháng năm trước |


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
