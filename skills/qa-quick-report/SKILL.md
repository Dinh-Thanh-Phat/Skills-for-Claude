---
name: qa-quick-report
description: >-
  Show quick test results inline in Claude Code extension FIRST before any file output. Use when
  running automation tests, viewing test results, or exporting reports. Keywords: "chạy test",
  "run tests", "test results", "xuất report", "automation results", "kết quả test", "test
  report". Excel export ONLY when user explicitly asks ("xuất excel", "export excel", "tạo file
  excel").
---

# QA Quick Report Skill

You are a **Senior QA Engineer** showing test results clearly and efficiently.

## Core Rules

1. **Always show inline results FIRST** — before creating any file.
2. **Excel export ONLY when explicitly requested** — never auto-generate Excel files.

---

## Step 1: Parse Test Results — Read `results.json`, NOT stdout

```python
import json
data = json.load(open('test-results/results.json'))
s = data['stats']
total   = s['expected'] + s['unexpected'] + s['skipped'] + s['flaky']
passed  = s['expected']
failed  = s['unexpected']
flaky   = s.get('flaky', 0)
skipped = s['skipped']
duration_ms = data.get('duration', 0)
```

Extract:
- Total / Pass / Fail / **Flaky** / Skip counts (flaky = passed on retry — not the same as pass)
- Failed test names + file:line + error summary (first line only)
- Total duration
- **Comparison with previous run** if `test-results/results-prev.json` exists:
  - New failures (failed now, passed last time) → regression
  - Newly passing (failed last time, passed now) → fix landed
  - Newly flaky → investigate

---

## Step 2: Show Inline Quick Report (ALWAYS, IMMEDIATELY)

Output a formatted summary directly in chat — readable in the Claude Code extension:

```
## Test Results — [YYYY-MM-DD HH:mm]

| Metric      | Count |
|-------------|-------|
| Total       | X     |
| ✅ PASS     | Y     |
| ❌ FAIL     | Z     |
| ⏭️ SKIP    | N     |

**Pass Rate:** X% — [✅ ALL PASS / ❌ FAILURES DETECTED]
**Duration:** Xs

### ❌ Failed Tests
- `file.spec.ts:LINE` — Suite › Test name › error message (first line)
- `file.spec.ts:LINE` — Suite › Test name › error message (first line)

### Next Steps
- [if FAIL] Run `test-failure-triage` to batch categorize: test bugs vs system bugs
  - System bugs → `test.skip(true, 'reason')` + report to user
  - Test bugs → fix with `npx playwright test --last-failed`
- [if all PASS] Ready for release check with `qa-regression` skill
```

### Format rules

- Use markdown table (renders in Claude Code extension)
- Keep inline report under 50 lines — link to full log if verbose
- List FAILED tests: filename:line, suite path, first error line only
- Show ✅ ❌ ⏭️ emojis for fast visual scanning

---

## Step 3: Excel Export — ONLY IF EXPLICITLY REQUESTED

Only generate Excel files if the user says:
- "xuất excel" / "export excel"
- "tạo file excel" / "tạo excel report"
- "create excel file" / "generate excel report"

If requested, invoke `qa-excel-export` skill logic to create both files:
1. `test_cases_automation_[YYYYMMDD].xlsx`
2. `test_cases_manual_[YYYYMMDD].xlsx`

**Do NOT auto-generate Excel files.** The inline report is always enough unless Excel is asked for.

---

## Examples

### All Pass
```
## Test Results — 2026-04-18 10:30

| Metric   | Count |
|----------|-------|
| Total    | 45    |
| ✅ PASS  | 45    |
| ❌ FAIL  | 0     |
| ⏭️ SKIP | 0     |

**Pass Rate:** 100% — ✅ ALL PASS
**Duration:** 38s
```

### Has Failures
```
## Test Results — 2026-04-18 10:30

| Metric   | Count |
|----------|-------|
| Total    | 45    |
| ✅ PASS  | 42    |
| ❌ FAIL  | 3     |
| ⏭️ SKIP | 0     |

**Pass Rate:** 93.3% — ❌ FAILURES DETECTED
**Duration:** 41s

### ❌ Failed Tests
- `login.spec.ts:45` — LoginPage › valid credentials › expected 200 got 401
- `checkout.spec.ts:88` — Checkout › payment submit › timeout waiting for #confirm-btn
- `profile.spec.ts:12` — Profile › update name › element not found: .save-btn

### Next Steps
- Investigate with `qa-bug-report` skill or track with `bd create`
```
