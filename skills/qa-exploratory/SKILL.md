---
name: qa-exploratory
description: Guide exploratory testing sessions with structured charters, heuristics, and observation frameworks. Use when asked to "explore this feature", "do exploratory testing", "test this manually", "what could go wrong", "test this like a user", "find bugs in", "session-based testing". Applies SBET (Session-Based Exploratory Testing) methodology.
---

# QA Exploratory Testing Skill

You are a **Senior QA Engineer** running a structured exploratory testing session.

## Methodology: Session-Based Exploratory Testing (SBET)

Exploratory testing is NOT random clicking. It is:
- **Simultaneous** learning, design, and execution
- **Time-boxed** (typically 60-90 min sessions)
- **Documented** with observations and findings
- **Charter-driven** with a mission and scope

---

## Session Charter Template

Start every exploratory session with a charter:

```markdown
## Exploratory Testing Charter

**Mission:** Explore [feature/area] to discover [type of issues]
**Target:** [specific feature, page, flow]
**Tester:** [name]
**Duration:** [e.g., 60 min]
**Environment:** [staging / prod / local]
**Build/Version:** [commit or version]

**Focus areas:**
1. [Primary area]
2. [Secondary area]

**Out of scope:**
- [What you're NOT exploring today]
```

---

## Exploratory Testing Heuristics (SFDPOT)

Apply these heuristics systematically:

### S — Structure
- What are the data structures? (tables, forms, lists)
- What are the field constraints? (types, lengths, formats)
- What happens with empty states?
- What happens with maximum data?

### F — Function
- What does this feature claim to do?
- Does it actually do it?
- Does it do anything it shouldn't?
- What are the success criteria?

### D — Data
- Test with valid/invalid/missing data
- Test with special characters: `'; DROP TABLE`, `<script>`, `null`, `undefined`, `0`, `-1`
- Test with Unicode, emojis, RTL text
- Test with very long strings (>255 chars)
- Test with whitespace-only input

### P — Platform
- Different browsers: Chrome, Firefox, Safari, Edge
- Different screen sizes: mobile (375px), tablet (768px), desktop
- Different OS: Windows, Mac, mobile
- Slow network (DevTools throttle to 3G)
- Offline behavior

### O — Operations
- What operations can a user perform?
- Can they do them in unexpected orders?
- What if they do the same operation twice?
- What if they interrupt an operation (navigate away mid-submit)?
- What if they use browser back/forward?

### T — Time
- What happens with session timeouts?
- What if there's a slow API response?
- What about concurrent actions (two tabs, two users)?
- What about date/time boundaries? (midnight, new year, DST)

---

## Observation Log Template

During the session, log every observation:

```markdown
## Session Notes — [date] [start time]

### Charter
[paste charter]

---

### Observations

**[HH:MM] OBS-001 — [brief title]**
- What I did: [exact action]
- What happened: [exact observation]
- Expected: [what should have happened]
- Severity: [Bug/Question/Enhancement/Note]
- Evidence: [screenshot, console error]

**[HH:MM] OBS-002 — ...**

---

### Session Summary
- Duration: [X min]
- Areas covered: [list]
- Areas NOT covered (future sessions): [list]
- Bugs found: [count by severity]
- Questions raised: [list]
- Automation candidates identified: [list]
```

---

## Exploratory Testing Checklists

### For Web Forms
- [ ] Submit with all fields empty
- [ ] Submit with only required fields filled
- [ ] Submit with maximum valid data
- [ ] Paste instead of type (different clipboard data)
- [ ] Use Tab key to navigate all fields
- [ ] Use Enter to submit (keyboard-only flow)
- [ ] Drag text into fields
- [ ] Right-click field (context menu behavior)
- [ ] Copy-paste email with spaces around it
- [ ] Try SQL injection: `' OR '1'='1`
- [ ] Try XSS: `<img src=x onerror=alert(1)>`
- [ ] Submit the same form twice quickly (double-click)
- [ ] Refresh page mid-form (does data persist?)

### For Lists/Tables
- [ ] Empty state (no records)
- [ ] Single record
- [ ] Very large data set (1000+ records)
- [ ] Sort each column (ascending/descending)
- [ ] Filter combinations
- [ ] Select all + bulk action
- [ ] Pagination (first, last, jump to page)
- [ ] Search with special characters
- [ ] Search with no results

### For Modals/Dialogs
- [ ] Click outside to close
- [ ] Press Escape to close
- [ ] Scroll inside modal
- [ ] Open modal, navigate back (browser back)
- [ ] Multiple overlapping modals

### For Authentication
- [ ] Login with wrong password
- [ ] Login with correct password + wrong email
- [ ] Access protected page without login (direct URL)
- [ ] Login, then paste another user's resource URL
- [ ] Logout, then press browser back
- [ ] Login from two browsers simultaneously
- [ ] Session expiry behavior

### For File Upload
- [ ] Upload correct file type
- [ ] Upload wrong file type
- [ ] Upload empty file (0 bytes)
- [ ] Upload very large file
- [ ] Upload file with special characters in name
- [ ] Upload multiple files if allowed
- [ ] Cancel upload mid-progress

---

## Bug Hunting Mindset

Think like an attacker, a confused user, and a broken network:
1. **What assumptions does this code make?** Violate them.
2. **What's the happy path?** Find all the sad paths.
3. **What's new?** Recent changes = higher regression risk.
4. **What's complex?** Complex logic = more bugs.
5. **What's integrated?** Integration points = failure points.

## Charters for Specific Test Types

### API Exploratory Charter
```markdown
**Mission:** Explore /api/users endpoints for security and edge cases
**Methods to test:** GET, POST, PUT, DELETE, OPTIONS
**Heuristics:**
- Missing required fields → 400 with clear message?
- Wrong types (string where number expected) → 400?
- SQL injection in path/query → blocked at validation, not at DB?
- Auth token expired → 401? Wrong scope → 403?
- Pagination edge: page=0, page=-1, page=10000?
- Rate limit: send 100 requests in 1s → 429?
- Bulk endpoint: send 10000 items?
```

### Mobile App Exploratory Charter
```markdown
**Mission:** Explore checkout flow on Android + iOS
**Heuristics:**
- Background app mid-flow → state preserved when resumed?
- Lock screen → unlock → still authenticated?
- Network drop mid-submit → recovery?
- Low memory: kill app → re-open → state?
- Permission denied for camera/location → graceful fallback?
- Notification tap → deep link works?
- Slow 3G network — does UI lock up?
```

Common places bugs hide:
- First time user experience
- After logout/login
- With special characters
- When session expires
- When API is slow or fails
- On mobile browsers
- After browser refresh
