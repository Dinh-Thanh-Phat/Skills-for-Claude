---
name: ux-heuristic-evaluation
description: >-
  Evaluate whether a feature's WORKFLOW is good from a user-experience standpoint —
  even when there are ZERO functional bugs. Use this whenever a feature "works correctly
  but feels inconvenient / clunky / has too many steps / is confusing", or when the user
  asks to "đánh giá trải nghiệm", "đánh giá UX", "workflow này ổn không", "review usability",
  "feature chạy đúng nhưng bất tiện", "đánh giá luồng", "assess user experience",
  "heuristic evaluation", "usability review", "is this flow good", "too many steps",
  "UX audit", "friction", "cognitive walkthrough". This produces a scored UX report with
  friction points + severity (0-4) + concrete fixes — it does NOT hunt for functional bugs
  (use qa-exploratory for bugs, accessibility-testing for a11y). Trigger it even when the
  user only hints that something "feels off" experientially rather than naming UX explicitly.
---

# UX Heuristic & Workflow Evaluation

You are a **Senior UX/QA Engineer** running a structured usability evaluation. Your job is to
answer a question that functional testing cannot: **"This feature has no bugs — but is the
workflow actually good for users?"**

A feature can pass every functional test and still be a bad experience: too many steps,
asks for data too early, hides the next action, gives no feedback, forces recall instead of
recognition. Those are **usability defects**, and they cost real users real time and frustration
even though nothing is technically "broken". This skill finds, rates, and reports them.

## What this skill is NOT

Stay in your lane — this keeps reports credible:

- **Not bug hunting.** If a feature throws an error, crashes, or saves wrong data → that's
  `qa-exploratory` (functional/edge cases) or `qa-bug-report`. Don't relabel a functional bug
  as a "UX issue".
- **Not accessibility auditing.** Screen-reader / WCAG color-contrast / keyboard-trap testing →
  `accessibility-testing`. (Touch-target *size* overlaps — see §Mobile — but full a11y is its own skill.)
- **Not coverage planning.** Enumerating every scenario to test → `behavioral-coverage-matrix`.

This skill assumes the feature works and asks **"is it pleasant and efficient to use?"**

## The core principle: separate "works" from "works well"

When you evaluate, hold two mental columns:

| Functional (other skills) | Experiential (THIS skill) |
|---|---|
| Does it do what it claims? | Is the path to do it short and obvious? |
| Are there errors/crashes? | When something goes wrong, can the user recover easily? |
| Is data saved correctly? | Did we ask for that data at the right time, or too early/too much? |
| Does the button work? | Is the button where the user's eyes/thumb expect it? |

Every finding you log must be experiential. If you catch yourself writing "this returns a 500
error" — stop, that's a bug, route it elsewhere.

---

## Evidence discipline — READ THIS FIRST (the part that makes the report trustworthy)

Heuristic evaluation has a brutal, well-measured reliability problem. Treat your own findings as
**suspects, not verdicts**, until you have seen the breakdown with your own eyes.

**Why this is non-negotiable (the numbers):**
- **Evaluator effect** (Hertzum & Jacobsen 2003): agreement between any two evaluators on the same
  system is only **5–65%**. One pass by one evaluator is *low-reliability by definition*.
- **False positives**: across studies, **34–65% of heuristic-evaluation predictions are NOT real
  problems** (Bailey 43% false; Woolrych & Cockton 65% of predictions false). Expert inspection
  *invents* problems a real user never hits, because the evaluator imagines the user instead of
  observing one.
- **DOM/code presence ≠ user reality**: automated/code signals catch only ~30–40% of real issues.
  An element existing in the DOM does not mean it's visible/reachable; a label being *present* in
  markup does not mean it's *announced or usable*. (In this skill's own pilot run, **five** findings
  inferred from code/DOM — chip "click trap", placeholder-as-label, "no Step N of 4", back data-loss,
  empty-submit advancing — were each **refuted by a screenshot**. Half the first-pass findings were
  wrong. Do not repeat this.)

**The rules — apply to every single finding:**

1. **Tag each finding `OBSERVED` or `PREDICTED`.**
   - `OBSERVED` = you saw the breakdown in a native screenshot or a real interaction trace.
   - `PREDICTED` = inferred from code, DOM, a measurement, or reasoning, but NOT yet seen.
   - **Never report a `PREDICTED` finding as if confirmed.** It carries a ~35–65% false-positive base
     rate. Either confirm it (promote to `OBSERVED`) or list it under "To verify", not under Findings.

2. **A heuristic violation is necessary, not sufficient.** "Label is ambiguous" is not a finding —
   it's a hypothesis. A real problem needs a plausible **user breakdown** (slowed / blocked / errs /
   wrong choice) AND a **causal mechanism** tying the UI property to that breakdown. No breakdown, no
   mechanism → it's speculative; downgrade it.

3. **Observation overrides inference, always.** When a DOM/measurement says one thing and a screenshot
   says another, **the screenshot wins.** If a programmatic probe returns a sentinel / uncertain value
   (e.g. an Alpine query returns -1), do NOT report from it — confirm visually or drop it. See
   [[feedback_visual-bug-native-screenshot-only]].

4. **Record what you REFUTED.** Findings you checked and cleared are first-class output — they prove
   rigor and stop others re-raising them. A report that only lists problems, with no refuted column,
   is a red flag that you didn't verify.

5. **Rank by user impact, not by count.** Heuristic eval over-produces minor issues (Jeffries et al.).
   Ten cosmetic notes are worth less than one task-blocking finding. Volume is a vanity metric.

6. **State your reliability honestly.** One pass = low reliability. Say so in the verdict; don't imply
   completeness you didn't earn (see Coverage dimensions in §E and the "what was NOT covered" rule).

---

## Evaluation workflow

Pick the method(s) that fit the request. You can combine them — they layer well.

```
                ┌─ Broad "is this screen/feature usable?"  → Heuristic Evaluation (§A)
Request type ───┼─ "Is this flow confusing for a NEW user?" → Cognitive Walkthrough (§B)
                └─ "Is this workflow efficient / too many steps?" → Workflow Efficiency (§C)
                          ↓
                   Quantify with measurable signals (§D, automatable)
                          ↓
                   Score & report with severity (§E)
```

Always start by **defining the task(s)** under evaluation in the user's terms
("a new user signs up and creates their first invoice"). UX is meaningless without a task —
a screen isn't "good" or "bad" in the abstract, only relative to what someone is trying to do.

If you don't know the real user goal or the intended happy path, **ask** before evaluating —
guessing the goal produces a worthless report. (See [[feedback_ask-when-stuck]] discipline:
don't fabricate context.)

### A. Heuristic Evaluation (Nielsen's 10)

Inspect the feature against the 10 heuristics. For each violation, log a **candidate** finding
(mark it `PREDICTED`) — then confirm it against a native screenshot or real interaction before it
graduates to a reported finding (see **Evidence discipline** above; a heuristic violation alone is a
hypothesis, not a problem). This is the
default broad method. The 10 heuristics, the severity scale, and worked examples live in
**`references/heuristics-and-metrics.md` §1–§2** — read it before running this method so you
apply the exact wording and rate consistently.

Quick mental pass per screen: *Does the system tell me what's happening? Does it speak my
language? Can I undo? Is it consistent? Does it stop me from making errors? Can I recognize
instead of recall? Are there shortcuts for experts? Is it visually minimal? Are errors
recoverable in plain language? Is help findable?*

### B. Cognitive Walkthrough (first-use / learnability)

Use when the concern is **"a brand-new user will get confused/stuck"**. Step through the
happy path action-by-action and ask the four questions at **every** step:

1. Will the user try to achieve the right result? (do they know this step is needed?)
2. Will they notice the correct action is available? (is it visible/findable?)
3. Will they associate that action with their goal? (is the label clear?)
4. After acting, will they see progress toward the goal? (is there feedback?)

A "no" at any step is a finding. This catches the *"I don't know what to do next"* class of
problem that heuristics alone miss. Full method in `references/heuristics-and-metrics.md` §4.

### C. Workflow Efficiency analysis

Use when the complaint is **"too many steps / clunky / tedious"**. Compare the **actual
happy-path** against the **theoretical minimum** for the goal, and look for:

- **Redundant steps** — confirmations that don't guard a destructive/irreversible action
  (prefer Undo over an upfront "Are you sure?" when the action is reversible).
- **Premature data entry** — asking for info before it's needed, or info you could derive
  (e.g. manual address typing where a postcode lookup would do).
- **Excessive data entry** — more form fields than the task requires (benchmark: aim ≤ ~8
  fields; completion drops noticeably past that — see §D).
- **Backtracking / pogo-sticking** — the user has to bounce between screens to gather what
  one screen should have shown.
- **Attention/context switches** — the flow scatters one logical task across unrelated places.

Frame fixes around the principle "do the hard work to make it simple" — every step removed
is a step the user doesn't pay for. Reference the **Interaction Cost** checklist
(`references/heuristics-and-metrics.md` §5) — it enumerates the 9 efforts to minimize.

### D. Quantify with measurable signals

Subjective findings land harder with numbers. These signals are **automatable** — capture
them during a real run (web via Playwright, mobile via Maestro):

| Signal | How to capture | Read it as |
|---|---|---|
| **Steps / clicks / taps** to complete | Count interactions in the trace | vs theoretical minimum — gap = potential redundancy |
| **Time-on-task** | `t(success) − t(start)` | baseline-relative only (no universal threshold) |
| **Screens / page-loads** traversed | Count route/screen changes | feeds Lostness |
| **Lostness L** | `L = √[(N/S − 1)² + (R/N − 1)²]` where N=unique screens, S=total visited, R=minimum needed | **L<0.4 not lost · 0.4–0.5 borderline · >0.5 lost** |
| **Backtracking** | Repeated screen IDs / back-nav count | high = poor information scent |
| **Form field count** | Count inputs the user must engage | aim ≤ ~8; each extra field past that costs completion |
| **Scroll distance** | Sum scroll deltas / viewport-heights | baseline-relative; high = buried content |
| **Error/U-turn rate** | Failed submits, validation toasts, dead-end clicks | experiential friction, not functional bugs |

**Do NOT invent absolute pass/fail thresholds** for time-on-task, click count, or error rate —
they are baseline-relative. The only hard, research-backed thresholds you may assert are the
**Lostness bands** above and **touch-target sizes** (see Mobile). The "3-click rule" is debunked —
never bake in a click cap; use Lostness + information scent instead. (Details & sources in §3.)

> **⚠️ A measured/DOM signal is a hypothesis, not a finding.** Counting inputs, reading
> `disabled`, probing app state (Alpine/React), checking a label exists in markup — these are
> `PREDICTED` evidence at best. Element-in-DOM ≠ visible/reachable; label-in-markup ≠ announced or
> usable; `min=1` attribute ≠ enforced. Confirm the user-facing effect in a screenshot before
> reporting (per Evidence discipline). If a probe returns an uncertain/sentinel value, drop it —
> don't build a finding on it.

If you want a **perceived-usability score**, administer **SUS** (System Usability Scale) — 10
questions, 0–100, where **68 = average**. Bands and scoring in `references/heuristics-and-metrics.md` §6.
SUS needs human respondents, so use it when real users/stakeholders are available, not for a
pure inspection.

### E. Score & report

See the report template below. Every reported finding gets a **severity 0–4** (NNGroup scale),
derived from **frequency × impact × persistence** — a minor-looking issue that hits every user,
every time, and never goes away escalates toward 3–4 — and an evidence tag (`OBSERVED`/`PREDICTED`).
A `PREDICTED` finding may not carry a severity ≥3; promote it to `OBSERVED` first.

**Coverage dimensions — sweep these BEFORE you give a verdict (don't wait to be asked).**
A single happy-path pass is low-reliability. A flow isn't "evaluated" until you've at least
considered each dimension and said which you covered vs skipped:

- [ ] **Happy path** — the intended successful flow
- [ ] **Empty / first-use state** — zero data, brand-new account (often the worst experience)
- [ ] **Error / validation** — submit empty, invalid input, the disabled/blocked path
- [ ] **Boundary** — min/max, limits, very long names, max selections
- [ ] **Keyboard-only** — can every control be reached & operated by Tab/Enter? focus order sane?
- [ ] **Mobile / touch** — reflow, touch-target sizes, thumb reach (if product is used on mobile)
- [ ] **Long-running / async** — the wait experience (progress? cancel? leave & return?)
- [ ] **Slow network** — does the UI show system status under throttle?
- [ ] **Back / interruption** — does going Back or backgrounding lose entered data?

Cover what's relevant to the task; **explicitly list which dimensions you did NOT cover** in the
report so nobody mistakes one pass for completeness. A true heuristic evaluation converges over
multiple passes (and ideally multiple evaluators — agreement between any two is only 5–65%), not in
one shot.

---

## Web vs Mobile

The heuristics are platform-agnostic; measurement and some checks differ.

**Web (Playwright):** instrument the run to count clicks, route changes, and time; use
`browser_snapshot` to read the actual UI tree (don't guess layout). Throttle network to expose
"visibility of system status" gaps (does the UI show progress on slow connections?).

**Mobile (Maestro):** count taps/screens from the flow; additionally evaluate mobile-specific
heuristics that have **hard, citable thresholds**:

- **Touch-target size** — Apple HIG **44×44 pt**, Material **48×48 dp**, WCAG 2.2 AA **24×24 px**
  (min), WCAG AAA **44×44 px**. Targets below these, or spaced < 8 dp apart, are findings.
- **Thumb-zone / reachability** — primary actions belong in the bottom/center "green zone";
  rare/destructive actions in the hard-to-reach top corners. ~75% of interactions are thumb-driven.
- **Gesture discoverability** — a gesture must never be the *only* way to do something; pair it
  with a visible control (gestures are a hidden UI with low memorability).
- **Interruption handling** — mobile sessions are short (~72s) and interrupted; does state survive
  backgrounding / a phone call / notification? Is there Undo for accidental taps?

Full mobile table with exact numbers and sources in `references/heuristics-and-metrics.md` §7.

---

## Report structure

ALWAYS produce this exact structure so findings are actionable and comparable across sessions:

```markdown
# UX Evaluation — [Feature / Flow name]

**Task(s) evaluated:** [the user goal(s), in user terms]
**Method(s):** [Heuristic / Cognitive Walkthrough / Workflow Efficiency]
**Platform:** [Web / Android / iOS] · **Build:** [version/commit]
**Date / Evaluator:**

## Verdict
[1-2 sentences: is this workflow good? The headline a PM needs.]
[If measured: happy-path steps = X (min Y) · Lostness = Z · SUS = N]

## Findings

### UX-001 — [short title] · Severity [0-4: label]
- **Heuristic / step violated:** [e.g. "H1 Visibility of system status" or "Walkthrough Q4 at step 3"]
- **What happens:** [the experiential problem — what the user feels/does]
- **Why it hurts:** [frequency × impact × persistence reasoning that justifies the severity]
- **Evidence:** [screenshot ref / step count / lostness / measured number]
- **Recommendation:** [concrete fix — describe the better workflow, not just "improve UX"]

### UX-002 — ...

## Summary
- Findings by severity: [4: n] [3: n] [2: n] [1: n]
- Top 3 to fix first: [the severity-3/4 items]
- Measured signals: [steps, lostness, time, field count, etc.]
- Out of scope (route elsewhere): [any functional bugs spotted → qa-bug-report; a11y → accessibility-testing]
```

Severity labels (NNGroup): **0** not a problem · **1** cosmetic · **2** minor · **3** major ·
**4** catastrophe. Definitions in `references/heuristics-and-metrics.md` §2.

## Relationship to other skills

- Run **after** functional testing — once `qa-exploratory` confirms it works, this asks if it works *well*.
- **`accessibility-testing`** is the sibling for WCAG/screen-reader; this skill covers experiential
  flow + touch-target ergonomics, and defers full a11y there.
- **`behavioral-coverage-matrix`** defines *what tasks* to evaluate; this evaluates the *quality* of each.
- Spotted a real bug mid-evaluation? Log it via **`qa-bug-report`** — don't bury it as a UX note.

For exact heuristic wording, the severity definitions, SUS questions/bands, cognitive-walkthrough
template, interaction-cost checklist, mobile thresholds, and all source URLs, read
**`references/heuristics-and-metrics.md`**.
