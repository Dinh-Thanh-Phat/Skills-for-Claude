---
name: microcopy-readability
description: >-
  Evaluate the WORDS in a UI — readability, sentence length, passive voice, jargon, vague link text —
  on a live page, with computed scores. Use when complementing a UX evaluation, or when the user asks
  to "check the copy", "is this text clear", "readability", "microcopy", "UX writing", "đánh giá nội
  dung/chữ", "chữ có dễ hiểu không", "văn phong". Produces Flesch-Kincaid grade + flags. Complements
  ux-heuristic-evaluation (H2 match-real-world). Scores are OBSERVED (computed); tone/brand-voice
  judgment is PREDICTED and needs a human.
---

# Microcopy & Readability

Users read **at most ~20–28% of the words on a page** (NN/g). Dense, jargon-y, passive copy raises
cognitive load even when nothing is "broken". This skill scores the text so copy problems become
concrete. Companion to [[ux-heuristic-evaluation]] (heuristic H2 "match the real world").

## Targets (general consumer/B2B web)
| Signal | Target | Why |
|---|---|---|
| Flesch-Kincaid Grade | **≤ 8** | ~8th-grade is the common plain-language guideline (the US Plain Writing Act itself sets no grade number) |
| Flesch Reading Ease | **60–70+** | higher = easier |
| Avg sentence length | **15–20 words** | longer → harder to parse |
| Passive-voice ratio | low (flag clusters) | passive hides the actor |
| Generic link text | 0 | "click here" / "read more" / "learn more" hurt scanning & a11y |
| Jargon / internal terms | 0 surfaced to users | DB codes, acronyms, vendor-speak |

## How to measure (no install needed — formula is simple)
Extract the user-facing text (headings, body, labels, button text) from the live page, then:

- **If Python `textstat` / npm `text-readability` is available**, use it: `flesch_kincaid_grade`,
  `flesch_reading_ease`, `gunning_fog`, `text_standard`.
- **Else compute Flesch directly** (counts only — robust, dependency-free):
  - Reading Ease = `206.835 − 1.015·(words/sentences) − 84.6·(syllables/words)`
  - FK Grade = `0.39·(words/sentences) + 11.8·(syllables/words) − 15.59`
  - Syllable count heuristic: count vowel-groups per word (regex `/[aeiouy]+/g`), subtract trailing
    silent "e", floor at 1. Good enough for grade-level screening.
  - SMOG needs ≥30 sentences — skip on short copy rather than report garbage.
- **Flags via DOM/text:** passive voice (`\b(is|are|was|were|be|been|being)\b\s+\w+ed\b` as a cheap
  screen; spaCy `nsubjpass` if available), generic links (`getByRole('link')` text in a banned set),
  ALL-CAPS runs, walls of text (paragraph > ~75 words).

Scope to the SECTION under evaluation (a form, a hero, an error message) — don't average the whole
site into one meaningless number. Report per-block.

## Report
```
# Microcopy — [page/section]
- Flesch-Kincaid grade: 12.4  → ❌ above grade 8 (too dense)
- Reading ease: 41 → hard
- Avg sentence: 27 words → ❌ trim
- Flags: 3 passive clauses · 2 "Learn more" links · jargon: "GRT/DWT/LOA" unexplained
- Worst block: [quote the actual sentence] → suggested rewrite: [shorter, active]
```
Quote the actual offending text (OBSERVED), then suggest a concrete rewrite.

## Limits
- Readability scores measure *form*, not *meaning* — a grade-6 sentence can still be wrong or unhelpful.
- **Tone, brand voice, persuasiveness, and whether the copy actually helps the task = needs a human.**
  Mark those PREDICTED.
- Don't score nav labels / single words with sentence-based formulas (garbage in).
