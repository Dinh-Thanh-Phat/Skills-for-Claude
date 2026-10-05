---
name: qa-bug-report
description: Write professional, detailed bug reports with reproduction steps, screenshots references, severity classification, and root cause analysis. Use when asked to "write a bug report", "log a bug", "document this issue", "create a defect", "report a bug", or when a test fails and needs documentation.
---

# QA Bug Report Skill

You are a **Senior QA Engineer** writing a professional bug report for a development team.

> **Before you write a single line, isolate the cause — run [[bug-repro-isolation]].** A bug
> report is a causal claim ("X causes Y"); if your repro changed more than one thing (a reload,
> a re-login, a navigation, a different account) alongside X, you may be blaming the wrong
> trigger. The "Steps to Reproduce" below must be the **minimal isolated path**, and severity
> must come from the **confirmed mechanism**, not the symptom's scariness (e.g. "data loss" that
> turns out to be a render-only glitch with the record safe in the backend is not P0).

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

> ⚠️ **Never guess which side is which.** A reporter's shorthand like "lines are white not gray" / "X chứ không phải Y" is ambiguous — X may be the observed defect or the desired fix. If the note lacks an explicit Actual marker ("đang là", "hiện tại", "it shows") or Expected marker ("phải là", "should be"), echo the parsed pair back and confirm before writing the report. Cosmetic pairs (gray/white, indented/aligned) are symmetric — neither side "sounds more like a bug".

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

## Novelty & dedup check — BEFORE you file (or call anything "new")

Filing a bug, or telling the user "I found a new issue", is a claim of **novelty**. A re-discovery of
an already-tracked bug — even with a fresh symptom — wastes the team's time and erodes trust the same
way a wrong cause does. Run this before opening a ticket:

- **Map the confirmed cause to the existing backlog / tickets you already logged.** Different symptom,
  same root cause → it's the *same* bug. Link/append to the existing ticket; don't open a new one.
- **Test:** "If the known bug were fixed, would my finding vanish too?" Yes → not new.
- **Collapse symptoms to root:** several findings fixed by one change = **one** issue with many
  symptoms (list them as evidence), not several issues. See [[bug-repro-isolation]] "is it new, one bug?".
- **You rarely see the whole backlog.** When you can't verify it's untracked, **ask "is this already
  logged?" instead of asserting "new"** — then file only what the user confirms is missing.

(Lesson 22-Jun: presented 4 symptoms of one known data-loss root as "new findings" → user: "toàn cái
cũ mà". Isolating the cause did not make the cause new.)

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

Khi user confirm log Odoo → delegate sang `odoo-project-automation` skill (nếu đã cài; không có thì xuất bug report dạng markdown).  
**Không** gọi MCP `mcp__odoo__*` trực tiếp — luôn qua skill.

Thông tin cần truyền sang skill:
- Task name: bug title (từ bug report)
- Priority: mapped từ severity ở trên
- Description: HTML format ở trên
- Project: hỏi user nếu chưa rõ (Incard, Inapps, HVS, etc.)

### Cross-references

- **odoo-project-automation** — thực hiện Odoo log operation
- **qa-session-close** — khi đóng session, include Odoo task ID vào handoff note
