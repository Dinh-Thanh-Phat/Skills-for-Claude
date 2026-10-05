# Skills-for-Claude

166 Claude Code skills for QA automation — Playwright E2E, Maestro mobile, LLM/chatbot evaluation,
test design and debugging discipline. Clone, run one command, restart Claude Code.

## Install (2 minutes)

```bash
git clone https://github.com/Dinh-Thanh-Phat/Skills-for-Claude.git
cd Skills-for-Claude
```

| OS | Command |
|---|---|
| Windows (PowerShell) | `.\setup.ps1` |
| macOS / Linux / Git Bash | `bash setup.sh` |

Then **restart Claude Code**. Only requirement: Python 3.8+ (the wrappers tell you if it's missing).

What it does — nothing is overwritten without a backup in `~/.claude/backups/<timestamp>/`:

1. Copies `skills/*` → `~/.claude/skills/` (unchanged skills are skipped)
2. Installs one hook, `fix-flat-skill.py` (turns a stray `skills/foo.md` into `skills/foo/SKILL.md` so it loads)
3. **Merges** hooks/plugins into `~/.claude/settings.json` — your existing settings are kept
4. Installs the Claude Code plugins the skills hand off to (`superpowers`, `playwright`, …)
5. Creates `~/.claude/shared-context/` templates if missing, then lists optional tools it found

Options (pass to `setup.ps1` / `setup.sh` or `python install.py`):

| Flag | Effect |
|---|---|
| `--dry-run` | show what would change, touch nothing |
| `--with-qa-gates` | add hooks that remind/enforce full test coverage when a prompt mentions testing ([docs](docs/QA-HOOKS.md)) |
| `--with-beads` | run `bd prime` at session start (needs [beads](https://github.com/gastownhall/beads)) |
| `--project <dir>` | also copy the project-level skills in `project-example/` into `<dir>/.claude/skills` |
| `--skip-settings` / `--skip-plugins` | leave settings.json / plugins alone |

## Use

You don't call skills by name — describe the task and Claude loads the matching one:

- *"test the checkout form"* → `qa-router` picks coverage, locator, assertion and data skills
- *"this Playwright test is flaky in CI"* → `e2e-test-stability`, `flaky-test-prevention`
- *"write a Maestro flow for login"* → `maestro-mobile`
- *"evaluate our chatbot answers"* → `chatbot-tester` pipeline

Full list by category: **[SKILLS.md](SKILLS.md)**. Tools/API keys some skills need: **[docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)**.

## Update

```bash
git pull
.\setup.ps1        # or: bash setup.sh
```

Changed skills are replaced (old copy backed up); your own extra skills in `~/.claude/skills` are never touched.

## Repo layout

```
skills/            installed skills, one folder each: <name>/SKILL.md (+ references/, scripts/)
hooks/             hook scripts the installer can copy to ~/.claude/hooks
config/            settings.base.json (plugins), hooks.json (hook sets), shared-context templates
project-example/   project-level skills (React/Figma/OpenSpec) — opt-in via --project
docs/              REQUIREMENTS.md, QA-HOOKS.md
tools/             check_skills.py (lint + regenerate SKILLS.md), google_auth.py (Drive/Sheets token)
install.py         the installer; setup.ps1 / setup.sh just find Python and call it
personal/          maintainer-only skills, notes and sync hook — NOT installed
```

## Contributing a skill

1. Create `skills/<kebab-name>/SKILL.md` with front-matter `name:` and `description:` (the description is what
   makes Claude pick it — include trigger phrases). Save as UTF-8 **without BOM**.
2. No machine-specific paths — use `~/...` or an env var.
3. `python tools/check_skills.py --catalog` must report 0 problems; commit the regenerated `SKILLS.md`.
