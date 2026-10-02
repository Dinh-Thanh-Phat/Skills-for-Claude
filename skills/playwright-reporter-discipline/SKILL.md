---
name: playwright-reporter-discipline
description: Rules cho Playwright reporters — tránh CLI flag override config, đảm bảo results.json được ghi đúng
triggers:
  - chạy npx playwright test
  - kết quả test để update sheet/report
  - results.json không được ghi
  - --reporter flag trên CLI
scope: Playwright test runs + automation scripts đọc kết quả test
---

# Playwright Reporter Discipline — Rules

## Vấn đề cốt lõi

`--reporter` trên CLI OVERRIDE toàn bộ reporters trong `playwright.config.ts`.

```bash
# ❌ SAI — chỉ output JSON ra stdout, results.json KHÔNG được ghi
npx playwright test tests/cms/ --reporter=json

# ✅ ĐÚNG — dùng config reporters (list + html + json file)
npx playwright test tests/cms/
```

## Hành vi của Playwright reporters

```
playwright.config.ts:
  reporter: [
    ['list'],                                              # console output
    ['html', { outputFolder: 'test-results/html-report' }],
    ['json', { outputFile: 'test-results/results.json' }], # file output
  ]

CLI --reporter=json → REPLACES cả 3 reporters trên bằng json → stdout
                    → results.json KHÔNG được ghi (outputFile trong config bị bỏ qua)
                    → output file từ background task bị truncate nếu quá lớn
```

## Khi nào cần --reporter trên CLI

Chỉ dùng khi KHÔNG có config sẵn, hoặc muốn thêm reporter mà KHÔNG thay thế:

```bash
# Xem live output khi CI không hiển thị
npx playwright test --reporter=list  # NHƯNG mất file reporters

# ✅ Thêm reporter BỔ SUNG, GIỮ reporters trong config (Playwright 1.63+)
npx playwright test tests/cms/ --add-reporter=list
npx playwright test --add-reporter=./my-ci-reporter.ts   # path tới custom reporter, comma-separated được

# Nếu BUỘC phải dùng --reporter=json → set env để ghi ra file thay vì stdout
# bash:
PLAYWRIGHT_JSON_OUTPUT_NAME=results.json npx playwright test --reporter=json
# PowerShell:
$env:PLAYWRIGHT_JSON_OUTPUT_NAME="results.json"; npx playwright test --reporter=json
# (PLAYWRIGHT_JSON_OUTPUT_DIR chọn thư mục; mặc định cwd/config dir)
```

> Trước 1.63 không có `--add-reporter` — với project pin version cũ thì vẫn phải sửa config hoặc dùng env var. Kiểm tra `npx playwright --version` trước.

## Protocol trước mỗi test run

### Bước 1 — Xác định reporters trong config
```bash
grep -A5 "reporter" playwright.config.ts
```

### Bước 2 — Chạy KHÔNG có --reporter flag
```bash
# ✅ Dùng config mặc định
npx playwright test tests/cms/

# Kết quả: list reporter → console, json reporter → results.json
```

### Bước 3 — Verify results.json sau khi chạy
```python
import json
data = json.load(open('test-results/results.json'))
s = data['stats']
total = s['expected'] + s['unexpected'] + s['skipped'] + s['flaky']
print(f"PASS={s['expected']} FAIL={s['unexpected']} SKIP={s['skipped']} FLAKY={s['flaky']} TOTAL={total}")

# Red flag: total == skipped và duration < 5 phút → auth setup failed
if s['expected'] == 0 and s['skipped'] > 100:
    print("⚠️ WARNING: Có thể auth setup failed — tất cả tests bị skip!")
```

### Bước 4 — Sanity check trước khi update sheet
```
Expected total ≈ số tests từ --list
Expected duration > 5 phút cho bộ 300+ tests
expected (PASS) > 0
```

## Dấu hiệu nhận biết vấn đề

| Symptom | Nguyên nhân | Fix |
|---------|-------------|-----|
| All tests skipped, duration < 3 phút | Auth setup failed | Chạy global.setup.ts riêng để debug |
| results.json không đổi sau khi chạy | Dùng --reporter=json CLI | Bỏ flag, chạy lại |
| results.json chỉ có `"skipped": N` | Setup failed hoặc --reporter override | Kiểm tra auth, bỏ CLI flag |

## Debug auth setup riêng

```bash
# Chạy setup riêng để kiểm tra
npx playwright test tests/cms/global.setup.ts --reporter=list

# Nếu pass → auth OK, vấn đề khác
# Nếu fail → fix auth trước
```

## Blob Reporter Cho Sharding (Playwright 1.37+)

```bash
# Mỗi shard ghi 1 blob
npx playwright test --shard=1/3 --reporter=blob
npx playwright test --shard=2/3 --reporter=blob
npx playwright test --shard=3/3 --reporter=blob

# Sau đó merge thành HTML + JSON
# ⚠️ json reporter qua CLI in ra stdout → set env để ghi file
PLAYWRIGHT_JSON_OUTPUT_NAME=results.json npx playwright merge-reports --reporter html,json ./blob-report
```

`blob-report/` upload làm CI artifact; merge step tải về gộp lại.

## Checklist trước mỗi lần chạy test để lấy kết quả

- [ ] Bỏ `--reporter` flag trên CLI — dùng config mặc định (cần thêm reporter → `--add-reporter`, Playwright 1.63+)
- [ ] Chạy: `npx playwright test tests/cms/` (không có flag thêm)
- [ ] Sau khi xong: verify `results.json` có `expected > 0`
- [ ] Nếu `expected == 0` và `duration < 5 phút` → auth failed, chạy setup riêng
- [ ] Chỉ sau khi verify results.json hợp lệ mới chạy script update sheet
- [ ] Sharding CI: dùng `--reporter=blob` per shard + `merge-reports` step cuối
