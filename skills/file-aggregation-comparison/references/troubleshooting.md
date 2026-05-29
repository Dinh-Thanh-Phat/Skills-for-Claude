# Troubleshooting Guide

## Common Errors & Fixes

### 1. UnicodeDecodeError khi đọc CSV

**Lỗi:** `UnicodeDecodeError: 'utf-8' codec can't decode byte`

**Fix:**
```python
# Thử lần lượt encodings
for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'gbk']:
    try:
        df = pd.read_csv(file, encoding=enc)
        print(f"Success with encoding: {enc}")
        break
    except UnicodeDecodeError:
        continue
```

**Gốc rễ:** File được save từ Excel với BOM (`utf-8-sig`) hoặc từ Windows (`cp1252`).

---

### 2. Key column không match dù giá trị "trông giống nhau"

**Lỗi:** Records không join được dù key columns có cùng value

**Debug:**
```python
# Inspect actual bytes
val_a = df_a[key_col].iloc[0]
val_b = df_b[key_col].iloc[0]
print(repr(val_a))  # Sẽ thấy '\xa0' (non-breaking space) hoặc '000123' vs '123'
print(repr(val_b))
```

**Fix phổ biến:**
```python
# Leading zeros: standardize format
df["id"] = df["id"].astype(str).str.zfill(6)  # "123" → "000123"

# Non-breaking spaces và whitespace variations
df["name"] = df["name"].str.replace('\xa0', ' ').str.strip()

# Số điện thoại: chuẩn hóa format
df["phone"] = df["phone"].str.replace(r'[\s\-\(\)\+]', '', regex=True)

# Leading zeros trong số: giữ nguyên dạng string
df["code"] = df["code"].astype(str)

# Float vs int: "100.0" vs "100"
df["id"] = df["id"].astype(float).astype(int).astype(str)
```

---

### 3. Schema mismatch quá lớn

**Lỗi:** 2 files có quá nhiều columns khác nhau, không biết map thế nào

**Approach:**
```python
def suggest_column_mapping(cols_a: list, cols_b: list) -> dict:
    """Suggest mapping dựa trên string similarity"""
    from rapidfuzz import process, fuzz
    mapping = {}
    for col_a in cols_a:
        best = process.extractOne(col_a.lower(), [c.lower() for c in cols_b], scorer=fuzz.ratio)
        if best and best[1] >= 70:
            mapping[col_a] = cols_b[[c.lower() for c in cols_b].index(best[0])]
    return mapping

mapping = suggest_column_mapping(old_df.columns.tolist(), new_df.columns.tolist())
print("Suggested mapping:", mapping)
# User review mapping trước khi apply
new_df = new_df.rename(columns={v: k for k, v in mapping.items()})
```

---

### 4. MemoryError với file lớn

**Lỗi:** `MemoryError` khi load file > 200MB

**Fix 1: Chunked reading**
```python
# Chỉ works với CSV, không với Excel
chunk_list = []
for chunk in pd.read_csv(large_file, chunksize=10_000):
    # Process mỗi chunk
    processed = chunk[chunk["amount"] > 0]  # ví dụ filter
    chunk_list.append(processed)
df = pd.concat(chunk_list, ignore_index=True)
```

**Fix 2: Chọn chỉ columns cần thiết**
```python
cols_needed = ["order_id", "amount", "date", "region"]
df = pd.read_excel(file, usecols=cols_needed)
```

**Fix 3: Dùng polars (nhanh gấp 5-10x)**
```python
import polars as pl
df = pl.read_excel(file).to_pandas()  # hoặc giữ nguyên polars
```

---

### 5. Date format mismatch

**Lỗi:** `2024-01-15` trong file A, `15/01/2024` trong file B → không join được

**Fix:**
```python
def normalize_date(series: pd.Series) -> pd.Series:
    """Thử nhiều date formats"""
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y%m%d"]
    for fmt in formats:
        try:
            return pd.to_datetime(series, format=fmt, errors='coerce')
        except:
            continue
    return pd.to_datetime(series, infer_datetime_format=True, errors='coerce')

df_a["date"] = normalize_date(df_a["date"])
df_b["date"] = normalize_date(df_b["date"])
```

---

### 6. Merged file có quá nhiều columns (_x, _y suffix)

**Lỗi:** Sau merge, có `amount_x`, `amount_y`, `name_x`, `name_y`...

**Fix:**
```python
# Option 1: Chỉ merge key columns, sau đó add columns cần thiết
merged = df_a[KEY_COLUMNS].merge(df_b[KEY_COLUMNS + ["amount", "status"]], on=KEY_COLUMNS, how="outer")

# Option 2: Sau khi merge, resolve conflicts
def resolve_merge_conflicts(df: pd.DataFrame) -> pd.DataFrame:
    """Khi có _x/_y columns, ưu tiên _x (old) nếu _y null"""
    x_cols = [c for c in df.columns if c.endswith('_x')]
    for col_x in x_cols:
        base = col_x[:-2]
        col_y = base + "_y"
        if col_y in df.columns:
            df[base] = df[col_x].where(df[col_x].notna(), df[col_y])
            df = df.drop(columns=[col_x, col_y])
    return df
```

---

### 7. Excel file bị protect hoặc corrupt

**Lỗi:** `InvalidFileException` hoặc file mở nhưng rỗng

**Debug:**
```python
# Check file không bị corrupt
from openpyxl import load_workbook
try:
    wb = load_workbook(file, read_only=True)
    print(f"Sheets: {wb.sheetnames}")
    ws = wb.active
    print(f"Max row: {ws.max_row}, Max col: {ws.max_column}")
except Exception as e:
    print(f"Error: {e}")
    # Thử xlrd cho file .xls cũ
    import xlrd
    wb = xlrd.open_workbook(file)
```

**Fix cho file .xls cũ (Excel 97-2003):**
```python
# pandas đọc .xls cần xlrd
pip install xlrd==1.2.0  # xlrd 2.x không support .xls

df = pd.read_excel(file, engine='xlrd')
```

---

### 8. Progress bar cho long operations

```python
from tqdm import tqdm  # pip install tqdm

# Cho loop-based operations
for i, chunk in enumerate(tqdm(chunks, desc="Processing")):
    ...

# Cho pandas apply
from tqdm import tqdm
tqdm.pandas()
df["result"] = df["text"].progress_apply(expensive_function)
```
