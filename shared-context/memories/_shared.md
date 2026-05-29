# Shared Memory — Global (all projects)

Cross-project corrections, Duy behaviour preferences, and global patterns.

---

## Platform

- **OS:** Windows 11 — use forward slashes in bash, Windows paths in PowerShell
- **Shell:** Git Bash (MINGW64) — HOME = `/c/Users/wi`
- **Projects root:** `d:/HK8/Learning/`
- **Duy location:** `d:/HK8/Learning/DQ/duy/duy/`

## Tools

- **bd (beads):** `C:/Users/wi/AppData/Roaming/npm/bd.exe` — shell wrapper fixed to call .exe directly
- **dolt:** `C:/Program Files/dolt/bin/dolt.exe` — added to Windows USER PATH permanently
- **openspec:** v1.2.0 — installed globally via npm
- **Always prepend PATH for dolt in bash:** `export PATH="$PATH:/c/Program Files/dolt/bin"`

## Behaviour

- Use `bd` for ALL task tracking — never TodoWrite or markdown task lists
- Log all script runs to `data/logs.csv` in duy project dir
- All outputs go to `data/outputs/`
- Python for automation — never N8N, Make, Zapier

## File Hygiene — áp dụng mọi project

**Xóa ngay trong session, không để tích lũy:**
- Script thất bại → xóa ngay khi có working replacement
- Helper/temp script chỉ dùng 1 lần → xóa ngay sau khi chạy xong
- Output file bị superseded (markdown → Excel, v1 → v2) → xóa phiên bản cũ
- `__pycache__/`, `.pyc`, temp files → luôn xóa trước khi kết thúc session

**Cấu trúc thư mục chuẩn cho mọi project có scripts:**
```
project/
├── [main-output]              ← file output cuối cùng (Excel, PDF, report)
├── scripts/                   ← tất cả Python generators/scripts
└── references/                ← source documents (scope, Q&A, spec)
```
File mới luôn vào đúng thư mục — không để ở root.

**Quy tắc đặt tên script:**
- Script chính: `build_[feature].py`
- Script bổ sung: `add_[feature]_[range].py` (vd: `add_sheets_21_22.py`)
- KHÔNG dùng: `append_partN.py`, `export_v2.py`, `fix_temp.py` — đây là dấu hiệu của failed iteration chưa được dọn

**Trước khi kết thúc session có viết scripts:**
1. List tất cả files đã tạo trong session
2. Xóa files thất bại/temp/superseded
3. Chỉ giữ files cần thiết cho session sau

## Python Code Generation — áp dụng mọi project

- **Không inject Python source vào file có sẵn qua string** → viết file riêng
- **Validate trước khi save:** `ast.parse(code)` + `compile()` — không save file lỗi syntax
- **Không dùng Bash `-c` cho code > 3 dòng** → ghi file trước, chạy file
- **Verify path tồn tại trước khi chạy** — đặc biệt paths có Unicode/tiếng Việt
- **`get_column_letter(n)` thay vì `chr(64+n)`** cho openpyxl (breaks ở col > 26)
- **Grep uniqueness trước Edit tool** — `old_string` phải xuất hiện đúng 1 lần
