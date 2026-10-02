---
name: python-code-gen-safety
description: Safety rules for generating and modifying Python files — prevents syntax injection errors, unicode path failures, Edit tool ambiguity, and Bash -c overflow. Invoke whenever generating, appending, or patching Python scripts.
triggers:
  - generating a Python script
  - appending code to an existing .py file
  - patching / modifying a Python file
  - using Edit tool on a .py file
  - running a Python script via Bash
scope: global
---

# Python Code Generation Safety Rules

You are generating Python code. Follow ALL rules below — they exist because each was violated and caused real failures.

---

## RULE 1 — Never inject Python source into an existing file via string manipulation

**Violation pattern (FORBIDDEN):**
```python
# Writing Python source code inside a triple-quoted string then appending to a file
new_code = """
def my_func():
    cases.append(tc(
        'ID', 'Module',
        'Description with \n in it',   # ← single \n becomes a REAL newline in new_code
                                       #   (writing \\n would be safe — easy to get wrong)
        ...
    ))
"""
with open('target.py', 'a') as f:
    f.write(new_code)
```

**Why it fails:** `\n` inside a triple-quoted string literal becomes an actual newline character. When written into a Python source file, any string like `'step 1\n2. step 2'` becomes a multi-line unterminated string literal → `SyntaxError`.

**Correct pattern:** Write new functions to a **separate new file**. Import from it or run it standalone.
```python
# Good: add_new_features.py — a standalone script that does its own thing
# Never merge new function definitions into existing files via string injection
```

---

## RULE 2 — Always validate Python syntax before saving

Before writing any generated Python source to disk:

```python
import ast

generated_code = "..."  # your generated source

try:
    ast.parse(generated_code)
except SyntaxError as e:
    print(f"[SYNTAX ERROR] Line {e.lineno}: {e.msg}")
    print(f"  Offending text: {e.text}")
    raise  # Do NOT save a broken file
```

Run `ast.parse()` + `compile()` for full validation:
```python
try:
    tree = ast.parse(generated_code)
    compile(tree, '<string>', 'exec')
    print("[OK] Syntax valid")
except (SyntaxError, ValueError) as e:
    print(f"[ERROR] {e}")
```

---

## RULE 3 — Never pass long Python code via Bash `-c`

**Forbidden:**
```bash
python -c "
def foo():
    ...  # 30+ lines of code
"
```

**Why it fails:** OS has a command-line length limit (cmd.exe ~8 KB, CreateProcess ~32 K chars on Windows). Long code → `[WinError 206] The filename or extension is too long` (Windows) / `E2BIG` (POSIX), plus shell quoting mangles quotes and `$`.

**Rule:** If code is > 3 lines, write it to a `.py` file first, then run the file:
```bash
# Write first
python write_script.py   # generates output_script.py

# Then run
python output_script.py
```

---

## RULE 4 — Verify file paths before running (especially non-ASCII / Vietnamese)

Vietnamese folder names like `The Client Bọok` contain Unicode characters (`ọ` = U+1ECD). Copy-paste errors silently drop or mangle these.

**Always verify:**
```python
import os
path = r'D:\HK8\Learning\DQ\The Client Bọok\output.xlsx'
assert os.path.exists(os.path.dirname(path)), f"Directory not found: {os.path.dirname(path)}"
```

**In Bash, always quote paths:**
```bash
python "D:\path with spaces\script.py"
```

**Before hardcoding a path in a script, verify the directory exists:**
```python
import os
dir_path = os.path.dirname(output_path)
if not os.path.isdir(dir_path):
    raise FileNotFoundError(f"Output directory does not exist: {dir_path}")
```

---

## RULE 5 — Grep for uniqueness before using Edit tool on Python files

The Edit tool requires `old_string` to be **unique** in the file.

**Before every Edit call:**
```bash
# Count occurrences of the string you plan to replace
grep -c "return cases" target.py
# If count > 1, include more surrounding context to make it unique
```

If the string appears multiple times, either:
- Include 3–5 lines of surrounding context to make it unique
- Use `replace_all=true` if you intend to replace all occurrences
- Write a Python script to do the targeted replacement instead

---

## RULE 6 — Use `get_column_letter()` for openpyxl column indices

**Forbidden:**
```python
ws.column_dimensions[chr(64 + col_idx)].width = width
# Breaks when col_idx > 26 (chr(64+27) = '[' — not a valid column letter)
```

**Correct:**
```python
from openpyxl.utils import get_column_letter
ws.column_dimensions[get_column_letter(col_idx)].width = width
```

---

## RULE 7 — Prefer standalone scripts over patching existing files

When you need to **extend** an existing Python codebase (add new functions, new data):

| Need | Do This |
|---|---|
| Add new sheet functions | Write `add_sheet_XY.py` — standalone script that imports the workbook and adds sheets |
| Add new test case data | Add to a separate `cases_extra.py`, import from main |
| Fix a bug in one function | Use Edit tool with sufficient context for uniqueness |
| Restructure the whole file | Read → generate new content → Write (full rewrite) |

**Never:** append raw Python source code strings to an existing `.py` file.

---

## RULE 8 — Verify Dependencies Installed Before Running

```python
import importlib.util, sys
# pip distribution name → import name (they often differ: pdfminer.six → pdfminer,
# python-docx → docx, Pillow → PIL, opencv-python → cv2). Never derive one from the other.
REQUIRED = {'openpyxl': 'openpyxl', 'pandas': 'pandas', 'pdfminer.six': 'pdfminer'}

def check_deps():
    missing = [dist for dist, mod in REQUIRED.items()
               if importlib.util.find_spec(mod) is None]
    if missing:
        print(f"Missing deps: {missing}\nRun: pip install {' '.join(missing)}")
        sys.exit(1)

check_deps()
```

## RULE 9 — Shell Injection Through Subprocess

Cross-ref `windows-node-subprocess`: never pass user-controlled strings via `shell=True`.

```python
# ❌ DANGEROUS — user input
subprocess.run(f"npx test {user_input}", shell=True)

# ✅ Pass as list (no shell interpretation)
subprocess.run(['npx', 'test', user_input])      # POSIX
subprocess.run(['npx.cmd', 'test', user_input])  # Windows
```

## Pre-flight Checklist (run before saving any generated Python file)

```
[ ] ast.parse() passes with no SyntaxError
[ ] compile() passes with no SyntaxError  
[ ] All file paths verified: os.path.isdir(dirname) == True
[ ] No chr(64 + n) for openpyxl — use get_column_letter(n)
[ ] Code not passed via Bash -c (unless < 3 lines)
[ ] Edit tool: old_string appears exactly once in file (grep first)
[ ] Non-ASCII characters in paths double-checked character by character
```
