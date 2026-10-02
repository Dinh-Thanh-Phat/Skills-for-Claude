---
name: file-aggregation-comparison
description: |
  Skill chuyên hỗ trợ nhân viên tổng hợp, so sánh và truy xuất dữ liệu từ nhiều file Excel/CSV.
  LUÔN dùng skill này khi user:
  - Nói "so sánh", "compare", "diff", "reconcile", "tìm khác biệt", "what changed"
  - Nói "merge", "tổng hợp", "consolidate", "combine", "gộp files", "ghép file"
  - Mention 2+ files cùng lúc và muốn làm gì đó với chúng
  - Cần "VLOOKUP", "tra cứu", "lookup", "tìm giá trị từ file khác"
  - Cần "aggregate data", "summary report", "báo cáo tổng hợp"
  - "tổng hợp đơn hàng", "tổng hợp doanh thu", "gộp báo cáo"
  - "truy xuất dữ liệu", "lọc dữ liệu", "filter", "pivot table"
  - "Match data between files", "find missing records", "đối chiếu"
  - Ngay cả khi user chỉ nói "tôi có 2 files Excel, muốn xem chỗ nào khác nhau"
---

# File Aggregation & Comparison Skill

Bạn là **Data Analyst** hỗ trợ nhân viên văn phòng xử lý dữ liệu Excel/CSV nhanh và chính xác.

## Nhận diện yêu cầu — Chọn đúng mode

| User nói gì | Mode |
|------------|------|
| "gộp file", "merge", "tổng hợp nhiều file" | **AGGREGATION** |
| "so sánh", "tìm khác biệt", "tháng này vs tháng trước" | **COMPARISON** |
| "VLOOKUP", "tra cứu", "lấy giá trị từ file khác" | **LOOKUP** |
| "lọc", "filter", "tìm đơn của khách X", "pivot" | **RETRIEVAL** |
| "match", "đối chiếu", "tên giống nhau nhưng khác chữ" | **MATCHING** |

Một task thường cần **combine 2-3 modes**. Ví dụ: gộp 12 file monthly → tổng hợp → pivot theo region.

## Bước đầu tiên — Thu thập thông tin

Hỏi ngay (hoặc suy luận từ context) trước khi viết code:
1. **File paths** ở đâu? Format gì (.xlsx, .csv)?
2. **Key column** để join/match là cột nào? (Mã đơn, Mã KH, SKU...)
3. **Output** muốn gì? (Excel nhiều sheet, CSV, báo cáo tổng hợp?)
4. **Điều kiện đặc biệt?** Bỏ qua hoa/thường? Trim spaces? Format ngày?

Đừng tự đoán key column — sai key column = kết quả sai toàn bộ.

---

## MODE 1: AGGREGATION — Gộp nhiều files thành 1

**Use cases phổ biến:**
- Merge 12 file báo cáo tháng → file năm
- Gộp dữ liệu từ nhiều chi nhánh/khu vực
- Consolidate timesheet từ nhiều teams
- Tổng hợp đơn hàng từ nhiều nguồn

```python
#!/usr/bin/env python3
"""
File Aggregator — Gộp nhiều Excel/CSV thành 1 file tổng hợp
Cách dùng: Sửa CONFIG bên dưới rồi chạy: python aggregator.py
"""

import pandas as pd
import glob
from pathlib import Path
from datetime import datetime

# ─── CONFIG — SỬA CHỖ NÀY ────────────────────────────────────────────────────
INPUT_PATTERN  = "data/inputs/*.xlsx"   # Hoặc list file: ["file1.xlsx", "file2.xlsx"]
SHEET_NAME     = 0                       # 0 = sheet đầu tiên, hoặc "Sheet1"
KEY_COLUMNS    = ["ma_don_hang"]         # Cột để detect duplicate
GROUP_BY_COLS  = ["khu_vuc", "thang"]   # Cột để group (để [] nếu không group)
SUM_COLS       = ["doanh_thu", "chi_phi"] # Cột để sum (để [] nếu không sum)
OUTPUT_DIR     = Path("data/outputs")
# ─────────────────────────────────────────────────────────────────────────────

DATE_STR = datetime.now().strftime("%Y%m%d")

def load_all(pattern) -> pd.DataFrame:
    files = sorted(glob.glob(pattern)) if isinstance(pattern, str) else pattern
    if not files:
        raise FileNotFoundError(f"Không tìm thấy file nào: {pattern}")

    print(f"Tìm thấy {len(files)} file:")
    dfs, failed = [], []
    for f in files:
        try:
            if str(f).endswith(('.xlsx', '.xls')):      # .xls cần thêm: pip install xlrd
                df = pd.read_excel(f, sheet_name=SHEET_NAME)
            else:
                df = pd.read_csv(f, encoding='utf-8-sig')
        except Exception as e:
            failed.append((f, e))
            print(f"  ✗ {f}: {e}")
            continue
        # Normalize column names TRƯỚC khi concat — nếu không, "Doanh Thu" và "doanh_thu"
        # thành 2 cột khác nhau và dữ liệu bị tách / NaN
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        df['_nguon_file'] = Path(f).name
        dfs.append(df)
        print(f"  ✓ {Path(f).name}: {len(df):,} dòng")

    if not dfs:
        raise RuntimeError(f"Không đọc được file nào ({len(failed)} lỗi)")
    if failed:
        # Không im lặng bỏ qua — báo rõ để user quyết định chạy tiếp hay không
        print(f"⚠️  {len(failed)}/{len(files)} file lỗi, KẾT QUẢ THIẾU dữ liệu từ: {[str(f) for f, _ in failed]}")

    return pd.concat(dfs, ignore_index=True)

def remove_duplicates(df: pd.DataFrame):
    key_cols = [c for c in KEY_COLUMNS if c in df.columns]
    if not key_cols:
        return df, pd.DataFrame()
    dupes = df[df.duplicated(subset=key_cols, keep=False)]
    clean = df.drop_duplicates(subset=key_cols, keep='first')
    print(f"  Duplicate: {len(dupes):,} dòng → giữ lại {len(clean):,} dòng")
    return clean, dupes

def make_summary(df: pd.DataFrame) -> pd.DataFrame:
    group_cols = [c for c in GROUP_BY_COLS if c in df.columns]
    sum_cols   = [c for c in SUM_COLS if c in df.columns]
    if not group_cols:
        return pd.DataFrame()
    agg = {'_nguon_file': 'count'} | {c: 'sum' for c in sum_cols}
    return df.groupby(group_cols).agg(agg).reset_index().rename(columns={'_nguon_file': 'so_dong'})

def export(df_all, df_clean, df_dupes, df_summary):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"tonghop_{DATE_STR}.xlsx"

    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        df_clean.to_excel(writer, sheet_name='Tất cả dữ liệu', index=False)
        if not df_summary.empty:
            df_summary.to_excel(writer, sheet_name='Tổng hợp', index=False)
        if not df_dupes.empty:
            df_dupes.to_excel(writer, sheet_name='Duplicate', index=False)

    print(f"\n[OK] Xuất file: {out}")
    print(f"  Tất cả dữ liệu : {len(df_clean):,} dòng")
    print(f"  Tổng hợp        : {len(df_summary):,} nhóm")
    print(f"  Duplicate       : {len(df_dupes):,} dòng")

def main():
    print("=== TỔNG HỢP FILE ===\n")
    df_all            = load_all(INPUT_PATTERN)
    df_clean, df_dupes = remove_duplicates(df_all)
    df_summary         = make_summary(df_clean)
    export(df_all, df_clean, df_dupes, df_summary)

if __name__ == "__main__":
    main()
```

---

## MODE 2: COMPARISON — So sánh 2 files, tìm khác biệt

**Use cases phổ biến:**
- So sánh báo cáo tháng này vs tháng trước
- Tìm đơn hàng mới/bị xóa/thay đổi giá
- Reconcile dữ liệu giữa 2 hệ thống
- So sánh bảng giá nhà cung cấp

Xem full code với color highlighting: `references/comparison-guide.md`

**Output standard — 4 sheets:**

| Sheet | Màu | Nội dung |
|-------|-----|---------|
| `Summary` | — | Thống kê: bao nhiêu dòng thêm/xóa/thay đổi |
| `Added` | Xanh lá | Dòng có trong file MỚI, không có trong file CŨ |
| `Deleted` | Đỏ | Dòng có trong file CŨ, không có trong file MỚI |
| `Modified` | Vàng | Dòng thay đổi: hiển thị giá trị CŨ → MỚI |

**Snippet chạy nhanh với pandas.compare():**
```python
import pandas as pd

old = pd.read_excel("bao_cao_thang_truoc.xlsx")
new = pd.read_excel("bao_cao_thang_nay.xlsx")

# Align theo key column
old = old.set_index("ma_don_hang").sort_index()
new = new.set_index("ma_don_hang").sort_index()

# So sánh chỉ phần chung
common_idx = old.index.intersection(new.index)
diff = old.loc[common_idx].compare(new.loc[common_idx], result_names=("Cũ", "Mới"))

added   = new[~new.index.isin(old.index)]    # Dòng mới
deleted = old[~old.index.isin(new.index)]    # Dòng bị xóa

print(f"Thêm mới: {len(added)}, Xóa: {len(deleted)}, Thay đổi: {len(diff)}")
```

---

## MODE 3: LOOKUP — Thay thế VLOOKUP

**Use cases phổ biến:**
- Lấy tên KH, địa chỉ từ file danh mục vào file đơn hàng
- Gán giá sản phẩm từ bảng giá vào file đơn
- Lookup mã vùng, mã nhân viên

Xem full code + examples: `references/lookup-retrieval-guide.md`

**VLOOKUP → pandas.merge() (1-to-1):**
```python
import pandas as pd

don_hang  = pd.read_excel("don_hang.xlsx")        # File chính
danh_muc  = pd.read_excel("danh_muc_kh.xlsx")     # Bảng tra cứu

# Tương đương: =VLOOKUP(A2, danh_muc!A:C, 2, 0)
result = don_hang.merge(
    danh_muc[["ma_kh", "ten_kh", "dia_chi"]],  # Chỉ lấy cột cần
    on="ma_kh",
    how="left"    # left = giữ tất cả dòng trong don_hang, dù không match
)
# Xem dòng không lookup được
missing = result[result["ten_kh"].isna()]
print(f"Không tìm thấy KH: {len(missing)} dòng")
```

**Multi-condition VLOOKUP (nhiều điều kiện):**
```python
# Tương đương VLOOKUP theo (ma_sp + kho_hang)
result = don_hang.merge(
    bang_gia[["ma_sp", "kho_hang", "don_gia"]],
    on=["ma_sp", "kho_hang"],
    how="left"
)
```

---

## MODE 4: RETRIEVAL — Lọc & Truy xuất dữ liệu

**Use cases phổ biến:**
- Lọc tất cả đơn hàng của khách X trong tháng Y
- Tạo pivot table: doanh thu theo khu vực × tháng
- Tìm top 10 sản phẩm bán chạy
- Xuất riêng từng sheet cho từng nhân viên/khu vực

Xem full code + examples: `references/lookup-retrieval-guide.md`

**Filter nhanh:**
```python
import pandas as pd
df = pd.read_excel("don_hang.xlsx")

# Lọc theo điều kiện
ket_qua = df[
    (df["khu_vuc"] == "HCM") &
    (df["thang"] == "2026-03") &
    (df["trang_thai"] == "Hoàn thành")
]

# Pivot table (như Excel)
pivot = pd.pivot_table(
    df,
    values="doanh_thu",
    index="khu_vuc",
    columns="thang",
    aggfunc="sum",
    margins=True,     # Thêm dòng "Total"
    margins_name="Tổng"
).round(0)

# Xuất Excel
with pd.ExcelWriter("output.xlsx", engine='openpyxl') as writer:
    ket_qua.to_excel(writer, sheet_name="Lọc HCM T3", index=False)
    pivot.to_excel(writer, sheet_name="Pivot Doanh Thu")
```

---

## MODE 5: MATCHING — Đối chiếu, Fuzzy Match

Dùng khi tên/địa chỉ có typo hoặc format khác nhau giữa 2 hệ thống.

Xem full code: `references/data-matching-guide.md`

---

## Chọn thư viện đúng

| Thư viện | Dùng cho | Tốc độ ghi |
|---------|---------|-----------|
| `openpyxl` | Đọc + sửa file Excel có sẵn | Chậm hơn |
| `xlsxwriter` | Tạo file Excel mới với format đẹp | **3x nhanh hơn** |
| `pandas` | Mọi data manipulation | — |
| `polars` | File > 200MB (nhanh 5-10x pandas) | — |
| `duckdb` | File > 1GB, SQL-style query | — |
| `rapidfuzz` | Fuzzy string matching | — |

**Quan trọng:** `openpyxl` phù hợp cho đọc/sửa file có sẵn. Khi tạo file output lớn (>100K dòng), dùng `xlsxwriter` — nhanh gấp 3x và tốn ít RAM hơn.

```bash
# Cài tất cả
pip install pandas openpyxl xlsxwriter rapidfuzz tqdm
# Large files:
pip install polars duckdb
```

---

## Performance nhanh

| File size | Approach |
|-----------|----------|
| < 50MB | pandas bình thường |
| 50–200MB | pandas + `usecols` để chỉ đọc cột cần |
| 200MB–1GB | polars |
| > 1GB | duckdb (SQL query không cần load RAM) |

Xem chi tiết: `references/performance-tips.md`

---

## References

| File | Nội dung |
|------|---------|
| `references/comparison-guide.md` | Full code so sánh 2 files + color highlight Excel |
| `references/lookup-retrieval-guide.md` | VLOOKUP, filter, pivot, truy xuất dữ liệu |
| `references/data-matching-guide.md` | Fuzzy matching, cross-reference, dedup across files |
| `references/troubleshooting.md` | 8 lỗi phổ biến + cách fix |
| `references/performance-tips.md` | Large files >100MB, polars, DuckDB |
