# Odoo Project Automation - Complete Workflow Guide

## Overview

This skill automates task and bug management in your Odoo ERP instance at `https://erp.inapps.net` (UI at `/odoo/`; API calls must NOT use `/odoo/` — 303 redirect). It triggers only when the user's message contains "Odoo" or "ERP", and reads/writes via `mcp__odoo__*` tools. SKILL.md is the source of truth if anything here disagrees.

It handles:
- **Creating tasks/bugs** with auto-expanded descriptions
- **Moving tasks** through stages (BackLog → TODO → INPROGRESS → DEVELOPED → READY FOR TEST → DONE)
- **Closing tasks** with completion summaries
- **Updating task details** (assignee, tags, description)
- **Error handling** with helpful suggestions

## Core Workflow

### 1. Create a New Task

**Basic Example:**
```
Project: "Soundwise"
Task Name: "Implement user authentication"
Task Type: "task"
Description: "Add JWT-based login system"
Assignee: "Phat Dinh"
Tags: ["Task"]
```

**What Happens:**
1. Skill validates project exists → ❌ Error if not found
2. Skill validates assignee exists → ❌ Error if not found
3. Skill auto-expands description based on task_type:
   - **bug**: Steps to Reproduce + Expected + Actual
   - **task**: Implementation Plan + Success Criteria
   - **enhance**: Proposed Solution + Benefits
   - **refactor**: Objective + Success Criteria
   - **docs**: Documentation Scope + Acceptance Criteria
4. Skill shows confirmation dialog with full details
5. ⏳ **WAITS FOR YOUR CONFIRMATION** ("yes"/"confirm")
6. ✅ Creates task in Odoo with expanded description

### 2. Move Task Through Workflow

**Example:**
```
Project: "TRS"
Task Name: "Database migration"
Current Status: "TODO"
New Status: "INPROGRESS"
Notes: "Starting implementation - database schema finalized"
```

**Stages (Soundwise/Olivia share these ids):**
```
BackLog (175) → TODO (176) → INPROGRESS (177) → DEVELOPED (180) → READY FOR TEST (181) → DONE (182)
```
Odoo allows moving to any stage (forward, back, or reopening from DONE) — there is no enforced transition rule. Stage names are UPPERCASE; search with `ilike`. Other projects may have their own stages — query `project.task.type` with `project_ids in [project_id]`.

**What Happens:**
1. Validates project exists
2. Validates the target stage exists in that project → ❌ Error if not found
3. Shows confirmation with current → new status
4. ⏳ **WAITS FOR YOUR CONFIRMATION**
5. ✅ Moves task to new status

### 3. Close/Complete Task

**Example:**
```
Project: "Olivia - CRM App"
Task Name: "User profile page"
Summary: "✅ Completed implementation with edit, upload photo, and delete account features. All tests passing. Ready for QA."
```

**What Happens:**
1. Validates project exists
2. Shows confirmation with task details and summary
3. ⏳ **WAITS FOR YOUR CONFIRMATION**
4. ✅ Moves task to DONE and/or sets `state = "1_done"` (circle), posts the summary to chatter

### 4. Update Task Details

**Example:**
```
Project: "Soundwise"
Task Name: "API rate limiting"
Assignee: "Huong Nguyen"  # Change from current
Tags: ["Task"]
```

**What Happens:**
1. Validates project exists
2. Shows all fields being changed
3. ⏳ **WAITS FOR YOUR CONFIRMATION**
4. ✅ Updates task with new details

---

## Error Handling

### Project Not Found
```
❌ ERROR

Project 'InvalidProject' not found.

Details:
  - Available projects: Soundwise (76), TRS, Olivia - CRM App (64), Website InApps (79), FCCX (80), ...
```

**Solution:** Use exact project name, or `ilike` search on `project.project`.

### Assignee Not Found
```
❌ ERROR

Assignee 'John Doe' not found.

Details:
  - Available assignees:
    • Phuc Do
    • Phat Dinh
    • Anh Hoang
    • Anh Huynh
    • Demo User
    • Gotham
    • Hoa Tran
    • Huong Nguyen
    • InApps Customer Success
```

**Solution:** Use exact assignee name from list above.

### Stage Not Found
```
❌ ERROR

Stage 'Develop' not found in project 'Soundwise'.

Available: BackLog, TODO, INPROGRESS, DEVELOPED, READY FOR TEST, DONE
```

**Solution:** Use the real stage name. (Odoo has no "terminal stage" rule — a DONE task can be moved back if needed.)

### Task Not Found

When you refer to a task by name that doesn't exist:
```
❌ ERROR

Task 'Non-existent task' not found in project 'Soundwise'.

Suggestion: List all tasks in project first or verify task name spelling.
```

**Solution:** Verify exact task name or use task ID instead.

---

## Input Parameters Reference

### Task Types

| Type | Auto-Expansion Format | Use For |
|------|----------------------|---------|
| **bug** | Steps to Reproduce + Expected + Actual | Defects, issues, problems |
| **task** | Implementation Plan + Success Criteria | Features, general work |
| **enhance** | Proposed Solution + Benefits | Improvements, optimizations |
| **refactor** | Objective + Refactoring Plan | Code cleanup, architecture |
| **docs** | Documentation Scope + Format | Documentation, guides |

### Priority Levels

Odoo 19 `project.task.priority` (verified in 19.0 source):

| Value | Odoo label | Stars | Use When |
|-------|------|-------|----------|
| **"3"** | Urgent | ⭐⭐⭐ | Blocking production, crash, payment, security |
| **"2"** | High | ⭐⭐ | Broken feature, wrong data, needed soon |
| **"1"** | Medium | ⭐ | Normal / cosmetic (default for bugs) |
| **"0"** | Low | — | Nice to have, can defer |

There is no `"4"`; `"0"` is the LOWEST.

### Available Tags

**Confirmed live `project.tags`:**
- `bug` (id 5) - Defect/issue (older notes say `"bugs"` — live name is `bug`)
- `Task` (id 6) - Feature/work
- `Enhancement` (id 27) - Enhancement/optimization
- `Feedback` (id 28)
- `Customer` (id 1)

Other names (`backend`, `frontend`, `mobile`, `performance`, `security`, `database`, `documentation`, `urgent`, `review`) are UNVERIFIED — search `project.tags` before using; don't create tags silently.

---

## Confirmation Flow

**Why confirmation?** Prevents accidental task creation/modification.

**Confirmation Dialog Example:**
```
╔════════════════════════════════════════════════════════════════╗
║                   CREATE TASK - PLEASE CONFIRM                  ║
╚════════════════════════════════════════════════════════════════╝

📋 Task Details:
  Project:     Soundwise
  Task Name:   Login button not responsive
  Type:        bug
  Assignee:    Phuc Do
  Status:      TODO
  Tags:        bug
  Priority:    3 (Urgent)

📝 Description (Auto-expanded):
────────────────────────────────────────────────────────────────
[BUG REPORT - 2026-05-05 10:30:45]

STEPS TO REPRODUCE:
1. Navigate to login page on mobile device
2. Click login button
3. Observe no response

EXPECTED RESULT:
Login modal opens / redirects to login page

ACTUAL RESULT:
Button click is not responsive

...
────────────────────────────────────────────────────────────────

⚠️  Please review the details above.
✅ Type 'yes' or 'confirm' to proceed
❌ Type 'no' or 'cancel' to abort
🔄 Type 'edit' to modify any field
```

**How to Respond:**
- ✅ **Approve:** "yes", "confirm", "ok", "proceed"
- ❌ **Cancel:** "no", "cancel", "abort"
- 🔄 **Modify:** "edit" (will return to input screen)

---

## Output Format

### Success Example
```
✅ Task created successfully

Project: Soundwise
Task: Login button not responding on mobile
Task ID: 1001
Type: bug
Assignee: Phuc Do
Status: TODO
Tags: bug

Created: 2026-05-05T10:30:45.123456
```

### Error Example
```
❌ ERROR

Project 'InvalidName' not found.

Details:
  - Available projects: Soundwise, TRS, Olivia - CRM App, Website InApps, FCCX, ...
```

### Both Formats
- **Human-readable:** ✅/❌ with emoji, formatted text
- **JSON:** Complete details for automation/logging
```json
{
  "success": true,
  "action": "create",
  "task_id": 1001,
  "project": "Soundwise",
  "task_name": "Login button not responding on mobile",
  "assignee": "Phuc Do",
  "tags": ["bug"],
  "priority": "3",
  "created_at": "2026-05-05T10:30:45.123456"
}
```

---

## Best Practices

1. **Be Specific in Descriptions**
   - ❌ "Fix button" 
   - ✅ "Fix login button not responding on mobile Safari"

2. **Use Appropriate Priority**
   - "3" (Urgent) for production-blocking issues
   - "1" (Medium) for normal work
   - "0" (Low) for nice-to-have items — never for critical

3. **Include Context in Notes**
   - When moving tasks, add notes explaining why
   - When closing, explain what was done

4. **Tag Consistently**
   - Use same tags across similar work
   - Helps with filtering and reporting

5. **Review Before Confirming**
   - Read auto-expanded description
   - Check assignee and tags
   - Verify the target stage name exists

---

## Workflow Examples

### Example 1: Report and Assign a Critical Bug
```
Project: Soundwise
Task Name: Payment webhook timeout
Task Type: bug
Description: Webhook requests timing out after 5 seconds, payments not recorded
Assignee: Phuc Do
Tags: [bug, payment, critical]
Priority: 0
```

**Flow:**
1. Show confirmation dialog with expanded bug format
2. Highlight Critical priority
3. Wait for "yes"
4. ✅ Create task
5. You can immediately assign to someone for action

### Example 2: Create and Move Enhancement
```
Step 1 - Create:
Project: TRS
Task Name: Add user activity logging
Task Type: enhance
Description: Track all user actions for audit trail
Assignee: Anh Huynh
Tags: [enhance, audit, backend]
Status: Todo

Step 2 - Move to In Progress:
Project: TRS
Task Name: Add user activity logging
New Status: In Progress
Notes: Started design review
```

**Flow:**
1. Create task (gets to Todo)
2. Move to In Progress (when work starts)
3. Move to Develop (when implementation begins)
4. Move to Done (when complete and tested)

### Example 3: Complete Task with Summary
```
Project: Olivia - CRM App
Task Name: Export contacts to CSV
Summary: ✅ Feature complete. Tested with 500+ contacts. 
         Performance: < 2 seconds. Ready for QA verification.
```

**Flow:**
1. Task worked on, tested, ready
2. Move to Done with detailed summary
3. Summary shows what was accomplished
4. QA can review and verify

---

## Troubleshooting

### Confirmation Times Out
- Resubmit with "yes"/"confirm"
- Or create new task if connection lost

### Task Not Found After Creation
- Wait 30 seconds (sync delay)
- Refresh Odoo page
- Check correct project name

### Cannot Move to Status
- Check workflow rules above
- Remember: can only move forward or back one state
- Terminal states (Done) cannot be left

### Assignee Not Available
- List all available assignees
- Use exact name spelling (case-sensitive)
- Contact admin if user should be added

