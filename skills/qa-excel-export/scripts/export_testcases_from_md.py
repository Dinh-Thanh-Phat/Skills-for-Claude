#!/usr/bin/env python3
"""
Test Case Excel Exporter — GENERIC, tai dung cho moi project.

Doc cac file markdown module (NN_*.md) -> 1 file Excel, MOI MODULE 1 SHEET.
Khong go lai test case bang tay: parse truc tiep tu markdown de 2 nguon luon khop.

CACH DUNG
    python export_testcases_from_md.py <output-dir> [<Project Name>]
    hoac sua BASE_DIR / PROJECT ben duoi roi: python export_test_cases.py

FORMAT MARKDOWN DAU VAO — xem references/deliverable-format.md
    | ID | Cat | Pri | Title |
    |---|---|---|---|
    | AUTH-001 | POS | critical | Signup thanh cong |

    - **Pre:** ...
    - **Steps:** 1) ... 2) ...
    - **Test data:** ...
    - **Expected:** 1) ... 2) ...

    Nhieu case lien tiep CHIA SE 1 bullet block -> parser tu gan cho ca nhom.
    Cat = ⛔BLOCKED -> Result = BLOCKED, khong yeu cau Expected.

BAT BUOC SAU KHI CHAY
    Load lai file Excel va spot-check >=2 case, trong do >=1 case thuoc nhom
    chia se bullet block, de xac nhan parser gan dung.
"""

import os
import re
import sys
import glob
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

# ─── CONFIG (sua 2 dong nay, hoac truyen qua argv) ────────────────────────────
BASE_DIR = sys.argv[1] if len(sys.argv) > 1 else r"."
PROJECT = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(os.path.abspath(BASE_DIR))

DATE_STR = datetime.now().strftime("%Y%m%d")
OUT_FILE = os.path.join(BASE_DIR, f"{PROJECT}_TestCases_manual_{DATE_STR}.xlsx")

# ─── COLORS ───────────────────────────────────────────────────────────────────
C_HEADER_BG = "1F4E79"
C_HEADER_TX = "FFFFFF"
C_PASS = "92D050"
C_FAIL = "FF0000"
C_PENDING = "FFFF00"
C_BLOCKED = "FFA500"
C_ROW_ALT = "EBF3FB"
C_ROW_NRM = "FFFFFF"
C_P0 = "FFC7CE"   # do nhat - P0
C_P1 = "FFEB9C"   # vang nhat - P1
C_P2 = "E2EFDA"   # xanh nhat - P2

HEADERS = [
    "ID", "Module", "Sub-module", "Test Case Description", "Pre-condition",
    "Test Case Procedure", "Test Data", "Expected Output", "Actual Result",
    "Result", "Test Date", "Priority", "Category", "Note",
]
WIDTHS = [14, 22, 22, 44, 34, 56, 26, 52, 26, 11, 12, 9, 12, 34]
COL_RESULT = 10
COL_PRIORITY = 12

PRI_MAP = {"critical": "P0", "high": "P1", "medium": "P2", "low": "P3"}

# Regex nhan dien 1 dong test case: | ID | Cat | Pri | Title |
RE_CASE = re.compile(
    r"^\|\s*(?P<id>[A-Z]{2,4}(?:-[A-Z0-9]+)+)\s*\|"
    r"\s*(?P<cat>[^|]*?)\s*\|"
    r"\s*(?P<pri>[^|]*?)\s*\|"
    r"\s*(?P<title>[^|]*?)\s*\|?\s*$"
)
RE_H1 = re.compile(r"^#\s+(.*)$")
RE_H2 = re.compile(r"^##\s+(.*)$")
RE_BULLET_FIELD = re.compile(r"^-\s+\*\*(?P<key>[^*]+?):?\*\*:?\s*(?P<val>.*)$")
RE_BULLET_PLAIN = re.compile(r"^-\s+(?P<val>.+)$")

# Anh xa nhan bullet trong markdown -> cot Excel
FIELD_MAP = {
    "pre": "pre", "pre-condition": "pre", "precondition": "pre",
    "steps": "steps", "steps chung": "steps", "step": "steps",
    "test data": "data", "testdata": "data",
    "expected": "expected", "expected result": "expected",
    "note": "note", "ghi chu": "note", "ghi chú": "note",
    "trang thai": "note", "trạng thái": "note",
    "hanh dong qa": "note", "hành động qa": "note",
    "priority note": "note", "ghi chu severity": "note", "ghi chú severity": "note",
    "cau hoi": "note", "câu hỏi": "note",
}


def clean_md(text: str) -> str:
    """Bo markup markdown de o Excel doc duoc."""
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()


def norm_key(key: str) -> str:
    k = clean_md(key).lower().strip().rstrip(":")
    return FIELD_MAP.get(k, "note")


def split_steps(val: str) -> str:
    """'1) A. 2) B.' hoac '1. A 2. B' -> moi buoc 1 dong."""
    val = clean_md(val)
    val = re.sub(r"\s+(?=\d+\)\s)", "\n", val)
    if "\n" not in val:
        val = re.sub(r"(?<=[.!?])\s+(?=\d+\.\s)", "\n", val)
    return val.strip()


def parse_file(path: str):
    """Tra ve (module_name, [case_dict...])."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    module = os.path.basename(path)
    submodule = ""
    group_ctx = ""
    cases = []
    pending = []          # nhom case lien tiep dang cho bullet block
    block = {}            # bullet block dang thu thap
    last_key = None
    in_frontmatter_table = False

    def flush():
        """Gan bullet block cho ca nhom case lien tiep phia truoc."""
        nonlocal pending, block, last_key
        if pending and block:
            for c in pending:
                for k, v in block.items():
                    if not c.get(k):
                        c[k] = v
        pending = []
        block = {}
        last_key = None

    for i, raw in enumerate(lines):
        line = raw.rstrip()

        # Ten module = dong tieu de dau tien
        if i == 0 and line.startswith("# "):
            module = clean_md(line[2:])
            continue

        m1 = RE_H1.match(line)
        m2 = RE_H2.match(line)
        if m1 and not line.startswith("##"):
            flush()
            submodule = clean_md(m1.group(1))
            group_ctx = ""
            continue
        if m2:
            flush()
            group_ctx = clean_md(m2.group(1))
            if not submodule:
                submodule = group_ctx
            continue

        mc = RE_CASE.match(line)
        if mc:
            cat = clean_md(mc.group("cat"))
            pri = clean_md(mc.group("pri")).lower()
            # Loai dong header bang va dong phan cach
            if cat.lower() in ("cat", "category", "---", ":---") or set(cat) <= {"-", ":"}:
                continue
            if block:          # da co bullet -> nhom truoc da xong
                flush()
            case = {
                "id": clean_md(mc.group("id")),
                "module": module,
                "submodule": submodule or group_ctx,
                "title": clean_md(mc.group("title")),
                "cat": cat.replace("⛔", "").strip() or "POS",
                "pri": PRI_MAP.get(pri, "P2"),
                "blocked": "BLOCKED" in cat.upper() or "⛔" in mc.group("cat"),
                "pre": "", "steps": "", "data": "", "expected": "", "note": "",
            }
            pending.append(case)
            cases.append(case)
            continue

        mf = RE_BULLET_FIELD.match(line)
        if mf and pending:
            key = norm_key(mf.group("key"))
            val = mf.group("val")
            val = split_steps(val) if key == "steps" else clean_md(val)
            block[key] = (block.get(key, "") + "\n" + val).strip() if key in block else val
            last_key = key
            continue

        mp = RE_BULLET_PLAIN.match(line)
        if mp and pending:
            val = clean_md(mp.group("val"))
            key = "note"
            block[key] = (block.get(key, "") + "\n" + val).strip() if key in block else val
            last_key = key
            continue

        # Dong tiep noi cua bullet truoc (thut le)
        if pending and last_key and line.startswith("  ") and line.strip():
            block[last_key] = block[last_key] + "\n" + clean_md(line)
            continue

        if not line.strip():
            continue

        # Van ban thuong -> ket thuc bullet block
        if not line.startswith("|"):
            flush()

    flush()

    # Case khong co Expected: hoac la cross-reference sang module khac,
    # hoac la case 1 dong (UI/PERF/A11Y) chua duoc viet chi tiet.
    # Danh dau ro de nguoi review biet phai lam gi, khong de o trong im lang.
    RE_XREF = re.compile(
        r"(xem|Xem|Chi tiết|chi tiết|Trùng|trùng|Ripple|ripple)\s+[A-Z]{2,4}-[A-Z0-9-]+"
    )
    for c in cases:
        if c["expected"] or c["blocked"]:
            continue
        xref = RE_XREF.search(c["note"]) or RE_XREF.search(c["title"])
        if xref:
            c["expected"] = f"→ Dùng Expected của case được tham chiếu: {c['note'] or c['title']}"
            c["note"] = (c["note"] + "\nCROSS-REF: chỉ chạy 1 lần ở module gốc.").strip()
        else:
            c["expected"] = "[CẦN BỔ SUNG] Case 1 dòng — Expected chi tiết viết khi có Figma/build."
            c["note"] = (c["note"] + "\nTODO: bổ sung Expected khi có Figma/build.").strip()

    return module, cases


# ─── STYLE HELPERS ────────────────────────────────────────────────────────────
def fill(color):
    return PatternFill("solid", fgColor=color)


def border():
    thin = Side(style="thin", color="BFBFBF")
    return Border(left=thin, right=thin, top=thin, bottom=thin)


RESULT_FILL = {"PASS": C_PASS, "FAIL": C_FAIL, "PENDING": C_PENDING, "BLOCKED": C_BLOCKED}
PRI_FILL = {"P0": C_P0, "P1": C_P1, "P2": C_P2, "P3": C_P2}


def write_sheet(ws, cases):
    for c, h in enumerate(HEADERS, 1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.fill = fill(C_HEADER_BG)
        cell.font = Font(name="Calibri", size=11, bold=True, color=C_HEADER_TX)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border()
    ws.row_dimensions[1].height = 32

    for r, case in enumerate(cases, 2):
        result = "BLOCKED" if case["blocked"] else "PENDING"
        row = [
            case["id"], case["module"], case["submodule"], case["title"],
            case["pre"], case["steps"], case["data"], case["expected"],
            "", result, "", case["pri"], case["cat"], case["note"],
        ]
        alt = fill(C_ROW_ALT) if r % 2 == 0 else fill(C_ROW_NRM)
        for c, val in enumerate(row, 1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.border = border()
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.font = Font(name="Calibri", size=10)
            if c == COL_RESULT:
                cell.fill = fill(RESULT_FILL[result])
                cell.alignment = Alignment(horizontal="center", vertical="center")
                if result == "FAIL":
                    cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
                else:
                    cell.font = Font(name="Calibri", size=10, bold=True)
            elif c == COL_PRIORITY:
                cell.fill = fill(PRI_FILL.get(case["pri"], C_ROW_NRM))
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.font = Font(name="Calibri", size=10, bold=True)
            else:
                cell.fill = alt

        # Chieu cao dong theo do dai noi dung
        longest = max(len(str(row[4])), len(str(row[5])), len(str(row[7])), len(str(row[3])))
        ws.row_dimensions[r].height = min(300, max(30, 15 * (longest // 55 + 1)))

    for c, w in enumerate(WIDTHS, 1):
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}{len(cases) + 1}"


def add_summary(wb, per_module, all_cases):
    ws = wb.create_sheet("00_SUMMARY", 0)
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 42
    for col in "CDEFGHIJKL":
        ws.column_dimensions[col].width = 11

    ws.merge_cells("A1:L1")
    t = ws.cell(row=1, column=1, value=f"TETHERTAILS — TEST CASE SUMMARY (manual, {DATE_STR})")
    t.fill = fill(C_HEADER_BG)
    t.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 34

    cats = ["POS", "NEG", "SEC", "EDGE", "BOUNDARY", "UI", "PERF", "A11Y", "PLAT"]
    hdr = ["Sheet", "Module", "Cases", "P0", "P1", "P2", "BLOCKED"] + cats
    for c, h in enumerate(hdr, 1):
        cell = ws.cell(row=2, column=c, value=h)
        cell.fill = fill(C_HEADER_BG)
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border()
    ws.row_dimensions[2].height = 28

    for c, w in enumerate([10, 42, 9, 7, 7, 7, 11] + [9] * len(cats), 1):
        ws.column_dimensions[get_column_letter(c)].width = w

    r = 3
    for sheet_name, module, cases in per_module:
        vals = [
            sheet_name, module, len(cases),
            sum(1 for x in cases if x["pri"] == "P0"),
            sum(1 for x in cases if x["pri"] == "P1"),
            sum(1 for x in cases if x["pri"] == "P2"),
            sum(1 for x in cases if x["blocked"]),
        ]
        for cat in cats:
            vals.append(sum(1 for x in cases if cat in x["cat"].upper()))
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.border = border()
            cell.font = Font(name="Calibri", size=10)
            cell.alignment = Alignment(
                horizontal="left" if c == 2 else "center", vertical="center"
            )
            if c == 4 and v:
                cell.fill = fill(C_P0)
                cell.font = Font(name="Calibri", size=10, bold=True)
            if c == 7 and v:
                cell.fill = fill(C_BLOCKED)
                cell.font = Font(name="Calibri", size=10, bold=True)
        r += 1

    # Dong TONG
    total = ["", "TỔNG", len(all_cases),
             sum(1 for x in all_cases if x["pri"] == "P0"),
             sum(1 for x in all_cases if x["pri"] == "P1"),
             sum(1 for x in all_cases if x["pri"] == "P2"),
             sum(1 for x in all_cases if x["blocked"])]
    for cat in cats:
        total.append(sum(1 for x in all_cases if cat in x["cat"].upper()))
    for c, v in enumerate(total, 1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.fill = fill(C_HEADER_BG)
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.border = border()
        cell.alignment = Alignment(
            horizontal="left" if c == 2 else "center", vertical="center"
        )
    ws.row_dimensions[r].height = 24

    notes = [
        "",
        "GHI CHÚ QUAN TRỌNG:",
        "1. Toàn bộ case đang ở trạng thái PENDING — Phase 1 (manual), chưa execute, chưa viết automation.",
        "2. Case tô màu cam ở cột Result = BLOCKED: spec chưa chốt (NOT CONFIRMED / out-of-scope mâu thuẫn).",
        "   → KHÔNG viết Expected result cho các case này. Xem file 99_OPEN_ITEMS_AND_QUESTIONS.md mục A và B.",
        "3. Nhóm case UI viết theo mô tả text của spec — CHƯA có Figma để verify layout thật.",
        "4. Có 16 điều kiện môi trường phải gỡ trước khi execute (OTP staging, counter moderation vendor,",
        "   API contract, thiết bị GPS, Apple sandbox...). Xem 99_OPEN_ITEMS_AND_QUESTIONS.md mục D.",
        "5. Một số case là cross-reference trỏ tới module khác (vd REC-002 → xem CAL-001):",
        "   giữ trong danh sách để truy vết theo requirement, nhưng khi chạy chỉ chạy 1 lần ở module gốc.",
        "6. Priority: P0 = auth/mất data/payment/security/PDPA · P1 = core CRUD + cross-module · P2 = edge/a11y/perf/platform",
    ]
    r += 1
    for line in notes:
        cell = ws.cell(row=r, column=1, value=line)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=12)
        cell.font = Font(name="Calibri", size=10,
                         bold=line.startswith(("GHI CHÚ", "2.")),
                         color="C00000" if line.startswith(("GHI CHÚ", "2.", "4.")) else "000000")
        cell.alignment = Alignment(vertical="center")
        r += 1

    ws.freeze_panes = "A3"


def sheet_name_for(fname: str, module: str) -> str:
    """Ten sheet <=31 ky tu, khong ky tu bi cam."""
    num = fname.split("_")[0]
    body = re.sub(r"^§?\d+(\.\d+)?\s*[—-]\s*", "", module)
    body = re.sub(r"\s*\(P0\)$", "", body)
    body = re.sub(r"[\[\]:*?/\\]", "", body)
    name = f"{num}_{body}"
    return name[:31].rstrip()


def main():
    files = sorted(glob.glob(os.path.join(BASE_DIR, "[01]*.md")))
    files = [f for f in files if re.match(r"^\d{2}_", os.path.basename(f))
             and not os.path.basename(f).startswith("00_")]
    if not files:
        raise SystemExit(f"Khong tim thay file module trong {BASE_DIR}")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    per_module, all_cases = [], []
    for path in files:
        fname = os.path.basename(path)
        module, cases = parse_file(path)
        if not cases:
            print(f"[WARN] {fname}: 0 case parse duoc")
            continue
        sname = sheet_name_for(fname, module)
        ws = wb.create_sheet(sname)
        write_sheet(ws, cases)
        per_module.append((sname.split("_")[0], module, cases))
        all_cases.extend(cases)
        print(f"[OK] {sname:34s} {len(cases):4d} cases")

    add_summary(wb, per_module, all_cases)
    wb.save(OUT_FILE)

    print(f"\n[DONE] {OUT_FILE}")
    print(f"       {len(all_cases)} cases / {len(per_module)} module sheets + 1 summary")
    blocked = [c["id"] for c in all_cases if c["blocked"]]
    print(f"       BLOCKED: {len(blocked)} -> {', '.join(blocked)}")
    xref = [c["id"] for c in all_cases if c["expected"].startswith("→")]
    todo = [c["id"] for c in all_cases if c["expected"].startswith("[CẦN BỔ SUNG]")]
    print(f"       CROSS-REF (chay o module goc): {len(xref)}")
    print(f"       CAN BO SUNG Expected (case 1 dong, cho Figma/build): {len(todo)}")
    if todo:
        print("       " + ", ".join(todo[:30]) + (" ..." if len(todo) > 30 else ""))


if __name__ == "__main__":
    main()
