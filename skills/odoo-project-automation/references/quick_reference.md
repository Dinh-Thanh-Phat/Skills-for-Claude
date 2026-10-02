# Odoo Project Automation - Quick Reference

> Trigger rule: only when the user's message contains "Odoo" or "ERP". All reads/writes go through `mcp__odoo__*` (search_records → preview_write/validate_write → execute_approved_write). SKILL.md is the source of truth if anything here disagrees.

## Create Task Syntax

```
project: "PROJECT_NAME"
task_name: "TASK_TITLE"
task_type: "TYPE"              # bug | task | enhance | refactor | docs
description: "SHORT_DESC"
assignee: "ASSIGNEE_NAME"      # written to user_ids (many2many)
tags: ["TAG1", "TAG2"]         # Optional — resolve via project.tags first
priority: "1"                  # Optional: Odoo 19 → "0"=Low, "1"=Medium, "2"=High, "3"=Urgent
status: "TODO"                 # Optional: real stage name; TODO (176) is the usual default
```

## Move Task Syntax

```
project: "PROJECT_NAME"
task_name: "TASK_TITLE"
action: "move"
new_status: "NEW_STATUS"       # BackLog | TODO | INPROGRESS | DEVELOPED | READY FOR TEST | DONE
notes: "REASON_FOR_MOVE"       # Optional
```

## Close Task Syntax

```
project: "PROJECT_NAME"
task_name: "TASK_TITLE"
action: "close"
summary: "COMPLETION_SUMMARY"  # Optional but recommended
```

---

## Project Names (Exact Spelling)

| Project | project_id |
|---|---|
| `Soundwise` | 76 |
| `TRS` | - |
| `Olivia - CRM App` | 64 |
| `Website InApps` | 79 |
| `FCCX` | 80 |

Not exhaustive — resolve others with `search_records` on `project.project` (`ilike`).

## Assignee Names (Exact Spelling)

- `Phuc Do`
- `Phat Dinh`
- `Anh Hoang`
- `Anh Huynh`
- `Demo User`
- `Gotham`
- `Hoa Tran`
- `Huong Nguyen`
- `InApps Customer Success`

## Task Types

| Type | Format | Use When |
|------|--------|----------|
| `bug` | Steps + Expected + Actual | Issues/defects |
| `task` | Plan + Criteria | Features/work |
| `enhance` | Solution + Benefits | Improvements |
| `refactor` | Objective + Plan | Code cleanup |
| `docs` | Scope + Format | Documentation |

## Priority Levels (Odoo 19 `project.task.priority`)

| Value | Odoo label | Stars | Use When |
|-------|------|-------|----------|
| `"3"` | Urgent | ⭐⭐⭐ | Production blocking, crash, payment, security, cannot login |
| `"2"` | High | ⭐⭐ | Broken feature, wrong data, 404, timeout |
| `"1"` | Medium | ⭐ | Cosmetic / minor UI (default for bugs) |
| `"0"` | Low | — | Nice to have |

There is no `"4"`. `"0"` is the LOWEST priority — never use it for critical.

## Workflow States (stages)

```
BackLog (175) → TODO (176) → INPROGRESS (177) → DEVELOPED (180) → READY FOR TEST (181) → DONE (182)
```

**Rules:**
- Stage names are UPPERCASE in Odoo — search with `ilike`.
- Odoo allows moving a task to any stage (forward, back, or reopening from DONE). There is no enforced "terminal" stage.
- The "done" circle is a separate field: `state = "1_done"` (not `kanban_state`, which doesn't exist in Odoo 19).

## Available Tags

Confirmed live `project.tags`: `bug` (5), `Task` (6), `Enhancement` (27), `Feedback` (28), `Customer` (1).
Other names (`refactor`, `docs`, `backend`, `frontend`, `mobile`, `performance`, `security`, `database`, `urgent`, `review`) are UNVERIFIED — search `project.tags` before using.

---

## Common Use Cases

### 1. Report a Critical Bug (Urgent)
```
project: "Soundwise"
task_name: "Payment button crashes"
task_type: "bug"
description: "Clicking pay button causes app to crash on iOS"
assignee: "Phuc Do"
tags: ["bug"]
priority: "3"
```

### 2. Create Feature for Next Sprint
```
project: "TRS"
task_name: "Add user activity logging"
task_type: "task"
description: "Track all user actions for audit trail compliance"
assignee: "Anh Huynh"
tags: ["Task"]
priority: "1"
status: "TODO"
```

### 3. Create Performance Enhancement
```
project: "Soundwise"
task_name: "Optimize search queries"
task_type: "enhance"
description: "Add database indexing for faster search performance"
assignee: "Hoa Tran"
tags: ["Enhancement"]
priority: "1"
```

### 4. Start Working (Move Task)
```
project: "Soundwise"
task_name: "Payment button crashes"
action: "move"
new_status: "INPROGRESS"
notes: "Starting investigation and fix"
```

### 5. Mark Task Done
```
project: "Soundwise"
task_name: "Payment button crashes"
action: "close"
summary: "✅ Fixed: Updated iOS SDK to v3.2, tested on iPhone 12-14, approved by QA"
```

---

## Response Format

### Success Example
```
✅ Task created successfully

Project: Soundwise
Task: Payment button crashes
Task ID: 1001
Type: bug
Assignee: Phuc Do
Status: TODO
Tags: bug
Priority: 3 (Urgent)

Created: 2026-05-05T10:30:45
```

### Error Example
```
❌ ERROR: Assignee 'John Doe' not found

Available assignees:
- Phuc Do
- Phat Dinh
- Anh Hoang
- Anh Huynh
- Demo User
- Gotham
- Hoa Tran
- Huong Nguyen
- InApps Customer Success
```

---

## Confirmation Flow

1. **Validate inputs** → Project/assignee/stage/tags exist? (`search_records`)
2. **Show confirmation** → Review auto-expanded description (bugs: Actual and Expected on separate labelled lines)
3. **Wait for response** → "yes"/"confirm" or "no"/"cancel"
4. **Execute** → `validate_write` → `execute_approved_write` (`confirm=true`)
5. **Show result** → Success or verbatim error

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Project not found" | Use exact project name, or `ilike` search |
| "Assignee not found" | Use exact assignee name from list |
| "Stage not found" | Use the real UPPERCASE stage name (`ilike`) |
| "Task not found" | Verify exact task name spelling |
| Task created but not visible | Wait 30 seconds, refresh Odoo page |

---

## Tips

✅ **DO:**
- Use specific descriptions (auto-expansion quality depends on it)
- Review confirmation dialog before confirming
- Add context in notes when moving tasks
- Use the correct priority value ("3" = Urgent)
- Tag consistently across tasks

❌ **DON'T:**
- Use wrong project/assignee names
- Skip the confirmation dialog
- Use `"0"` for critical bugs (it means Low)
- Leave descriptions empty
- Use inconsistent tag names

---

## Integration Examples

### Claude Code
```
"I need to create a bug for the login issue in Soundwise project on Odoo..."
→ Skill triggers (message contains "Odoo")
→ Shows confirmation
→ Creates task in Odoo
```

### Natural Language
```
"Move the user profile page task in Olivia to INPROGRESS on Odoo - I'm starting implementation"
→ Skill parses request
→ Shows confirmation
→ Moves task
```

### With Details
```
"Create enhancement in TRS on ERP: Add dark mode support, assign to Anh Huynh, medium priority"
→ Skill validates (priority "1" = Medium)
→ Shows confirmation with auto-expanded description
→ Creates task
```

---

## For More Information

- **SKILL.md** - Complete feature reference (source of truth)
- **workflow_guide.md** - Detailed workflows and examples
- **README.md** - Overview
