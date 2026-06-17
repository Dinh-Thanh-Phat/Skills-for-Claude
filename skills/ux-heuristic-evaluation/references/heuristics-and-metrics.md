# UX Evaluation Reference — Heuristics, Severity, Metrics, Mobile

Detailed reference for the `ux-heuristic-evaluation` skill. Read the section you need; don't
load the whole file unless doing a full multi-method evaluation.

## Table of contents
1. Nielsen's 10 Usability Heuristics
2. Severity Rating Scale (0–4)
3. Quantitative metrics & the debunked 3-click rule
4. Cognitive Walkthrough
5. Interaction Cost & cognitive-load taxonomy
6. System Usability Scale (SUS)
7. Mobile-specific heuristics & touch-target thresholds
8. Workflow efficiency & form benchmarks
9. Sources
10. Reliability & false-positives (why evidence discipline matters)

---

## 1. Nielsen's 10 Usability Heuristics

Source: NNGroup — https://www.nngroup.com/articles/ten-usability-heuristics/ (the canonical
1994 list, still maintained). Use the exact titles in findings so they're recognizable.

| # | Heuristic | Definition | Smell to look for |
|---|---|---|---|
| H1 | **Visibility of System Status** | Keep users informed via timely feedback. | No loading/progress indicator; action with no confirmation; silent saves. |
| H2 | **Match Between System and Real World** | Speak the user's language; familiar concepts, not jargon. | Internal codes/labels; database terms surfaced to users; unnatural ordering. |
| H3 | **User Control and Freedom** | Clear "emergency exit", undo/redo. | No way to cancel/go back; destructive action with no undo; trapped in a flow. |
| H4 | **Consistency and Standards** | Same word/action = same meaning; follow conventions. | Same thing named two ways; button in different place per screen; non-standard patterns. |
| H5 | **Error Prevention** | Prevent problems before they occur (better than error messages). | Easy to enter invalid data; no input constraints; no confirmation for irreversible acts. |
| H6 | **Recognition Rather than Recall** | Make options visible; don't force memory across screens. | User must remember a code/value from a previous screen; hidden options. |
| H7 | **Flexibility and Efficiency of Use** | Accelerators/shortcuts for experts, invisible to novices. | No keyboard shortcuts; no bulk actions; expert forced through novice path every time. |
| H8 | **Aesthetic and Minimalist Design** | Remove irrelevant/rarely-needed content. | Cluttered screen; competing CTAs; info dump where focus is needed. |
| H9 | **Help Users Recognize, Diagnose, Recover from Errors** | Plain-language errors; state problem; suggest fix. | Error codes shown to users; "Something went wrong" with no next step. |
| H10 | **Help and Documentation** | Ideally none needed; if present, findable & task-focused. | No help where it's needed; help that doesn't match the task. |

**How to run a heuristic evaluation** (https://www.nngroup.com/articles/how-to-conduct-a-heuristic-evaluation/):
3–5 independent evaluators ideally; each spends ~1–2 hrs over the same narrow scope.
Three phases: **Prepare** (agree scope + heuristics) → **Evaluate independently** (pass 1 = explore,
pass 2 = flag violations + recommendations) → **Consolidate** (cluster findings, agree severity).
When running solo as an agent, simulate the independent passes: do an exploration pass first,
then a deliberate violation-hunting pass, then rate.

---

## 2. Severity Rating Scale (NNGroup 0–4)

Source: https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/

| Rating | Exact definition |
|---|---|
| **0** | I don't agree that this is a usability problem at all. |
| **1** | **Cosmetic** problem only: need not be fixed unless extra time is available. |
| **2** | **Minor** usability problem: fixing this should be given low priority. |
| **3** | **Major** usability problem: important to fix, high priority. |
| **4** | **Usability catastrophe**: imperative to fix before release. |

Severity = combination of three factors. Reason explicitly about each in the finding:
- **Frequency** — common or rare?
- **Impact** — easy or hard for users to overcome?
- **Persistence** — one-time (overcome once learned) or repeatedly bothersome?

A cosmetic-looking issue that is **frequent + high-impact + persistent** escalates toward 3–4.
Conversely a scary-sounding issue that's rare and easily worked around may only be a 2.

---

## 3. Quantitative metrics & the debunked 3-click rule

Sources: https://www.nngroup.com/articles/usability-metrics/ ,
https://measuringu.com/task-completion/ , https://measuringu.com/lostness/

- **Task success rate** — observed average ≈ **78%** across ~1,200 tasks (MeasuringU). Treat
  <70–75% as a clear problem signal, but it's descriptive, not a regulatory threshold.
- **Time-on-task** — report the geometric mean; **baseline-relative only**, no universal constant.
- **Lostness L** — the most automatable composite (Smith 1996):

  ```
  L = sqrt[ (N/S − 1)^2 + (R/N − 1)^2 ]
  ```

  N = unique screens visited · S = total screens visited (with repeats) · R = minimum screens
  required (optimal path). Range 0 (perfect) → 1 (lost).
  **Thresholds:** L < 0.4 = not lost · 0.4–0.5 = indeterminate · > 0.5 = lost.
  All three inputs are countable from a Playwright/Maestro navigation trace.

- **3-click rule is DEBUNKED** (https://www.nngroup.com/articles/3-click-rule/): Porter's study
  (44 users / 620 tasks) found no drop-off or satisfaction change after the 3rd click; NN/g found
  findability *rose ~600%* when items moved to 4 clicks with better information scent. **Never bake
  a click cap into a finding.** Judge by information scent (do links clearly signal what's behind
  them?) and Lostness, not raw click count.

---

## 4. Cognitive Walkthrough

Source: https://www.nngroup.com/articles/cognitive-walkthroughs/
Template: https://media.nngroup.com/media/articles/attachments/Blank_Cognitive-Walkthrough_Template.pdf

Task-specific, learnability/first-use focused. Step through ONE task as a novice and ask at
**each step**:

1. Will the user **try to achieve the right result**? (do they know this action is needed?)
2. Will the user **notice the correct action** is available? (visible/findable?)
3. Will the user **associate the correct action** with the result they want? (label clarity?)
4. After the action, will the user **see progress** toward the goal? (feedback?)

A "no" at any question = a finding, tagged e.g. "Walkthrough Q3 at step 4 (Checkout)".

**vs Heuristic Evaluation:** walkthrough is task-path-specific and simulates a first-time user
(learnability). Heuristic eval is broad principle-based expert inspection, not tied to one path.
Use walkthrough for *"is this confusing to a new user"*, heuristics for *"does this violate
general usability principles"*.

---

## 5. Interaction Cost & cognitive-load taxonomy

**Interaction Cost** (NNGroup, https://www.nngroup.com/articles/interaction-cost-definition/) —
"the sum of efforts, mental and physical, that users must deploy to reach their goals." Minimize
these 9 components; each maps to a measurable signal — use as a friction checklist:

1. Reading
2. Scrolling
3. Looking around (locating info)
4. Comprehending information
5. Clicking or touching (without mistakes)
6. Typing
7. Page loads and waiting times
8. Attention switches
9. Memory load

**Cognitive load types** (apply to UI):
- **Intrinsic** — inherent task difficulty (can't remove, only manage).
- **Extraneous** — load from *how* the UI presents info (clutter, split attention). **This is the
  type to reduce** — declutter, group, progressive disclosure, recognition over recall.
- **Germane** — productive schema-building (helpful).

Measurement instrument for human studies: **NASA-TLX**.

---

## 6. System Usability Scale (SUS)

Sources: https://measuringu.com/sus/ , https://measuringu.com/interpret-sus-score/

10-item Likert questionnaire (Brooke 1996), administered post-task → single **0–100** global
score. Reliable even at small samples. Needs human respondents.

**Questions** (1 = Strongly Disagree → 5 = Strongly Agree; odd = positive, even = negative):
1. I think that I would like to use this system frequently.
2. I found the system unnecessarily complex.
3. I thought the system was easy to use.
4. I think I would need the support of a technical person to use this system.
5. I found the various functions in this system were well integrated.
6. I thought there was too much inconsistency in this system.
7. I would imagine that most people would learn to use this system very quickly.
8. I found the system very cumbersome to use.
9. I felt very confident using the system.
10. I needed to learn a lot of things before I could get going with this system.

**Scoring:** odd items → (response − 1); even items → (5 − response); each becomes 0–4; sum
(0–40); × 2.5 → **0–100**. The score is **not** a percentage.

**Interpretation:**
- **68 = average** (50th percentile, grade C). Above = above average.
- > 80.3 = grade A (≈ top 10%). < 51 = grade F (≈ bottom 15%).
- **Acceptability** (Bangor 2009): < 50 Not Acceptable · 50–70 Marginal · > 70 Acceptable.
- **Adjective scale**: 0–25 Worst Imaginable · 25–39 Poor · 39–51.6 OK · 51.7–73.5 Good ·
  73.6–85 Excellent · 85.1–100 Best Imaginable.
- Sauro–Lewis curved grades (full table at the source URL): A+ 84.1–100; A 80.8–84; B 74.1–77.1;
  C 65–71; D 51.7–62.6; F 0–51.6.

---

## 7. Mobile-specific heuristics & touch-target thresholds

Sources: https://www.nngroup.com/articles/mobile-ux/ ,
https://www.smashingmagazine.com/2016/09/the-thumb-zone-designing-for-mobile-users/ ,
https://www.nngroup.com/articles/touch-target-size/ ,
https://support.google.com/accessibility/android/answer/7101858 ,
https://m3.material.io/foundations/designing/structure

**Touch-target minimums (hard, citable — use as pass/fail):**

| Standard | Min size | Note |
|---|---|---|
| Apple HIG | **44 × 44 pt** | all controls |
| Material / Android | **48 × 48 dp** (≈ 9 mm) | icon may be 24×24 dp but tappable area must reach 48 dp via padding |
| WCAG 2.2 SC 2.5.8 (Minimum) | **24 × 24 CSS px** | Level AA; 24 px circle must not overlap a neighbor |
| WCAG 2.1 SC 2.5.5 (Enhanced) | **44 × 44 CSS px** | Level AAA |
| NNGroup | **1 cm × 1 cm** (≈ 10 mm) | physical recommendation |

Spacing: Material recommends **≥ 8 dp** between targets.

**Thumb zone / reachability:** green = easy reach (bottom-center) → primary actions/nav here;
yellow = stretch; red = hard (top corners) → rare/destructive actions here. ~49% hold the phone
one-handed; ~75% of interactions are thumb-driven (Hoober). This is why bottom nav / bottom sheets
work.

**Gesture discoverability:** gestures are a "hidden, alternate UI" with low memorability and
discoverability. **Never make a gesture the only path** to an action — always pair with a visible
control.

**One-handed use:** primary actions in the bottom/green zone; account for both left/right grips;
keep critical/destructive controls out of top corners.

**Interruption handling:** "design for interruptions." Mobile session ≈ **72s** vs desktop ≈ 150s.
Save state; allow resumption after calls/notifications/backgrounding; provide **Undo** (accidental
taps are common).

---

## 8. Workflow efficiency & form benchmarks

Sources: GOV.UK Service Manual
(https://www.gov.uk/service-manual/design/introduction-designing-government-services ,
https://designnotes.blog.gov.uk/2015/07/03/one-thing-per-page/ ,
https://www.gov.uk/guidance/government-design-principles) ,
Baymard (https://baymard.com/learn/ux-audit , https://baymard.com/research/checkout-usability ,
https://baymard.com/lists/cart-abandonment-rate)

- **Smallest number of steps:** "Good services get a user to take the smallest number of steps
  possible to reach their goal." Compare actual happy-path steps vs theoretical minimum to expose
  redundancy. Pattern **"one thing per page"** splits complexity while keeping each step minimal.
- **"Do the hard work to make it simple"** — GOV.UK design principle; complexity belongs to the
  builder, not the user.
- **Premature / excessive data entry:** "Reducing how much data a user has to give reduces how
  much they have to do." Canonical fix: postcode/address lookup vs manual entry. Don't ask for
  data you don't need or ask too early.
- **Redundant confirmations:** remove confirmation steps that don't guard a truly destructive/
  irreversible action; prefer **Undo** over upfront confirmation when the action is reversible.
- **Friction log / UX audit:** walk the end-to-end flow, record every confusion/hesitation/
  extra-effort point, color-code by severity, document with screenshots.

**Form / checkout benchmarks (Baymard):**
- Industry avg ≈ **11.3 form fields**; recommend **≤ ~8**. Each field past ~8 costs ~4–6%
  completion. Guest checkout 6–8 fields; a case study cut 16 → 8 fields.
- Forced account creation is a top abandonment cause.
- Cart abandonment **70.22%** overall (mobile **85.65%**); ~1 in 5 abandon due to "too long /
  complicated checkout"; fixing checkout usability can yield **+35.26%** conversion.

---

## 9. Sources (quick list)

- Nielsen 10 heuristics — https://www.nngroup.com/articles/ten-usability-heuristics/
- Running a heuristic eval — https://www.nngroup.com/articles/how-to-conduct-a-heuristic-evaluation/
- Severity ratings — https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/
- Cognitive walkthrough — https://www.nngroup.com/articles/cognitive-walkthroughs/
- Usability metrics — https://www.nngroup.com/articles/usability-metrics/
- Task completion — https://measuringu.com/task-completion/
- Lostness — https://measuringu.com/lostness/
- 3-click rule debunked — https://www.nngroup.com/articles/3-click-rule/
- Interaction cost — https://www.nngroup.com/articles/interaction-cost-definition/
- SUS — https://measuringu.com/sus/ , https://measuringu.com/interpret-sus-score/
- Mobile UX — https://www.nngroup.com/articles/mobile-ux/
- Thumb zone — https://www.smashingmagazine.com/2016/09/the-thumb-zone-designing-for-mobile-users/
- Touch target size — https://www.nngroup.com/articles/touch-target-size/
- Material touch targets — https://support.google.com/accessibility/android/answer/7101858
- GOV.UK service manual — https://www.gov.uk/service-manual/design/introduction-designing-government-services
- Baymard UX audit / checkout — https://baymard.com/learn/ux-audit , https://baymard.com/research/checkout-usability

---

## 10. Reliability & false-positives (why the SKILL.md "Evidence discipline" exists)

Heuristic/expert evaluation is **low-reliability and high-false-positive** unless you anchor every
finding to observation. The numbers below are the justification — quote them when stakeholders push
back on "but you only found a few confirmed issues".

**Evaluator effect** — Hertzum & Jacobsen (2003), *The Evaluator Effect: A Chilling Fact About
Usability Evaluation Methods*, IJHCI 15(1):183–204. https://mortenhertzum.dk/publ/IJHCI2003.pdf
- Agreement between **any two evaluators** on the same system with the same method is only
  **5–65%**. Affects heuristic eval, cognitive walkthrough, AND think-aloud; affects both problem
  detection and severity ratings; persists for novices and experts.
- Causes: vague goals → variable scenarios; vague procedure → anchoring; **vague problem criteria →
  "anything" gets logged as a problem.**
- It measures **reliability, not validity** — low agreement doesn't even tell you the findings are
  *correct*. Mitigation: **multiple evaluators**, merged; the effect is managed, not eliminated.

**False-positive rates** (predicted problems that real users never hit):
- Bailey, Allan & Raiello: **43%** of HE-flagged problems were not real; HE caught only **21%** of the
  genuine problems user-testing found. https://measuringu.com/effective-he/
- Cross-study: **~34%** of HE problems are "false alarms" not seen in user tests (same source).
- Woolrych & Cockton: **65% of HE predictions were false**; heuristics "mostly incorrectly confirm
  false predictions." https://researchportal.northumbria.ac.uk/en/publications/why-and-when-five-test-users-arent-enough
- Cockton & Woolrych, *Sale Must End* (Interactions IX.5, 2002): **69% of predictions tied to an
  inappropriate heuristic.** https://interactions.acm.org/archive/view/september-2002/sale-must-end1
- Jeffries et al. (CHI'91): HE finds the **most** problems but skewed to **minor** ones; user testing
  finds the **major** ones → count ≠ value.

**Why expert inspection over-predicts:** no real user is present, so the evaluator *imagines* one and
*predicts* a problem. Recognition that something violates a heuristic ≠ evidence a user is impeded. A
**real** problem = observed (or strongly predicted) **user breakdown** (slowed/blocked/errs/fails) +
a **causal mechanism**. A **speculative** finding has only a heuristic label and an imagined user.

**Automated/DOM signals mislead** — automated checks catch only **~30–40%** of real issues; the rest
need manual observation. https://testparty.ai/blog/automated-accessibility-testing-guide
- Element in DOM ≠ visible/reachable; alt/label *present* ≠ *meaningful or announced*; focusable ≠
  logical focus order; `min`/`max` attribute ≠ enforced. Treat all such signals as `PREDICTED`.

**Structured problem-report format** reduces false matches — Lavery, Cockton & Atkinson (1997),
*Comparison of evaluation methods using structured usability problem reports*, BIT 16(4–5):246–266.
https://www.tandfonline.com/doi/abs/10.1080/014492997119824 — report each finding as
**problem + observed evidence + user impact + causal context**, not just a heuristic name.

**Distilled rules (mirrored in SKILL.md Evidence discipline):** tag OBSERVED vs PREDICTED · heuristic
violation is necessary not sufficient · observation overrides inference · record refuted findings ·
rank by impact not count · state reliability (one pass = low) honestly.
