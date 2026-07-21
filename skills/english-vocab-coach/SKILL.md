---
name: english-vocab-coach
description: All-in-one English vocabulary learning coach for a Vietnamese learner. Use whenever the user wants to learn, review, expand, quiz, or collect English vocabulary — even casually. Four modes: (1) EXPAND a single word into a rich card (meaning, IPA, examples, collocations, synonyms/antonyms, word family, mnemonic); (2) EXTRACT worth-learning words from a pasted text/article/subtitle at the user's CEFR level; (3) BUILD an Anki/Quizlet-ready flashcard deck (CSV) from a word list or topic; (4) QUIZ the user with spaced-repetition scheduling that persists progress across sessions; (5) run a scheduled DAILY routine (Windows Task Scheduler) that every morning generates new words on a rotating topic + the words due for review and publishes them to a Google Sheet. Triggers on: "học từ vựng", "từ vựng tiếng Anh", "học từ mới", "mở rộng từ này", "từ X nghĩa là gì và cách dùng", "tạo flashcard", "tạo deck Anki", "trích từ mới từ đoạn này", "quiz từ vựng", "ôn từ vựng", "kiểm tra từ vựng", "lịch nhắc học từ vựng", "nhắc học từ hàng ngày", "từ mới mỗi ngày", "list từ vựng hàng ngày", "make flashcards", "vocabulary drill", "daily vocabulary reminder", "teach me words about <topic>", "extract vocabulary from this article". Also manages the daily schedule (change time, pause, topics). Prefer this skill over ad-hoc answers whenever the request is about acquiring or reviewing English words.
---

# English Vocab Coach

A practical vocabulary coach for a Vietnamese learner of English. The goal is durable learning, so every mode leans on the two things that actually move the needle: **learning words in context** (collocations + real example sentences, never bare word→gloss) and **spaced repetition** (reviewing right before you forget).

Detect the user's intent and pick one of the four modes below. When unsure which mode fits, ask one short question rather than guessing.

## First: know the learner

Before producing content, make sure you know the learner's **CEFR level** (A1–C2) and **goal** (giao tiếp / IELTS / công việc / thi cử). If it was stated earlier in the conversation, reuse it. If not and it materially changes the output (e.g. which words count as "worth learning", how hard example sentences should be), ask once. Default to **B1, general communication** if the user says "cứ làm đi" / doesn't care.

Store what you learn about the learner (level, goal, topics they're studying, recurring weak words) in the progress file described under Mode 4 so future sessions pick up where they left off.

## Language convention

The learner is Vietnamese. Write **Vietnamese glosses and explanations**, but keep the **English word, IPA, and English example sentences in English** — mixing an all-English definition defeats the purpose for a beginner, and translating the example sentences defeats immersion. For A2+ learners, add a short English definition alongside the Vietnamese one so they get English-thinking practice.

---

## Mode 1 — Expand a word

Trigger: user gives one word/phrase and wants to understand + remember it ("từ X nghĩa là gì", "mở rộng từ resilient", "dạy tui từ này").

Output this card **in chat** using the exact template below. Every field earns its place — skip a field only when it genuinely doesn't apply (e.g. no meaningful antonym), and say so rather than padding.

```
## <word>  /IPA/  (part of speech)

**Nghĩa:** <Vietnamese gloss> — <short English definition for A2+>

**Ví dụ (in context):**
1. <natural sentence at learner's level>
2. <a second sentence in a different, common situation>

**Collocations (đi kèm với):** <3–5 high-frequency collocations, bolded head word>

**Word family:** <noun / verb / adj / adv forms, with IPA shifts if the stress moves>

**Synonyms:** <2–3, with a one-line note on nuance/register>
**Antonyms:** <1–2, or "—" if none natural>

**Mnemonic:** <a vivid or funny hook, ideally leaning on Vietnamese sound or imagery>

**Register / note:** <formal? informal? common mistake VN learners make? false friend?>
```

Why this shape: collocations + two contrasting example sentences are what let the learner *produce* the word, not just recognize it. The mnemonic and the VN-specific "common mistake" note are where most textbooks fall short and where you add real value.

If the word has several distinct senses, cover the **top 1–2 most frequent** senses only — dumping all dictionary senses overwhelms and dilutes memory. Note that more senses exist.

After the card, offer: *"Muốn mình thêm từ này vào deck Anki / bộ ôn tập không?"* — if yes, hand off to Mode 3/4.

---

## Mode 2 — Extract vocabulary from text

Trigger: user pastes an article / paragraph / subtitle / email and wants the words worth learning ("trích từ mới từ đoạn này", "từ nào trong bài này đáng học").

Steps:
1. Read the text and identify candidate words **at or slightly above** the learner's level (the "i+1" principle — words they don't know yet but are ready for). Skip words far below their level (they know them) and far above (rare/technical words not worth the effort unless topic-relevant to their goal).
2. Prefer words and **collocations** that recur or that are high-frequency in general English, not one-off rare words.
3. Cap at **10–15 items** per text. Learning 8 words well beats "collecting" 40. If the text is rich, say what you left out and why.
4. Present as a compact table: `| Word/Phrase | IPA | Nghĩa (VN) | Câu trong bài (context gốc) |`. Using the sentence *from their own text* as the example is the strongest possible context.

Then offer to turn the list into a deck (Mode 3) — that's almost always the next step.

---

## Mode 3 — Build a flashcard deck (Anki / Quizlet)

Trigger: user wants a deck from a word list or a topic ("tạo flashcard cho 20 từ này", "tạo deck Anki chủ đề business meeting").

1. If given a **topic** rather than a list, first generate a leveled word list (respect the 10–15 cap and the learner's goal — e.g. an IELTS goal biases toward academic collocations).
2. For each word, build a card with: front = the word (+ IPA), back = VN gloss + one in-context example sentence + key collocations. A card without an example sentence is a weak card — always include one.
3. Generate the deck file with the bundled script so the format is guaranteed importable:

   ```bash
   python "<skill-dir>/scripts/vocab_tools.py" build-deck --input <words.json> --out <deck.csv>
   ```

   The script writes an Anki-ready CSV (also imports fine into Quizlet). See `scripts/vocab_tools.py` for the exact JSON input shape and the Anki import instructions it prints.
4. Save decks under the learner's vocab workspace (see below), and tell the user the file path + the one-line "how to import into Anki" steps the script prints.

Do NOT hand-format CSV in chat and ask the user to paste it — comma/quote escaping breaks Anki imports. Always go through the script.

---

## Mode 4 — Quiz with spaced repetition

Trigger: "quiz từ vựng", "ôn từ", "kiểm tra tui", "test me on my words".

This is the mode that makes learning stick. It uses **active recall** (the learner must *produce* the answer, not just recognize it) and a lightweight **spaced-repetition schedule** persisted to disk so review timing survives across sessions.

Progress file: `<vocab workspace>/progress.json`. Load it at the start of a quiz; if it doesn't exist, the script creates it. It tracks per-word: the word, times seen, times correct, current interval (days), and next-due date. Also stores the learner profile (level, goal, topics).

Quiz loop:
1. Run the script to get the words **due for review** today (plus any brand-new words the user just added):
   ```bash
   python "<skill-dir>/scripts/vocab_tools.py" due --progress <progress.json>
   ```
2. Quiz the due words one at a time. Vary the question type so recall is robust, not rote:
   - VN → EN production ("cho từ tiếng Anh nghĩa là 'kiên cường'")
   - Fill-in-the-blank using a fresh example sentence (`The bridge was ___ enough to survive the flood.`)
   - "Use this word in your own sentence" (then you gently correct it — this is the highest-value drill)
3. After each answer, grade it and record the result:
   ```bash
   python "<skill-dir>/scripts/vocab_tools.py" grade --progress <progress.json> --word <w> --correct <true|false>
   ```
   The script applies the interval logic (correct → interval grows; wrong → interval resets to 1 day, word comes back soon). This is why wrong answers aren't failures — they schedule the word for more practice, which is exactly right.
4. At the end, give a short summary: how many reviewed, accuracy, which words are still shaky (reset to short interval), and when the next batch is due.

Keep the quiz **conversational and encouraging** — this is a coach, not an exam. Correct mistakes with the *why*, not just "sai rồi".

---

## Mode 5 — Daily automated routine (scheduled)

A hands-off daily flow: every morning it picks a rotating topic, generates a fresh
batch of new words, pulls the words due for spaced-repetition review, and publishes
both to a Google Sheet the learner can open on their phone. This is already set up on
this machine — this section documents how it works and how to manage it, so you can
adjust it or rebuild it elsewhere.

**How it runs:** Windows Task Scheduler task `EnglishVocabDaily` fires
`scripts/run_daily_vocab.cmd` at 07:00 local daily, which runs `scripts/daily_vocab.py`.
Task Scheduler (OS-level) is used deliberately instead of an in-session cron because the
in-session scheduler dies when Claude exits; the OS task survives reboots and runs
whether or not Claude is open. The machine must be **on** at 07:00 — if it's off, the
task runs on the next wake (`-StartWhenAvailable`).

**What `daily_vocab.py` does** (all steps deterministic except word generation, so a
`claude -p` hiccup still publishes the review list and logs the error):
1. Rotate to today's topic: `topics[ today.toordinal() % len(topics) ]`.
2. `claude -p` → JSON array of `words_per_day` items (word, ipa, pos, gloss_vi, example,
   collocations, mnemonic). Read from stdout — no MCP dependency.
3. Compute due-for-review words from `progress.json` (spaced repetition), *before*
   adding today's new words.
4. Fold new words into `progress.json` (dedup by word, scheduled due today).
5. Write Google Sheet tabs **"New Words"** and **"To Review"** via `sheets_lib.py`
   (local Google token — works headless, no browser).
6. Save `progress.json`; append a line to `run_log.csv`.

**Config** lives at `<workspace>/config.json` (created with defaults on first run):
`level`, `goal`, `words_per_day`, `spreadsheet_title`, and the `topics` rotation list.
Edit this file to change level, pace, or topics — no code change needed.

**Managing the schedule** (PowerShell):
- Change time: `Set-ScheduledTask -TaskName EnglishVocabDaily -Trigger (New-ScheduledTaskTrigger -Daily -At 8:00am)`
- Pause: `Disable-ScheduledTask -TaskName EnglishVocabDaily` / resume with `Enable-ScheduledTask`
- Run now (test): `Start-ScheduledTask -TaskName EnglishVocabDaily`
- Remove: `Unregister-ScheduledTask -TaskName EnglishVocabDaily -Confirm:$false`
- Health: check `LastTaskResult` (0 = OK) via `Get-ScheduledTaskInfo`, and tail
  `<workspace>/task_stdout.log` + `run_log.csv`.

**To rebuild on another machine:** register a daily Task Scheduler action pointing at
`run_daily_vocab.cmd` (fix the python + npm paths inside it), ensure the Google token
exists at the path in `sheets_lib.py`, and confirm `claude -p` is authenticated for the
user the task runs as. Real email sending is intentionally NOT part of this flow — no
available tool can *send* mail (only draft), so the Sheet is the delivery channel.

To connect this to the review quiz (Mode 4): the daily routine and the quiz share the
same `progress.json`, so words delivered in the morning Sheet are the same words the
quiz schedules. A quiz session just reads the words the learner has actually studied.

## Vocab workspace

Keep all of a learner's files together so progress accumulates. Default location: `d:/HK8/Learning/DQ/vocab/`. Create it if missing. Typical contents:

```
vocab/
├── config.json            # daily-routine config: level, goal, words_per_day, topics (Mode 5)
├── progress.json          # spaced-repetition state + per-word cards + profile (Modes 4 & 5)
├── run_log.csv            # one line per daily run (Mode 5)
├── task_stdout.log        # scheduler stdout/stderr (Mode 5)
├── decks/                 # generated Anki CSVs (Mode 3)
└── extracted/             # word lists pulled from texts (Mode 2)
```

If the user names a different folder, use that instead and remember it in progress.json.

## Guiding principles (why this skill works)

- **Context over glosses.** Bare word→translation pairs are the least effective way to learn. Every card carries a real example sentence and collocations so the learner can actually use the word.
- **Fewer words, learned deeply.** The 10–15 caps are deliberate. Overloading kills retention and motivation.
- **Spaced repetition is the engine.** The progress file exists so review timing is honest — you review a word right as you're about to forget it, which is when repetition pays off most.
- **Active recall beats re-reading.** Quizzes force production; that's where memory forms.
- **The learner is Vietnamese.** Lean on VN sound-alikes for mnemonics and flag false friends / typical VN-learner mistakes — that's value a generic tool won't give.
