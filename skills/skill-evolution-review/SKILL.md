---
name: skill-evolution-review
description: Morning review gate for the daily-skill-evolution routine's output. Use every morning (or whenever the user says "kiểm tra skill evolution", "review skill sáng nay", "soát skill mới", "check today's skills") BEFORE merging skill-evolution into main. Runs deterministic duplicate/conflict checks plus a semantic review, then gives a per-skill MERGE / HOLD verdict and the exact merge commands.
---

# Skill Evolution — Morning Review Gate

Run this when the user asks to review the previous run of the `daily-skill-evolution` routine, before they merge `skill-evolution` → `main`. Goal: catch duplicates, name collisions, and contradictions that the routine's LLM judgment may have missed. The human merges; this gate gives them a confident verdict.

Repo: `Dinh-Thanh-Phat/Skills-for-Claude`. Routine commits to branch `skill-evolution`; `main` is the clean/merged baseline.

## Steps (execute in order, report findings)

1. **Sync & list unmerged work.**
   ```
   git fetch origin main skill-evolution
   git log --oneline origin/main..origin/skill-evolution        # run commits not yet merged
   git diff --stat origin/main...origin/skill-evolution         # files added/changed
   ```
   If nothing unmerged → tell the user "không có gì mới để soát" and stop.

2. **Classify each changed skill** from the diff: NEW dir vs UPDATED existing file.

3. **Deterministic checks (no guessing):**
   - **Name collision** — for each NEW `skills/<name>/`, check it does NOT already exist on `main`:
     `git ls-tree -r --name-only origin/main | grep "^skills/<name>/"`. If it exists on main but the run treated it as NEW → ⚠️ HOLD (should have been an UPDATE; risk of clobber).
   - **Trigger/description overlap** — extract the new skill's `description:` trigger keywords, then grep every existing skill's `description:` on main for the same keywords:
     `git grep -h "^description:" origin/main -- 'skills/**/SKILL.md'`. High keyword overlap with an existing skill → ⚠️ HOLD or recommend folding into that skill (routing ambiguity).

4. **Semantic review (judgment):** read each NEW/UPDATED `SKILL.md` body in full. For each, find the closest existing skill and check:
   - Does it duplicate guidance already covered elsewhere? (redundant)
   - Does it **contradict** an existing skill (opposite advice)? → ⚠️ HOLD, name the conflicting skill.
   - Are the cited sources real and on-topic? Is the content actionable, not fluff?
   - Does it follow repo conventions (frontmatter name+description, ## Sources)?

5. **Verdict per skill:** `✅ MERGE` or `⚠️ HOLD — <reason>`. Be specific; quote the conflicting skill/line.

6. **Overall recommendation:**
   - All ✅ → give the exact merge commands:
     ```
     git checkout main && git pull
     git merge origin/skill-evolution
     git push
     # then sync to local: ./setup.ps1   (or setup.sh)
     ```
   - Any ⚠️ → recommend the user either (a) cherry-pick only the good skills, or (b) have the next routine run fix the flagged skill. Offer to edit/remove the flagged skill on the branch directly.

## Principles

- **Deterministic checks first, judgment second** — name collision and keyword overlap are decided by commands, not vibes.
- **Default to HOLD when unsure** — a false HOLD costs a question; a false MERGE pollutes the skill library.
- **Quote evidence** — every HOLD names the specific file/line/conflicting skill.
- **Never auto-merge** — output the commands; the user runs the merge.
