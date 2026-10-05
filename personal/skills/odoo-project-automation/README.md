# Odoo Project Automation Skill

## 🎯 What This Skill Does

Automates task and bug management in the InApps Odoo 19 ERP (`https://erp.inapps.net`, DB `inapps`).

**Trigger rule:** only when the user's message contains "Odoo" or "ERP". Project names alone (Soundwise, TRS, HVS…) never trigger it.

**Core Features:**
- ✅ Create tasks/bugs with auto-expanded HTML descriptions
- ✅ Move tasks through stages (BackLog → TODO → INPROGRESS → DEVELOPED → READY FOR TEST → DONE)
- ✅ Close tasks with completion summaries (`state = "1_done"`)
- ✅ Update task details (assignee via `user_ids`, tags via `tag_ids`, description)
- ✅ Smart confirmation workflow (always asks before executing)
- ✅ Comprehensive error handling with helpful suggestions

SKILL.md is the source of truth if anything here disagrees.

---

## 📁 Skill Structure

```
odoo-project-automation/
├── SKILL.md                          # Main skill documentation (source of truth)
├── README.md                         # This file
├── evals/
│   └── evals.json                   # Test cases
├── scripts/
│   └── __pycache__/                 # Leftover bytecode only — no .py sources, not used
└── references/
    ├── quick_reference.md           # Syntax cheat-sheet
    └── workflow_guide.md            # Complete workflow guide
```

---

## 🚀 Quick Start

### 1. Create a Bug Task
```
Project: Soundwise
Task Name: Login button not responding
Task Type: bug
Description: Button click doesn't work on mobile
Assignee: Phuc Do
Tags: ["bug"]
Priority: "3" (Urgent)
```

**What Happens:**
1. Skill validates project & assignee exist (`mcp__odoo__search_records`)
2. Shows confirmation dialog with auto-expanded description
3. Waits for your "yes" or "no"
4. Creates task in Odoo (if confirmed) via `validate_write` → `execute_approved_write`

### 2. Move Task Through Workflow
```
Project: TRS
Task Name: Database migration
Action: move
New Status: INPROGRESS
Notes: Schema design approved
```

**Stages:** BackLog → TODO → INPROGRESS → DEVELOPED → READY FOR TEST → DONE

### 3. Close Task with Summary
```
Project: Olivia - CRM App
Task Name: User profile page
Action: close
Summary: ✅ Feature complete, tested with 50+ records
```

---

## 📋 Available Projects

| Project | project_id | Purpose |
|---------|-----|---------|
| **Soundwise** | 76 | Main application |
| **TRS** | - | Task/Resource System |
| **Olivia - CRM App** | 64 | CRM application |
| **Website InApps** | 79 | Company website |
| **FCCX** | 80 | i18n RU/UA |

Not exhaustive — resolve others with an `ilike` search on `project.project`.

---

## 👥 Available Assignees

- Phuc Do (Lead Backend)
- Phat Dinh (Frontend Lead)
- Anh Hoang (QA)
- Anh Huynh (Frontend)
- Demo User
- Gotham (Infrastructure)
- Hoa Tran (Backend)
- Huong Nguyen (Backend)
- InApps Customer Success

---

## 🏷️ Task Types

| Type | Description | Auto-Expansion Format |
|------|-------------|-----|
| **bug** | Defects/issues | Steps to Reproduce + Expected + Actual |
| **task** | Features/work | Implementation Plan + Success Criteria |
| **enhance** | Improvements | Proposed Solution + Benefits |
| **refactor** | Code cleanup | Objective + Plan + Risks |
| **docs** | Documentation | Scope + Format + Audience |

## 🔢 Priority (Odoo 19 `project.task.priority`)

| Value | Label | Stars |
|---|---|---|
| `"3"` | Urgent | ⭐⭐⭐ |
| `"2"` | High | ⭐⭐ |
| `"1"` | Medium | ⭐ |
| `"0"` | Low | — |

No `"4"`; `"0"` is the LOWEST — never use it for critical.

## 🏷️ Tags

Confirmed live: `bug` (5), `Task` (6), `Enhancement` (27), `Feedback` (28), `Customer` (1). Older notes say `"bugs"` — the live record name is `bug`. Any other tag name: search `project.tags` first.

---

## 📊 Workflow Stages

```
BackLog (175) → TODO (176) → INPROGRESS (177) → DEVELOPED (180) → READY FOR TEST (181) → DONE (182)
```

**Rules:**
- Stage names are UPPERCASE — search with `ilike`
- Odoo allows moving to any stage (forward, back, or reopening DONE) — there is no enforced transition rule
- The done "circle" is the separate `state` field (`1_done`), not a stage and not `kanban_state`

---

## ✅ Key Features

### 1. **Auto-Expanded Descriptions**
- Different templates per task type
- Fills in standard sections automatically
- Example bug format:
  ```
  Steps to Reproduce:
  1. [auto-filled]
  2. [auto-filled]
  
  Expected Result:
  [auto-filled]
  
  Actual Result:
  [your description]
  ```

### 2. **Confirmation Workflow**
- Always shows preview before action
- Waits for explicit "yes" or "no"
- Prevents accidental changes
- Shows full details including auto-expanded description

### 3. **Error Handling**
- Validates project exists → ❌ Error if not
- Validates assignee exists → ❌ Error if not
- Validates target stage exists in the project → ❌ Error if not
- Provides helpful suggestions in error messages

### 4. **Dual Output Format**
- **Human-readable:** Emoji + formatted text (default)
- **JSON:** Complete details for integration/logging

---

## 📝 Implementation Details

### How it talks to Odoo
- All reads/writes via **`mcp__odoo__*`** tools: `search_records` → `preview_write` / `validate_write` → `execute_approved_write` (`confirm=true`); chatter via `chatter_post`.
- The old `scripts/odoo_manager.py` / `scripts/skill_handler.py` no longer exist — don't look for them.
- Fallback only: Python XML-RPC for binary image attachments (`ir.attachment` + `message_post`) — see SKILL.md "Bulk Operations → Fallback".

### API Connection
- **Endpoint:** `https://erp.inapps.net` (API calls must NOT use `/odoo/` — 303 redirect)
- **API key:** never stored in this skill folder — read at runtime from a local credentials file / env var
- **Deprecation:** XML-RPC/JSON-RPC (`/xmlrpc`, `/xmlrpc/2`, `/jsonrpc`) are scheduled for removal in Odoo 22 (fall 2028); replacement is `POST /json/2/<model>/<method>` with `Authorization: bearer <API_KEY>`

---

## 💡 Usage Examples

### Example 1: Report Critical Bug
```
I found a critical bug in Soundwise on Odoo - the payment webhook is timing out 
after 5 seconds. This is blocking all transactions.

Details:
- Task: Payment webhook timeout
- Type: bug
- Assignee: Phuc Do
- Tags: bug
- Priority: "3" (Urgent)
```

**Skill Response:**
1. Shows confirmation with auto-expanded bug format
2. Displays: Steps to Reproduce, Expected Result, Actual Result sections
3. Waits for your confirmation
4. Creates task with all details

### Example 2: Create Enhancement
```
On Odoo: we want to add caching to our search queries for better performance.

Details:
- Project: TRS
- Task: Add caching to search queries
- Type: enhance
- Assignee: Anh Huynh
- Tags: Enhancement
```

**Skill Response:**
1. Shows confirmation with enhancement format
2. Displays: Proposed Solution, Benefits, Acceptance Criteria
3. Waits for confirmation
4. Creates task

### Example 3: Move Task to DONE
```
Move "User profile page" in Olivia - CRM App on Odoo from DEVELOPED to DONE
Summary: Feature complete, tested with 50+ user profiles, performance <2s
```

**Skill Response:**
1. Shows confirmation with task details
2. Displays: Current stage → New stage
3. Waits for confirmation
4. Moves task to DONE with summary

---

## 🔒 Confirmation Flow

**Why confirmation?** Prevents accidental task creation/modification.

**Example confirmation dialog:**
```
╔════════════════════════════════════════════════════════════════╗
║                   CREATE TASK - PLEASE CONFIRM                  ║
╚════════════════════════════════════════════════════════════════╝

📋 Task Details:
  Project:     Soundwise
  Task Name:   Payment webhook timeout
  Type:        bug
  Assignee:    Phuc Do
  Status:      TODO
  Tags:        bug
  Priority:    3 (Urgent)

📝 Description (Auto-expanded):
────────────────────────────────────────────────────────────────
[BUG REPORT - 2026-05-05 10:30:45]

STEPS TO REPRODUCE:
1. Send webhook request to /webhooks/payment
2. Wait for response
3. Observe timeout error after 5 seconds

EXPECTED RESULT:
Webhook processes within 2 seconds

ACTUAL RESULT:
Payment webhook is timing out after 5 seconds, blocking transactions

...
────────────────────────────────────────────────────────────────

⚠️  Please review the details above.
✅ Type 'yes' or 'confirm' to proceed
❌ Type 'no' or 'cancel' to abort
```

**How to respond:**
- ✅ **Approve:** "yes", "confirm", "ok", "proceed"
- ❌ **Cancel:** "no", "cancel", "abort"

---

## 🐛 Error Handling

### Project Not Found
```
❌ ERROR: Project 'InvalidName' not found
Available: Soundwise, TRS, Olivia - CRM App, Website InApps, FCCX, ...
```
**Fix:** Use exact project name

### Assignee Not Found
```
❌ ERROR: Assignee 'John Doe' not found
Available: Phuc Do, Phat Dinh, Anh Hoang, Anh Huynh, ...
```
**Fix:** Use exact assignee name

### Stage Not Found
```
❌ ERROR: Stage 'Develop' not found
Available: BackLog, TODO, INPROGRESS, DEVELOPED, READY FOR TEST, DONE
```
**Fix:** Use the real UPPERCASE stage name

---

## 🎓 Best Practices

1. **Be Specific** - Detailed descriptions → Better auto-expansion
2. **Use Correct Names** - Project/assignee names are case-sensitive
3. **Choose Right Type** - Affects auto-expansion format
4. **Review Confirmation** - Check details before confirming
5. **Add Context** - Include notes when moving tasks
6. **Tag Consistently** - Helps with filtering/reporting

---

## 📚 Documentation

- **SKILL.md** - Main skill reference with all features (source of truth)
- **references/quick_reference.md** - Syntax cheat-sheet
- **references/workflow_guide.md** - Complete workflow examples and troubleshooting
- **evals.json** - Test cases showing real usage scenarios

---

## 🔧 Integration

### With Claude Code
```
I need to create a bug in Soundwise project on Odoo...
```
Skill triggers because the message contains "Odoo".

### With Odoo
Tasks are created directly in Odoo ERP (UI: `https://erp.inapps.net/odoo/`)

### Output Formats
- **Display:** Emoji + formatted text (user-friendly)
- **API:** JSON format for integration/logging

---

**Endpoint:** `https://erp.inapps.net` · **Odoo:** 19.0 · **Access:** `mcp__odoo__*` tools (XML-RPC fallback only for binary attachments)
