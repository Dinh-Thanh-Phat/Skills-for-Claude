---
name: ask-when-stuck
description: "⚠️ P0 — HIGHEST PRIORITY. Use when: (1) UI element/locator not found after 1-2 attempts, (2) test keeps failing after 1-2 fix attempts, (3) timeout is unclear after 1 measurement, (4) any repeated failure with no clear root cause. STOP and ask BEFORE attempt 3."
priority: P0
---

# Ask When Stuck — P0 Skill

## ⚠️ Priority: HIGHEST (P0)

**This skill overrides the instinct to keep trying.** When you are stuck, asking is not giving up — it is the correct action. Every extra attempt without information is wasted tokens and wasted time.

---

## Core Rule

```
Attempt 1: Most obvious approach
Attempt 2: One reasonable alternative

→ Still failing? STOP IMMEDIATELY. Ask the user.
```

**Do NOT proceed to attempt 3.**

---

## This Applies To All Stuck Scenarios — Not Just Locators

| Stuck Scenario | After 1-2 tries → Ask for |
|---------------|--------------------------|
| Element/locator not found | Screenshot, HTML snippet, exact label |
| Test assertion keeps failing | Screenshot of actual state, console errors |
| Timeout unclear (what's slow?) | Server logs, network tab, environment info |
| Flaky test root cause unknown | Timing data, server behavior, env details |
| API/request failing unexpectedly | Response body, server logs, auth state |
| Step transition not happening | Video/trace of what actually renders |

---

## Red Flags — Stop Immediately

These thoughts mean you are rationalizing continued guessing:

| Thought | Reality |
|---------|---------|
| "Let me try one more selector" | After 2 tries, ask. More tries = more wrong. |
| "Maybe the element has a different class" | You can't see the DOM. The user can. Ask. |
| "I'll try all common patterns" | Wastes tokens, still gets it wrong. |
| "Let me increase the timeout again" | You don't know what's slow. Measure first, then ask if unclear. |
| "One more fix and I'll have it" | This is the thought that leads to 10 failed attempts. |
| "Let me check the source one more time" | Source without visual context still fails. Ask for screenshot. |
| "The test is probably just flaky" | "Probably" = you don't know. Ask for evidence. |

---

## Asking Templates

### For UI element not found:
```
Tôi đang cố tìm [element description] nhưng sau 2 lần thử vẫn chưa tìm được đúng.

Bạn có thể cung cấp:
- [ ] Screenshot của màn hình hiện tại
- [ ] Text/label hiển thị trên element đó
- [ ] Hoặc inspect element và paste HTML snippet cho tôi

Điều này giúp tôi tìm đúng selector ngay lần đầu.
```

### For test keeps failing:
```
Test [tên test] đã fail 2 lần liên tiếp với cùng lỗi: [error message]

Tôi cần thêm thông tin để xác định root cause:
- [ ] Screenshot hoặc video của lần fail gần nhất
- [ ] Console errors (nếu có)
- [ ] Behavior thực tế vs. expected behavior

Thay vì thử lần 3, tôi muốn xác nhận với bạn trước.
```

### For timeout/flaky test:
```
Test [tên test] bị timeout sau [X]s. Tôi đo được [operation] mất khoảng [Y]s
nhưng chưa rõ nguyên nhân tại sao lại chậm như vậy.

Bạn có biết:
- [ ] Staging server có cold start behavior không?
- [ ] Có request nào đang pending / queue không?
- [ ] Gần đây environment có thay đổi gì không?
```

---

## Why P0 — Lesson Learned (April 2026)

During auth test fixing, the "keep trying" instinct caused:
- Timeout escalation: 15s → 25s → 45s (3 iterations with no measurement)
- Test timeout: 30s → 60s → 90s (3 iterations with no measurement)
- Total waste: 4 test runs (~15 min) before reaching stable config

**What one well-timed question would have revealed:**
- "Replit cold start can take 28-30s on first request"
- → Set all timeouts correctly in ONE step instead of three

**The cost of asking:** ~30 seconds  
**The cost of not asking:** 15+ minutes of trial and error

---

## When This Does NOT Apply

- You have a clear DOM snapshot and just need to refine syntax
- The element is found but behavior is unexpected (different problem — that's debugging)
- You are exploring codebase structure (not finding UI elements)
- First attempt succeeded partially (has useful signal to continue)
