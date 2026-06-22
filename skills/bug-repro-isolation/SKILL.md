---
name: bug-repro-isolation
description: >
  Reproduce and attribute a bug correctly BEFORE you report it — change one variable at a
  time, use the minimal repro path, and never blame the user action you were testing for an
  effect that an environmental change (page reload, re-navigation, re-login, cache clear, new
  tab) actually caused. Use this skill whenever you are about to claim "doing X causes Y",
  assign a bug severity, or write a bug report from an exploratory/QA session — especially if
  your repro involved more than one step between the trigger and the symptom. Triggers on:
  "X causes Y", "back button wipes data", "this breaks when", "reproduce the bug", "confirm
  the bug", "why does this happen", "assign severity", "log this bug", "data is lost when",
  "stuck after", any exploratory testing where you attribute a cause.
---

# Bug Reproduction & Cause Isolation

A bug report is a **causal claim**: "doing X produces wrong result Y." If the X is wrong, the
whole report is wrong — engineers chase a phantom, the real bug stays open, and you burn trust.
The single most common way to get X wrong is to **change two things at once** and credit the
effect to the more interesting one.

This skill exists because of a real failure: an evaluator reported **"clicking Back wipes the
user's saved data — Major data-loss bug."** What actually happened: they had **reloaded the
page** (resuming a flow at a later step) *and then* clicked Back. The empty form was caused by
the **reload not re-hydrating the form**, not by Back. In a clean session, Back preserved
everything. Two variables (reload + Back) were changed; the effect was blamed on Back. The user
had to catch it. Don't be that evaluator.

## The one rule that prevents most false bugs

**Isolate one variable.** Between the start state and the symptom, change exactly one thing —
the thing you want to test. If your repro path contains a reload, a re-login, a navigation, a
tab switch, a network blip, a different account, *and* the action under test, you cannot yet say
which one caused the symptom. This is the scientific-method core of debugging: control every
variable except the one under study, or your result is confounded and meaningless.

## Symptom observed ≠ mechanism confirmed

Seeing the bad outcome (empty form, stuck button, wrong number) means you confirmed a **symptom**.
It does **not** mean you confirmed the **cause**. These are two separate verification steps:

| You saw | You may write | You may NOT yet write |
|---|---|---|
| The form was empty | "Form renders empty after <full path>" | "Back **wipes** data" (names a cause) |
| The button stayed disabled | "Button disabled in state Z" | "Validation **is broken**" (names a mechanism) |
| The number was wrong | "Total showed 0 here" | "The sum **doesn't update**" (names a cause) |

A cause-naming verb (*wipes, breaks, loses, deletes, ignores, fails to*) is a promise you found
the mechanism. Don't use one until you've isolated the trigger.

## Severity follows the confirmed cause, not the scary symptom

"Data loss" *sounds* like Severity-3/Major, so there's pressure to label it that the instant you
see an empty field. Resist. **Severity is a property of the confirmed mechanism, not of the
symptom's vibe.** A scary-looking symptom with an unconfirmed or benign cause (data is safe in
the backend; only the form failed to re-hydrate) is not Major. Assign severity *after* isolation,
and re-check: *is the data actually gone, or just not shown?* Backend-persisted + UI-not-rendered
is a very different (and lower) severity than true destruction. (Mirrors the evidence discipline
in [[ux-heuristic-evaluation]]: a `PREDICTED` cause can't carry a high severity.)

## The workflow

1. **State the causal claim explicitly.** Write the sentence you intend to report: "When the
   user does **X**, **Y** happens." Underline X. That is the *only* variable allowed to change.

2. **List every variable in your current repro path.** Be honest. Reload? New tab? Re-login?
   Came from a different step? Different data/account? Prior failed submit? Each is a suspect.

3. **Reduce to the minimal path.** Strip every step that isn't X. Reproduce from the cleanest
   start state with **only** X between start and symptom. If you can't reproduce Y now, X was not
   the cause — one of the steps you stripped was. Go find which (add them back one at a time).

4. **Run the control (the A/B).** Do the exact same path **without** X. If Y still happens
   without X, X is innocent. (Clean session, no reload: does Back *still* preserve data? If yes,
   "Back wipes data" is refuted.) The control is what turns a guess into a finding.

5. **Distinguish symptom from cause.** Confirm what's really true: is the data gone from the
   system, or just not displayed? Probe the layer that matters (backend record, network call,
   stored state) — not just the rendered DOM.

6. **Only now: name the cause and assign severity.** Write the report with the isolated trigger,
   note the control you ran, and set severity from the confirmed mechanism.

## After isolating the cause: is it actually NEW, and is it ONE bug?

Isolating the cause is not the last step. Two more checks decide whether you have a *finding* worth
reporting as new — skip them and you'll waste the team's time re-raising what they already track.

**1. Dedup against what's already known.** Before you label anything "new", map the confirmed cause
to the existing backlog / known-issues list / tickets you logged this session. A different *symptom*
(empty form, stuck button, lost edit, wrong number) does **not** make it a new bug if it traces back
to a cause already on file. Ask: *"If this cause were fixed, would my finding disappear too?"* If yes,
it's the same bug — link to the existing ticket, don't open a new one. You usually don't have the
whole backlog in view, so when unsure, **say "is this already tracked?" and ask** rather than
asserting novelty.

**2. Collapse symptoms to their root — one cause = one issue.** A single underlying defect often
surfaces as several symptoms across the flow (e.g. "reload empties form", "exit loses input",
"interrupt sends you back to step 2", "re-entry shows blank" can all be *one* root: the flow never
persists/re-hydrates state). Reporting each symptom as a separate "finding" inflates the list and
hides that they share one fix. Group them under the root cause; list the symptoms as evidence of it,
not as independent bugs.

> Real failure (22-Jun, onboarding): after correctly isolating "the form never re-hydrates state", I
> presented reload-loss, exit-loss, interrupt-reset, and blank-re-entry as *four new findings* — they
> were all the **one known root** (N1 data-loss) plus the known duplicate-create bug. The user replied
> "list này toàn cái cũ mà" (this list is all old). Lesson: isolating the cause ≠ the cause being new.

## When you can't fully isolate

If you genuinely can't strip a variable (e.g., the symptom only appears after a real reload),
then **the reload is part of the trigger** — say so precisely: "Form does not re-hydrate after a
page reload when resuming at step N" is a correct, useful report. "Back wipes data" is not. Name
the trigger you actually proved, even if it's narrower or less dramatic than your first guess.

## Red flags — stop and isolate

- Your repro has a reload / re-login / navigation **and** the action you're blaming.
- You're about to write *wipes / breaks / loses / deletes / ignores* and you haven't run the control.
- You're assigning Major/Critical from the symptom's scariness, before isolating the cause.
- You changed two things since the last good state and only mention one in the report.
- A teammate says "I can't reproduce that" — that's usually a confound in *your* path, not theirs.
  Re-derive the minimal repro before defending the finding.
- You're about to call something "new" / "I found a bug" without checking it against the known-issues
  list — and you haven't asked "is this already tracked?"
- Your report has several findings that would all be fixed by the **same** change — that's one bug
  with many symptoms, not many bugs.

## Relationship to other skills

- Run this the moment you attribute a cause during [[playwright-diagnosis-first]] or any
  exploratory pass — it's the isolation step before "fix" or "report".
- Feeds [[qa-bug-report]]: the "Steps to Reproduce" you log must be the **minimal isolated path**,
  plus the control you ran ("Back alone preserves data; only after reload does the form empty").
- Complements [[ux-heuristic-evaluation]] evidence discipline (`OBSERVED` vs `PREDICTED`) — here
  the analog is *symptom observed* vs *cause confirmed*.
- When still stuck after isolating, escalate per [[ask-when-stuck]] rather than guessing a cause.
