#!/usr/bin/env python3
"""vocab_tools.py — helpers for the english-vocab-coach skill.

Three subcommands:

  build-deck  Turn a JSON word list into an Anki/Quizlet-ready CSV.
  due         List words due for review today from a progress file.
  grade       Record a quiz result and reschedule the word (spaced repetition).

The spaced-repetition schedule is a simple, robust interval ladder (Leitner-style,
lightly SM-2 flavored): a correct answer promotes the word to the next interval,
a wrong answer sends it back to a 1-day interval so it comes around again soon.
This is intentionally simple — the value is in *honest timing*, not clever math.

All dates are plain calendar dates (YYYY-MM-DD) so a "day" means a day, which is
what a human learner actually experiences.

JSON input for build-deck (a list of objects):
[
  {
    "word": "resilient",
    "ipa": "/rɪˈzɪliənt/",
    "gloss_vi": "kiên cường, bền bỉ, mau phục hồi",
    "example": "She stayed resilient after losing her job.",
    "collocations": "remain resilient, resilient economy, resilient to shocks"
  }
]
Only "word" and "gloss_vi" are required; the rest are filled with "" if missing.
"""

import argparse
import csv
import datetime
import json
import sys
from pathlib import Path

# Interval ladder in days. A word climbs one rung per correct answer.
INTERVAL_LADDER = [1, 2, 4, 7, 14, 30, 60, 120]


def today():
    return datetime.date.today()


def parse_date(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()


def fmt_date(d):
    return d.strftime("%Y-%m-%d")


# --------------------------------------------------------------------------- #
# build-deck
# --------------------------------------------------------------------------- #
def build_deck(args):
    words = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(words, list) or not words:
        sys.exit("Input JSON must be a non-empty list of word objects.")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Anki front/back format. Front = word + IPA. Back = gloss + example + collocations.
    # Anki 2.1.54+ file headers (https://docs.ankiweb.net/importing/text-files.html):
    # declare separator/HTML/columns instead of a plain "Front,Back" row, which would
    # otherwise risk being imported as a card.
    with out.open("w", encoding="utf-8", newline="") as f:
        f.write("#separator:Comma\n#html:true\n#columns:Front,Back\n")
        w = csv.writer(f)
        for i, item in enumerate(words):
            word = (item.get("word") or "").strip()
            gloss = (item.get("gloss_vi") or "").strip()
            if not word or not gloss:
                sys.exit(f"Item {i} is missing required 'word' or 'gloss_vi'.")
            ipa = (item.get("ipa") or "").strip()
            example = (item.get("example") or "").strip()
            colls = (item.get("collocations") or "").strip()

            front = f"{word}<br><small>{ipa}</small>" if ipa else word
            back_parts = [gloss]
            if example:
                back_parts.append(f"<br><i>{example}</i>")
            if colls:
                back_parts.append(f"<br><b>Collocations:</b> {colls}")
            back = "".join(back_parts)
            w.writerow([front, back])

    print(f"Wrote {len(words)} cards -> {out}")
    print()
    print("Import into Anki:")
    print("  1. Anki > File > Import > select this CSV")
    print("  2. Field separator: Comma. Allow HTML in fields: YES (checkbox).")
    print("  3. Field 1 -> Front, Field 2 -> Back. Import.")
    print("Quizlet: Import > paste, set 'Comma' between term/definition, 'New line' between cards.")


# --------------------------------------------------------------------------- #
# progress file helpers
# --------------------------------------------------------------------------- #
def load_progress(path):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"profile": {"level": None, "goal": None, "topics": []}, "words": {}}


def save_progress(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_word(data, word):
    w = data["words"].get(word)
    if w is None:
        w = {
            "word": word,
            "seen": 0,
            "correct": 0,
            "rung": -1,          # index into INTERVAL_LADDER; -1 = brand new
            "next_due": fmt_date(today()),  # new words are due immediately
        }
        data["words"][word] = w
    return w


# --------------------------------------------------------------------------- #
# due
# --------------------------------------------------------------------------- #
def due(args):
    data = load_progress(args.progress)
    t = today()
    due_words = []
    for word, w in data["words"].items():
        try:
            nd = parse_date(w.get("next_due", fmt_date(t)))
        except (ValueError, TypeError):
            nd = t
        if nd <= t:
            due_words.append(w)

    # New words (rung -1) first, then the ones overdue longest.
    due_words.sort(key=lambda w: (w["rung"] != -1, w.get("next_due", "")))

    out = {
        "date": fmt_date(t),
        "due_count": len(due_words),
        "total_tracked": len(data["words"]),
        "profile": data.get("profile", {}),
        "due_words": [w["word"] for w in due_words],
        "details": due_words,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


# --------------------------------------------------------------------------- #
# grade
# --------------------------------------------------------------------------- #
def grade(args):
    data = load_progress(args.progress)
    w = ensure_word(data, args.word)
    correct = str(args.correct).lower() in ("true", "1", "yes", "y")

    w["seen"] += 1
    if correct:
        w["correct"] += 1
        w["rung"] = min(w["rung"] + 1, len(INTERVAL_LADDER) - 1)
        if w["rung"] < 0:
            w["rung"] = 0
    else:
        # Reset — the word wasn't learned yet, bring it back tomorrow.
        w["rung"] = 0

    interval = INTERVAL_LADDER[w["rung"]]
    next_due = today() + datetime.timedelta(days=interval)
    w["next_due"] = fmt_date(next_due)

    save_progress(args.progress, data)
    print(json.dumps({
        "word": w["word"],
        "correct": correct,
        "seen": w["seen"],
        "accuracy": round(w["correct"] / w["seen"], 2),
        "interval_days": interval,
        "next_due": w["next_due"],
    }, ensure_ascii=False, indent=2))


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="english-vocab-coach helper")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build-deck", help="JSON word list -> Anki CSV")
    b.add_argument("--input", required=True)
    b.add_argument("--out", required=True)
    b.set_defaults(func=build_deck)

    d = sub.add_parser("due", help="list words due for review today")
    d.add_argument("--progress", required=True)
    d.set_defaults(func=due)

    g = sub.add_parser("grade", help="record a quiz result and reschedule")
    g.add_argument("--progress", required=True)
    g.add_argument("--word", required=True)
    g.add_argument("--correct", required=True, help="true/false")
    g.set_defaults(func=grade)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
