---
name: odoo-context-before-logging
description: Use ONLY when the user explicitly mentions "Odoo" or "ERP" AND wants to log/create/report a task or bug for a NAMED project (e.g. "log a bug for HVS on Odoo", "tạo task cho Soundwise lên Odoo", "report this issue to the FE project on ERP"). This skill runs FIRST as a context-gathering gate — it explores the named project on disk and on Odoo to understand its flow, conventions, team, stages, and existing tickets BEFORE handing off to odoo-project-automation to actually write the ticket. This makes the logged task/bug accurate, deduplicated, and reproducible instead of a vague one-liner. Trigger it even when the user just says "log this bug to <project> on Odoo" without spelling out the steps — the whole point is that you fill in the context they didn't. Do NOT trigger when "Odoo"/"ERP" is absent, or for logging that has no named project.
compatibility: Uses mcp__odoo__* tools (odoo-project-automation has no scripts/ sources — its only Python path is an XML-RPC fallback for binary image attachments), the Explore agent, and reads ~/.claude/shared-context/. No extra dependencies.
---

# Odoo: Gather Project Context Before Logging

When the user asks to log a task or bug **for a named project on Odoo**, the quality of the ticket is decided *before* you write anything. A ticket logged blind ("Login broken — please fix") sits in the backlog. A ticket logged with the real flow, exact location, reproduction steps, and a check that it isn't a duplicate gets actioned. This skill is the discipline that produces the second kind.

**Your job: understand the project first, then log.** Do not call `odoo-project-automation` until you have completed the context phase below (or consciously decided a step doesn't apply and said so).

## Guardrails (read first)

- **Only act when "Odoo"/"ERP" is explicit.** Project names alone (Soundwise, HVS, FE…) are ambiguous and must NOT trigger Odoo work — this matches the project rule in CLAUDE.md and `odoo-project-automation`.
- **Log content in English** (title + description), even if the user chats in Vietnamese. Chat replies stay in the user's language. (See `feedback_log-tasks-in-english`.)
- **Don't claim a bug is new until you've checked.** Searching existing Odoo tickets is part of this skill, not optional. (See `lesson_dedup-before-claiming-new-bug`.)
- **Don't claim "X causes Y" from a single confounded repro.** Isolate one variable. (See `bug-repro-isolation`.)
- **Visual/layout bugs:** confirm with a native-resolution screenshot you look at yourself before asserting — don't infer from DOM or thumbnails.
- Everything still goes through `odoo-project-automation`'s confirmation step — you assemble the ticket, the user approves, then it's created.

## Step 1 — Resolve the project to a real place

Map the name the user said to the disk path and knowledge, so "the project" means something concrete.

1. Read `~/.claude/shared-context/registry.md` → match the spoken name to a **Slug** and **Disk Path**. If the name is fuzzy (e.g. "the client book" → `the-client-book`), confirm the match.
2. Read, if present:
   - `~/.claude/shared-context/knowledge/[slug].md` — accumulated project knowledge (flows, gotchas, conventions).
   - `~/.claude/shared-context/memories/[slug]/` — project-specific memories.
3. Note the **Odoo project name** — it may differ from the disk slug (e.g. disk `the-client-book` ↔ Odoo "Olivia - CRM App"). The knowledge file or memories usually record the mapping. If you can't find it, ask the user which Odoo project to log into rather than guessing.

If the project isn't in the registry, stop and ask — don't invent a path or an Odoo project.

## Step 2 — Understand the flow (disk)

You're logging *about a feature*, so understand how that feature actually works before describing what's wrong or what to build.

- For anything beyond a trivial typo, dispatch the **Explore** agent against the project's Disk Path to map the relevant flow: which files/components/routes implement the feature, the happy path, and where the reported behavior lives. Ask it for the concrete file:line anchors, not a summary.
- Pull out what makes the ticket precise: the real route/URL, the component or endpoint name, the expected behavior per the code, and any nearby known issues already documented in the knowledge file.

This is what lets you write "Expected" from how the system is *meant* to work, not a guess.

## Step 3 — Understand the project on Odoo

Read the live Odoo project so the ticket fits its conventions and lands in the right place. Use `mcp__odoo__*` tools (the user's message contains "Odoo", so they're authorized).

1. **Find the project & its stages** — `search_records` on `project.project` by name, then its `project.task.type` stages (names + ids + sequence). You need the real stage to file into, and stage names are often UPPERCASE — use `ilike`.
2. **Team & tags** — who the assignees are and what tags the project actually uses, so you don't invent an assignee or tag that doesn't exist.
3. **Existing tickets (dedup — do not skip for bugs).** `search_records` on `project.task` within this project for the same area/symptom (search by keyword from the title and the feature name). Then decide:
   - **Match found** → propose updating/commenting on the existing ticket (or moving its stage) instead of creating a duplicate. Tell the user "this looks like <id> — update it?" rather than silently filing a second one.
   - **No match** → proceed to create, now confident it's genuinely new.

Pull the known Odoo IDs (project ids, stage ids, assignee ids) from `odoo-project-automation` and the `reference_odoo-*` memories where they're already recorded — don't re-derive what's documented.

## Step 4 — For bugs: make it reproducible and isolated

Skip to Step 5 for tasks/features. For a bug, assemble what a developer needs to act in the next hour:

- **Reproduction steps** from a known starting state — exact route, UI element, values, in order.
- **Expected vs Actual** — Expected from Step 2 (how the code says it should behave); Actual = observed, not assumed cause.
- **Isolate the cause** before writing any "X breaks Y" claim — change one variable, run a control. A symptom is not a root cause.
- **Technical context** for AI-assisted fixing (these map directly onto `odoo-project-automation` fields): `page_url`, `element_selector`, `error_message`, `network_request`, `stack_trace`.
- **Visual evidence** — reference a native-resolution screenshot you've actually viewed for any layout/visual claim. Any screenshot goes **inline in the description** (not just a chatter attachment) — see `odoo-project-automation`'s "Screenshots — ALWAYS embed inline" section for the attach-then-`<img src="/web/image/ir.attachment/{id}/datas">` flow. This is the default for every ticket with an image, not something to do only when asked.

If you can't reproduce or can't isolate after a couple of tries, stop and ask the user rather than logging a shaky theory (see `ask-when-stuck`).

## Step 5 — Hand off to odoo-project-automation

Now you have: the right Odoo project + stage, a real assignee/tags, a deduped decision, and an accurate English description. Compose the ticket and invoke **`odoo-project-automation`** to create/update it with its confirmation flow. Pass through everything you gathered — type, title, description, assignee, tags, stage, and (for bugs) the technical-context fields.

Before confirming, show the user a short summary of *why* you filed it the way you did: which Odoo project/stage, whether it was new or a dup of an existing ticket, and the key context you found. That transparency is the payoff of doing the context phase.

## Step 6 — Write back what you learned

If exploring surfaced a durable flow detail, gotcha, or the disk↔Odoo project-name mapping, append it to `~/.claude/shared-context/knowledge/[slug].md` so the next log is faster. Per CLAUDE.md's auto-writing rule, completed task results go to `~/.claude/shared-context/results/[project]/`.

## Quick reference

See [references/example-run.md](references/example-run.md) for a full worked example (HVS bug, from spoken request to filed ticket) showing each step's output.
