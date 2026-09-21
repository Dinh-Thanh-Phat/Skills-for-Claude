#!/usr/bin/env python3
"""Stop hook: block ending the turn while QA coverage-category bd issues are still open.

qa-coverage-gate.py (UserPromptSubmit) only injects a reminder at prompt-submit time — it
cannot verify the model actually complied before declaring work done. This hook closes that
gap at the other end: it runs when Claude is about to stop, checks whether any bd issue
labeled 'qa-coverage' is still open (created via the qa-router "full case(s)" rule, one issue
per POS/NEG/EDGE/SEC/A11Y/BOUNDARY/STATE/ERROR category), and blocks the stop if so.

Zero friction: silently exits 0 when bd isn't available, isn't a beads project, or there are
no open qa-coverage issues (the overwhelming majority of turns).
"""
import json
import os
import subprocess
import sys

os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + r"C:\Program Files\dolt\bin"


def main():
    # Stop hooks receive JSON on stdin; drain it but don't need the fields.
    try:
        sys.stdin.read()
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["bd", "list", "--status=open", "--label", "qa-coverage", "--json", "--limit", "0"],
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception:
        sys.exit(0)  # bd not installed / not on PATH / not a beads project -> stay silent

    if result.returncode != 0:
        sys.exit(0)  # e.g. no .beads db in this project -> stay silent, don't block on noise

    try:
        issues = json.loads(result.stdout or "[]")
    except Exception:
        sys.exit(0)

    if not issues:
        sys.exit(0)

    lines = [f"  - {i.get('id', '?')}: {i.get('title', '(no title)')}" for i in issues[:20]]
    if len(issues) > 20:
        lines.append(f"  ... and {len(issues) - 20} more")

    reason = (
        "⚠️ P0 STOP GATE (qa-coverage-stop-gate hook): "
        f"{len(issues)} open 'qa-coverage' bd issue(s) exist — created by the qa-router "
        "\"full case(s)\" rule (one per POS/NEG/EDGE/SEC/A11Y/BOUNDARY/STATE/ERROR category). "
        "Ending the turn now means declaring the work done while these are still open.\n"
        + "\n".join(lines)
        + "\n\nBefore stopping: close each with `bd close <id>` once that category is actually "
        "PASS/FAIL/BLOCKED, OR if a category genuinely doesn't apply here, close it with a stated "
        "reason (`bd close <id> --reason \"...\"`) instead of leaving it open. If you believe this "
        "is a false positive (these issues are stale from unrelated past work), say so explicitly "
        "to the user rather than silently ending the turn."
    )

    print(json.dumps({
        "decision": "block",
        "reason": reason,
        "continue": True,
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
