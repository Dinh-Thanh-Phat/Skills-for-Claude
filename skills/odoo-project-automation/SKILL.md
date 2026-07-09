---
name: odoo-project-automation
description: Use ONLY when user explicitly mentions "Odoo" or "erp" in their message. DO NOT trigger based on project names (Soundwise, TRS, HVS, HaiVan Ship, etc.) alone — those names are ambiguous. Handles creating, moving, closing, updating, or bulk-operating tasks/bugs in Odoo projects. Bug descriptions render as structured HTML with Steps/Expected/Actual + Technical Context table. Bug priority auto-assessed (1–3 stars) from keywords. Auto-tags bugs as "bugs", tasks as "task". Supports bulk move between stages and bulk mark-done via state field.
compatibility: Requires Python 3.8+, no external dependencies (uses standard library xmlrpc)
---

# Odoo Project Automation Skill

Automate task and bug management in Odoo ERP. Descriptions output as **HTML** (not plain text). Bugs get auto-priority stars and auto-tag.

## Quick Reference

### Create Task/Bug
```
project: "Soundwise"
task_name: "Login button not responding"
task_type: "bug"
description: "Button click doesn't work on mobile"
assignee: "Phuc Do"
tags: ["bug", "mobile"]
priority: "0"  # 0=Critical, 2=Medium, 4=Backlog

# Optional technical context (for bug type only — helps AI find & fix quickly)
page_url: "https://app.soundwise.com/login"
element_selector: "#login-btn"           # CSS or XPath
error_message: "TypeError: cannot read properties of null"
network_request: "POST /api/auth 500 Internal Server Error"
stack_trace: "at LoginButton.handleClick (login.js:42)"
```

### Move Task Between States
```
project: "TRS"
task_name: "Database migration"
action: "move"
new_status: "In Progress"
notes: "Schema design approved, starting implementation"
```

### Close Task
```
project: "Olivia - CRM App"
task_name: "User profile page"
action: "close"
summary: "✅ Completed with all features tested"
```

---

## Auto-Priority (Bug only)

Priority stars are **auto-assessed** from description + error_message + api_endpoint keywords. No need to set manually.

| Stars | When | Keywords |
|-------|------|----------|
| ⭐⭐⭐ 3 | Critical | crash, 500, payment, data loss, all users, security, cannot login, auth |
| ⭐⭐ 2 | High | broken, invalid, error, wrong data, stale, 404, timeout, always, 100% |
| ⭐ 1 | Normal | everything else (cosmetic, minor UI) |

Override: pass `priority` explicitly if needed.

## Auto-Tag

- `type=bug` → tag `"bugs"` added automatically
- `type=task/enhance/refactor/docs` → tag `"task"` added automatically

---

## Understanding Task Types

### Bug
**Format:** Steps to Reproduce + Expected Result + Actual Result + Technical Context
**Use for:** Defects, issues, problems
**Auto-expansion includes:**
- Steps to Reproduce (user fills in)
- Expected Result section
- Actual Result (from your description)
- **Technical Context** (optional, for AI-assisted debugging):
  - `page_url` — exact URL where bug occurs
  - `element_selector` — CSS/XPath of broken element
  - `error_message` — console or API error
  - `network_request` — failing HTTP request info
  - `stack_trace` — full stack trace

#### ⚠️ Expected vs Actual — NEVER guess the direction

Short bug notes from the reporter are almost always ambiguous about which side is the bug and which side is the fix. **Guessing wrong inverts the whole ticket** and the dev implements the bug.

**Ambiguous patterns — treat as UNKNOWN direction, do not resolve them yourself:**

| Note | Reading 1 | Reading 2 |
|---|---|---|
| "2 line màu trắng chứ không phải màu xám" | Actual = white (bug), Expected = gray | Expected = white, Actual = gray (bug) |
| "X chứ không phải Y" / "X not Y" | Actual = X | Expected = X |
| "phải là X" / "should be X" | — | Expected = X (unambiguous) |
| "đang bị X" / "it's showing X" | Actual = X (unambiguous) | — |
| "chữ light + dark thụt vô trong" | Actual = indented (bug) | Expected = indented |

**Rule:** Before writing a bug ticket, if the note does not contain an explicit *"đang là / hiện tại / it shows"* marker for Actual **or** an explicit *"phải là / should be / mong muốn"* marker for Expected, you MUST echo back the parsed pair and get confirmation:

```
Tôi hiểu như sau — xác nhận giúp:
  Actual (hiện tại):   lines đang màu xám
  Expected (mong muốn): lines phải màu trắng
Đúng hướng chưa?
```

Only after confirmation do you call `preview_write` / `execute_approved_write`.

**Never** infer direction from "which one sounds like a bug" — gray-vs-white, indented-vs-aligned, and most cosmetic pairs are symmetric; either could be the defect.

**Corollary for the title:** phrase it as the defect, not the fix. `"Theme lines are gray instead of white"` — a title like `"Change gray to white"` reads as a task and hides which state is broken.

### Task (Default)
**Format:** Implementation Plan + Success Criteria
**Use for:** Features, general work, general requests
**Auto-expansion includes:**
- Analysis & Planning phase
- Development phase with testing
- Deployment phase
- Success criteria checklist

### Enhancement
**Format:** Proposed Solution + Benefits
**Use for:** Improvements, optimizations, new capabilities
**Auto-expansion includes:**
- Background context
- Proposed implementation approaches
- Benefits breakdown
- Acceptance criteria
- Effort estimation

### Refactor
**Format:** Objective + Refactoring Plan + Risks
**Use for:** Code cleanup, architecture improvement, technical debt
**Auto-expansion includes:**
- Current state analysis
- Proposed refactoring approach
- Success metrics
- Risk assessment

### Docs
**Format:** Documentation Scope + Format + Audience
**Use for:** Documentation, guides, comments
**Auto-expansion includes:**
- What needs documenting
- Format and location
- Target audience
- Acceptance criteria

---

## Workflow States

### Soundwise Actual Stages (project_id=76)

| Stage Name | stage_id | sequence |
|---|---|---|
| BackLog | 175 | 0 |
| TODO | 176 | 1 |
| INPROGRESS | 177 | 2 |
| DEVELOPED | 180 | 3 |
| READY FOR TEST | 181 | 4 |
| DONE | 182 | 5 |

**Note:** Stage names in Odoo are UPPERCASE (e.g. `READY FOR TEST`, not `Ready for Test`). Use `ilike` when searching.

### Task Personal State (circle button on task card)

The colored circle (bottom-right of each task card) = `state` field. **Not** `kanban_state` (removed in Odoo 19).

| Value | Label | Circle color |
|---|---|---|
| `01_in_progress` | In Progress | Grey |
| `02_changes_requested` | Changes Requested | Orange |
| `03_approved` | Approved | Green |
| `1_done` | Done | Green (checkmark) |
| `1_canceled` | Cancelled | Red |

**To mark tasks "Done" (circle):** set `state = '1_done'`  
**To bulk mark:** `models.execute_kw(DB, uid, TOKEN, 'project.task', 'write', [task_ids, {'state': '1_done'}])`

---

## Projects & Team

### Available Projects
| Project | Code | Description |
|---------|------|-------------|
| **Soundwise** | - | Main application |
| **TRS** | - | Task/Resource System |
| **Olivia - CRM App** | - | CRM application |

### Available Assignees
- Phuc Do (Lead Backend)
- Phat Dinh (Frontend Lead)
- Anh Hoang (QA)
- Anh Huynh (Frontend)
- Demo User (Demo/Testing)
- Gotham (Infrastructure)
- Hoa Tran (Backend)
- Huong Nguyen (Backend)
- InApps Customer Success (Support)

### Available Tags
`bug`, `task`, `enhance`, `refactor`, `docs`, `backend`, `frontend`, `mobile`, `performance`, `security`, `database`, `urgent`, `review`

---

## Confirmation Workflow

**IMPORTANT:** Skill ALWAYS asks for confirmation before executing actions.

### Process:
1. You provide task details (project, name, type, description, etc.)
2. Skill validates inputs (project/assignee exist, etc.)
3. Skill shows confirmation dialog with:
   - Full task details
   - Auto-expanded description preview
   - Status transition (if moving)
   - Summary (if closing)
4. ⏳ **WAITS FOR YOUR CONFIRMATION**
5. ✅ You respond: "yes"/"confirm"/"ok"/"proceed"
6. ❌ Or cancel: "no"/"cancel"/"abort"
7. Action executes or is cancelled

---

## Error Handling

### Project Not Found
```
❌ ERROR: Project 'InvalidName' not found
Available: Soundwise, TRS, Olivia - CRM App
```
**Fix:** Use exact project name

### Assignee Not Found
```
❌ ERROR: Assignee 'John Doe' not found
Available: Phuc Do, Phat Dinh, Anh Hoang, ...
```
**Fix:** Use exact assignee name from list

### Invalid Status Transition
```
❌ ERROR: Cannot move from 'Done' to 'In Progress'
Done is terminal (final state)
```
**Fix:** Create new task instead

### Task Not Found
```
❌ ERROR: Task 'Non-existent task' not found
```
**Fix:** Verify exact task name or task ID

---

## Output Format

### Success Response (Human-Readable)
```
✅ Task created successfully

Project: Soundwise
Task: Login button not responding
Task ID: 1000
Type: bug
Assignee: Phuc Do
Status: Todo
Tags: bug, mobile
Priority: 0 (Critical)

Created: 2026-05-05T10:30:45.123456
```

### Success Response (JSON)
```json
{
  "success": true,
  "action": "create",
  "task_id": 1000,
  "project": "Soundwise",
  "task_name": "Login button not responding",
  "task_type": "bug",
  "status": "Todo",
  "assignee": "Phuc Do",
  "tags": ["bug", "mobile"],
  "priority": "0",
  "created_at": "2026-05-05T10:30:45.123456"
}
```

---

## Implementation Details

### Scripts Location
- `scripts/odoo_manager.py` - Core Odoo API manager (mock + real API support)
- `scripts/skill_handler.py` - Skill handler with confirmation workflow

### API Connection
- **Endpoint:** `https://erp.inapps.net` (NOT `/odoo/` — causes 303 redirect)
- **DB:** `inapps` (NOT `inapps-erp` — does not exist)
- **Login:** `phat.dinh@inapps.net` (NOT Gmail — causes auth failure)
- **Token:** Stored in `scripts/skill_handler.py`
- **Authentication:** XML-RPC via API key, **uid cached 24h** (no re-auth on every call)
- **Transport:** Persistent HTTPS connection (reuses SSL — no repeated handshakes)
- **Mode:** Real API (live, not mock)
- **Session cache:** `skills/odoo-project-automation/.odoo_session.json`
- **Odoo version:** 19.0

### Features
✅ **Real API Mode (Default)**
- Live Odoo integration
- Actual task creation in ERP
- Full workflow support

✅ **Confirmation Flow**
- Shows preview before action
- Waits for explicit confirmation
- Prevents accidental changes

✅ **Error Handling**
- Validates all inputs upfront
- Helpful error messages
- Suggests corrections

✅ **Description Auto-Expansion**
- Different templates per task type
- Pre-filled sections
- Structured format for clarity

---

## Bulk Operations

For large batches (move all tasks in a column, mark all done, etc.) write a Python script directly — faster than calling skill handler one-by-one.

### Pattern: Bulk move stage
```python
import xmlrpc.client
URL = "https://erp.inapps.net"
DB = "inapps"
USERNAME = "phat.dinh@inapps.net"
TOKEN = "<api_key>"
uid = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common").authenticate(DB, USERNAME, TOKEN, {})
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

# Find tasks in source stage
tasks = models.execute_kw(DB, uid, TOKEN, "project.task", "search_read",
    [[["project_id", "=", 76], ["stage_id", "=", 181]]],  # 181=READY FOR TEST
    {"fields": ["id", "name"], "limit": 200}
)
task_ids = [t["id"] for t in tasks]

# Bulk move to target stage
models.execute_kw(DB, uid, TOKEN, "project.task", "write",
    [task_ids, {"stage_id": 182}]  # 182=DONE
)
```

### Pattern: Bulk mark state (circle button)
```python
# Mark all tasks in DONE column as state=Done (green circle)
tasks = models.execute_kw(DB, uid, TOKEN, "project.task", "search_read",
    [[["project_id", "=", 76], ["stage_id", "=", 182]]],
    {"fields": ["id", "name", "state"], "limit": 200}
)
task_ids = [t["id"] for t in tasks]
models.execute_kw(DB, uid, TOKEN, "project.task", "write",
    [task_ids, {"state": "1_done"}]
)
```

### Common gotchas
- `kanban_state` field does NOT exist in Odoo 19 — use `state` instead
- List DB names: `xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/db").list()`
- Find stage IDs: query `project.task.type` with `project_ids in [project_id]`
- Run script with `python -X utf8` on Windows to avoid emoji encoding errors

---

## Example Workflows

### Workflow 1: Report and Track Bug
```
# Step 1: Create critical bug
Project: Soundwise
Task: Payment webhook timeout
Type: bug
Description: Webhook requests timeout after 5s, payments not recorded
Assignee: Phuc Do
Tags: [bug, payment, critical]
Priority: 0

# Step 2: Move to In Progress (when work starts)
Project: Soundwise
Task: Payment webhook timeout
New Status: In Progress
Notes: Investigation started

# Step 3: Move to Develop (when fixing)
Project: Soundwise
Task: Payment webhook timeout
New Status: Develop
Notes: Implemented retry logic with exponential backoff

# Step 4: Close (when complete)
Project: Soundwise
Task: Payment webhook timeout
Summary: ✅ Added retry logic (3 attempts, 5s timeout). 
         Tested with production webhook volume. 
         Monitoring for 48 hours before marking complete.
```

### Workflow 2: Create and Complete Feature
```
# Create feature task
Project: TRS
Task: Dark mode support
Type: enhance
Description: Add system dark mode detection and theme toggle
Assignee: Anh Huynh
Tags: [enhance, ui, ux]
Status: Todo

# Later: Move to Develop
Project: TRS
Task: Dark mode support
New Status: Develop

# Complete feature
Project: TRS
Task: Dark mode support
Summary: ✅ Implemented CSS variables for theming.
         Added system preference detection.
         Tested on Chrome, Firefox, Safari, mobile browsers.
         Ready for QA.
```

---

## Using with Claude Code

### Invoke the Skill
```
I need to log a bug in Soundwise project:
- Task: Login button broken on mobile
- Type: bug
- Assignee: Phuc Do
- Tags: bug, mobile, urgent
- Priority: Critical
```

### Skill Response
1. Shows confirmation dialog with auto-expanded description
2. Waits for your "yes" or "no"
3. Creates task or cancels based on your response
4. Shows result summary and JSON

### Move Task
```
Move "Login button broken" in Soundwise from Todo to In Progress
Notes: Investigation in progress
```

### Close Task
```
Close "Payment webhook timeout" in Soundwise
Summary: Fixed with retry logic, tested in production
```

---

## Tips for Best Results

1. **Be Specific** - Detailed descriptions generate better auto-expansions
2. **Use Correct Project Name** - Exact spelling matters (case-sensitive)
3. **Choose Right Task Type** - Affects auto-expansion format
4. **Add Meaningful Tags** - Helps with filtering and reporting
5. **Review Confirmation** - Check auto-expanded description before confirming
6. **Include Context in Notes** - When moving tasks, explain the change

---

## Read More
See `references/workflow_guide.md` for:
- Complete workflow examples
- Troubleshooting guide
- Best practices
- Error messages explanation
- Input validation rules
