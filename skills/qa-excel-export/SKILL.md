---
name: qa-excel-export
description: Export test cases to formatted Excel files — 2 files (automation & manual), each with color-coded rows for Pass/Fail/Pending. Use when asked to "export test cases to excel", "xuất test case ra excel", "create excel test report", "generate test case file", or after generating test cases with qa-test-generation skill.
---

# QA Excel Export Skill

You are a **Senior QA Engineer** exporting test cases to professional Excel reports.

---

## 🔴 CHUẨN MẶC ĐỊNH — ĐỌC TRƯỚC TIÊN

**Khi export bộ test cases sinh ra từ spec/PRD/scope doc → BẮT BUỘC dùng format ở
`references/deliverable-format.md`.** User đã xác nhận format này (TetherTails, 697 cases,
05-08-2026) và yêu cầu áp dụng mặc định cho mọi lần viết test cases. **Không cần user yêu cầu lại.**

Format đó **override** phần "Output Files" và "Column Format" cũ bên dưới ở 3 điểm:

| | Mặc định CŨ (bên dưới) | ✅ Mặc định MỚI |
|---|---|---|
| Sheet | 1 sheet + Summary | **MỖI MODULE 1 SHEET** + `00_SUMMARY` |
| Cột | 11 cột | **14 cột** (thêm `Sub-module`, `Priority`, `Category`) |
| Nguồn data | gõ tay vào list Python | **parse trực tiếp từ markdown** — không gõ test case 2 lần |

**Script sẵn có, đã chạy thật:** `scripts/export_testcases_from_md.py`
```bash
# copy vào output dir rồi chạy
python export_testcases_from_md.py "<output-dir>" "<ProjectName>"
```

Phần "Column Format" 11 cột bên dưới **chỉ dùng khi** user yêu cầu rõ format cũ, hoặc khi
export một nhóm case lẻ không có cấu trúc module (vd kết quả 1 lần chạy regression).

---

## ⚠️ Python Code Generation Safety Rules (MANDATORY)

Before writing any Python script for Excel export, follow the `python-code-gen-safety` skill rules. Summary of what caused failures in the past:

1. **Never inject Python source code via string manipulation** — Do NOT use `new_code = """..."""` with embedded Python functions containing `\n` in strings, then `f.write(new_code)`. The `\n` becomes a literal newline in the file → `SyntaxError`.
2. **Always write new sheet functions to a SEPARATE standalone file** — never patch an existing working `.py` file.
3. **Always validate syntax before saving:** `ast.parse(code)` — if it raises `SyntaxError`, fix before writing to disk.
4. **Always use `get_column_letter(n)` from openpyxl** — never `chr(64 + n)` (breaks for col > 26).
5. **Verify all file paths exist** before running (especially paths with Vietnamese/Unicode characters).
6. **Never pass long Python code via Bash `-c`** — write to file first, then `python file.py`.
7. **Grep for uniqueness before Edit tool** — `old_string` must appear exactly once.

## Output Files

Always generate **2 separate Excel files**:
1. `test_cases_automation_[YYYYMMDD].xlsx` — Bot/automation test cases
2. `test_cases_manual_[YYYYMMDD].xlsx` — Manual test cases

## Column Format (exact order)

| # | Column Name | Description |
|---|------------|-------------|
| A | ID | TC-001, TC-002... (auto for manual) / AT-001... (automation) |
| B | Module - Features | e.g., "Authentication - Login" |
| C | Test Case Description | Short title of the test case |
| D | Pre-condition | What must be true before running |
| E | Test Case Procedure | Step-by-step numbered steps |
| F | Test Data | Specific values, accounts, inputs |
| G | Expected Output | What should happen |
| H | Actual Result | Leave blank if not yet run |
| I | Result | PASS / FAIL / PENDING |
| J | Test Date | Leave blank if not yet run |
| K | Priority | P0 / P1 / P2 / P3 — based on business impact |
| L | Category | POS / NEG / UI / EDGE / SEC / PERF / A11Y / Platform (from qa-test-coverage-max 8-category matrix) |
| M | Note | Screenshot path, bug ID, comments |

## Result Status & Colors

| Status | Color | Meaning |
|--------|-------|---------|
| PASS | Green (#92D050) | Test passed |
| FAIL | Red (#FF0000) with white text | Test failed, bug found |
| PENDING | Yellow (#FFFF00) | Not enough conditions / blocked / not run yet |
| BLOCKED | Orange (#FFA500) | External dependency blocking |

## Step-by-Step Instructions

### 1. Collect Test Cases
Before writing the script, gather all test cases. For each test case, determine:
- Is it automation or manual (or both)?
- What is its current result status?

### 2. Write the Python Export Script

Create the file at: `data/outputs/export_test_cases.py`

```python
#!/usr/bin/env python3
"""
QA Test Case Excel Exporter
Generates formatted Excel files for automation and manual test cases.
"""

import openpyxl
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side
)
from openpyxl.utils import get_column_letter
from datetime import datetime
import os

# ─── CONFIG ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = "data/outputs"
DATE_STR = datetime.now().strftime("%Y%m%d")

# ─── COLORS ──────────────────────────────────────────────────────────────────
COLOR_HEADER_BG   = "1F4E79"   # Dark blue header
COLOR_HEADER_TEXT = "FFFFFF"   # White text
COLOR_PASS        = "92D050"   # Green
COLOR_FAIL        = "FF0000"   # Red
COLOR_PENDING     = "FFFF00"   # Yellow
COLOR_BLOCKED     = "FFA500"   # Orange
COLOR_ROW_ALT     = "EBF3FB"   # Light blue alternate row
COLOR_ROW_NORMAL  = "FFFFFF"   # White normal row

# ─── COLUMNS ─────────────────────────────────────────────────────────────────
HEADERS = [
    "ID",
    "Module - Features",
    "Test Case Description",
    "Pre-condition",
    "Test Case Procedure",
    "Test Data",
    "Expected Output",
    "Actual Result",
    "Result",
    "Test Date",
    "Note",
]

COLUMN_WIDTHS = [10, 25, 35, 30, 50, 25, 35, 35, 12, 14, 30]

# ─── TEST CASE DATA ───────────────────────────────────────────────────────────
# AUTOMATION TEST CASES
AUTOMATION_CASES = [
    # [ID, Module-Features, Description, Pre-condition, Steps, Test Data, Expected, Actual, Result, Date, Note]
    [
        "AT-001",
        "Authentication - Login",
        "Login with valid credentials",
        "User account exists and is active",
        "1. Navigate to /login\n2. Enter valid email\n3. Enter valid password\n4. Click 'Login'",
        "Email: test@example.com\nPassword: Test@123",
        "User redirected to dashboard. Welcome message shown.",
        "",
        "PENDING",
        "",
        "",
    ],
    # ADD MORE AUTOMATION CASES HERE
]

# MANUAL TEST CASES
MANUAL_CASES = [
    # [ID, Module-Features, Description, Pre-condition, Steps, Test Data, Expected, Actual, Result, Date, Note]
    [
        "TC-001",
        "Authentication - Login",
        "Login with valid credentials",
        "User account exists and is active",
        "1. Open browser\n2. Go to app URL\n3. Enter email\n4. Enter password\n5. Click Login",
        "Email: test@example.com\nPassword: Test@123",
        "Dashboard page loads with user's name",
        "",
        "PENDING",
        "",
        "",
    ],
    # ADD MORE MANUAL CASES HERE
]


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def make_fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)


def make_border() -> Border:
    thin = Side(style="thin", color="BFBFBF")
    return Border(left=thin, right=thin, top=thin, bottom=thin)


def result_fill(result: str) -> PatternFill | None:
    mapping = {
        "PASS":    make_fill(COLOR_PASS),
        "FAIL":    make_fill(COLOR_FAIL),
        "PENDING": make_fill(COLOR_PENDING),
        "BLOCKED": make_fill(COLOR_BLOCKED),
    }
    return mapping.get(result.upper())


def result_font(result: str) -> Font:
    if result.upper() == "FAIL":
        return Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    return Font(name="Calibri", size=11)


def write_sheet(ws, cases: list[list]) -> None:
    """Write headers + data rows to a worksheet."""

    # ── Header row
    for col_idx, header in enumerate(HEADERS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill    = make_fill(COLOR_HEADER_BG)
        cell.font    = Font(name="Calibri", size=11, bold=True, color=COLOR_HEADER_TEXT)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border  = make_border()

    ws.row_dimensions[1].height = 30

    # ── Data rows
    for row_idx, case in enumerate(cases, start=2):
        result = str(case[8]).upper() if len(case) > 8 else "PENDING"
        fill   = result_fill(result)
        font   = result_font(result)
        alt_bg = make_fill(COLOR_ROW_ALT) if row_idx % 2 == 0 else make_fill(COLOR_ROW_NORMAL)

        for col_idx, value in enumerate(case, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border    = make_border()
            cell.alignment = Alignment(vertical="top", wrap_text=True)

            # Colour the entire row lightly, then override Result cell
            if col_idx == 9 and fill:  # Result column
                cell.fill = fill
                cell.font = font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.fill = alt_bg
                cell.font = Font(name="Calibri", size=11)

        ws.row_dimensions[row_idx].height = 60

    # ── Column widths
    for col_idx, width in enumerate(COLUMN_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # ── Freeze header row + auto-filter
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}1"


def add_summary_sheet(wb, cases: list[list], sheet_name: str = "Summary") -> None:
    """Add a summary sheet with pass/fail/pending counts."""
    ws = wb.create_sheet(sheet_name)

    total   = len(cases)
    passed  = sum(1 for c in cases if str(c[8]).upper() == "PASS")
    failed  = sum(1 for c in cases if str(c[8]).upper() == "FAIL")
    pending = sum(1 for c in cases if str(c[8]).upper() in ("PENDING", ""))
    blocked = sum(1 for c in cases if str(c[8]).upper() == "BLOCKED")

    summary_data = [
        ("Total Test Cases", total),
        ("PASS",    passed),
        ("FAIL",    failed),
        ("PENDING", pending),
        ("BLOCKED", blocked),
        ("Pass Rate", f"{(passed/total*100):.1f}%" if total else "0%"),
    ]

    colors = {
        "Total Test Cases": "1F4E79",
        "PASS":    COLOR_PASS,
        "FAIL":    COLOR_FAIL,
        "PENDING": COLOR_PENDING,
        "BLOCKED": COLOR_BLOCKED,
        "Pass Rate": "1F4E79",
    }
    text_colors = {
        "FAIL": "FFFFFF",
        "Total Test Cases": "FFFFFF",
        "Pass Rate": "FFFFFF",
    }

    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 14

    for row_idx, (label, value) in enumerate(summary_data, start=2):
        lbl_cell = ws.cell(row=row_idx, column=1, value=label)
        val_cell = ws.cell(row=row_idx, column=2, value=value)
        bg = colors.get(label, "FFFFFF")
        txt = text_colors.get(label, "000000")
        for cell in (lbl_cell, val_cell):
            cell.fill   = make_fill(bg)
            cell.font   = Font(name="Calibri", size=12, bold=True, color=txt)
            cell.border = make_border()
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[row_idx].height = 25

    # Title
    title = ws.cell(row=1, column=1, value="TEST SUMMARY")
    ws.merge_cells("A1:B1")
    title.fill = make_fill("1F4E79")
    title.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    title.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 35


def create_workbook(filename: str, cases: list[list], sheet_label: str) -> str:
    wb = openpyxl.Workbook()

    # Main sheet
    ws = wb.active
    ws.title = sheet_label
    write_sheet(ws, cases)

    # Summary sheet
    add_summary_sheet(wb, cases)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    wb.save(path)
    print(f"[OK] Saved: {path}")
    return path


# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    print(f"Exporting test cases — {DATE_STR}")

    auto_file = create_workbook(
        f"test_cases_automation_{DATE_STR}.xlsx",
        AUTOMATION_CASES,
        "Automation Test Cases",
    )

    manual_file = create_workbook(
        f"test_cases_manual_{DATE_STR}.xlsx",
        MANUAL_CASES,
        "Manual Test Cases",
    )

    print("\n=== EXPORT COMPLETE ===")
    print(f"  Automation: {auto_file}  ({len(AUTOMATION_CASES)} cases)")
    print(f"  Manual:     {manual_file}  ({len(MANUAL_CASES)} cases)")


if __name__ == "__main__":
    main()
```

### 3. Populate Test Cases

Replace `AUTOMATION_CASES` and `MANUAL_CASES` lists with actual test data.

Format each row as:
```python
[
    "AT-001",                          # ID
    "Module - Feature",                # Module
    "Short description",               # Description
    "Pre-condition text",              # Pre-condition
    "1. Step one\n2. Step two",        # Steps (use \n for newlines)
    "user@test.com / Password123",     # Test Data
    "Expected outcome",                # Expected Output
    "",                                # Actual Result (blank if not run)
    "PENDING",                         # Result: PASS / FAIL / PENDING / BLOCKED
    "",                                # Test Date (blank or "2026-04-10")
    "",                                # Note (screenshot path, bug ID)
]
```

### 4. Screenshot Notes

For the Note column, reference screenshots like:
```python
"Screenshot: screenshots/AT-001_login_fail.png\nBug: BUG-042"
```

If using Playwright, screenshots are auto-saved. Reference them in the Note column by relative path.

### 5. Run the Script

```bash
cd [project-root]
pip install openpyxl
python data/outputs/export_test_cases.py
```

---

## Result Values

| Value | When to use |
|-------|------------|
| `PASS` | Test executed and passed |
| `FAIL` | Test executed and failed — add bug ID in Note |
| `PENDING` | Not yet run, or waiting on pre-conditions |
| `BLOCKED` | Cannot run — blocked by external dependency |

---

## Integration with qa-test-generation

After running `qa-test-generation`:
1. Take the generated test cases
2. Fill in `AUTOMATION_CASES` and `MANUAL_CASES` lists
3. Set `Result = "PENDING"` for all new cases
4. Run the export script
5. Fill in `Actual Result`, `Result`, `Test Date`, and `Note` after execution

---

## Behavior Rules

- Always generate the script with actual test case data populated (not empty placeholders)
- Use `PENDING` as default result for all new test cases
- Use `\n` for multi-line content in Steps and Pre-condition fields
- Always include both files (automation + manual), even if one is empty
- The script must be runnable immediately with `python export_test_cases.py`
- After writing the script, RUN it to produce the Excel files
