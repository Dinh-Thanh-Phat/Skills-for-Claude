---
name: qa-session-start
description: Pull context từ session trước và orient Claude trước khi bắt đầu test. Trigger khi user nói "test tiếp", "tiếp tục", "hôm nay test gì", "làm tiếp", "resume", "session mới", "bắt đầu hôm nay", hoặc đầu session không có context rõ ràng.
tags: [qa, session-management, context-recovery, beads]
---

# QA Session Start — Context Recovery

Skill này pull context từ session trước để Claude không bắt đầu mù. Không cần user giải thích lại từ đầu.

---

## Khi nào trigger

- User nói "test tiếp", "tiếp tục từ hôm qua", "làm tiếp", "resume", "bắt đầu hôm nay"
- Đầu session mà user chưa nói project/feature cụ thể
- User nói "hôm nay test gì tiếp" hoặc tương tự
- **User mention tên project** mà không kèm đủ context — ví dụ: "HVS", "Incard CMS", "Inapps", "The Client Book", "NQ", "PT", "FE", "Agentic"

**Không trigger khi:** User đã cung cấp đủ context (project + feature + mục tiêu rõ ràng)

---

## Project Name → Knowledge Slug Map

> **Disambiguation — HVS:**
> "HVS" = Playwright E2E test project tại `D:\HK8\Learning\DQ\HVS` (stack: TypeScript + Playwright).
> KHÔNG phải Odoo project "HaiVan Ship". Khi user nói "HVS ticket", "HVS test", "HVS check..." → đây là project này, KHÔNG dùng `odoo-project-automation`.

| User mention | Knowledge file |
|---|---|
| HVS | `hvs.md` |
| Incard CMS, Incard | `incard-cms.md` |
| Incard OCMS | `incard-ocms.md` |
| Inapps, Inapps Web | `inapps-web.md` |
| The Client Book, Client Book, Olivia | `the-client-book.md` |
| NQ | `nq.md` |
| PT | `pt.md` |
| FE | `fe.md` |
| Agentic, Chatbot | `agentic-chatbot.md` |
| Agentic Social | `agentic-social.md` |
| Skills | `skills-automation.md` |
| TetherTails, TetherTails app | `tethertails.md` |
| TetherTails Portal | `tethertails-portal.md` |
| Soundwise | `soundwise.md` |

Knowledge dir: `C:\Users\wi\.claude\shared-context\knowledge\`

---

## Quy trình

### Bước 0 — Project name detected (trigger mới)

Nếu trigger là **user mention tên project** (không kèm context):

1. Lookup slug từ bảng trên
2. Đọc `C:\Users\wi\.claude\shared-context\knowledge\[slug].md`
3. Present nhanh:

```
## [Tên Project] — Context từ knowledge

**Stack:** [stack]
**Last session:** [date] — [mô tả ngắn]
**Left off at:** [trạng thái]
**Next step:** [việc tiếp theo]
**Pending work:** [nếu có]

---
Bạn đang muốn làm gì với [Project] hôm nay?
```

4. Chờ user nói mục tiêu → route qua `qa-router` nếu cần

---

### Bước 1 — Đọc beads in-progress issues

```bash
bd list --status=in_progress
```

Tìm issues liên quan đến QA/test. Nếu có → đó là context session trước để lại.

### Bước 2 — Đọc beads ready (unblocked work)

```bash
bd ready
```

Show issues sẵn sàng để pick up.

### Bước 3 — Parse handoff note

Trong issue description, tìm block format:

```
Session [DATE] | [Project] | [Feature]
Tested: X pass / Y fail / Z skip | Bugs: ...
Coverage: +N behaviors (X/Y total) | Remaining: N scenarios
Resume: npx playwright test [spec] --grep "[pattern]"
Next: [mô tả việc quan trọng nhất]
```

Nếu tìm thấy → extract resume command + next priority.

### Bước 4 — Present context cho user

```
## Context từ session trước

**Project:** [tên project]
**Feature đang test:** [tên feature]
**Trạng thái:** [X passed / Y failed / Z skipped]
**Bugs đã log:** [BUG-XX (PY), ...]

**Còn lại chưa test:**
- [scenario 1]
- [scenario 2]

**Resume command:**
npx playwright test [spec] --grep "[pattern]"

**Việc quan trọng nhất tiếp theo:**
[mô tả]

---
Tiếp tục từ đây không, hay có gì thay đổi?
```

---

## Khi không có context (session hoàn toàn mới)

Nếu beads không có in-progress QA issues → hỏi intake:

```
Không tìm thấy session nào đang dở. Bắt đầu session mới:

1. Project: Incard CMS / Inapps / HVS / The Client Book / khác?
2. Feature/module cần test?
3. Có Figma, scope doc, hay screenshot không?
4. Mục tiêu: viết test cases / chạy test / debug / check coverage?
```

Sau đó → route sang `qa-router` để xác định skill cần invoke.

---

## Rules

1. **Không bắt đầu test ngay** — present context trước, chờ user confirm "ok tiếp" hoặc điều chỉnh
2. **Resume command là bắt buộc trong handoff** — nếu không tìm thấy, hỏi user về spec file
3. **Nếu user bổ sung context khác** — update hiểu biết và route lại qua `qa-router`

---

## Cross-references

- **qa-session-close** — tạo handoff note cuối session (counterpart của skill này)
- **beads** — nguồn dữ liệu chính (in-progress issues + notes)
- **qa-router** — sau khi có context, route sang skill phù hợp
- **qa-preflight** — sau khi confirm context, check env trước khi chạy test
