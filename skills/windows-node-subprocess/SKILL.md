---
name: windows-node-subprocess
description: Gọi npx/npm/node từ Python subprocess trên Windows — tránh FileNotFoundError
triggers:
  - subprocess.run với npx
  - subprocess.run với npm
  - FileNotFoundError khi gọi node commands từ Python
  - Python script chạy CLI tools trên Windows
scope: Python scripts chạy Node.js commands trên Windows
---

# Windows Node Subprocess — Rules

## Vấn đề

Trên Windows, `npx`, `npm` là các `.cmd` script (batch files), không phải executables — `subprocess` (shell=False) chỉ tự thêm `.exe`, nên `['npx', ...]` → FileNotFoundError. Riêng `node` là `node.exe` thật (không có `node.cmd`).

```python
# ❌ FAIL trên Windows — FileNotFoundError
subprocess.run(['npx', 'playwright', 'test', '--list'], ...)

# ✅ ĐÚNG — cách 1: shell=True
subprocess.run('npx playwright test --list', shell=True, ...)

# ✅ ĐÚNG — cách 2: explicit .cmd
subprocess.run(['npx.cmd', 'playwright', 'test', '--list'], ...)
```

## Quy tắc

### 1. Detect platform trước
```python
import shutil, subprocess

def node_cmd(cmd: str | list, **kwargs):
    """Run npx/npm/node cross-platform."""
    if isinstance(cmd, list):
        cmd = list(cmd)  # don't mutate the caller's list
        # shutil.which honours PATHEXT: 'npx' → '...\\npx.CMD', 'node' → '...\\node.EXE'
        # (blindly appending '.cmd' turns 'node' into a non-existent 'node.cmd')
        resolved = shutil.which(cmd[0])
        if resolved is None:
            raise FileNotFoundError(f"{cmd[0]} not found on PATH")
        cmd[0] = resolved
        return subprocess.run(cmd, **kwargs)
    else:
        # String command: dùng shell=True
        return subprocess.run(cmd, shell=True, **kwargs)
```

### 2. Khi nào dùng shell=True vs npx.cmd

| Scenario | Cách dùng |
|----------|-----------|
| Command đơn giản (không pipe), args cố định | `[shutil.which('npx'), ...]` hoặc `['npx.cmd', ...]` |
| Command có pipe hoặc redirect | `shell=True` — cần thiết |
| User/external input trong args | ⚠️ List KHÔNG an toàn với `.cmd`/`.bat` — xem dưới |

> **`.cmd` luôn chạy qua cmd.exe, kể cả khi truyền list.** Python docs: batch files "may be
> launched by the operating system in a system shell regardless of the arguments passed …
> without any escaping added by Python" (gh-114539, lớp lỗi "BatBadBut"). Vì vậy
> `['npx.cmd', 'test', user_input]` vẫn bị cmd.exe injection. Cách đúng:
> 1. Validate input bằng allow-list chặt (vd `^[\w./:@-]+$`) trước khi đưa vào bất kỳ `.cmd` nào.
> 2. Ưu tiên gọi thẳng `node.exe` + file JS của CLI: `['node', r'<project>\node_modules\@playwright\test\cli.js', 'test', arg]` — không qua cmd.exe.
> 3. Nếu bắt buộc chạy `.cmd` với input ngoài, Python docs gợi ý `shell=True` để Python escape ký tự đặc biệt — vẫn phải validate.

### 3. Luôn set cwd

```python
result = subprocess.run(
    'npx playwright test tests/cms/ --list',
    capture_output=True,
    text=True,
    cwd=r'D:\path\to\project',  # PHẢI có
    shell=True,
)
```

### 4. Kiểm tra kết quả

```python
if result.returncode != 0:
    print(f"STDERR: {result.stderr[:500]}")
    raise RuntimeError(f"Command failed: {result.returncode}")

output = result.stdout + result.stderr  # npx thường print lên stderr
```

## UTF-8 Encoding cho Output Tiếng Việt / Emoji

```python
import os
env = os.environ.copy()
env['PYTHONUTF8'] = '1'
env['PYTHONIOENCODING'] = 'utf-8'

result = subprocess.run(
    'npx playwright test', shell=True, capture_output=True,
    encoding='utf-8', errors='replace',   # ← bắt buộc nếu output có tiếng Việt
    env=env, cwd=PROJECT_DIR
)
```

## `CREATE_NO_WINDOW` — Ẩn Console Khi Chạy Ngầm

```python
import sys
flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
subprocess.run('npx playwright test', shell=True, creationflags=flags)
```

## Checklist trước khi viết subprocess

- [ ] Có `cwd=PROJECT_DIR` không?
- [ ] Trên Windows: dùng `shell=True` hoặc `npx.cmd`?
- [ ] Command có user/external input không? → Validate allow-list; ưu tiên `node.exe cli.js` thay vì `.cmd` (list KHÔNG chống injection với `.cmd`)
- [ ] Có kiểm tra `returncode` không?
- [ ] Output cần từ stdout hay stderr? (npx thường in lên stderr)
- [ ] Output có ký tự non-ASCII? → set `encoding='utf-8', errors='replace'` + `PYTHONUTF8=1`
- [ ] Script chạy ngầm (CI/scheduled)? → `creationflags=CREATE_NO_WINDOW`
