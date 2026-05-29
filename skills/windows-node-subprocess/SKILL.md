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

Trên Windows, `npx`, `npm`, `node` là các `.cmd` script (batch files), không phải executables.

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
import sys, subprocess

def node_cmd(cmd: str | list, **kwargs):
    """Run npx/npm/node cross-platform."""
    if isinstance(cmd, list):
        if sys.platform == 'win32':
            cmd[0] = cmd[0] + '.cmd'
        return subprocess.run(cmd, **kwargs)
    else:
        # String command: dùng shell=True
        return subprocess.run(cmd, shell=True, **kwargs)
```

### 2. Khi nào dùng shell=True vs npx.cmd

| Scenario | Cách dùng |
|----------|-----------|
| Command đơn giản (không pipe) | `['npx.cmd', ...]` — an toàn hơn |
| Command có pipe hoặc redirect | `shell=True` — cần thiết |
| User input trong command | Tuyệt đối KHÔNG dùng shell=True — injection risk |

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
- [ ] Command có user input không? → Nếu có: KHÔNG dùng shell=True
- [ ] Có kiểm tra `returncode` không?
- [ ] Output cần từ stdout hay stderr? (npx thường in lên stderr)
- [ ] Output có ký tự non-ASCII? → set `encoding='utf-8', errors='replace'` + `PYTHONUTF8=1`
- [ ] Script chạy ngầm (CI/scheduled)? → `creationflags=CREATE_NO_WINDOW`
