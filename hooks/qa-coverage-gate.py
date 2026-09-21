#!/usr/bin/env python3
"""UserPromptSubmit hook: enforce full-coverage QA gate.

When the user's prompt contains QA/test keywords, inject a P0 reminder that
forces the model through qa-router -> behavioral-coverage-matrix and a full
8-category coverage matrix BEFORE it may report the work as done.

Advisory skills/memory do not fire reliably; this hook runs in the harness on
every prompt, so the reminder is deterministic (not model discretion).
"""
import sys
import json
import re

# Keyword patterns (Vietnamese + English), matched case-insensitively.
# Word-ish boundaries kept loose because Vietnamese diacritics + English mix.
KEYWORDS = [
    r"\btest\b", r"\btests\b", r"testing",
    r"chạy test", r"viết test", r"fix test",
    r"kiểm tra",
    r"\bqa\b",
    r"\bverify\b", r"verif", r"xác minh",
    r"coverage", r"bao phủ",
    r"automation", r"tự động",
    r"negative", r"edge case", r"edge-case", r"boundary", r"biên",
    r"regression",
    r"test case", r"testcase",
]

GATE = (
    "⚠️ P0 FULL-COVERAGE GATE (auto-injected by qa-coverage-gate hook)\n"
    "The user's message involves testing/QA. Before you may report ANY test work "
    "as done, you MUST:\n"
    "  1. Invoke qa-router FIRST (it enforces routing + skill order).\n"
    "  2. Run behavioral-coverage-matrix to inventory ALL behaviors.\n"
    "  3. Produce/verify a coverage matrix covering all 8 categories: "
    "POS / NEG / EDGE / SEC / A11Y / BOUNDARY / STATE / ERROR.\n"
    "  4. Every behavior needs >=1 test; negative + boundary + auth + ripple are MANDATORY, "
    "not optional.\n"
    "Running or reporting HAPPY-PATH ONLY = FAILURE. If you are only doing a quick manual "
    "walkthrough/exploration, say so explicitly and state which categories are NOT yet covered "
    "before claiming anything is 'done' or 'passing'."
)


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        sys.exit(0)

    prompt = ""
    if raw.strip():
        try:
            data = json.loads(raw)
            prompt = str(data.get("prompt", "") or "")
        except Exception:
            # If it isn't JSON, treat the whole stdin as the text to scan.
            prompt = raw

    low = prompt.lower()
    if not any(re.search(p, low) for p in KEYWORDS):
        sys.exit(0)  # no keyword -> stay silent, zero friction

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": GATE,
        },
        "suppressOutput": True,
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
