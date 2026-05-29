---
name: qa-bug-report
description: Write professional, detailed bug reports with reproduction steps, screenshots references, severity classification, and root cause analysis. Use when asked to "write a bug report", "log a bug", "document this issue", "create a defect", "report a bug", or when a test fails and needs documentation.
---

# QA Bug Report Skill

You are a **Senior QA Engineer** writing a professional bug report for a development team.

## Severity Classification

Before writing, classify the bug:

| Severity | Criteria | Examples |
|----------|----------|---------|
| **P0 - Blocker** | App crashes, data loss, security breach, cannot proceed | Login broken, payment fails, data corruption |
| **P1 - Critical** | Core feature broken, no workaround | Can't create records, API returns 500 always |
| **P2 - Major** | Feature broken but workaround exists | Filter doesn't work, wrong data shown |
| **P3 - Minor** | Minor functional issue | Wrong label, incorrect tooltip |
| **P4 - Cosmetic** | UI/UX issue, no functional impact | Alignment off, wrong color |

## Bug Report Template

Generate a bug report in this format:

```markdown
## Bug Report: [Short, clear title — WHAT is broken, WHERE]

**ID:** BUG-[auto or sequential]
**Date:** [today]
**Reporter:** QA
**Severity:** P[0-4] - [Blocker/Critical/Major/Minor/Cosmetic]
**Status:** Open
**Assignee:** [dev team / component owner if known]

---

### Environment
- **URL/App:** [specific URL or app area]
- **Browser/OS:** [e.g. Chrome 123 / Windows 11]
- **Test Environment:** [staging / production / local]
- **User Role:** [admin / regular user / guest]
- **Test Data Used:** [specific account, record ID, etc.]

---

### Summary
[1-2 sentences: what happened vs what should happen]

---

### Steps to Reproduce
1. Go to [specific URL or screen]
2. [Exact action] — e.g. "Click the 'Save' button"
3. [Exact action]
4. Observe: [what actually happens]

**Minimum reproduction:** [Can you reproduce with fewer steps? Simpler data?]

---

### Expected Behavior
[What SHOULD happen according to requirements/design]

---

### Actual Behavior
[What ACTUALLY happens — be specific, include error messages verbatim]

```
Error: [paste exact error message]
```

---

### Evidence
- [ ] Screenshot: [description of what screenshot shows]
- [ ] Video: [if applicable]
- [ ] Console errors: [paste relevant errors]
- [ ] Network request: [paste relevant API call/response if applicable]
- [ ] Logs: [paste relevant log lines]

---

### Frequency
- [ ] Always (100%)
- [ ] Often (>50%)
- [ ] Sometimes (<50%)
- [ ] Rare (<10%)

**Reproducible on:** [list browsers/envs where reproduced]

---

### Impact
- **Who is affected:** [all users / admins only / specific condition]
- **Business impact:** [what workflow breaks, what's the workaround if any]
- **Data integrity risk:** [yes/no — does this corrupt or lose data?]

---

### Root Cause Analysis (if known)
[Optional: suspected cause from reading the code or error trace]

---

### Suggested Fix (if known)
[Optional: specific file/line/approach if you know it]

---

### Related
- Related to PR: #[number]
- Related tickets: #[number]
- First seen: [date or commit]
```

## How to Use This Skill

1. If the user describes a bug verbally, ask for any missing critical info (environment, steps, error message).
2. If a test failure is provided (Playwright report, console error, etc.), read it carefully and auto-populate the report.
3. Always include exact error messages — never paraphrase errors.
4. For Playwright failures: include the failed assertion, the selector used, and the full error stack.
5. Suggest severity based on the impact described.
6. Flag if this looks like a **regression** (was working before).

## Test Bug vs System Bug Classification

⚠️ **Before filing, confirm this is a SYSTEM bug, not a TEST bug.**

| Symptom | Likely class | Evidence needed |
|---|---|---|
| Test code expects X, app does Y, app is correct per spec | TEST BUG | Show the spec/Figma — fix test, don't file |
| Test selector matches wrong element | TEST BUG | DOM inspection showing real element |
| Test fills only required fields; non-required field doesn't persist | Could be either | Test by filling ALL fields manually; if still fails → SYSTEM |
| App shows validation error on valid input | SYSTEM BUG | Screenshot + Network tab showing API response |
| App fails silently on valid input | SYSTEM BUG | Screenshot + console + Network tab |

Reference: `feedback_fill-all-required-field-types` — only filling required fields can make
SYSTEM-looking bugs appear that are actually test bugs.

## Bug Report Naming Convention

Use this pattern for filenames + IDs:
- `BUG-<NN>-<short-slug>` — e.g. `BUG-24-create-redirect`
- Screenshot path: `data/outputs/screenshots/bug<NN>_<context>.png`
- Always link to the verification spec if one exists (e.g. `tests/cms/_verify_24.spec.ts`)

## Regression Detection Checklist
Ask yourself:
- Was this feature tested before? Check git blame or recent PRs.
- Does the error suggest a recent change broke something?
- Can you bisect it to a specific commit?

---

## Log to Odoo (Auto-Bridge)

Sau khi viết xong bug report, **luôn hỏi:**

> "Bạn muốn log bug này lên Odoo luôn không?"

### Mapping severity → Odoo priority

| Bug Severity | Odoo Priority |
|---|---|
| P0 Blocker / P1 Critical | 3 sao (urgent) |
| P2 Major | 2 sao |
| P3 Minor / P4 Cosmetic | 1 sao |

### Format description cho Odoo (HTML)

```html
<p><strong>Summary:</strong> [1-2 câu mô tả bug]</p>

<p><strong>Steps to Reproduce:</strong></p>
<ol>
  <li>[Step 1]</li>
  <li>[Step 2]</li>
  <li>Observe: [actual behavior]</li>
</ol>

<p><strong>Expected:</strong> [expected behavior]</p>
<p><strong>Actual:</strong> [actual behavior — paste error message nếu có]</p>

<p><strong>Evidence:</strong> Screenshot / console error / network tab</p>
<p><strong>Environment:</strong> [staging/prod] | [browser] | [role]</p>
<p><strong>Frequency:</strong> [Always/Often/Sometimes]</p>
```

### Cách thực hiện

Khi user confirm log Odoo → delegate sang `odoo-project-automation` skill.  
**Không** gọi MCP `mcp__odoo__*` trực tiếp — luôn qua skill.

Thông tin cần truyền sang skill:
- Task name: bug title (từ bug report)
- Priority: mapped từ severity ở trên
- Description: HTML format ở trên
- Project: hỏi user nếu chưa rõ (Incard, Inapps, HVS, etc.)

### Cross-references

- **odoo-project-automation** — thực hiện Odoo log operation
- **qa-session-close** — khi đóng session, include Odoo task ID vào handoff note
