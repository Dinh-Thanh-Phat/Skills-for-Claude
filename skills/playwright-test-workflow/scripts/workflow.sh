#!/bin/bash
# =============================================================================
# workflow.sh — Main Playwright Test Workflow Orchestrator
#
# Interactive entry point. Selects and runs the right scenario.
#
# Usage:
#   bash workflow.sh                           # interactive menu
#   bash workflow.sh a <feature> <url>         # run Scenario A directly
#   bash workflow.sh b <feature> <url>         # run Scenario B directly
#   bash workflow.sh c <spec-file> <url>       # run Scenario C directly
#
# Examples:
#   bash workflow.sh
#   bash workflow.sh a "login" "https://app.example.com/login"
#   bash workflow.sh b "homepage" "https://app.example.com"
#   bash workflow.sh c "tests/login.spec.ts" "https://app.example.com/login"
# =============================================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

B='\033[0;34m'; G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; N='\033[0m'

echo ""
echo -e "${B}╔═══════════════════════════════════════════════════╗${N}"
echo -e "${B}║   Playwright Test Workflow — Skill Orchestrator   ║${N}"
echo -e "${B}╚═══════════════════════════════════════════════════╝${N}"
echo ""

# ── If scenario provided as first arg, skip menu ─────────────────────────────
SCENARIO="${1:-}"
if [ -n "$SCENARIO" ]; then
  case "${SCENARIO,,}" in
    a) shift; bash "$SCRIPT_DIR/scenario-a.sh" "$@"; exit 0;;
    b) shift; bash "$SCRIPT_DIR/scenario-b.sh" "$@"; exit 0;;
    c) shift; bash "$SCRIPT_DIR/scenario-c.sh" "$@"; exit 0;;
  esac
fi

# ── Interactive menu ──────────────────────────────────────────────────────────
echo -e "  Which scenario applies?"
echo ""
echo -e "  ${Y}A)${N} Test-First Development"
echo     "     You have requirements but UI may not be built yet."
echo     "     Flow: Requirements → Manual tests → Snapshot → Automation"
echo ""
echo -e "  ${Y}B)${N} Snapshot-First Development"
echo     "     UI exists but you have no test plan yet."
echo     "     Flow: Snapshot → Extract elements → Generate tests"
echo ""
echo -e "  ${Y}C)${N} Debug & Fix"
echo     "     A test is failing and you need to diagnose why."
echo     "     Flow: Capture failure → Fresh snapshot → Diagnose → Fix → Re-run"
echo ""
read -p "  Enter scenario [A/B/C]: " CHOICE
echo ""

case "${CHOICE,,}" in
  a)
    read -p "  Feature name (e.g. 'login', 'exchange-table'): " FEATURE
    read -p "  URL to test: " URL
    bash "$SCRIPT_DIR/scenario-a.sh" "$FEATURE" "$URL"
    ;;
  b)
    read -p "  Feature name: " FEATURE
    echo "  Options:"
    echo "    1) Capture new snapshot from URL"
    echo "    2) Use existing snapshot file"
    read -p "  Choose [1/2]: " OPT
    if [ "$OPT" = "2" ]; then
      read -p "  Snapshot file path: " SNAP_FILE
      bash "$SCRIPT_DIR/scenario-b.sh" "$FEATURE" "" "--snapshot=$SNAP_FILE"
    else
      read -p "  URL to snapshot: " URL
      bash "$SCRIPT_DIR/scenario-b.sh" "$FEATURE" "$URL"
    fi
    ;;
  c)
    read -p "  Spec file path (e.g. tests/login.spec.ts): " SPEC
    read -p "  URL where test fails: " URL
    read -p "  Failing selector (optional, press ENTER to skip): " SEL
    if [ -n "$SEL" ]; then
      bash "$SCRIPT_DIR/scenario-c.sh" "$SPEC" "$URL" "--selector=$SEL"
    else
      bash "$SCRIPT_DIR/scenario-c.sh" "$SPEC" "$URL"
    fi
    ;;
  *)
    echo -e "${R}Invalid choice: $CHOICE${N}"
    exit 1
    ;;
esac
