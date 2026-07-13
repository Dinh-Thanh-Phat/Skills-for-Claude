---
name: odoo-timesheet
description: >-
  Log timesheet hours and set allocated time (task time budget) on Odoo.
  Use ONLY when the user's message mentions "Odoo" or "ERP" AND wants to record
  time worked or set/adjust a task's time budget — e.g. "log 3h on the Olivia
  testing task in Odoo", "chấm công 4 tiếng hôm nay cho task X trên Odoo",
  "record 2.5 hours timesheet for yesterday on ERP", "set allocated time to 8h
  for task Y in Odoo", "đặt allocated time / planned hours cho task này".
  Timesheet = actual hours spent (account.analytic.line). Allocated time = the
  planned time budget on a task (project.task.allocated_hours). Trigger this even
  when the user just says "log time"/"chấm công"/"ghi timesheet" for a named task
  as long as Odoo/ERP is mentioned. Do NOT trigger without "Odoo"/"ERP", and do
  NOT trigger for creating/moving tasks or bugs (that is odoo-project-automation).
---

# Odoo Timesheet & Allocated Time

Record **time spent** (timesheets) and set **allocated time** (task time budget) on
the InApps Odoo instance. Both operations write to Odoo, so accuracy matters — a
timesheet on the wrong task or with the wrong hours corrupts real project reporting.

**Environment** (Odoo 19.0): `erp.inapps.net`, database `inapps`, tz `Asia/Saigon`.
Connected user: `phat.dinh@inapps.net` (uid 18) → employee **Phat Dinh** (`employee_id` 8).

## 🚨 STOP — DATE GATE (do this before anything else)

**This skill's #1 repeated failure is logging hours on the WRONG DATE.** It has
happened 4× in a single session because the date was typed from memory instead of read.

Before you touch any tool, copy today's date out of your context, out loud:

> "currentDate in my context says `YYYY-MM-DD` → I will use that as the timesheet date."

Rules, non-negotiable:
- The `date` value comes **only** from the `currentDate` / `Today's date is …` line in
  the current turn's context (or `date +%Y-%m-%d`). Never from memory, never reused from
  an earlier entry or an earlier turn in the same session.
- User writes dates **D/M**: `13/7` → `2026-07-13`, `9/7` → `2026-07-09`. Not M/D.
- **Echo the resolved `YYYY-MM-DD` in every report** so the user can catch an off-by-day.
- If you cannot see a date in context, or the session may have crossed midnight, **ask**
  — do not guess.

See "Resolving the date" below for the same rules in detail.

## The two things this skill does

| Concept | Meaning | Where it lives |
|---|---|---|
| **Timesheet** | Actual hours a person worked on a task/project on a given day | A record in `account.analytic.line` (create one per entry) |
| **Allocated time** | The planned time *budget* for a task | The `allocated_hours` float field on `project.task` |

They are linked: logging a timesheet on a task increases that task's `effective_hours`
(time spent), and `remaining_hours = allocated_hours − effective_hours`. After any
write, report the task's remaining time so the user sees the budget impact.

## Golden rule: confirm the target before writing

The most damaging mistake is logging time against the wrong task. A task name like
"testing" can match dozens of tasks across projects. Before any write:

1. **Resolve the task/project by search, never by guess.** Search `project.task`
   with the user's keywords (and project if named). Show the matches you found.
2. **If exactly one match** and the user was specific, proceed to validate.
3. **If multiple matches or ambiguity**, list them (id, name, project) and ask which
   one — do not pick the first. This follows the ask-when-stuck discipline.

## Field reference

**Timesheet — `account.analytic.line` (create):**

| Field | Value | Notes |
|---|---|---|
| `task_id` | resolved task id | Task must belong to a timesheet-enabled project |
| `project_id` | the task's project id | Set it explicitly to be safe |
| `employee_id` | default **8** (Phat Dinh) | Override only if another person is named |
| `date` | `YYYY-MM-DD` | Default = today, read fresh from `currentDate` — see "Resolving the date". Never carry a date over from an earlier entry |
| `unit_amount` | hours as float | `3h30` → `3.5`, `45m` → `0.75`, `2 tiếng` → `2.0` |
| `name` | short description of the work | **Required.** Never leave it as Odoo's `/` placeholder — if the user gives no description, use a concise one derived from the task/work, or ask |

Do **not** set `account_id` — Odoo derives the analytic account from `project_id`.

**Allocated time — `project.task` (write):**

| Field | Value | Notes |
|---|---|---|
| `allocated_hours` | hours as float | This is the "Allocated Time" field. Same hour-parsing rules |

**Creating a new task — `project.task` (create):**

When the user asks to create a new task (e.g. a daily "[Testing] Verify bugs
YYYY-MM-DD"), ALWAYS place it in the **In Progress** column, not the default first
stage:

| Field | Value | Notes |
|---|---|---|
| `name` | task title | If it embeds a date, use the **resolved today** — see "Resolving the date" |
| `project_id` | resolved project id | |
| `allocated_hours` | budget as float | the `a=` value the user gives |
| `stage_id` | **177** ("INPROGRESS") | shared stage covering projects 76,67,64,79,80,68,83,60,63,66,70. If the target project is NOT in that list, search `project.task.type` for the project's own In-Progress stage (names vary: "In Progress" 16, "INPROGRESS" 177/210, "Doing" 130…) and use that id |

## Resolving the date

**Never type a date from memory or from an earlier turn in the conversation.** Defaulting
to a stale date silently files hours on the wrong day, and the user only catches it later.

1. Read today's date from the **`currentDate` value in your environment context** (or run
   `date +%Y-%m-%d`). Treat that as today in `Asia/Saigon`.
2. Resolve any relative expression ("hôm nay", "hôm qua", "thứ 2 tuần trước", "9/7")
   against that date. Vietnamese `9/7` = **D/M** → `2026-07-09`, not July 9th read as M/D.
3. **State the concrete `YYYY-MM-DD` you resolved to in your report**, so the user can spot
   an off-by-a-day before it matters.
4. In a long session that may span midnight or resume the next day, re-read the date for
   each write rather than reusing the one from a previous entry.

## Resolving the employee

Default to the connected user, **Phat Dinh (`employee_id` 8)**. Only change the employee
when the user names someone else ("log 3h for Vinh"). In that case resolve with
`mcp__odoo__search_employee` and confirm the match before writing. If a named employee
returns multiple results, list them and ask.

## Parsing hours

Users express time many ways. Convert everything to a float number of hours:

- `3h`, `3 hours`, `3 tiếng`, `3 giờ` → `3.0`
- `3h30`, `3.5h`, `3 hours 30 min`, `3 tiếng rưỡi` → `3.5`
- `45m`, `45 phút`, `0.75h` → `0.75`
- A full day → `8.0` (standard workday) — but confirm if the user said "a day" vaguely.

## The user's shorthand

This user writes terse one-liners. Recognise them:

```
odoo -> <project> -> <task description> với a = 4, ts = 2
HVS - retest trên prod mobile với a = 2, s = 1 và mark done lun
```

| Token | Means |
|---|---|
| `a = N` | `allocated_hours` = N (the task's time budget) |
| `s = N` / `ts = N` | the **timesheet** hours to log (time actually spent) |
| `mark done` | after logging, set the task's `state` — see below |
| `->` chain | project → task, in that order |

When the described task does not already exist, this user's intent is to **create it**
(they confirmed this pattern repeatedly), placed in the In Progress stage. Still search
first and show what you found; only skip the confirmation question when the description
is specific and no existing task plausibly matches.

## Marking a task done

Set the `state` field (this is the ✓ circle button in the Odoo UI, **not** `kanban_state`
and not a stage move):

```
model="project.task", operation="write", record_ids=[task_id],
values={"state": "1_done"}
```

Log the timesheet **before** marking done, so the hours land on an open task.

## Workflow — logging a timesheet

0. **Read the date first** — copy `currentDate` from context (see 🚨 DATE GATE). Do this
   before building any payload; it is the step most often skipped.
1. **Resolve the task** (see Golden rule). Capture `task_id` and its `project_id`.
2. **Resolve employee** (default 8; override if named).
3. **Parse date**: default = the `currentDate` you read in step 0. Only shift it if the
   user explicitly said "hôm qua"/a weekday/an explicit date. Never carry over a date.
4. **Determine description** (`name`). Ask if none can be reasonably inferred.
5. **Validate**: call `mcp__odoo__validate_write` with `model="account.analytic.line"`,
   `operation="create"`, and the `values` above. This returns an `approval` object with
   a token that is *stored in the server session* — that is what makes it executable.
6. **Execute**: call `mcp__odoo__execute_approved_write` passing that **full approval
   object** (including `token`, `validated_at`, `expires_at`) and `confirm=true`.
7. **Report outcome**: state the created line (date, hours, task, employee) and the
   task's updated `remaining_hours` — read `project.task` after the write to show how
   much of the allocated budget is left.

## Workflow — setting allocated time

1. **Resolve the task** and capture `task_id`.
2. **Parse hours** for the budget.
3. **Validate**: `mcp__odoo__validate_write` with `model="project.task"`,
   `operation="write"`, `record_ids=[task_id]`, `values={"allocated_hours": <float>}`.
4. **Execute**: `mcp__odoo__execute_approved_write` with the returned approval object and
   `confirm=true`.
5. **Report**: new `allocated_hours`, current `effective_hours` (time already spent),
   and the resulting `remaining_hours`. If spent already exceeds the new budget, call
   that out — it means the task is over-allocated.

## Reporting format

Keep it short and factual. Example after a timesheet:

```
✅ Timesheet logged
  Task:      [Testing] Verify bugs  (#2529, Olivia - CRM App)
  Employee:  Phat Dinh
  Date:      2026-07-07
  Hours:     3.0
  Note:      Regression pass on login flow
  → Task budget: 3.0 spent of 8.0 allocated · 5.0h remaining
```

## Edge cases & guardrails

- **Non-timesheet project**: if the resolved project has `allow_timesheets = false`, the
  create will fail. Surface that clearly instead of retrying — the project must enable
  timesheets first.
- **No allocated time set**: `allocated_hours = 0` means no budget; `remaining_hours`
  will show negative once time is logged. Mention it, don't treat it as an error.
- **Zero/blank hours**: don't log a `0` timesheet unless the user explicitly asks.
- **Ambiguous date** ("last Monday" near a week boundary): state the concrete date you
  resolved to so the user can catch a mistake.
- **Batch requests** ("log 3h Mon and 5h Tue"): this skill is single-entry by design —
  handle each entry as its own validate→execute cycle, confirming each, rather than one
  bulk write.
- Never mask a write failure. If `execute_approved_write` returns an error, report it
  verbatim and stop — do not invent a workaround that makes it look successful.
