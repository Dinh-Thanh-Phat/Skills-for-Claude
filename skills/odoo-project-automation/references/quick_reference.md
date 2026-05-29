# Odoo Project Automation - Quick Reference

## Create Task Syntax

```
project: "PROJECT_NAME"
task_name: "TASK_TITLE"
task_type: "TYPE"              # bug | task | enhance | refactor | docs
description: "SHORT_DESC"
assignee: "ASSIGNEE_NAME"
tags: ["TAG1", "TAG2"]         # Optional
priority: "0"                  # Optional: 0=Critical, 2=Medium (default), 4=Backlog
status: "Todo"                 # Optional: default is Todo
```

## Move Task Syntax

```
project: "PROJECT_NAME"
task_name: "TASK_TITLE"
action: "move"
new_status: "NEW_STATUS"       # Todo | In Progress | Develop | Done
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

- `Soundwise`
- `TRS`
- `Olivia - CRM App`

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

## Priority Levels

| Level | Name | Use When |
|-------|------|----------|
| `0` | Critical | Production blocking |
| `1` | High | High impact, urgent |
| `2` | Medium | Normal priority (default) |
| `3` | Low | Nice to have |
| `4` | Backlog | Future work |

## Workflow States

```
Backlog → Todo → In Progress → Develop → Done
```

**Rules:**
- Move forward: Todo → In Progress, In Progress → Develop, Develop → Done
- Move back: In Progress → Todo, Develop → In Progress
- Cannot skip states or leave Done

## Available Tags

`bug`, `task`, `enhance`, `refactor`, `docs`, `backend`, `frontend`, `mobile`, `performance`, `security`, `database`, `urgent`, `review`

---

## Common Use Cases

### 1. Report a Critical Bug (Urgent)
```
project: "Soundwise"
task_name: "Payment button crashes"
task_type: "bug"
description: "Clicking pay button causes app to crash on iOS"
assignee: "Phuc Do"
tags: ["bug", "critical", "mobile"]
priority: "0"
```

### 2. Create Feature for Next Sprint
```
project: "TRS"
task_name: "Add user activity logging"
task_type: "task"
description: "Track all user actions for audit trail compliance"
assignee: "Anh Huynh"
tags: ["task", "backend"]
priority: "2"
status: "Todo"
```

### 3. Create Performance Enhancement
```
project: "Soundwise"
task_name: "Optimize search queries"
task_type: "enhance"
description: "Add database indexing for faster search performance"
assignee: "Hoa Tran"
tags: ["enhance", "performance", "database"]
priority: "2"
```

### 4. Start Working (Move Task)
```
project: "Soundwise"
task_name: "Payment button crashes"
action: "move"
new_status: "In Progress"
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
Status: Todo
Tags: bug, critical, mobile
Priority: 0 (Critical)

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

1. **Skill validates inputs** → Project/assignee exist?
2. **Shows confirmation dialog** → Review auto-expanded description
3. **Waits for response** → "yes"/"confirm" or "no"/"cancel"
4. **Executes action** → Creates/moves/closes task
5. **Shows result** → Success or error message

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Project not found" | Use exact project name (case-sensitive) |
| "Assignee not found" | Use exact assignee name from list |
| "Cannot move to status" | Check workflow rules - can only move forward/back one state |
| "Task not found" | Verify exact task name spelling |
| Task created but not visible | Wait 30 seconds, refresh Odoo page |

---

## Tips

✅ **DO:**
- Use specific descriptions (auto-expansion quality depends on it)
- Review confirmation dialog before confirming
- Add context in notes when moving tasks
- Use appropriate priority level
- Tag consistently across tasks

❌ **DON'T:**
- Use wrong project/assignee names
- Skip the confirmation dialog
- Try to move Done tasks backwards
- Leave descriptions empty
- Use inconsistent tag names

---

## Integration Examples

### Claude Code
```
"I need to create a bug for the login issue in Soundwise project..."
→ Skill triggers automatically
→ Shows confirmation
→ Creates task in Odoo
```

### Natural Language
```
"Move the user profile page task in Olivia to In Progress - I'm starting implementation"
→ Skill parses request
→ Shows confirmation
→ Moves task
```

### With Details
```
"Create enhancement in TRS: Add dark mode support, assign to Anh Huynh, mark as medium priority"
→ Skill validates
→ Shows confirmation with auto-expanded description
→ Creates task
```

---

## For More Information

- **SKILL.md** - Complete feature reference
- **workflow_guide.md** - Detailed workflows and examples
- **README.md** - Implementation overview
