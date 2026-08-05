---
name: daily-skill-evolution
description: >-
  Daily 7AM (GMT+7) autonomous skill-evolution runbook for a REMOTE Claude Code routine. Use when
  the scheduled remote agent fires — it web-researches the latest best practices across the
  user's QA/automation domains, creates or updates skill files inside this repo
  (Skills-for-Claude), logs the changes, commits & pushes to the skill-evolution branch, then
  creates a Gmail draft report to thanhphat12tna234@gmail.com. Triggers on: the scheduled routine
  prompt, "run daily skill evolution", "evolve skills from web research".
---

# Daily Skill Evolution (Remote Runbook)

Executed by a **remote** Claude Code routine every day at **07:00 GMT+7 (00:00 UTC)**.
Runs in Anthropic cloud against the GitHub repo `Dinh-Thanh-Phat/Skills-for-Claude` — **no access to the user's local machine**.

## Scope — what this DOES and does NOT do

DOES:
- Web-research the latest best practices / new techniques / breaking changes in the user's focus domains.
- Create new skill files or update existing ones **inside this repo** (`skills/`).
- Maintain a changelog and create a Gmail draft report.

Does NOT (hard cloud limitations — documented so future-you doesn't re-attempt):
- ❌ Read the user's local chat-session transcripts (`C:\Users\wi\.claude\projects\*.jsonl`) — local only, not in cloud. The "learn from each chat session" idea needs a **local** component (a session-close hook that pushes lessons into this repo). Out of scope here. See "Future: hybrid mode".
- ❌ Edit the user's local `C:\Users\wi\.claude\skills\` directly. This repo IS the source of truth for skills; the user syncs to their machine via `setup.ps1`/`setup.sh` (or `git pull`) when at the machine.

## Focus domains (QA / testing ONLY)

This routine evolves **QA and testing** skills only. Stay strictly within these domains:

1. **Playwright / web E2E** — locators, network mocking, flaky-test prevention, reporters, config, accessibility.
2. **Maestro / mobile automation** — iOS + Android, ADB, speed, scaling, auth-state strategy.
3. **Test design & QA process** — coverage matrices, behavioral coverage, bug reports, test plans, diagnosis-first.
4. **AI chatbot / LLM testing** — QA generation, response evaluation, OCR, performance analysis, LLM security/red-teaming.

**OUT OF SCOPE — do NOT create or update skills for these** (even though such skills exist in the repo): frontend/dev work (Figma-to-code, React component building, design tokens), Odoo/ERP automation, Google Workspace automation (Sheets formatting). These are dev/automation, not testing. If a finding is genuinely a *testing technique* for one of these areas (e.g. how to test a design-token pipeline), it belongs under domain 1–4; the dev/build side does not.

Rotate emphasis day to day so domains get fresh coverage over the week — use the changelog to see what was last touched.

## Workflow (execute every step in order)

1. **Orient.** Confirm you are on a fresh checkout of `main`. `Glob` `skills/**/SKILL.md` and `.claude/skills/**/SKILL.md` to inventory existing skills. Read `skills/daily-skill-evolution/evolution-log.md` to see recent changes and which domain to rotate to.

2. **Research.** Pick 1–3 focus domains for today (rotate; don't repeat yesterday). Run `WebSearch` for the **current month/year** — e.g. "Playwright best practices <month> <year>", "Maestro flaky test 2026". Prefer official docs, changelogs, reputable engineering blogs. Capture concrete, actionable findings + source URLs.

3. **Decide: new vs update vs skip.** For each finding:
   - If an existing skill already covers it well → **skip** (no duplicates).
   - If a skill partially covers it → **update** that skill (surgical edit).
   - If nothing covers it and it's genuinely useful → **create** a new skill.
   - If trivial / speculative / unverified → **skip**. Quality over quantity. A 0-change day is acceptable — report it honestly.

4. **Write skills** following this repo's convention:
   - Path: `skills/<kebab-name>/SKILL.md`.
   - Frontmatter: `name:` (kebab) and `description:` (one line with "Use when..." + "Triggers on:" keywords).
   - Body: concise, actionable, code examples where relevant; match the tone of neighboring skills.
   - Cite source URL(s) under a `## Sources` heading.
   - Keep this routine's own bookkeeping files INSIDE `skills/daily-skill-evolution/` (log + `reports/`).

5. **Log.** Append one block per run to `skills/daily-skill-evolution/evolution-log.md`:
   ```
   ## <YYYY-MM-DD> (GMT+7)
   - CREATED: skills/<name> — <one-line why> — <source>
   - UPDATED: skills/<name> — <what changed> — <source>
   - (or) No changes — researched <domains>, nothing new worth adding.
   ```

6. **Commit & push — ONTO THE `skill-evolution` BRANCH, NEVER `main`.** The user keeps `main` clean and merges `skill-evolution` themselves when they want. Stage only the skill files + log you touched:
   ```
   git fetch origin
   git checkout skill-evolution 2>/dev/null || git checkout -b skill-evolution origin/skill-evolution
   git merge --ff-only origin/main 2>/dev/null || true   # stay current with main; ignore if it diverges
   git add skills/
   git commit -m "skill-evolution <YYYY-MM-DD>: +N created, ~M updated"
   git push origin skill-evolution
   ```
   ⚠ Do NOT push to `main` and do NOT open a PR (the user merges manually). If the push is rejected, pull/rebase onto `origin/skill-evolution` and retry.

7. **Report — create a Gmail DRAFT.** The attached Gmail connector can only create drafts (no send tool), and that is intended: the user reads the report in Gmail → Drafts. Use `mcp__Gmail__create_draft` (fallback name `mcp__claude_ai_Gmail__create_draft`) with:
   - `to`: `["thanhphat12tna234@gmail.com"]`
   - `subject`: `[Skill Evolution] <YYYY-MM-DD> — N created, M updated`
   - `htmlBody`: domains researched; each CREATED skill (name + 1-line purpose + source link); each UPDATED skill (name + what changed + source link); if 0 changes say so plainly; footer with commit hash + branch `skill-evolution`.
   - Do NOT try to "send" — creating the draft IS the deliverable.
   - **Fallback only if the draft tool errors/unavailable**: write the same report to `skills/daily-skill-evolution/reports/REPORT-<YYYY-MM-DD>.md`, commit & push to `skill-evolution`, note the draft failed. Never silently drop the report.

## Guardrails

- **No duplicates** — check the inventory before creating.
- **Verify before writing** — only encode techniques from credible sources; cite them.
- **Surgical edits** — when updating, add/adjust the relevant part, don't rewrite whole skills.
- **Honest reporting** — report exactly what changed, including "nothing changed today".
- **Stay in repo** — never assume local-machine access.

## Future: hybrid mode (not yet enabled)

To also "learn from each chat session" (the original request), add a **local** companion later: a session-close
hook on the user's machine that summarizes the session's lessons and pushes them to `skills/lessons-inbox/` in
this repo. This runbook would then read that inbox in step 1 and fold the lessons into skill updates. Requires the
local machine but only runs while the user is already working — no dedicated 7AM machine-on.

## Sources
- Constraints verified against Claude Code remote-routine capabilities (cloud sandbox, git-repo checkout, claude.ai MCP connectors — Gmail connector is draft-only).
