# personal/ — maintainer only, not installed

Content tied to one machine, account or client project. `install.py` ignores this folder
(`--include-personal` installs `personal/skills` for the maintainer).

- `skills/` — skills bound to private accounts/projects (Odoo company instance, InCard, vocab routine,
  daily skill-evolution routine) and `_update-log.md` (skill change log)
- `shared-context/` — the maintainer's project registry, knowledge notes and shared memory
- `hooks/sync-skills-repo.py` — PostToolUse hook that mirrors edits of `~/.claude/skills` into this repo
  and pushes. Routes skills that exist under `personal/skills/` (and `_update-log.md`) here, everything
  else to `skills/`. Repo path: `SKILLS_REPO` env var.
