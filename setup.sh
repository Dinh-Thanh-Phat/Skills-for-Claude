#!/usr/bin/env bash
# Skills-for-Claude — macOS / Linux / Git Bash entry point. All logic lives in install.py.
# Usage: bash setup.sh [--with-qa-gates] [--with-beads] [--dry-run] ...   (python3 install.py --help)
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for py in python3 python py; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    exec "$py" "$DIR/install.py" "$@"
  fi
done
echo "Python 3.8+ not found — install it (brew install python / apt install python3) and re-run." >&2
exit 1
