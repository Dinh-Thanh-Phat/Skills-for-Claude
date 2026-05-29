# Data Matching Guide — Fuzzy Matching & Cross-Reference

## Khi nào đọc file này

Khi user cần:
- Match tên khách hàng, địa chỉ có typos
- Cross-reference records giữa 2 hệ thống khác nhau
- Tìm missing records giữa 2 files
- Deduplicate records across multiple files
- Master data reconciliation

---

## Exact Match vs Fuzzy Match

| Loại dữ liệu | Match strategy |
|-------------|---------------|
| ID, Code, SKU | `pandas.merge()` — exact |
| Số điện thoại, email | `pandas.merge()` sau khi normalize |
| Tên người, tổ chức | `rapidfuzz` — fuzzy |
| Địa chỉ | `rapidfuzz` + normalize |
| Số tiền, ngày tháng | `pandas.merge()` với tolerance |

---

## Cross-Reference Script (Exact Match)

```python
#!/usr/bin/env python3
"""
Cross-Reference — Tìm records có/không có trong mỗi file
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import openpyxl
from openpyxl.styles import PatternFill, Font

OUTPUT_DIR = Path("data/outputs")
DATE_STR = datetime.now().strftime("%Y%m%d")

# CONFIG
FILE_A = "data/inputs/system_a.xlsx"   # ví dụ: warehouse
FILE_B = "data/inputs/system_b.xlsx"   # ví dụ: accounting
KEY_A = "product_code"                  # key column trong file A
KEY_B = "sku"                           # key column trong file B (có thể khác tên)

def load(path: str, key_col: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix in ('.xlsx', '.xls'):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path, encoding='utf-8-sig')

    # Normalize key
    df[key_col] = df[key_col].astype(str).str.strip().str.upper()
    print(f"  {path}: {len(df):,} records")
    return df

def cross_reference(df_a: pd.DataFrame, df_b: pd.DataFrame) -> dict:
    keys_a = set(df_a[KEY_A])
    keys_b = set(df_b[KEY_B])

    in_both = keys_a & keys_b
    only_in_a = keys_a - keys_b  # missing từ B
    only_in_b = keys_b - keys_a  # missing từ A

    matched_a = df_a[df_a[KEY_A].isin(in_both)]
    matched_b = df_b[df_b[KEY_B].isin(in_both)]

    # Merge matched records để compare values
    merged = matched_a.merge(
        matched_b,
        left_on=KEY_A,
        right_on=KEY_B,
        suffixes=("_A", "_B")
    )

    return {
        "only_in_a": df_a[df_a[KEY_A].isin(only_in_a)],
        "only_in_b": df_b[df_b[KEY_B].isin(only_in_b)],
        "matched":   merged,
        "stats": {
            "total_a":   len(keys_a),
            "total_b":   len(keys_b),
            "matched":   len(in_both),
            "only_in_a": len(only_in_a),
            "only_in_b": len(only_in_b),
        }
    }

def export(result: dict):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"cross_reference_{DATE_STR}.xlsx"

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Summary
        stats = result["stats"]
        summary_df = pd.DataFrame([
            {"Metric": "File A total", "Count": stats["total_a"]},
            {"Metric": "File B total", "Count": stats["total_b"]},
            {"Metric": "Matched (in both)", "Count": stats["matched"]},
            {"Metric": f"Only in A (missing from B)", "Count": stats["only_in_a"]},
            {"Metric": f"Only in B (missing from A)", "Count": stats["only_in_b"]},
            {"Metric": "Match rate A", "Count": f"{stats['matched']/stats['total_a']*100:.1f}%"},
            {"Metric": "Match rate B", "Count": f"{stats['matched']/stats['total_b']*100:.1f}%"},
        ])
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        result["matched"].to_excel(writer, sheet_name="Matched", index=False)
        result["only_in_a"].to_excel(writer, sheet_name="Only_in_A", index=False)
        result["only_in_b"].to_excel(writer, sheet_name="Only_in_B", index=False)

    print(f"[OK] {output_file}")
    print(f"  Matched:    {stats['matched']:,}")
    print(f"  Only in A:  {stats['only_in_a']:,}")
    print(f"  Only in B:  {stats['only_in_b']:,}")

def main():
    print("=== CROSS-REFERENCE ===")
    df_a = load(FILE_A, KEY_A)
    df_b = load(FILE_B, KEY_B)
    result = cross_reference(df_a, df_b)
    export(result)

if __name__ == "__main__":
    main()
```

---

## Fuzzy Matching Script

Dùng khi tên/địa chỉ có typos hoặc format khác nhau:

```python
#!/usr/bin/env python3
"""
Fuzzy Matcher — Match records dựa trên string similarity
Yêu cầu: pip install rapidfuzz
"""

import pandas as pd
from rapidfuzz import fuzz, process
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("data/outputs")
DATE_STR = datetime.now().strftime("%Y%m%d")

# CONFIG
FILE_A = "data/inputs/customers_crm.xlsx"       # nguồn chính
FILE_B = "data/inputs/customers_billing.xlsx"   # cần match
MATCH_COLUMN_A = "customer_name"                # column để fuzzy match trong A
MATCH_COLUMN_B = "company_name"                 # column để fuzzy match trong B
THRESHOLD = 80   # Score 0-100, 80 = 80% similar. Tăng lên nếu muốn stricthơn.
TOP_N = 3        # Trả về N candidates tốt nhất

def normalize_name(s: str) -> str:
    """Chuẩn hóa trước khi match"""
    import re
    s = str(s).lower().strip()
    # Bỏ các suffix phổ biến
    for suffix in ['co.,ltd', 'co., ltd', 'ltd', 'llc', 'inc', 'corp', 'company', 'cty', 'tnhh']:
        s = s.replace(suffix, '')
    # Bỏ ký tự đặc biệt
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def fuzzy_match(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.DataFrame:
    # Normalize
    df_a["_norm"] = df_a[MATCH_COLUMN_A].apply(normalize_name)
    df_b["_norm"] = df_b[MATCH_COLUMN_B].apply(normalize_name)

    choices = df_b["_norm"].tolist()
    results = []

    print(f"Matching {len(df_a):,} records from A against {len(df_b):,} records in B...")

    for idx, row in df_a.iterrows():
        query = row["_norm"]

        # Find top N matches
        matches = process.extract(
            query,
            choices,
            scorer=fuzz.token_sort_ratio,  # tốt cho tên có word order khác
            limit=TOP_N
        )

        for match_str, score, match_idx in matches:
            b_row = df_b.iloc[match_idx]
            results.append({
                "A_idx": idx,
                "A_name": row[MATCH_COLUMN_A],
                "B_name": b_row[MATCH_COLUMN_B],
                "match_score": score,
                "status": "HIGH" if score >= THRESHOLD else "LOW",
                # Copy các columns cần thiết từ A và B
                **{f"A_{col}": row[col] for col in df_a.columns if not col.startswith("_")},
                **{f"B_{col}": b_row[col] for col in df_b.columns if not col.startswith("_")},
            })

        if idx % 100 == 0:
            print(f"  Progress: {idx}/{len(df_a)}")

    return pd.DataFrame(results)

def export(result_df: pd.DataFrame):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"fuzzy_match_{DATE_STR}.xlsx"

    high = result_df[result_df["status"] == "HIGH"]
    low = result_df[result_df["status"] == "LOW"]

    # Unmatched (score quá thấp)
    matched_a_idx = set(high["A_idx"])
    # Cần check logic này tùy data

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        summary = pd.DataFrame([
            {"Metric": "Total in A", "Value": result_df["A_idx"].nunique()},
            {"Metric": "High confidence matches", "Value": high["A_idx"].nunique()},
            {"Metric": "Low confidence (review needed)", "Value": low["A_idx"].nunique()},
            {"Metric": "Threshold", "Value": THRESHOLD},
        ])
        summary.to_excel(writer, sheet_name="Summary", index=False)

        # Sort by score desc
        high_sorted = high.sort_values("match_score", ascending=False)
        high_sorted.to_excel(writer, sheet_name="High_Confidence", index=False)

        low_sorted = low.sort_values("match_score", ascending=False)
        low_sorted.to_excel(writer, sheet_name="Review_Needed", index=False)

    print(f"\n[OK] {output_file}")
    print(f"  High confidence: {high['A_idx'].nunique():,} records")
    print(f"  Need review:     {low['A_idx'].nunique():,} records")

def main():
    print("=== FUZZY MATCHER ===")
    df_a = pd.read_excel(FILE_A)
    df_b = pd.read_excel(FILE_B)
    print(f"A: {len(df_a):,} records | B: {len(df_b):,} records")

    result = fuzzy_match(df_a, df_b)
    export(result)

if __name__ == "__main__":
    main()
```

---

## Chọn Fuzzy Scorer phù hợp

| Scorer | Tốt cho |
|--------|---------|
| `fuzz.ratio` | String ngắn, ít thay đổi |
| `fuzz.partial_ratio` | String ngắn nằm trong string dài |
| `fuzz.token_sort_ratio` | Tên có word order khác ("Nguyen Van A" vs "A Van Nguyen") |
| `fuzz.token_set_ratio` | Tên có extra words ("TNHH ABC Corp" vs "ABC") |

**Recommend mặc định**: `token_sort_ratio` cho tên người/tổ chức.

---

## Deduplicate Across Files

```python
def dedup_across_files(files: list[str], key_col: str, fuzzy: bool = False) -> pd.DataFrame:
    """Tìm records trùng lặp khi merge nhiều files"""
    dfs = [pd.read_excel(f).assign(_source=Path(f).name) for f in files]
    merged = pd.concat(dfs, ignore_index=True)

    if not fuzzy:
        # Exact dedup
        dupes = merged[merged.duplicated(subset=[key_col], keep=False)]
        return dupes.sort_values(key_col)
    else:
        # Fuzzy dedup — expensive for large files
        # Chỉ dùng cho < 10K records
        seen = []
        deduped = []
        for _, row in merged.iterrows():
            name = normalize_name(str(row[key_col]))
            best = process.extractOne(name, seen, scorer=fuzz.token_sort_ratio)
            if best and best[1] >= 85:
                row["_duplicate_of"] = seen[best[2]]
                dupes.append(row)
            else:
                seen.append(name)
                deduped.append(row)
        return pd.DataFrame(deduped), pd.DataFrame(dupes)
```
