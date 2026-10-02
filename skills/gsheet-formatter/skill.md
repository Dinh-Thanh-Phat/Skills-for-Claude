---
name: gsheet-formatter
description: Format Google Sheets via Sheets API — wrap text, column widths, header styling, freeze row, alternating rows, conditional colors, borders. Generic template, adapts to any sheet structure.
triggers:
  - "format sheet"
  - "format google sheet"
  - "làm đẹp sheet"
  - "format lại sheet"
  - "căn hàng"
  - "xuống dòng sheet"
  - "sheet bị che chữ"
  - "auto resize cột"
scope: google-sheets
---

# Google Sheet Formatter Skill

Format bất kỳ Google Sheet nào qua Sheets API batchUpdate.
**Không** dùng Playwright UI click — API trực tiếp, nhanh và reliable hơn.

---

## Step 0 — Thu thập thông tin trước khi format

Hỏi hoặc suy luận từ context:

| Thông tin cần | Cách lấy |
|---|---|
| `SPREADSHEET_ID` | Từ URL: `docs.google.com/spreadsheets/d/<ID>/edit` |
| Tab name | User cung cấp, hoặc đọc từ sheet tabs |
| Số cột (N) | Đếm header row |
| Nội dung từng cột | Đọc header để quyết định width |
| Cột nào cần center | ID, status, date, số thứ tự |
| Cột nào cần conditional color | Status, Result, Priority, Type |
| Màu header | Hỏi user nếu không rõ; default: xanh đậm |
| Số data rows | Đọc sheet hoặc user nói |

---

## Step 1 — Khởi tạo Sheets API client

```python
import json
import google.oauth2.credentials
import googleapiclient.discovery

TOKEN_PATH = r"C:\Users\wi\.google-docs-token.json"

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
sheets = service.spreadsheets()
```

---

## Step 2 — Lấy Sheet ID từ tab name

```python
SPREADSHEET_ID = "..."  # từ URL
TAB_NAME = "..."        # tên tab cần format

meta = sheets.get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_id = next(
    s["properties"]["sheetId"]
    for s in meta["sheets"]
    if s["properties"]["title"] == TAB_NAME
)
```

---

## Step 3 — Cấu hình theo sheet cụ thể

Điều chỉnh các biến này cho từng sheet:

```python
# === CẤU HÌNH — thay đổi phần này cho mỗi sheet ===

NUM_COLS = 10        # số cột (A–J = 10, A–E = 5, ...)
NUM_ROWS = 145       # tổng rows bao gồm header (1 header + 144 data)

# Width (pixels) cho từng cột theo thứ tự từ trái sang phải
# Gợi ý: ID/STT ~50, short text ~100-130, medium ~200-250, long text ~300-400
col_widths = [50, 130, 220, 370, 270, 270, 70, 70, 70, 250]

# Các cột cần center-align (0-indexed): thường là ID, số thứ tự, status, type
CENTER_COLS = [0, 6, 7, 8]

# Header row height và data row height (pixels)
HEADER_HEIGHT = 40
DATA_ROW_HEIGHT = 80

# Header background color (RGB 0.0–1.0)
# Xanh đậm: (0.18, 0.36, 0.58) | Xanh lá: (0.13, 0.55, 0.13) | Tím: (0.36, 0.18, 0.58)
HEADER_BG = {"red": 0.18, "green": 0.36, "blue": 0.58}

# Conditional format rules: list of (text_value, background_color)
# Set = [] nếu không cần conditional format
# Cột áp dụng: CONDITIONAL_COL (0-indexed)
CONDITIONAL_COL = 8   # cột Result / Status / Priority...
CONDITIONAL_RULES = [
    ("PASS",   {"red": 0.72, "green": 0.88, "blue": 0.72}),
    ("FAIL",   {"red": 0.95, "green": 0.70, "blue": 0.70}),
    ("SKIP",   {"red": 1.0,  "green": 0.89, "blue": 0.60}),
    ("MANUAL", {"red": 0.88, "green": 0.80, "blue": 0.95}),
    # Thêm tuỳ ý: ("HIGH", {...}), ("LOW", {...}), ...
]

# Alternating row color (hàng chẵn) — set None để tắt
ALT_ROW_COLOR = {"red": 0.94, "green": 0.96, "blue": 0.99}
# True (mặc định) = dùng addBanding 1 request; False = loop repeatCell từng hàng
USE_BANDING = True
```

---

## Step 4 — Build requests và execute

```python
requests = []

# --- Column widths ---
for i, px in enumerate(col_widths):
    requests.append({"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
        "properties": {"pixelSize": px},
        "fields": "pixelSize",
    }})

# --- Freeze header row ---
requests.append({"updateSheetProperties": {
    "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
    "fields": "gridProperties.frozenRowCount",
}})

# --- Wrap + top-align tất cả cells ---
requests.append({"repeatCell": {
    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": NUM_ROWS,
              "startColumnIndex": 0, "endColumnIndex": NUM_COLS},
    "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"}},
    "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)",
}})

# --- Header styling ---
requests.append({"repeatCell": {
    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1,
              "startColumnIndex": 0, "endColumnIndex": NUM_COLS},
    "cell": {"userEnteredFormat": {
        "backgroundColor": HEADER_BG,
        "textFormat": {
            "bold": True,
            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
            "fontSize": 10,
        },
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE",
        "wrapStrategy": "WRAP",
    }},
    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
}})

# --- Row heights ---
requests.append({"updateDimensionProperties": {
    "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
    "properties": {"pixelSize": HEADER_HEIGHT},
    "fields": "pixelSize",
}})
requests.append({"updateDimensionProperties": {
    "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": 1, "endIndex": NUM_ROWS},
    "properties": {"pixelSize": DATA_ROW_HEIGHT},
    "fields": "pixelSize",
}})

# --- Center-align các cột chỉ định ---
for col in CENTER_COLS:
    requests.append({"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": NUM_ROWS,
                  "startColumnIndex": col, "endColumnIndex": col + 1},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(horizontalAlignment)",
    }})

# --- Alternating row colors ---
# Ưu tiên addBanding (1 request, xem mục "addBanding" bên dưới).
# Loop repeatCell này tạo ~NUM_ROWS/2 request — chỉ dùng khi sheet đã có banding
# mà không muốn xoá, hoặc cần tô màu "cứng" vào cell.
if ALT_ROW_COLOR and not USE_BANDING:
    for row in range(1, NUM_ROWS):
        if row % 2 == 0:
            requests.append({"repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": row, "endRowIndex": row + 1,
                          "startColumnIndex": 0, "endColumnIndex": NUM_COLS},
                "cell": {"userEnteredFormat": {"backgroundColor": ALT_ROW_COLOR}},
                "fields": "userEnteredFormat(backgroundColor)",
            }})

# --- Borders ---
requests.append({"updateBorders": {
    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": NUM_ROWS,
              "startColumnIndex": 0, "endColumnIndex": NUM_COLS},
    "top":    {"style": "SOLID", "width": 1, "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
    "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
    "left":   {"style": "SOLID", "width": 1, "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
    "right":  {"style": "SOLID", "width": 1, "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
    "innerHorizontal": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
    "innerVertical":   {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
}})

# --- Conditional format rules ---
for val, color in CONDITIONAL_RULES:
    requests.append({"addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": NUM_ROWS,
                        "startColumnIndex": CONDITIONAL_COL, "endColumnIndex": CONDITIONAL_COL + 1}],
            "booleanRule": {
                "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": val}]},
                "format": {"backgroundColor": color},
            },
        },
        "index": 0,
    }})

# --- Execute ---
result = sheets.batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()
print(f"Done! {len(result.get('replies', []))} operations applied")
```

---

## Hướng dẫn điều chỉnh col_widths

| Loại nội dung | Width (px) |
|---|---|
| STT, No, ID ngắn | 40–60 |
| Status, Type, Priority | 70–90 |
| Tên người, label ngắn | 100–140 |
| Mô tả ngắn, title | 180–250 |
| Steps, long description | 300–400 |
| URL, error message | 250–350 |

Tổng col_widths nên ≈ 1400–1800px để vừa màn hình 1080p không cần scroll ngang.

---

## addBanding — mặc định cho alternating rows (`USE_BANDING = True`)

Dùng `addBanding` thay cho loop repeatCell — 1 request thay vì ~N/2, sheet nào cũng nên dùng (không chỉ >300 rows).

⚠️ **`addBanding` KHÔNG idempotent:** nếu range đã có banding (lần chạy trước, hoặc user đã bật "Alternating colors"), request sẽ lỗi và **cả batchUpdate fail** (exact error text UNVERIFIED). Trước khi add, đọc `bandedRanges` của sheet và xoá cái cũ:

```python
meta = sheets.get(spreadsheetId=SPREADSHEET_ID, fields="sheets(properties.sheetId,bandedRanges)").execute()
for s in meta["sheets"]:
    if s["properties"]["sheetId"] == sheet_id:
        for br in s.get("bandedRanges", []):
            requests.insert(0, {"deleteBanding": {"bandedRangeId": br["bandedRangeId"]}})
```

```python
if ALT_ROW_COLOR and USE_BANDING:
  requests.append({"addBanding": {
    "bandedRange": {
        "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": NUM_ROWS,
                  "startColumnIndex": 0, "endColumnIndex": NUM_COLS},
        "rowProperties": {
            "firstBandColor":  {"red": 1, "green": 1, "blue": 1},
            "secondBandColor": ALT_ROW_COLOR,
        },
    }
}})
```

---

## Lưu ý

- Script **idempotent** cho hầu hết operations (chạy lại không hại). Riêng `addConditionalFormatRule` sẽ duplicate — xóa rules cũ trước nếu cần rerun:
  ```python
  # Xóa toàn bộ conditional rules của sheet trước khi add mới
  meta = sheets.get(spreadsheetId=SPREADSHEET_ID, includeGridData=False).execute()
  for s in meta["sheets"]:
      if s["properties"]["sheetId"] == sheet_id:
          for i, _ in enumerate(s.get("conditionalFormats", [])):
              requests.insert(0, {"deleteConditionalFormatRule": {"sheetId": sheet_id, "index": 0}})
  ```
- Credentials token: `C:\Users\wi\.google-docs-token.json` (OAuth authorized_user format)
- Python packages cần: `google-auth`, `google-api-python-client` (đã cài sẵn)
