# Comparison Guide — So sánh 2+ Files

## Khi nào đọc file này

Khi user cần:
- So sánh 2 Excel/CSV files, tìm added/deleted/modified rows
- Highlight differences giữa version cũ và mới
- Tạo reconciliation report
- Detect schema changes (columns added/removed)

---

## Full Comparison Script

```python
#!/usr/bin/env python3
"""
File Comparator — So sánh 2 files, tạo diff report với color highlighting
Output: data/outputs/comparison_<YYYYMMDD>.xlsx
"""

import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from pathlib import Path
from datetime import datetime
import sys

# ─── CONFIG ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("data/outputs")
DATE_STR = datetime.now().strftime("%Y%m%d")
OUTPUT_FILE = OUTPUT_DIR / f"comparison_{DATE_STR}.xlsx"

# THAY ĐỔI THEO TASK
OLD_FILE = "data/inputs/report_old.xlsx"
NEW_FILE = "data/inputs/report_new.xlsx"
KEY_COLUMNS = ["order_id"]          # Columns để identify rows
IGNORE_COLUMNS = ["last_updated"]   # Columns bỏ qua khi compare
COMPARE_CONFIG = {
    "ignore_case": True,            # Bỏ qua hoa/thường
    "trim_spaces": True,            # Bỏ qua leading/trailing spaces
    "numeric_tolerance": 0.01,      # Chấp nhận diff 0.01 cho số
    "date_format": "%Y-%m-%d",      # Format ngày tháng
}

# ─── COLORS ──────────────────────────────────────────────────────────────────
COLOR = {
    "added":     "C6EFCE",  # Green — row mới
    "deleted":   "FFC7CE",  # Red — row bị xóa
    "modified":  "FFEB9C",  # Yellow — row thay đổi
    "unchanged": "FFFFFF",  # White
    "header":    "1F4E79",  # Dark blue
    "old_val":   "FF6B6B",  # Red text cho old value
    "new_val":   "51CF66",  # Green text cho new value
}

# ─── LOAD ────────────────────────────────────────────────────────────────────
def load(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File không tìm thấy: {path}")

    if p.suffix in ('.xlsx', '.xls'):
        df = pd.read_excel(path)
    elif p.suffix == '.csv':
        try:
            df = pd.read_csv(path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding='latin-1')
    elif p.suffix == '.json':
        df = pd.read_json(path)
    else:
        raise ValueError(f"Unsupported format: {p.suffix}")

    print(f"  Loaded {path}: {len(df):,} rows × {len(df.columns)} cols")
    return df

# ─── NORMALIZE ───────────────────────────────────────────────────────────────
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data theo COMPARE_CONFIG trước khi compare"""
    df = df.copy()

    for col in df.select_dtypes(include='object').columns:
        if COMPARE_CONFIG["trim_spaces"]:
            df[col] = df[col].str.strip()
        if COMPARE_CONFIG["ignore_case"]:
            df[col] = df[col].str.lower()

    return df

# ─── CHECK SCHEMA ─────────────────────────────────────────────────────────────
def check_schema(old_df: pd.DataFrame, new_df: pd.DataFrame) -> dict:
    old_cols = set(old_df.columns)
    new_cols = set(new_df.columns)
    return {
        "added_columns":   sorted(new_cols - old_cols),
        "removed_columns": sorted(old_cols - new_cols),
        "common_columns":  sorted(old_cols & new_cols),
    }

# ─── COMPARE ─────────────────────────────────────────────────────────────────
def compare(old_df: pd.DataFrame, new_df: pd.DataFrame) -> dict:
    # Validate key columns
    for key in KEY_COLUMNS:
        if key not in old_df.columns:
            raise ValueError(f"Key column '{key}' không có trong OLD file. Columns: {list(old_df.columns)}")
        if key not in new_df.columns:
            raise ValueError(f"Key column '{key}' không có trong NEW file. Columns: {list(new_df.columns)}")

    schema = check_schema(old_df, new_df)
    compare_cols = [c for c in schema["common_columns"] if c not in KEY_COLUMNS + IGNORE_COLUMNS]

    # Set index để join
    old_idx = normalize(old_df).set_index(KEY_COLUMNS)
    new_idx = normalize(new_df).set_index(KEY_COLUMNS)

    old_keys = set(old_idx.index)
    new_keys = set(new_idx.index)

    added_keys   = new_keys - old_keys
    deleted_keys = old_keys - new_keys
    common_keys  = old_keys & new_keys

    # Find modified rows
    modified_rows = []
    unchanged_rows = []

    for key in common_keys:
        old_row = old_idx.loc[key] if key in old_idx.index else None
        new_row = new_idx.loc[key] if key in new_idx.index else None

        if old_row is None or new_row is None:
            continue

        changes = {}
        for col in compare_cols:
            if col not in old_idx.columns or col not in new_idx.columns:
                continue

            old_val = old_row[col] if col in old_row.index else None
            new_val = new_row[col] if col in new_row.index else None

            # Numeric tolerance
            try:
                if abs(float(old_val) - float(new_val)) <= COMPARE_CONFIG["numeric_tolerance"]:
                    continue
            except (TypeError, ValueError):
                pass

            if str(old_val) != str(new_val):
                changes[col] = {"old": old_val, "new": new_val}

        if changes:
            key_dict = {k: v for k, v in zip(KEY_COLUMNS, (key if isinstance(key, tuple) else [key]))}
            modified_rows.append({"_key": key, "_changes": changes, **key_dict})
        else:
            key_dict = {k: v for k, v in zip(KEY_COLUMNS, (key if isinstance(key, tuple) else [key]))}
            unchanged_rows.append(key_dict)

    # Build result DataFrames
    added_df   = new_df[new_df.set_index(KEY_COLUMNS).index.isin(added_keys)].reset_index(drop=True)
    deleted_df = old_df[old_df.set_index(KEY_COLUMNS).index.isin(deleted_keys)].reset_index(drop=True)

    return {
        "added":       added_df,
        "deleted":     deleted_df,
        "modified":    modified_rows,
        "unchanged":   unchanged_rows,
        "schema":      schema,
        "compare_cols": compare_cols,
    }

# ─── EXPORT ──────────────────────────────────────────────────────────────────
def make_fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)

def make_header_style():
    return Font(name="Calibri", size=11, bold=True, color="FFFFFF")

def write_df_to_sheet(ws, df: pd.DataFrame, row_color: str = "FFFFFF"):
    """Write DataFrame vào worksheet với color"""
    headers = list(df.columns)
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(1, col_idx, header)
        cell.fill = make_fill(COLOR["header"])
        cell.font = make_header_style()
        cell.alignment = Alignment(horizontal="center")

    for row_idx, row in enumerate(df.itertuples(index=False), 2):
        for col_idx, val in enumerate(row, 1):
            cell = ws.cell(row_idx, col_idx, val)
            cell.fill = make_fill(row_color)

    # Auto-fit columns
    for col_idx, col_name in enumerate(headers, 1):
        max_len = max(len(str(col_name)), 10)
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 40)

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}1"

def write_modified_sheet(ws, modified_rows: list, old_df: pd.DataFrame, new_df: pd.DataFrame):
    """Modified sheet: hiển thị OLD value → NEW value side-by-side"""
    if not modified_rows:
        ws.cell(1, 1, "No modifications found")
        return

    # Headers: Key columns + "Column | Old Value | New Value"
    ws.cell(1, 1, "Key").fill = make_fill(COLOR["header"])
    ws.cell(1, 1).font = make_header_style()
    ws.cell(1, 2, "Changed Column").fill = make_fill(COLOR["header"])
    ws.cell(1, 2).font = make_header_style()
    ws.cell(1, 3, "Old Value").fill = make_fill(COLOR["header"])
    ws.cell(1, 3).font = make_header_style()
    ws.cell(1, 4, "New Value").fill = make_fill(COLOR["header"])
    ws.cell(1, 4).font = make_header_style()

    row_idx = 2
    for mod in modified_rows:
        key = str(mod["_key"])
        for col_name, vals in mod["_changes"].items():
            ws.cell(row_idx, 1, key)
            ws.cell(row_idx, 2, col_name).fill = make_fill(COLOR["modified"])
            old_cell = ws.cell(row_idx, 3, str(vals["old"]))
            old_cell.fill = make_fill("FFE0E0")
            old_cell.font = Font(color=COLOR["old_val"])
            new_cell = ws.cell(row_idx, 4, str(vals["new"]))
            new_cell.fill = make_fill("E0FFE0")
            new_cell.font = Font(color=COLOR["new_val"])
            row_idx += 1

    for col_idx in range(1, 5):
        ws.column_dimensions[get_column_letter(col_idx)].width = 30
    ws.freeze_panes = "A2"

def export(result: dict, old_df: pd.DataFrame, new_df: pd.DataFrame):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()

    # Summary sheet
    ws_summary = wb.active
    ws_summary.title = "Summary"
    summary_data = [
        ("OLD File", OLD_FILE),
        ("NEW File", NEW_FILE),
        ("Comparison Date", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("", ""),
        ("OLD total rows", len(old_df)),
        ("NEW total rows", len(new_df)),
        ("", ""),
        ("Added rows", len(result["added"])),
        ("Deleted rows", len(result["deleted"])),
        ("Modified rows", len(result["modified"])),
        ("Unchanged rows", len(result["unchanged"])),
        ("", ""),
        ("Added columns", ", ".join(result["schema"]["added_columns"]) or "None"),
        ("Removed columns", ", ".join(result["schema"]["removed_columns"]) or "None"),
    ]
    row_colors = {
        "Added rows": COLOR["added"],
        "Deleted rows": COLOR["deleted"],
        "Modified rows": COLOR["modified"],
    }
    for row_idx, (label, value) in enumerate(summary_data, 1):
        ws_summary.cell(row_idx, 1, label).font = Font(bold=True)
        cell = ws_summary.cell(row_idx, 2, value)
        if label in row_colors:
            ws_summary.cell(row_idx, 1).fill = make_fill(row_colors[label])
            cell.fill = make_fill(row_colors[label])
    ws_summary.column_dimensions["A"].width = 20
    ws_summary.column_dimensions["B"].width = 40

    # Added sheet
    ws_added = wb.create_sheet("Added")
    write_df_to_sheet(ws_added, result["added"] if not result["added"].empty else pd.DataFrame(["No added rows"]), COLOR["added"])

    # Deleted sheet
    ws_deleted = wb.create_sheet("Deleted")
    write_df_to_sheet(ws_deleted, result["deleted"] if not result["deleted"].empty else pd.DataFrame(["No deleted rows"]), COLOR["deleted"])

    # Modified sheet
    ws_modified = wb.create_sheet("Modified")
    write_modified_sheet(ws_modified, result["modified"], old_df, new_df)

    # Schema Changes sheet (nếu có)
    if result["schema"]["added_columns"] or result["schema"]["removed_columns"]:
        ws_schema = wb.create_sheet("Schema Changes")
        ws_schema.cell(1, 1, "Added Columns").font = Font(bold=True)
        ws_schema.cell(1, 2, "Removed Columns").font = Font(bold=True)
        for i, col in enumerate(result["schema"]["added_columns"], 2):
            ws_schema.cell(i, 1, col).fill = make_fill(COLOR["added"])
        for i, col in enumerate(result["schema"]["removed_columns"], 2):
            ws_schema.cell(i, 2, col).fill = make_fill(COLOR["deleted"])

    wb.save(OUTPUT_FILE)
    print(f"\n[OK] Output: {OUTPUT_FILE}")

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    print("=== FILE COMPARATOR ===")
    print(f"  OLD: {OLD_FILE}")
    print(f"  NEW: {NEW_FILE}")
    print(f"  Key columns: {KEY_COLUMNS}\n")

    old_df = load(OLD_FILE)
    new_df = load(NEW_FILE)

    result = compare(old_df, new_df)

    print(f"\n=== RESULTS ===")
    print(f"  Added:     {len(result['added']):,} rows (green)")
    print(f"  Deleted:   {len(result['deleted']):,} rows (red)")
    print(f"  Modified:  {len(result['modified']):,} rows (yellow)")
    print(f"  Unchanged: {len(result['unchanged']):,} rows")
    if result["schema"]["added_columns"]:
        print(f"  New cols:  {result['schema']['added_columns']}")
    if result["schema"]["removed_columns"]:
        print(f"  Del cols:  {result['schema']['removed_columns']}")

    export(result, old_df, new_df)

if __name__ == "__main__":
    main()
```

---

## Version Comparison (3+ files)

Khi user muốn compare v1 → v2 → v3, chạy pairwise:
```python
versions = ["file_v1.xlsx", "file_v2.xlsx", "file_v3.xlsx"]
for i in range(len(versions) - 1):
    OLD_FILE = versions[i]
    NEW_FILE = versions[i+1]
    OUTPUT_FILE = OUTPUT_DIR / f"diff_{i+1}_to_{i+2}_{DATE_STR}.xlsx"
    # ... run compare()
```

---

## Side-by-Side HTML Report

Khi user muốn HTML output thay vì Excel:
```python
def to_html_report(result: dict) -> str:
    html = """
    <html><head>
    <style>
      .added { background: #C6EFCE; }
      .deleted { background: #FFC7CE; }
      .modified { background: #FFEB9C; }
      table { border-collapse: collapse; width: 100%; }
      th { background: #1F4E79; color: white; padding: 8px; }
      td { border: 1px solid #ddd; padding: 6px; }
    </style></head><body>
    """
    html += f"<h2>Comparison Report — {datetime.now().strftime('%Y-%m-%d')}</h2>"
    html += f"<p>Added: {len(result['added'])} | Deleted: {len(result['deleted'])} | Modified: {len(result['modified'])}</p>"

    # Added table
    if not result['added'].empty:
        html += "<h3 style='color:green'>Added Rows</h3>"
        html += result['added'].to_html(classes='added', index=False)

    # Deleted table
    if not result['deleted'].empty:
        html += "<h3 style='color:red'>Deleted Rows</h3>"
        html += result['deleted'].to_html(classes='deleted', index=False)

    html += "</body></html>"
    return html
```
