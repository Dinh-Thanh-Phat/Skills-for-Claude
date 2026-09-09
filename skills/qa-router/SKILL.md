---
name: qa-router
description: Entry point cho mọi task QA — enforce routing rules và invoke đúng skill theo đúng thứ tự. PHẢI invoke trước khi làm bất kỳ task QA nào. Triggers on: "viết test", "test cases", "chạy test", "run test", "debug test", "test fail", "tại sao fail", "coverage", "gap coverage", "bug report", "log bug", "xong hôm nay", "kết thúc session", "test mobile", "maestro", "test feature", "generate test", "viết automation", "fix test", "test này fail".
tags: [qa, routing, orchestration, entry-point]
triggers:
  - "viết test"
  - "test cases"
  - "chạy test"
  - "run test"
  - "debug test"
  - "test fail"
  - "tại sao fail"
  - "coverage"
  - "gap coverage"
  - "bug report"
  - "log bug"
  - "xong hôm nay"
  - "kết thúc session"
  - "test mobile"
  - "maestro"
  - "generate test"
  - "viết automation"
  - "fix test"
  - "đánh giá UX"
  - "đánh giá trải nghiệm"
  - "workflow ổn không"
  - "feature bất tiện"
  - "usability review"
  - "chạy full case"
  - "full cases"
  - "test full"
  - "full flow"
---

# QA Router — Entry Point cho Mọi Task QA

> **Mục đích:** Skill dành cho Claude, không phải user. Enforce rules từ memory và đảm bảo Claude invoke đúng skill theo đúng thứ tự.

---

## CRITICAL RULES — Enforce trước khi làm gì

| Rule | Enforcement |
|---|---|
| Figma/screenshot đi kèm → `qa-test-coverage-max` TRƯỚC | Hard block |
| "Coverage > 90%" → `behavioral-coverage-matrix` định nghĩa trước | Hard block |
| Test fail/debug → `playwright-diagnosis-first` TRƯỚC, code sau | Hard block |
| Viết test cases → Manual TRƯỚC, đợi confirm, automation sau | Hard block |
| 1-2 lần fail bất kỳ → DỪNG, invoke `ask-when-stuck` | Hard block |
| Trước khi chạy test → `qa-preflight` TRƯỚC | Hard block |
| Claim "X gây Y" / gán severity / log bug → `bug-repro-isolation` (cô lập 1 biến) TRƯỚC | Hard block |
| Viết bộ test cases từ spec/PRD → theo `qa-excel-export/references/deliverable-format.md` | Hard block |
| Xuất Excel test cases → **MỖI MODULE 1 SHEET**, 14 cột, parse từ markdown (không gõ tay 2 lần) | Hard block |
| User nói "full case(s)"/"test full"/"full flow" — **cho MỌI hình thức test, kể cả manual/exploratory trên device thật, không chỉ automation code** — → PHẢI build behavior inventory + 8-category matrix (POS/NEG/EDGE/SEC/A11Y/BOUNDARY/STATE/ERROR) làm checklist TRƯỚC KHI chạy case đầu tiên, và KHÔNG được report/dừng lại cho tới khi mọi dòng trong checklist có status PASS/FAIL/BLOCKED (kèm lý do) — không được tự ý dừng giữa chừng rồi liệt kê phần còn thiếu như "gap" sau khi đã báo "xong" | Hard block |

**"Hard block"** = không được skip dù user không mention, dù request có vẻ đơn giản.

> **Recurring failure đã xảy ra nhiều lần (xem `[[feedback_automation-must-cover-all-cases-not-happy-path]]`):**
> user nói "chạy full cases" → Claude tự làm một lượt walkthrough thủ công vài case dễ thấy nhất rồi
> report như xong, để lộ phần thiếu chỉ khi user hỏi lại "sao ít vậy". Đây là lỗi ÁP DỤNG lặp lại
> (đã có skill mà không dùng để tự chặn mình TRƯỚC khi báo cáo), không phải thiếu quy trình.
> Fix: liệt kê matrix TRƯỚC (kể cả khi giao cho subagent), rồi mới chạy — không đảo ngược thứ tự.

> **UX evaluation là FLOW RIÊNG — KHÔNG bám đuôi test run.** Chạy `ux-heuristic-evaluation`
> chỉ khi user yêu cầu đánh giá trải nghiệm/workflow (xem nhánh "Đánh giá UX" bên dưới).
> KHÔNG tự append đánh giá UX vào mỗi lần chạy bộ test cases — tốn token/thời gian vô ích.
> Functional test và UX evaluation là 2 task tách biệt, chạy độc lập.

---

## Intake Step — Chạy đầu tiên khi thiếu context

Trước khi route, kiểm tra xem đã có đủ 4 thông tin này chưa:

| Info | Cần biết để làm gì |
|---|---|
| **Project** | Biết đường dẫn, URL staging, test file location |
| **Feature/module** | Biết scope cần test |
| **Artifacts** | Figma / scope doc / bug report → quyết định skill nào đầu tiên |
| **Mục tiêu** | Viết test / chạy test / debug / coverage check |

**Nếu thiếu bất kỳ thông tin nào** → hỏi gộp 1 lần duy nhất trước khi làm gì:

```
Trước khi bắt đầu, tôi cần biết thêm:

1. Project: Incard CMS / Inapps / HVS / The Client Book / khác?
2. Feature/module đang test là gì?
3. Có Figma, scope doc, hay screenshot nào không?
4. Mục tiêu: viết test cases / chạy test / debug fail / check coverage?

(Cái nào đã rõ thì bỏ qua)
```

**Không hỏi nếu** user đã cung cấp đủ — ví dụ "viết test cho Create Card ở Incard CMS, có Figma đây" → đủ rồi, route thẳng.

---

## Decision Tree

### "Viết / generate test cases"

```
User nói: "viết test cases", "test cases cho X", "generate tests"
                    ↓
          Có Figma hoặc screenshot?
         /                        \
        YES                        NO
         ↓                          ↓
  qa-test-coverage-max      behavioral-coverage-matrix
         ↓                          ↓
              qa-test-generation (viết MANUAL test cases)
                    ↓
    Output THEO CHUẨN: qa-excel-export/references/deliverable-format.md
    README + 00_COVERAGE_MATRIX + NN_<module>.md + 99_OPEN_ITEMS + export script
                    ↓
         qa-excel-export (MỖI MODULE 1 SHEET, parse từ markdown)
                    ↓
         ⛔ DỪNG — Present manual test cases
         "Bạn review xong thì mình mới viết automation"
                    ↓
         Chờ user confirm "ok viết automation"
                    ↓
              qa-e2e-complete (viết Playwright code)
```

> **Chuẩn deliverable là mặc định, không phải tuỳ chọn.** User đã xác nhận format này
> (TetherTails, 697 cases, 05-08-2026). Không hỏi lại "bạn muốn format nào".

### "Chạy test / run suite"

```
User nói: "chạy test", "run", "npx playwright test..."
                    ↓
             qa-preflight (check env trước)
                    ↓
         Env ok? → playwright-test-workflow
         Env vấn đề? → Báo user, fix env trước
```

### "Debug / test fail"

```
User nói: "test fail", "tại sao fail", "fix test", "debug"
                    ↓
        playwright-diagnosis-first (screenshot/trace trước)
                    ↓
         Fail lần 1-2 vẫn chưa rõ?
                    ↓
              ask-when-stuck (hỏi user ngay)
         KHÔNG tự code thêm lần 3
```

### "Coverage"

```
User nói: "coverage còn thiếu gì", "coverage gap", "coverage > X%"
                    ↓
         behavioral-coverage-matrix (inventory trước)
                    ↓
         Report gap → qa-test-generation (nếu cần viết thêm)
```

### "Bug report"

```
User nói: "viết bug report", "log bug", "tìm ra bug"
                    ↓
   bug-repro-isolation (cô lập 1 biến → xác nhận NGUYÊN NHÂN, không chỉ triệu chứng)
                    ↓
              qa-bug-report (viết report với minimal repro + control đã chạy)
                    ↓
         Hỏi: "Log lên Odoo luôn không?"
                    ↓
         YES → odoo-project-automation
```

> **Mọi causal claim ("làm X gây Y") + mọi lần gán severity → `bug-repro-isolation` TRƯỚC.**
> Đặc biệt nếu repro có reload/điều hướng/đăng nhập lại lẫn với hành động đang test —
> đừng đổ lỗi cho hành động khi một thay đổi môi trường mới là thủ phạm (bài học sự cố
> "Back xoá data" = thực ra reload không re-hydrate form). Hard block.

### "Kết thúc session"

```
User nói: "xong", "done", "kết thúc", "hôm nay test được gì"
                    ↓
              qa-session-close (summary + handoff)
                    ↓
              beads (create/close issues)
```

### "State change / test tạo data"

```
Test có create/update/delete dữ liệu thật?
                    ↓
         state-ripple-verify (check ripple sang modules khác)
                    ↓
         test-data-lifecycle (đảm bảo cleanup strategy)
                    ↓
         qa-e2e-complete (viết cross-module assertions)
```

### "Mobile testing"

```
User nói: "test mobile", "maestro", "test app"
                    ↓
         qa-preflight (device check trước)
                    ↓
    ⚠️ VERSION GATE — check TRƯỚC khi đổ lỗi cho test/app:
    Android targetSdk 36 / device API 36 → android-16-qa-gate
    iOS 26 + Xcode 26.x            → ios-26-test-gotchas
                    ↓
         maestro-mobile (viết/chạy flow)
```

> **Version gate là hard block khi có dấu hiệu.** Element-not-found sau khi update Xcode,
> hoặc "nội dung bị che status bar / back không chạy" sau khi bump targetSdk = lỗi PLATFORM,
> không phải lỗi locator. Sửa selector lần 3 là sai hướng — đọc skill version gate trước.

### "Đánh giá UX / trải nghiệm / workflow"

```
User nói: "đánh giá UX", "trải nghiệm thế nào", "workflow này ổn không",
          "feature chạy đúng nhưng bất tiện", "usability review", "too many steps"
                    ↓
              ux-heuristic-evaluation (Nielsen + severity + metrics)
                    ↓
         Report: friction points + severity 0-4 + đề xuất fix
```

### "Không biết bắt đầu"

```
User vague: "giúp tôi với QA", "không biết test gì"
                    ↓
              skill-discovery (show menu)
```

---

## Two-Phase Rule — Enforcement Cụ Thể

Khi user nói **"viết test"** mà không specify manual hay automation:

1. Luôn viết manual test cases trước — dạng bảng markdown, không phải code
2. Present và dừng lại:
   ```
   Đây là [N] manual test cases cho [feature].
   Bạn review xong thì mình mới viết automation (Playwright code).
   Có cần thêm/bớt scenario nào không?
   ```
3. Chờ user confirm — "ok", "triển", "viết automation đi"
4. Chỉ sau confirm → invoke `qa-e2e-complete`

---

## Ambiguity Resolution

Khi request không rõ, hỏi **1 câu** trước khi route:

| Ambiguous | Hỏi |
|---|---|
| "Test feature X" — viết hay chạy? | "Bạn muốn viết test cases hay chạy test luôn?" |
| "Fix test" — fail do env hay code? | "Test fail với error gì? Paste stack trace không?" |
| "Coverage" — đo hay tăng? | "Bạn muốn check coverage hiện tại hay viết test để tăng?" |

---

## Anti-patterns Claude phải tránh

| Anti-pattern | Đúng phải làm |
|---|---|
| Viết Playwright code ngay khi user nói "viết test" | Manual test cases trước, đợi confirm |
| Generate test cases không có behavior inventory | `behavioral-coverage-matrix` trước |
| Debug bằng cách edit code ngay | `playwright-diagnosis-first` → screenshot/trace trước |
| Chạy test không check env | `qa-preflight` trước |
| Thử locator lần 3+ | `ask-when-stuck` sau lần 2 |
| Tổng kết bằng cách nói "xong" | `qa-session-close` → beads |

---

## Cross-references (flow thường dùng)

- Viết test: `qa-router` → `behavioral-coverage-matrix` → `qa-test-generation` → `qa-e2e-complete`
- Chạy test: `qa-router` → `qa-preflight` → `playwright-test-workflow`
- Đánh giá UX (flow RIÊNG, chạy độc lập): `qa-router` → `ux-heuristic-evaluation` (feature đúng nhưng bất tiện)
- Debug: `qa-router` → `playwright-diagnosis-first` → `ask-when-stuck`
- Bug report: `qa-router` → `bug-repro-isolation` (cô lập nguyên nhân) → `qa-bug-report` → `odoo-project-automation`
- Close: `qa-router` → `qa-session-close` → `beads`
