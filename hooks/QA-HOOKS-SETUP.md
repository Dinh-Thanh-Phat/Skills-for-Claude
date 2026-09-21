# QA coverage hooks — how to re-register on a new machine

Copy `qa-coverage-gate.py` and `qa-coverage-stop-gate.py` to `~/.claude/hooks/`, then add to
`~/.claude/settings.json` (merge into existing `hooks`, don't replace):

```json
"UserPromptSubmit": [{"matcher": "", "hooks": [{"type": "command",
  "command": "python3 C:/Users/<you>/.claude/hooks/qa-coverage-gate.py", "timeout": 10,
  "statusMessage": "QA coverage gate..."}]}],
"Stop": [{"matcher": "", "hooks": [{"type": "command",
  "command": "python3 C:/Users/<you>/.claude/hooks/qa-coverage-stop-gate.py", "timeout": 10,
  "statusMessage": "QA coverage stop gate..."}]}]
```

- `qa-coverage-gate.py` (UserPromptSubmit): injects the full-coverage reminder when a prompt has test keywords.
- `qa-coverage-stop-gate.py` (Stop): blocks ending the turn while any `bd` issue labeled `qa-coverage` is open
  (needs `bd` on PATH; silently exits 0 if bd/beads db is absent). Then open `/hooks` once or restart.
- Not backed up on purpose: `settings.json` (may hold secrets), `knowledge/hvs.md`, `knowledge/trs.md` (contain test credentials).
