#!/usr/bin/env python3
"""daily_vocab.py — the daily vocabulary routine for english-vocab-coach.

Run once per morning (via Windows Task Scheduler). It:
  1. Picks today's topic by rotating through the configured topic list.
  2. Generates N fresh vocabulary items for that topic by calling `claude -p`
     (the model returns a JSON array; no MCP needed — we read stdout).
  3. Reads progress.json, computes which previously-learned words are DUE for
     spaced-repetition review today, and folds the new words into the schedule.
  4. Writes two tabs in the Google Sheet — "New Words" (today's batch) and
     "To Review" (due words) — via the local Google token (sheets_lib).
  5. Saves progress.json.

Everything except word generation is deterministic, so the routine is robust:
if `claude -p` ever fails, we still publish the review list and log the error.

Config + state live in the vocab workspace (default d:/HK8/Learning/DQ/vocab/):
  config.json    - level, goal, words_per_day, topics[], spreadsheet_title
  progress.json  - spaced-repetition state + per-word card content
  run_log.csv    - one line per run (append; never overwrite)
"""

import csv
import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sheets_lib  # noqa: E402

WORKSPACE = Path(r"d:/HK8/Learning/DQ/vocab")
INTERVAL_LADDER = [1, 2, 4, 7, 14, 30, 60, 120]

DEFAULT_CONFIG = {
    "level": "B1",
    "goal": "general communication",
    "words_per_day": 15,
    "spreadsheet_title": "English Vocabulary — Daily",
    "topics": [
        "travel", "business & work", "food & cooking", "health & fitness",
        "technology & internet", "emotions & feelings", "money & shopping",
        "education & learning", "environment & nature", "media & entertainment",
        "relationships & family", "city & transport", "science", "sport",
        "describing personality", "weather & climate", "housing & home",
        "job interviews", "phrasal verbs (daily life)", "academic writing",
    ],
}


def today():
    return datetime.date.today()


def fmt(d):
    return d.strftime("%Y-%m-%d")


def load_json(path, default):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default


def save_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def log_run(msg):
    p = WORKSPACE / "run_log.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    new = not p.exists()
    with p.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "message"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), msg])


def already_succeeded_today():
    """True if run_log.csv already has an OK line dated today.

    Lets the task fire from multiple triggers (07:00 daily + at-logon) yet run
    at most once per day. A PARTIAL run (claude -p failed, no new words) is NOT
    counted as done, so a later trigger retries and can still fetch new words.
    """
    p = WORKSPACE / "run_log.csv"
    if not p.exists():
        return False
    stamp = fmt(today())
    try:
        with p.open(encoding="utf-8", newline="") as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[0].startswith(stamp) and row[1].startswith("OK"):
                    return True
    except (OSError, csv.Error):
        return False
    return False


# --------------------------------------------------------------------------- #
def pick_topic(config):
    topics = config["topics"]
    idx = today().toordinal() % len(topics)
    return topics[idx]


def find_claude():
    for name in ("claude", "claude.cmd", "claude.exe"):
        found = shutil.which(name)
        if found:
            return found
    # Common npm global location on Windows.
    fallback = Path.home() / "AppData/Roaming/npm/claude.cmd"
    return str(fallback) if fallback.exists() else "claude"


def generate_words(config, topic):
    n = config["words_per_day"]
    prompt = (
        f'Output ONLY a JSON array (no prose, no markdown fences) of {n} English '
        f'vocabulary items about the topic "{topic}" at CEFR level {config["level"]}, '
        f'for a learner whose goal is {config["goal"]}. Choose useful, high-frequency '
        f'words/collocations at or slightly above that level (i+1); avoid words far '
        f'below the level and rare/obscure words. Each item must be an object with keys: '
        f'"word","ipa","pos","gloss_vi","example","collocations","mnemonic". '
        f'gloss_vi is a short Vietnamese meaning; example is a natural English sentence '
        f'using the word in context; collocations is an array of 2-4 common collocations; '
        f'mnemonic is a memory hook (may use Vietnamese sound-alikes). '
        f'Return exactly {n} items.'
    )
    claude = find_claude()
    # On Windows, `claude` resolves to a .cmd wrapper that spawns node. A plain
    # subprocess.run(timeout=) can't reap that grandchild — its open pipes keep
    # Python blocked past the timeout until Task Scheduler force-kills the whole
    # task (exit 0xC000013A), so we never reach the graceful "publish anyway"
    # path. Launch in its own process group and force-kill the TREE on timeout
    # so a hung claude degrades to a logged PARTIAL run instead of a silent kill.
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    proc = subprocess.Popen(
        [claude, "-p", prompt, "--output-format", "text"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", errors="replace", shell=False,
        creationflags=creationflags,
    )
    try:
        stdout, stderr = proc.communicate(timeout=300)
    except subprocess.TimeoutExpired:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True)
        else:
            proc.kill()
        proc.communicate()
        raise RuntimeError("claude -p timed out after 300s (process tree killed)")
    out = (stdout or "").strip()
    if proc.returncode != 0 or not out:
        raise RuntimeError(f"claude -p failed rc={proc.returncode}: {(stderr or '')[:500]}")
    # Defensive: strip accidental ```json fences and grab the JSON array.
    out = re.sub(r"^```(?:json)?|```$", "", out, flags=re.MULTILINE).strip()
    m = re.search(r"\[.*\]", out, flags=re.DOTALL)
    if m:
        out = m.group(0)
    items = json.loads(out)
    if not isinstance(items, list) or not items:
        raise ValueError("model returned no items")
    return items


# --------------------------------------------------------------------------- #
def colls_to_str(c):
    if isinstance(c, list):
        return ", ".join(c)
    return str(c or "")


def add_new_words(progress, items, topic):
    """Fold new words into the SR schedule with their card content. Skip dups."""
    added = []
    for it in items:
        word = (it.get("word") or "").strip()
        if not word or word.lower() in {w.lower() for w in progress["words"]}:
            continue
        progress["words"][word] = {
            "word": word,
            "topic": topic,
            "ipa": it.get("ipa", ""),
            "pos": it.get("pos", ""),
            "gloss_vi": it.get("gloss_vi", ""),
            "example": it.get("example", ""),
            "collocations": colls_to_str(it.get("collocations")),
            "mnemonic": it.get("mnemonic", ""),
            "seen": 0,
            "correct": 0,
            "rung": -1,
            "next_due": fmt(today()),
            "added": fmt(today()),
        }
        added.append(progress["words"][word])
    return added


# Passive spaced-repetition ladder for the Sheet: a word resurfaces this many days
# after it was first added, regardless of whether the learner ever formally quizzed
# it. This is what makes "review daily" work for someone who just reads the Sheet.
# (Mode 4's interactive quiz layers active grading on top via the per-word `rung`.)
REVIEW_OFFSETS = {1, 3, 7, 16, 35, 75, 150}


def due_words(progress):
    """Words to resurface for review today, by days-since-added (passive SR)."""
    t = today()
    out = []
    for w in progress["words"].values():
        added = w.get("added")
        if not added:
            continue
        try:
            age = (t - datetime.datetime.strptime(added, "%Y-%m-%d").date()).days
        except (ValueError, TypeError):
            continue
        if age in REVIEW_OFFSETS:
            out.append(w)
    out.sort(key=lambda w: w.get("added", ""))
    return out


# --------------------------------------------------------------------------- #
NEW_HEADER = ["Date", "Topic", "Word", "IPA", "POS", "Nghĩa (VN)",
              "Example", "Collocations", "Mnemonic"]
REVIEW_HEADER = ["Date", "Word", "Nghĩa (VN)", "Example", "Seen", "Accuracy", "Next due"]


def publish(config, new_cards, review_cards):
    sheets, _ = sheets_lib.get_services()
    sid = sheets_lib.find_or_create_spreadsheet(config["spreadsheet_title"])
    d = fmt(today())

    sheets_lib.ensure_tab(sheets, sid, "New Words")
    sheets_lib.write_header(sheets, sid, "New Words", NEW_HEADER)
    new_rows = [[
        d, c.get("topic", ""), c["word"], c.get("ipa", ""), c.get("pos", ""),
        c.get("gloss_vi", ""), c.get("example", ""),
        c.get("collocations", ""), c.get("mnemonic", ""),
    ] for c in new_cards]
    sheets_lib.append_rows(sheets, sid, "New Words", new_rows)

    sheets_lib.ensure_tab(sheets, sid, "To Review")
    sheets_lib.write_header(sheets, sid, "To Review", REVIEW_HEADER)
    # A PARTIAL run already published today's review list; the retry (next trigger)
    # must not append the same rows again.
    if sheets_lib.has_rows_for_date(sheets, sid, "To Review", d):
        print("To Review already published today — not appending again.")
        return sid
    rev_rows = []
    for c in review_cards:
        acc = round(c["correct"] / c["seen"], 2) if c.get("seen") else 0
        rev_rows.append([
            d, c["word"], c.get("gloss_vi", ""), c.get("example", ""),
            c.get("seen", 0), acc, c.get("next_due", ""),
        ])
    sheets_lib.append_rows(sheets, sid, "To Review", rev_rows)
    return sid


# --------------------------------------------------------------------------- #
def main():
    # Idempotency guard: the task fires from several triggers (07:00 daily +
    # at-logon) so it delivers on the first time the machine is used each day,
    # even if it was asleep/off at 07:00. Skip if today already succeeded.
    if "--force" not in sys.argv and already_succeeded_today():
        print("Already generated today's vocab — skipping (use --force to override).")
        return

    config = load_json(WORKSPACE / "config.json", None)
    if config is None:
        config = DEFAULT_CONFIG
        save_json(WORKSPACE / "config.json", config)
    else:
        # Backfill any missing keys from defaults.
        for k, v in DEFAULT_CONFIG.items():
            config.setdefault(k, v)

    progress = load_json(WORKSPACE / "progress.json",
                         {"profile": {}, "words": {}})
    progress.setdefault("words", {})
    progress.setdefault("profile", {})
    progress["profile"].update({"level": config["level"], "goal": config["goal"]})

    topic = pick_topic(config)
    review_cards = due_words(progress)  # compute BEFORE adding today's new words

    new_cards, gen_error = [], None
    try:
        items = generate_words(config, topic)
        new_cards = add_new_words(progress, items, topic)
    except Exception as e:  # noqa: BLE001 - we want to publish review list regardless
        gen_error = str(e)

    sid = publish(config, new_cards, review_cards)
    save_json(WORKSPACE / "progress.json", progress)

    url = f"https://docs.google.com/spreadsheets/d/{sid}"
    if gen_error:
        log_run(f"PARTIAL topic={topic} new=0 review={len(review_cards)} "
                f"ERROR={gen_error[:200]} {url}")
        print(f"[partial] word generation failed: {gen_error}")
    else:
        log_run(f"OK topic={topic} new={len(new_cards)} review={len(review_cards)} {url}")
    print(f"Topic: {topic} | new: {len(new_cards)} | to review: {len(review_cards)}")
    print(f"Sheet: {url}")


if __name__ == "__main__":
    main()
