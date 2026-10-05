---
name: qa-session-close
description: Tổng kết session test và tạo handoff note để session tiếp theo pick up đúng chỗ. Trigger khi user nói "done", "xong hôm nay", "kết thúc", "tổng kết", "hôm nay test được gì", "wrap up".
tags: [qa, session-management, handoff, beads, context-recovery]
---

# QA Session Close — Tổng Kết Session Test

> **Counterpart:** `qa-session-start` — skill ngược lại, dùng để pickup context khi bắt đầu session mới.

Skill này tổng kết đúng cách khi kết thúc một session test — đảm bảo context không bị mất và session tiếp theo có thể pickup ngay mà không cần re-investigate từ đầu.

---

## Khi nào trigger

- User nói "done", "xong hôm nay", "kết thúc", "tổng kết", "hôm nay test được gì"
- Trước khi user đóng máy / nghỉ giữa test cycle
- Sau khi chạy xong một batch test và có kết quả
- Khi chuyển sang test feature/project khác

---

## Quy trình thực hiện

### Bước 1 — Thu thập dữ liệu session

**1a. Spec files đã chạy** — scan conversation history hoặc hỏi user:
```
Spec files nào đã chạy trong session này?
(VD: tests/cms/create-card.spec.ts, tests/cms/edit-card.spec.ts)
```

**1b. Kết quả từ results.json** — nếu có Playwright results:
```
Đọc: [project]/test-results/results.json
      [project]/playwright-report/results.json
→ Lấy: passed / failed / skipped counts
```

**1c. Bug IDs đã log** — scan conversation để tìm BUG-XX IDs và Odoo task IDs.

**1d. Beads issues liên quan:**
```bash
bd list --status=in_progress  # issues đang làm dở
```

---

### Bước 2 — Tạo Session Summary (tối đa 30 dòng)

```markdown
## QA Session Summary — [DATE]

**Project:** [Incard CMS / Inapps / HVS / The Client Book / ...]
**Feature:** [tên feature / module]
**Tester:** QA

---

### Đã test

| Behavior | Result | Note |
|---|---|---|
| [hành vi 1] | ✅ PASS | |
| [hành vi 2] | ❌ FAIL | BUG-XX |
| [hành vi 3] | ⏭ SKIP | [lý do] |

**Spec files:** `[path/spec1.spec.ts]`, `[path/spec2.spec.ts]`
**Kết quả:** X passed / Y failed / Z skipped

---

### Bugs tìm được

| ID | Mô tả | Severity | Odoo Task |
|---|---|---|---|
| BUG-XX | [mô tả ngắn] | P[0-4] | #[odoo-id] |

---

### Coverage delta

- **Trước session:** X behaviors covered / Y total
- **Sau session:** X+N behaviors covered / Y total
- **Tăng thêm:** +N behaviors

---

### Chưa test (còn lại)

- [ ] [behavior/scenario 1]
- [ ] [behavior/scenario 2]

---

### Blockers

- [env issue, missing data, feature chưa deploy, etc.]
- Không có blocker (nếu sạch)

---

### Resume

```
# Web (Playwright)
npx playwright test [spec-file] --grep "[test name pattern]"
# Mobile (Maestro)
maestro test [flows/path/flow.yaml]            # hoặc: maestro test [flows/dir] --include-tags [tag]
```

**Next priority:**
1. [việc quan trọng nhất]
2. [việc tiếp theo]
```

---

### Bước 3 — Cập nhật Beads

**3a. Close issues đã hoàn thành:**
```bash
bd close <id> --reason "Tested: X passed, Y failed. BUG-XX → Odoo #task-id"
```

**3b. Tạo issue cho unfinished work:**
```bash
bd create --title="[Project] Test [feature]: remaining scenarios" \
  --description="Unfinished from session [DATE]. Resume: npx playwright test [spec] --grep '[pattern]'" \
  --type=task --priority=2
```

**3c. Tạo issue cho bugs cần track:**
```bash
bd create --title="[Project] BUG-XX: [mô tả ngắn]" \
  --description="Odoo #[task-id]. Found [DATE]. Severity P[N]." \
  --type=bug --priority=1
```

**3d. Push:**
```bash
bd dolt push
git pull --rebase && git push   # CLAUDE.md: session chưa xong khi git push chưa thành công
```

**3e. Cập nhật project knowledge** (để `qa-session-start` Bước 0 đọc được trạng thái mới):

Sửa `~/.claude/shared-context/knowledge/<slug>.md` (slug theo bảng trong `qa-session-start`):
```markdown
**Last session:** [DATE] — [1 câu: đã test gì, kết quả X pass / Y fail]
**Left off at:** [trạng thái / spec hoặc flow đang dở]
**Next step:** [việc quan trọng nhất tiếp theo + resume command]
```
Sửa tại chỗ các dòng này (không append bản trùng). Project chưa có file knowledge → báo user.

---

### Bước 4 — Beads-ready handoff (1 liner để paste vào note)

```
Session [DATE] | [Project] | [Feature]
Tested: X pass / Y fail / Z skip | Bugs: BUG-XX (P1), BUG-YY (P3)
Coverage: +N behaviors (X/Y total) | Remaining: N scenarios
Resume: npx playwright test [spec] --grep "[pattern]"   (mobile: maestro test [flow.yaml])
Next: [1 câu mô tả việc quan trọng nhất]
```

---

## Rules bắt buộc

1. **Resume command là bắt buộc** — không có = handoff note không hợp lệ
2. **Không bỏ qua beads** — luôn tạo issues cho unfinished work trước khi đóng session
3. **Bug severity phải rõ** — luôn có P-level, không ghi chung chung "bug found"
4. **Coverage delta phải đo được** — "4/7 scenarios" tốt hơn "một số scenarios"
5. **Blockers phải cụ thể** — "thiếu viewer account để test permission scenarios"

---

## Cross-references

- **qa-bug-report** — viết full bug report cho mỗi bug tìm được trong session
- **beads** — tạo/update/close issues sau session
- **behavioral-coverage-matrix** — tính coverage delta nếu cần chi tiết
- **test-rerun-discipline** — khi resume, dùng `--last-failed` trước khi full run
