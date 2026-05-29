# Performance Tips — Xử lý Large Files (>100MB, >1M rows)

## Khi nào đọc file này

Khi user có:
- File > 100MB
- > 500,000 rows
- Script chạy quá chậm (> 5 phút)
- MemoryError

---

## Decision Tree: Chọn approach nào?

```
File size?
├── < 50MB → pandas bình thường ✓
├── 50-200MB → pandas + usecols/dtypes optimization
├── 200MB-2GB → polars hoặc chunked pandas
└── > 2GB → dask hoặc database (SQLite/DuckDB)
```

---

## 1. Pandas Optimization (50-200MB)

```python
import pandas as pd
import numpy as np

# Trick 1: Chỉ đọc columns cần thiết
COLS_NEEDED = ["order_id", "date", "amount", "region"]
df = pd.read_excel(file, usecols=COLS_NEEDED)

# Trick 2: Chỉ định dtypes để tiết kiệm memory
dtype_map = {
    "order_id": "str",
    "amount": "float32",   # float32 thay vì float64 = 50% memory
    "region": "category",  # category cho string có ít unique values
    "status": "category",
}
df = pd.read_csv(file, dtype=dtype_map)

# Trick 3: Parse dates khi load (không sau khi load)
df = pd.read_csv(file, parse_dates=["order_date"])

# Check memory usage
print(df.memory_usage(deep=True).sum() / 1024**2, "MB")
```

---

## 2. Polars — Nhanh gấp 5-10x pandas

```python
import polars as pl

# Đọc file
df = pl.read_csv("large_file.csv", infer_schema_length=1000)
df = pl.read_excel("large_file.xlsx")

# Các operations phổ biến (syntax khác pandas)
# Filter
df_filtered = df.filter(pl.col("amount") > 1000)

# Group by aggregate
summary = df.group_by(["region", "month"]).agg([
    pl.col("amount").sum().alias("total_amount"),
    pl.col("order_id").count().alias("order_count"),
    pl.col("amount").mean().alias("avg_amount"),
])

# Join (equivalent của pandas merge)
joined = df_a.join(df_b, on="order_id", how="inner")

# Convert về pandas nếu cần openpyxl/xlsxwriter
df_pandas = df.to_pandas()

# Viết ra file
df.write_csv("output.csv")
df.write_parquet("output.parquet")  # Compact format cho archiving
```

**Khi nào dùng polars vs pandas:**
- Polars: Khi tốc độ là ưu tiên, data pipeline, large aggregations
- Pandas: Khi cần compatibility với openpyxl/xlsxwriter formatting

---

## 3. Chunked Processing — CSV large files

```python
import pandas as pd
from pathlib import Path

CHUNK_SIZE = 50_000  # rows per chunk

def process_large_csv(file: str, output_file: str):
    """Process large CSV theo từng chunk"""
    result_chunks = []

    print(f"Processing {file} in chunks of {CHUNK_SIZE:,}...")

    for i, chunk in enumerate(pd.read_csv(file, chunksize=CHUNK_SIZE)):
        # Process mỗi chunk
        chunk_result = (
            chunk
            .assign(amount=lambda x: x['amount'].fillna(0))
            .query("status == 'active'")
            .groupby("region")["amount"].sum()
            .reset_index()
        )
        result_chunks.append(chunk_result)

        if (i + 1) % 10 == 0:
            print(f"  Processed {(i+1) * CHUNK_SIZE:,} rows...")

    # Merge chunks và final aggregation
    final = pd.concat(result_chunks).groupby("region")["amount"].sum().reset_index()
    final.to_csv(output_file, index=False)
    print(f"[OK] {output_file}")
```

---

## 4. DuckDB — SQL trên large files (>2GB)

DuckDB xử lý files lớn tốt nhất vì không cần load toàn bộ vào RAM:

```python
import duckdb

# Query trực tiếp từ file mà không load vào RAM
result = duckdb.sql("""
    SELECT
        region,
        SUM(amount) as total_amount,
        COUNT(*) as order_count
    FROM read_csv_auto('large_file.csv')
    WHERE status = 'active'
      AND date >= '2024-01-01'
    GROUP BY region
    ORDER BY total_amount DESC
""").df()  # .df() convert về pandas

# Compare 2 large files
diff = duckdb.sql("""
    SELECT a.order_id, a.amount as old_amount, b.amount as new_amount
    FROM read_csv_auto('file_old.csv') a
    FULL OUTER JOIN read_csv_auto('file_new.csv') b
        ON a.order_id = b.order_id
    WHERE a.amount != b.amount
       OR a.order_id IS NULL
       OR b.order_id IS NULL
""").df()

# Tốt để merge nhiều files
merged = duckdb.sql("""
    SELECT *, filename
    FROM read_csv_auto('data/inputs/*.csv', filename=true)
""").df()
```

**Install:** `pip install duckdb`

---

## 5. Streaming Excel với openpyxl (read-only mode)

Khi file Excel > 50MB và chỉ cần đọc:

```python
from openpyxl import load_workbook

# read_only=True: không load toàn bộ vào RAM
wb = load_workbook("large_file.xlsx", read_only=True, data_only=True)
ws = wb.active

rows = []
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i == 0:
        headers = row
        continue
    rows.append(dict(zip(headers, row)))

    if len(rows) >= 10_000:
        # Process batch
        chunk_df = pd.DataFrame(rows)
        # ... process chunk
        rows = []

wb.close()
```

---

## 6. Benchmark: Thời gian ước tính

| Operation | 100K rows | 1M rows | 10M rows |
|-----------|-----------|---------|----------|
| pandas read_csv | ~1s | ~8s | ~80s |
| polars read_csv | ~0.3s | ~2s | ~15s |
| duckdb query | ~0.5s | ~2s | ~10s |
| pandas groupby | ~0.5s | ~4s | ~40s |
| polars groupby | ~0.1s | ~0.5s | ~3s |
| fuzzy match (rapidfuzz) | ~5s | ~50s | N/A* |

*Fuzzy match O(n²) — không scale tốt. Với > 100K records, cần blocking strategy.

---

## 7. Fuzzy Match Optimization cho Large Datasets

```python
from rapidfuzz import process

# Naive O(n²) — chậm
for a in df_a["name"]:
    best = process.extractOne(a, df_b["name"].tolist())

# Tối ưu với blocking (grouping trước)
# Ví dụ: chỉ compare trong cùng city/region
for group_key, group_a in df_a.groupby("city"):
    group_b = df_b[df_b["city"] == group_key]["name"].tolist()
    if not group_b:
        continue
    for name in group_a["name"]:
        best = process.extractOne(name, group_b)

# Dùng cdist cho batch comparison (nhanh hơn loop)
from rapidfuzz import process
matrix = process.cdist(df_a["name"].tolist(), df_b["name"].tolist(), scorer=fuzz.ratio)
# matrix[i][j] = score giữa df_a row i và df_b row j
```

---

## Checklist Performance

Trước khi submit script cho large files:
- [ ] Dùng `usecols` để chỉ load columns cần thiết
- [ ] Set `dtype` cho columns lớn (đặc biệt string → category)
- [ ] Dùng polars nếu pandas quá chậm
- [ ] Dùng DuckDB nếu file > 1GB
- [ ] Có progress indicator (tqdm hoặc print mỗi N chunks)
- [ ] Test với 1000-row sample trước khi chạy full data
