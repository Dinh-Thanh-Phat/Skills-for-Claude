---
name: conversion-funnel-audit
description: >-
  Audit a conversion flow (sign-up / lead form / checkout) for friction against Baymard-style
  research benchmarks — field count, guest checkout, inline validation, autocomplete, trust signals.
  Use when evaluating a form/checkout/signup, complementing a UX evaluation, or when the user asks
  about "conversion", "checkout UX", "form too long", "abandonment", "đánh giá form/đăng ký/thanh
  toán", "tỉ lệ chuyển đổi". Emits RISK FLAGS vs benchmarks (not predicted conversion %). Complements
  ux-heuristic-evaluation. Structural checks are OBSERVED; uplift magnitude is PREDICTED / needs A-B.
---

# Conversion / Funnel Audit

Conversion flows leak users to fixable friction. Avg cart abandonment is **70.22%** (Baymard, 50
studies); top *fixable* causes: extra costs 39%, **forced account 19%**, distrust 19%, **too long/
complex 18%**. Cutting a form 11→4 fields ≈ **+120%** conversions (HubSpot). This skill flags those
risks structurally. Companion to [[ux-heuristic-evaluation]] (and [[form-validation-testing]] for the
functional side).

## Checklist — emit a RISK FLAG per failing item (OBSERVED via DOM)
Source: https://baymard.com/lists/cart-abandonment-rate , https://baymard.com/blog/checkout-flow-average-form-fields

**Form length & effort**
- [ ] Visible required fields **> 8** → 🚩 (avg checkout 11.3; aim ≤ 8; each extra field costs completion)
- [ ] Asks for data not needed yet / could be derived (e.g. manual address vs postcode lookup) → 🚩
- [ ] No sensible defaults / no field pre-fill where possible → 🚩

**Friction reducers present?**
- [ ] `autocomplete` attrs on name/email/address/cc fields (else browser can't autofill) → 🚩 if missing
- [ ] `inputmode="numeric"` / `type="tel"`/`"email"` on the right fields (mobile keyboards) → 🚩 if missing
- [ ] **Inline, per-field validation** (error shown at the field on blur, not only on submit) → 🚩 if missing
- [ ] Clear single primary CTA per step (not competing buttons) → 🚩

**Checkout/commerce specifics**
- [ ] **Guest checkout** offered (not forced account creation) → 🚩 (forced account = 19% abandon)
- [ ] Total incl. shipping/fees visible **before** the payment step → 🚩 (extra-cost surprise = 39%)
- [ ] Trust signals near payment (HTTPS lock, security/badge, return policy) → 🚩 if absent
- [ ] Step count shown / progress indicator on multi-step → 🚩 if missing

**Touch (if mobile applies)** — tap targets ≥ 44 pt; numeric keypad for numeric fields.

## How to run (read-only)
Navigate to the flow with Playwright (do NOT submit real data). For each step:
- Count visible inputs/required; read `type`, `inputmode`, `autocomplete`, `required` attributes.
- Detect inline validation by triggering blur on an empty/invalid field and checking for a field-level
  message (read-only — no submit). If you can't without submitting, mark it PREDICTED.
- Screenshot each step.

## Report
```
# Conversion audit — [flow]  (steps: N)
🚩 HIGH: forced account creation (no guest option) — 19% abandonment driver
🚩 MED: 11 fields (aim ≤8) — consider splitting/removing [list the trimmable ones]
🚩 MED: no inline validation — errors only surface on submit
🟢 OK: autocomplete present · total shown before payment · HTTPS+badge
Priority: [the HIGH flags first]
```

## Limits
- These are **risk flags from research benchmarks**, OBSERVED structurally. The **actual uplift** from
  fixing them is PREDICTED — only A/B testing on real traffic confirms magnitude. Never quote a
  specific "+X% conversion" as a promise.
- Whether a field is *truly* necessary is a business call — flag, don't dictate.
