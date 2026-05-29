---
name: gsheet-safe-write
description: Protocol đọc và validate Google Sheet structure trước khi ghi — tránh duplicate rows, mismatch format
triggers:
  - viết script update Google Sheet
  - append rows vào sheet
  - update columns trong sheet có sẵn
  - Google Sheets API batchUpdate
scope: Mọi Python scripts tương tác với Google Sheets qua API
---

# Google Sheets Safe Write — Protocol

## Vấn đề

Script không đọc sheet trước → assume sai format → append duplicate / ghi nhầm cột.

```
Lỗi thực tế: Sheet có format "1.1 Description"
Script assume: TC-XXX-NNN format
Kết quả: Regex không match → 335 dòng trùng bị append
```

## Protocol bắt buộc (3 bước trước khi ghi)

### Bước 1 — Đọc và IN ra mẫu sheet

```python
# LUÔN làm trước khi viết bất kỳ update nào
sample = sheets.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="SheetName!A1:J5",  # header + 4 dòng đầu
).execute()

for i, row in enumerate(sample.get('values', [])):
    print(f"Row {i+1}: {row}")

# Dừng lại, đọc output, confirm format TRƯỚC KHI tiếp tục
```

### Bước 2 — Validate trước khi ghi (dry-run)

```python
def dry_run_preview(rows_to_write: list, label="DRY RUN"):
    print(f"\n=== {label}: {len(rows_to_write)} rows ===")
    for i, row in enumerate(rows_to_write[:5]):  # in 5 dòng đầu
        print(f"  [{i+1}] {row[:3]}...")  # in 3 cột đầu
    if len(rows_to_write) > 5:
        print(f"  ... ({len(rows_to_write) - 5} more)")
    
    confirm = input("\nConfirm write? (y/n): ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return False
    return True

# Dùng trong script:
if not dry_run_preview(new_rows, "APPEND NEW TEST ROWS"):
    sys.exit(0)
```

> **Note:** Bỏ `input()` khi chạy automated (CI). Thay bằng print + manual review.

### Bước 3 — Tìm existing IDs trước khi append

```python
# Đọc toàn bộ sheet
all_rows = sheets.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="SheetName!A:J",
).execute().get('values', [])

# In header để biết format
print(f"Header: {all_rows[0] if all_rows else 'EMPTY'}")
print(f"Row 2 sample: {all_rows[1] if len(all_rows) > 1 else 'EMPTY'}")
print(f"Total rows (incl header): {len(all_rows)}")

# Chỉ sau khi hiểu format → mới build regex/logic tìm IDs
```

## Template script an toàn

```python
"""Safe Google Sheet update script."""
import json
import google.oauth2.credentials
import googleapiclient.discovery

SPREADSHEET_ID = "your-id"
TOKEN_PATH = r"C:\Users\wi\.google-docs-token.json"

def connect():
    with open(TOKEN_PATH) as f:
        tok = json.load(f)
    creds = google.oauth2.credentials.Credentials(
        token=None,
        refresh_token=tok["refresh_token"],
        client_id=tok["client_id"],
        client_secret=tok["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    service = googleapiclient.discovery.build("sheets", "v4", credentials=creds)
    return service.spreadsheets()

sheets = connect()

# === STEP 1: LUÔN ĐỌC TRƯỚC ===
print("=== READING CURRENT SHEET ===")
current = sheets.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="Sheet!A1:J5",
).execute()
for i, row in enumerate(current.get('values', [])):
    print(f"Row {i+1}: {row}")

# === STEP 2: BUILD logic dựa trên format thực tế ===
# (Sau khi đọc output ở trên xong mới code tiếp)

# === STEP 3: DRY-RUN PREVIEW ===
print("\n=== PREVIEW CHANGES ===")
# Print changes trước khi apply

# === STEP 4: APPLY (sau khi confirm) ===
```

## Checklist trước khi chạy sheet script

- [ ] Đã đọc header row chưa?
- [ ] Đã in sample data (3-5 dòng) để xác nhận format chưa?
- [ ] Regex/logic tìm ID match với format thực tế chưa?
- [ ] Có dry-run preview trước append/delete chưa?
- [ ] Biết rõ số dòng hiện tại và sẽ thêm bao nhiêu chưa?
- [ ] Có backup plan nếu cần rollback chưa? (xóa rows appended)

## Phantom Row — `appendSpreadsheetRows` (cẩn trọng)

⚠️ `appendSpreadsheetRows` có thể ghi vào row ngoài `gridProperties.rowCount` (phantom).
`deleteDimension` sau đó sẽ trim mất. Đã mất 2 lần critical bug row trong session 2026-05-19.

**Fix cho critical rows** — expand grid trước rồi `values.update` vào row cụ thể:

```python
meta = sheets.get(spreadsheetId=SID).execute()
sm = next(s for s in meta['sheets'] if s['properties']['title'] == TAB)
current_rows = sm['properties']['gridProperties']['rowCount']
target_row = 33

if target_row > current_rows:
    sheets.batchUpdate(spreadsheetId=SID, body={'requests': [{
        'updateSheetProperties': {
            'properties': {'sheetId': sm['properties']['sheetId'],
                           'gridProperties': {'rowCount': target_row + 10}},
            'fields': 'gridProperties.rowCount',
        }
    }]}).execute()

sheets.values().update(
    spreadsheetId=SID,
    range=f"{TAB}!A{target_row}:M{target_row}",
    valueInputOption='USER_ENTERED',
    body={'values': [[...]]},
).execute()
```

Sau mọi `deleteDimension`: đọc lại 3-4 row cuối để verify rows quan trọng còn.

## Pattern rollback sau khi append sai

```python
# Xóa rows sai bằng deleteDimension
sheets.batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': [{'deleteDimension': {
        'range': {
            'sheetId': CMS_SHEET_ID,
            'dimension': 'ROWS',
            'startIndex': FIRST_BAD_ROW - 1,  # 0-based
            'endIndex': LAST_BAD_ROW,           # exclusive
        }
    }}]}
).execute()
print(f"Deleted rows {FIRST_BAD_ROW}–{LAST_BAD_ROW}")
```
