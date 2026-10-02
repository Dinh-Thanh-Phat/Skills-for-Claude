---
name: playwright-artifact-cleanup
description: Prevent disk overflow from Playwright test artifacts (screenshots, videos, traces, test-results). Use when setting up a new test project, after noticing disk usage growing, or when configuring playwright.config.ts artifact settings.
triggers:
  - "disk space / ổ đĩa đầy khi chạy test"
  - "playwright artifacts tích lũy"
  - "dọn dẹp test-results/"
  - "video/screenshot/trace chiếm nhiều dung lượng"
  - "configure playwright artifact retention"
scope: playwright, disk-management, test-infrastructure
---

# Playwright Artifact Cleanup

## Core Problem
Playwright mặc định lưu video, screenshot, trace cho MỌI test → disk tích lũy rất nhanh.

---

## Step 1: Config đúng ngay từ đầu (`playwright.config.ts`)

```ts
use: {
  // Chỉ giữ artifacts khi test FAIL
  video: 'retain-on-failure',       // KHÔNG dùng 'on'
  screenshot: 'only-on-failure',    // KHÔNG dùng 'on'
  trace: 'retain-on-failure',       // KHÔNG dùng 'on' hoặc 'always'
},

// Trỏ output ra ngoài project dir (tránh tích lũy trong repo)
outputDir: 'D:/HK8/Learning/DQ/test/test-results',
```

### Mức độ artifact theo môi trường:

| Môi trường | video | screenshot | trace |
|---|---|---|---|
| Local dev | `retain-on-failure` | `only-on-failure` | `retain-on-failure` |
| CI | `off` | `only-on-failure` | `on-first-retry` (or `retain-on-first-failure`, v1.44+) |
| Debug | `on` | `on` | `on` |

---

## Step 2: Cleanup script sau mỗi run

Tạo file `scripts/cleanup-artifacts.ps1`:

```powershell
# Xóa artifacts cũ hơn N ngày
$outputDir = "D:\HK8\Learning\DQ\test\test-results"
$keepDays = 3

if (Test-Path $outputDir) {
    Get-ChildItem $outputDir -Recurse |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$keepDays) } |
        Remove-Item -Recurse -Force
    Write-Host "Cleaned artifacts older than $keepDays days"
}
```

---

## Step 3: npm script tiện dụng (`package.json`)

```json
{
  "scripts": {
    "test": "playwright test",
    "test:clean": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/cleanup-artifacts.ps1 && playwright test",
    "clean:artifacts": "rimraf test-results/ && rimraf playwright-report/"
  }
}
```

---

## Step 4: .gitignore (tránh commit artifacts)

```gitignore
test-results/
playwright-report/
*.webm
*.zip
```

---

## Checklist khi setup project mới

- [ ] `video`, `screenshot`, `trace` đều là `retain-on-failure` (không phải `on`)
- [ ] `outputDir` trỏ ra ngoài project dir (`D:/HK8/Learning/DQ/test/`)
- [ ] `test-results/` và `playwright-report/` trong `.gitignore`
- [ ] Có script cleanup artifacts cũ

---

## Dấu hiệu cần cleanup ngay

- `test-results/` > 500MB
- Có video của tests đã pass (lãng phí)
- Disk C: hoặc D: báo đầy sau khi chạy test suite lớn
