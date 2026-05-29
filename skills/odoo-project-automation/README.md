# Odoo Project Automation Skill

## 🎯 What This Skill Does

Automates task and bug management in your Odoo ERP system at `https://erp.inapps.net/odoo/`.

**Core Features:**
- ✅ Create tasks/bugs with auto-expanded descriptions
- ✅ Move tasks through workflow states (Backlog → Todo → In Progress → Develop → Done)
- ✅ Close tasks with completion summaries
- ✅ Update task details (assignee, tags, description)
- ✅ Smart confirmation workflow (always asks before executing)
- ✅ Comprehensive error handling with helpful suggestions

---

## 📁 Skill Structure

```
odoo-project-automation/
├── SKILL.md                          # Main skill documentation
├── README.md                         # This file
├── evals/
│   └── evals.json                   # Test cases
├── scripts/
│   ├── odoo_manager.py              # Core Odoo API manager (mock + real)
│   └── skill_handler.py             # Skill handler with confirmation flow
└── references/
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
Tags: ["bug", "mobile"]
Priority: 0 (Critical)
```

**What Happens:**
1. Skill validates project & assignee exist
2. Shows confirmation dialog with auto-expanded description
3. Waits for your "yes" or "no"
4. Creates task in Odoo (if confirmed)

### 2. Move Task Through Workflow
```
Project: TRS
Task Name: Database migration
Action: move
New Status: In Progress
Notes: Schema design approved
```

**Workflow:** Backlog → Todo → In Progress → Develop → Done

### 3. Close Task with Summary
```
Project: Olivia - CRM App
Task Name: User profile page
Action: close
Summary: ✅ Feature complete, tested with 50+ records
```

---

## 📋 Available Projects

| Project | Purpose |
|---------|---------|
| **Soundwise** | Main application |
| **TRS** | Task/Resource System |
| **Olivia - CRM App** | CRM application |

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

---

## 📊 Workflow States

```
Backlog → Todo → In Progress → Develop → Done
```

**Rules:**
- Can move forward one state at a time
- Can move back one state at a time
- Cannot skip states
- Cannot leave Done (terminal state)

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
- Validates workflow transitions → ❌ Error if invalid
- Provides helpful suggestions in error messages

### 4. **Dual Output Format**
- **Human-readable:** Emoji + formatted text (default)
- **JSON:** Complete details for integration/logging

---

## 📝 Implementation Details

### Files

**odoo_manager.py** (Core Manager)
- `OdooManager` class handles all Odoo operations
- Supports mock mode (default) and real API mode
- Methods:
  - `create_task()` - Create new task/bug
  - `move_task()` - Move to different status
  - `close_task()` - Mark as Done
  - `update_task()` - Update details
  - `list_projects()` - List all projects
  - `validate_inputs()` - Validate project/assignee

**skill_handler.py** (User Interface)
- `OdooSkillHandler` class orchestrates user interactions
- Methods:
  - `show_confirmation_dialog()` - Show preview
  - `execute_create_task()` - Create with confirmation
  - `execute_move_task()` - Move with confirmation
  - `execute_close_task()` - Close with confirmation
  - `process_confirmation()` - Handle "yes"/"no" response

### API Connection
- **Endpoint:** `https://erp.inapps.net/odoo/`
- **Authentication:** XML-RPC with token
- **Token:** Securely stored in skill handler
- **Mode:** Mock (testing) or Real (production)

---

## 💡 Usage Examples

### Example 1: Report Critical Bug
```
I found a critical bug in Soundwise - the payment webhook is timing out 
after 5 seconds. This is blocking all transactions.

Details:
- Task: Payment webhook timeout
- Type: bug
- Assignee: Phuc Do
- Tags: bug, payment, critical
- Priority: 0 (Critical)
```

**Skill Response:**
1. Shows confirmation with auto-expanded bug format
2. Displays: Steps to Reproduce, Expected Result, Actual Result sections
3. Waits for your confirmation
4. Creates task with all details

### Example 2: Create Enhancement
```
We want to add caching to our search queries for better performance.

Details:
- Project: TRS
- Task: Add caching to search queries
- Type: enhance
- Assignee: Anh Huynh
- Tags: enhance, performance
```

**Skill Response:**
1. Shows confirmation with enhancement format
2. Displays: Proposed Solution, Benefits, Acceptance Criteria
3. Waits for confirmation
4. Creates task

### Example 3: Move Task to Production
```
Move "User profile page" in Olivia - CRM App from Develop to Done
Summary: Feature complete, tested with 50+ user profiles, performance <2s
```

**Skill Response:**
1. Shows confirmation with task details
2. Displays: Current status → New status
3. Waits for confirmation
4. Moves task to Done with summary

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
  Status:      Todo
  Tags:        bug, payment, critical
  Priority:    0 (Critical)

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
Available: Soundwise, TRS, Olivia - CRM App
```
**Fix:** Use exact project name

### Assignee Not Found
```
❌ ERROR: Assignee 'John Doe' not found
Available: Phuc Do, Phat Dinh, Anh Hoang, Anh Huynh, ...
```
**Fix:** Use exact assignee name

### Invalid Status Transition
```
❌ ERROR: Cannot move from 'Done' to 'In Progress'
Done is terminal state (final)
```
**Fix:** Create new task instead

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

- **SKILL.md** - Main skill reference with all features
- **workflow_guide.md** - Complete workflow examples and troubleshooting
- **evals.json** - Test cases showing real usage scenarios

---

## 🔧 Integration

### With Claude Code
```
I need to create a bug in Soundwise project...
```
Skill automatically triggers and handles the request.

### With Odoo
Tasks are created directly in Odoo ERP at `https://erp.inapps.net/odoo/`

### Output Formats
- **Display:** Emoji + formatted text (user-friendly)
- **API:** JSON format for integration/logging

---

## ✨ Summary

This **odoo-project-automation** skill provides a complete, user-friendly interface to Odoo task management with:

- ✅ Smart auto-expansion of descriptions (5 task types)
- ✅ Confirmation workflow (prevents accidents)
- ✅ Full error handling (helpful error messages)
- ✅ Workflow state management (linear progression)
- ✅ Team management (9 assignees)
- ✅ Multi-format output (human-readable + JSON)
- ✅ Comprehensive documentation (SKILL.md + guides)

**Ready to use!** Just invoke the skill and let it guide you through creating, moving, and closing tasks in Odoo.

---

**API Endpoint:** `https://erp.inapps.net/odoo/`  
**Authentication:** Secure token-based  
**Mode:** Mock (default, testing) or Real API (production)  
**Status:** ✅ Complete and ready for deployment
