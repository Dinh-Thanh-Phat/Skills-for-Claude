# Lookup & Retrieval Guide — VLOOKUP, Filter, Pivot

## Khi nào đọc file này

Khi user cần:
- Tra cứu dữ liệu từ file khác (tương đương VLOOKUP)
- Lọc dữ liệu theo điều kiện
- Tạo pivot table, báo cáo tổng hợp
- Xuất riêng từng sheet cho từng nhóm/nhân viên/khu vực

---

## 1. VLOOKUP Equivalents

### 1-column VLOOKUP (đơn giản nhất)

```python
import pandas as pd

# Bài toán: Có file đơn hàng, cần lấy thêm Tên KH + Địa chỉ từ file danh mục
don_hang = pd.read_excel("don_hang.xlsx")
danh_muc = pd.read_excel("danh_muc_khach_hang.xlsx")

# Excel: =VLOOKUP(A2, danh_muc!A:C, 2, 0)
# Python:
result = don_hang.merge(
    danh_muc[["ma_kh", "ten_kh", "dia_chi", "so_dien_thoai"]],
    on="ma_kh",        # Cột chung để join
    how="left"         # "left" = giữ tất cả dòng trong don_hang
)

# Kiểm tra dòng không lookup được (VLOOKUP trả về #N/A)
missing = result[result["ten_kh"].isna()]
print(f"⚠ Không tìm thấy KH: {len(missing)} dòng")
print(missing[["ma_kh"]].to_string())

result.to_excel("don_hang_daydu.xlsx", index=False)
```

### Multi-column VLOOKUP (nhiều điều kiện)

```python
# Bài toán: Lookup đơn giá từ bảng giá theo (Mã SP + Kho hàng)
# Excel cần làm thủ công hoặc XLOOKUP phức tạp
# Python đơn giản:

bang_gia = pd.read_excel("bang_gia.xlsx")
don_hang = pd.read_excel("don_hang.xlsx")

result = don_hang.merge(
    bang_gia[["ma_sp", "kho", "don_gia", "dvt"]],
    on=["ma_sp", "kho"],   # Multi-key
    how="left"
)

# Tính thành tiền
result["thanh_tien"] = result["so_luong"] * result["don_gia"]
result.to_excel("don_hang_co_gia.xlsx", index=False)
```

### XLOOKUP (lấy nhiều cột cùng lúc)

```python
# Thay vì nhiều VLOOKUP, 1 merge lấy hết
result = don_hang.merge(
    danh_muc,          # Không filter columns → lấy tất cả
    on="ma_kh",
    how="left",
    suffixes=("", "_dm")  # Tránh conflict nếu có cột trùng tên
)
```

### Lookup có fallback (nếu không match)

```python
# Nếu không match, dùng giá trị mặc định thay vì NaN
result = don_hang.merge(danh_muc, on="ma_kh", how="left")
result["ten_kh"] = result["ten_kh"].fillna("CHƯA CÓ TRONG DANH MỤC")
result["don_gia"] = result["don_gia"].fillna(0)
```

### Lookup ngược (VLOOKUP từ phải sang trái)

```python
# Excel VLOOKUP chỉ tìm từ trái sang phải
# Python không giới hạn này:

result = don_hang.merge(
    danh_muc[["ten_kh", "ma_kh"]],  # ten_kh ở trước ma_kh cũng được
    on="ma_kh",
    how="left"
)
```

---

## 2. Filter — Lọc dữ liệu theo điều kiện

### Filter cơ bản

```python
import pandas as pd
df = pd.read_excel("du_lieu.xlsx")

# Lọc 1 điều kiện
hcm = df[df["khu_vuc"] == "HCM"]

# Lọc nhiều điều kiện (AND)
hcm_thang3 = df[
    (df["khu_vuc"] == "HCM") &
    (df["thang"] == "2026-03")
]

# Lọc nhiều điều kiện (OR)
mien_nam = df[
    (df["khu_vuc"] == "HCM") |
    (df["khu_vuc"] == "Cần Thơ") |
    (df["khu_vuc"] == "Vũng Tàu")
]
# Cách ngắn gọn hơn:
mien_nam = df[df["khu_vuc"].isin(["HCM", "Cần Thơ", "Vũng Tàu"])]

# Lọc khoảng giá trị
don_lon = df[(df["gia_tri"] >= 10_000_000) & (df["gia_tri"] <= 100_000_000)]

# Lọc theo ngày
df["ngay_dat"] = pd.to_datetime(df["ngay_dat"])
thang_3 = df[df["ngay_dat"].between("2026-03-01", "2026-03-31")]
```

### Filter theo text (CONTAINS, STARTSWITH)

```python
# Tìm KH có tên chứa "Công ty"
cong_ty = df[df["ten_kh"].str.contains("Công ty", case=False, na=False)]

# Tìm mã SP bắt đầu bằng "SP-A"
sp_a = df[df["ma_sp"].str.startswith("SP-A", na=False)]

# Tìm theo pattern regex
import re
vat_tu = df[df["ten_sp"].str.match(r"^VT-\d{4}$", na=False)]
```

### Dùng .query() — gần giống SQL WHERE

```python
# Cú pháp gọn, dễ đọc
result = df.query("khu_vuc == 'HCM' and gia_tri > 5_000_000 and trang_thai == 'Hoàn thành'")

# Dùng biến
khu_vuc_can_loc = "HN"
result = df.query("khu_vuc == @khu_vuc_can_loc")
```

---

## 3. Pivot Table — Báo cáo tổng hợp

### Pivot cơ bản (như Excel)

```python
import pandas as pd

df = pd.read_excel("don_hang.xlsx")
df["ngay_dat"] = pd.to_datetime(df["ngay_dat"])
df["thang"] = df["ngay_dat"].dt.strftime("%Y-%m")

# Pivot: Doanh thu theo Khu vực × Tháng
pivot = pd.pivot_table(
    df,
    values="doanh_thu",         # Giá trị cần tổng hợp
    index="khu_vuc",            # Dòng
    columns="thang",            # Cột
    aggfunc="sum",              # sum / count / mean / max / min
    fill_value=0,               # Thay NaN bằng 0
    margins=True,               # Thêm dòng/cột "Tổng"
    margins_name="TỔNG"
).round(0)

print(pivot)
pivot.to_excel("pivot_doanh_thu.xlsx")
```

### Pivot nhiều aggregation

```python
# Vừa sum doanh thu, vừa count số đơn
pivot = pd.pivot_table(
    df,
    values=["doanh_thu", "ma_don_hang"],
    index="khu_vuc",
    columns="thang",
    aggfunc={"doanh_thu": "sum", "ma_don_hang": "count"}
)
```

### GroupBy — Tổng hợp linh hoạt hơn pivot

```python
# Tổng hợp theo khu vực
summary = df.groupby("khu_vuc").agg(
    so_don      = ("ma_don_hang", "count"),
    tong_dt     = ("doanh_thu", "sum"),
    tb_don_hang = ("doanh_thu", "mean"),
    don_lon_nhat= ("doanh_thu", "max"),
).reset_index()

summary["ti_le_phan_tram"] = (summary["tong_dt"] / summary["tong_dt"].sum() * 100).round(1)
summary = summary.sort_values("tong_dt", ascending=False)
```

### Top N

```python
# Top 10 sản phẩm bán chạy
top10 = (
    df.groupby("ten_sp")["so_luong"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

# Top 5 KH theo doanh thu
top_kh = df.groupby("ten_kh")["doanh_thu"].sum().nlargest(5).reset_index()
```

---

## 4. Xuất riêng từng sheet cho từng nhóm

Bài toán phổ biến: Từ 1 file tổng, xuất ra từng sheet (hoặc file) riêng cho từng khu vực/nhân viên.

```python
import pandas as pd
from pathlib import Path

df = pd.read_excel("don_hang_tong.xlsx")
OUTPUT_DIR = Path("data/outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Option A: Nhiều sheet trong 1 file
with pd.ExcelWriter(OUTPUT_DIR / "bao_cao_theo_kvuc.xlsx", engine='openpyxl') as writer:
    for khu_vuc, group in df.groupby("khu_vuc"):
        sheet_name = str(khu_vuc)[:31]  # Excel giới hạn 31 ký tự
        group.to_excel(writer, sheet_name=sheet_name, index=False)
    # Sheet tổng hợp
    df.to_excel(writer, sheet_name="TẤT CẢ", index=False)

print("Done: bao_cao_theo_kvuc.xlsx")

# Option B: Mỗi khu vực 1 file riêng
for khu_vuc, group in df.groupby("khu_vuc"):
    filename = f"don_hang_{khu_vuc}_{DATE_STR}.xlsx"
    group.to_excel(OUTPUT_DIR / filename, index=False)
    print(f"  ✓ {filename}: {len(group):,} dòng")
```

---

## 5. Truy xuất dữ liệu nâng cao

### Tìm dòng trùng lặp

```python
# Tìm tất cả duplicate theo ma_don_hang
dupes = df[df.duplicated(subset=["ma_don_hang"], keep=False)]
print(f"Có {len(dupes)} dòng duplicate")
dupes.sort_values("ma_don_hang").to_excel("duplicate_orders.xlsx", index=False)
```

### So sánh 2 cột (trong cùng file)

```python
# Ví dụ: So sánh số lượng kế hoạch vs thực tế
df["chenh_lech"] = df["thuc_te"] - df["ke_hoach"]
df["ty_le_dat"] = (df["thuc_te"] / df["ke_hoach"] * 100).round(1)

# Flag dòng không đạt KPI
df["trang_thai_kpi"] = df["ty_le_dat"].apply(
    lambda x: "Đạt" if x >= 100 else ("Gần đạt" if x >= 80 else "Không đạt")
)
```

### Conditional lookup (IF + VLOOKUP)

```python
# Tương đương: =IF(A2="VIP", VLOOKUP(B2, bang_gia_vip, 3, 0), VLOOKUP(B2, bang_gia_thuong, 3, 0))
import numpy as np

bang_gia_vip     = pd.read_excel("bang_gia_vip.xlsx").set_index("ma_sp")["don_gia"]
bang_gia_thuong  = pd.read_excel("bang_gia_thuong.xlsx").set_index("ma_sp")["don_gia"]

df["don_gia"] = np.where(
    df["loai_kh"] == "VIP",
    df["ma_sp"].map(bang_gia_vip),
    df["ma_sp"].map(bang_gia_thuong)
)
```

### Running total & cộng dồn

```python
# Cộng dồn doanh thu theo ngày
df = df.sort_values("ngay_dat")
df["dt_cong_don"] = df.groupby("khu_vuc")["doanh_thu"].cumsum()

# So sánh với cùng kỳ năm ngoái
df["ngay_dat"] = pd.to_datetime(df["ngay_dat"])
df["nam"] = df["ngay_dat"].dt.year
df["thang"] = df["ngay_dat"].dt.month

this_year = df[df["nam"] == 2026].groupby("thang")["doanh_thu"].sum()
last_year = df[df["nam"] == 2025].groupby("thang")["doanh_thu"].sum()
yoy = pd.DataFrame({"2025": last_year, "2026": this_year})
yoy["tang_truong"] = ((yoy[2026] / yoy[2025] - 1) * 100).round(1)
```

---

## 6. Quick Reference — Excel → Python

| Thao tác Excel | Python/Pandas |
|---------------|---------------|
| VLOOKUP | `df.merge(lookup, on="key", how="left")` |
| XLOOKUP | `df.merge(lookup, on="key", how="left")` |
| IF + VLOOKUP | `np.where(condition, map1, map2)` |
| COUNTIF | `df.groupby("col")["col"].count()` |
| SUMIF | `df.groupby("col")["val"].sum()` |
| AVERAGEIF | `df.groupby("col")["val"].mean()` |
| Pivot Table | `pd.pivot_table(df, values, index, columns, aggfunc)` |
| Filter | `df[df["col"] == "value"]` |
| Remove Duplicate | `df.drop_duplicates(subset=["key"])` |
| Sort | `df.sort_values("col", ascending=False)` |
| Text Contains | `df["col"].str.contains("text", case=False)` |
| Date Filter | `df["date"].between("2026-01-01", "2026-03-31")` |
| Running Total | `df["col"].cumsum()` |
| % of Total | `df["val"] / df["val"].sum() * 100` |

---

## 7. Full Script — Lookup + Filter + Pivot + Export

```python
#!/usr/bin/env python3
"""
Báo cáo tổng hợp: VLOOKUP + Filter + Pivot → Excel nhiều sheet
"""
import pandas as pd
from pathlib import Path
from datetime import datetime

# ─── CONFIG ──────────────────────────────────────────────────────────────────
FILE_DON_HANG  = "data/inputs/don_hang.xlsx"
FILE_DANH_MUC  = "data/inputs/danh_muc_kh.xlsx"
FILE_BANG_GIA  = "data/inputs/bang_gia.xlsx"
OUTPUT_DIR     = Path("data/outputs")
DATE_STR       = datetime.now().strftime("%Y%m%d")
LOC_THANG      = "2026-03"   # Filter tháng, để "" để lấy tất cả
# ─────────────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load
    print("Đang load dữ liệu...")
    df        = pd.read_excel(FILE_DON_HANG)
    danh_muc  = pd.read_excel(FILE_DANH_MUC)
    bang_gia  = pd.read_excel(FILE_BANG_GIA)

    # 2. Normalize
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    df["ngay_dat"] = pd.to_datetime(df["ngay_dat"], errors='coerce')
    df["thang"] = df["ngay_dat"].dt.strftime("%Y-%m")

    # 3. VLOOKUP: gán tên KH + địa chỉ
    df = df.merge(
        danh_muc[["ma_kh", "ten_kh", "khu_vuc", "loai_kh"]],
        on="ma_kh", how="left"
    )

    # 4. VLOOKUP: gán đơn giá
    df = df.merge(
        bang_gia[["ma_sp", "don_gia"]],
        on="ma_sp", how="left"
    )
    df["thanh_tien"] = df["so_luong"] * df["don_gia"].fillna(0)

    # 5. Filter
    df_loc = df[df["thang"] == LOC_THANG] if LOC_THANG else df
    print(f"Dữ liệu sau lọc: {len(df_loc):,} dòng")

    # 6. Pivot
    pivot_kv = pd.pivot_table(
        df_loc, values="thanh_tien", index="khu_vuc",
        columns="thang", aggfunc="sum", fill_value=0, margins=True, margins_name="TỔNG"
    ).round(0)

    top10_sp = (
        df_loc.groupby("ten_sp")["thanh_tien"]
        .sum().nlargest(10).reset_index()
        .rename(columns={"thanh_tien": "doanh_thu"})
    )

    # 7. Missing lookups
    missing_kh = df_loc[df_loc["ten_kh"].isna()][["ma_kh"]].drop_duplicates()
    missing_gia = df_loc[df_loc["don_gia"].isna()][["ma_sp"]].drop_duplicates()

    # 8. Export
    out_file = OUTPUT_DIR / f"bao_cao_{LOC_THANG or 'all'}_{DATE_STR}.xlsx"
    with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
        df_loc.to_excel(writer, sheet_name="Chi tiết", index=False)
        pivot_kv.to_excel(writer, sheet_name="Pivot Khu vực")
        top10_sp.to_excel(writer, sheet_name="Top 10 SP", index=False)
        if not missing_kh.empty:
            missing_kh.to_excel(writer, sheet_name="KH thiếu danh mục", index=False)
        if not missing_gia.empty:
            missing_gia.to_excel(writer, sheet_name="SP thiếu giá", index=False)

    print(f"\n[OK] {out_file}")
    print(f"  Chi tiết : {len(df_loc):,} dòng")
    print(f"  Top 10 SP: {top10_sp['ten_sp'].tolist()[:3]}...")
    if not missing_kh.empty:
        print(f"  ⚠ KH thiếu danh mục: {len(missing_kh)} mã")
    if not missing_gia.empty:
        print(f"  ⚠ SP thiếu giá: {len(missing_gia)} mã")

if __name__ == "__main__":
    main()
```
