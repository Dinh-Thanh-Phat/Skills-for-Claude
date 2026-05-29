#!/bin/bash
# =============================================================================
# SCENARIO C: Debug & Fix
# Failing test → Fresh snapshot → Diagnose selector → Fix → Re-run
#
# Use when: A test was passing, now fails. Or a test never passed.
# The snapshot reveals what the DOM currently looks like vs what the test expects.
#
# Usage:
#   bash scenario-c.sh <spec-file> <url> [--selector="<failing-selector>"]
#
# Example:
#   bash scenario-c.sh "tests/login.spec.ts" "https://exchange.fccx.io/signin"
#   bash scenario-c.sh "tests/exchange.spec.ts" "https://exchange.fccx.io" \
#     --selector="page.getByRole('combobox', { name: 'Currency' })"
# =============================================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(pwd)"

B='\033[0;34m'; G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; N='\033[0m'

# ── Args ──────────────────────────────────────────────────────────────────────
SPEC_FILE=${1:-""}
URL=${2:-""}
shift 2 2>/dev/null || true

FAILING_SELECTOR=""
for arg in "$@"; do
  [[ "$arg" == --selector=* ]] && FAILING_SELECTOR="${arg#--selector=}"
done

FEATURE=$(basename "${SPEC_FILE%.spec.ts}" 2>/dev/null || echo "debug")
DATE=$(date +%Y%m%d_%H%M)
OUTPUT_DIR="$ROOT_DIR/data/outputs"
SNAPSHOT_DIR="$OUTPUT_DIR/snapshots"
DEBUG_DIR="$OUTPUT_DIR/debug"
SNAPSHOT_FILE="$SNAPSHOT_DIR/${FEATURE}-debug-${DATE}.txt"
FAILURE_LOG="$DEBUG_DIR/${FEATURE}-failure-${DATE}.log"
DEBUG_REPORT="$DEBUG_DIR/${FEATURE}-debug-${DATE}.md"

mkdir -p "$OUTPUT_DIR" "$SNAPSHOT_DIR" "$DEBUG_DIR"

GATE_FILE="$DEBUG_DIR/.scenario-c-${FEATURE}.gates"
load_gates() { [[ -f "$GATE_FILE" ]] && source "$GATE_FILE" || true; }
save_gate()  { echo "${1}=done" >> "$GATE_FILE"; }
gate_done()  { load_gates; [[ "${!1}" == "done" ]]; }

echo -e "${R}╔══════════════════════════════════════════════╗${N}"
echo -e "${R}║  SCENARIO C: Debug & Fix                     ║${N}"
echo -e "${R}╚══════════════════════════════════════════════╝${N}"
echo -e "  Spec     : ${Y}${SPEC_FILE:-'(will ask)'}${N}"
echo -e "  URL      : ${Y}${URL:-'(will ask)'}${N}"
echo -e "  Selector : ${Y}${FAILING_SELECTOR:-'(auto-detect from failure)'}${N}"
echo ""

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 1: Capture Test Failure ─────────────────────────${N}"

if gate_done "step1"; then
  echo -e "  ✅ Failure already captured. Log: ${FAILURE_LOG}"
else
  if [ -z "$SPEC_FILE" ]; then
    read -p "  Enter spec file path: " SPEC_FILE
  fi

  if [ -f "$SPEC_FILE" ]; then
    echo "  Running failing test to capture output..."
    npx playwright test "$SPEC_FILE" --reporter=list 2>&1 | tee "$FAILURE_LOG" || true
    echo ""
    echo -e "  ${Y}Failure log saved: $FAILURE_LOG${N}"
  else
    echo -e "  ${Y}Spec file not found. Enter failure manually.${N}"
    echo "  Paste the Playwright error output, then press Ctrl+D:"
    cat > "$FAILURE_LOG"
  fi
  save_gate "step1"
fi

# ── Extract failing selector from log ────────────────────────────────────────
if [ -z "$FAILING_SELECTOR" ] && [ -f "$FAILURE_LOG" ]; then
  EXTRACTED=$(grep -oP "(?<=locator\.)[^\)]+\)" "$FAILURE_LOG" 2>/dev/null | head -1 || true)
  if [ -n "$EXTRACTED" ]; then
    echo -e "  Auto-detected failing selector: ${Y}$EXTRACTED${N}"
    FAILING_SELECTOR="$EXTRACTED"
  fi
fi

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 2: Capture Fresh Snapshot of Current UI ─────────${N}"

if gate_done "step2"; then
  echo -e "  ✅ Snapshot already captured."
  SNAPSHOT_FILE=$(ls "$SNAPSHOT_DIR/${FEATURE}-debug-"*.txt 2>/dev/null | tail -1)
  echo "  Using: $SNAPSHOT_FILE"
else
  if [ -z "$URL" ]; then
    read -p "  Enter the URL where the test fails: " URL
  fi
  echo "  Capturing fresh snapshot..."
  npx ts-node "$SCRIPT_DIR/take-snapshot.js" "$URL" "$SNAPSHOT_FILE"
  save_gate "step2"
fi

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 3: Diagnose with Snapshot Parser ────────────────${N}"

# Fill debug report template
cat "$SCRIPT_DIR/../templates/debug-report.md" > "$DEBUG_REPORT"
echo "" >> "$DEBUG_REPORT"
echo "## Failure Log" >> "$DEBUG_REPORT"
echo '```' >> "$DEBUG_REPORT"
cat "$FAILURE_LOG" >> "$DEBUG_REPORT"
echo '```' >> "$DEBUG_REPORT"

echo ""
echo -e "  ${Y}👉 Invoke skill: playwright-snapshot-parser (Selector Debugger mode)${N}"
echo "     Paste this prompt into Claude:"
echo ""
echo "  ┌────────────────────────────────────────────────────────────┐"
echo "  │ Debug this failing Playwright selector.                    │"
echo "  │                                                            │"

if [ -n "$FAILING_SELECTOR" ]; then
echo "  │ Failing selector: ${FAILING_SELECTOR}"
echo "  │                                                            │"
fi

echo "  │ Current UI snapshot (what the DOM actually looks like now):│"
echo "  │ [paste contents of: ${SNAPSHOT_FILE}]"
echo "  │                                                            │"
echo "  │ Please provide:                                            │"
echo "  │ 1. Why the selector fails (diagnosis)                      │"
echo "  │ 2. What the correct selector should be                     │"
echo "  │ 3. Whether the UI changed (a11y regression?)               │"
echo "  └────────────────────────────────────────────────────────────┘"
echo ""
echo "  Snapshot preview (first 40 lines):"
echo "  ───────────────────────────────────"
head -40 "$SNAPSHOT_FILE" 2>/dev/null
echo "  ───────────────────────────────────"
echo ""
read -p "  Press ENTER after you have the diagnosis and fix from Claude..."

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 4: Apply Fix to Spec File ───────────────────────${N}"

echo ""
echo -e "  ${Y}👉 Apply the suggested fix to: $SPEC_FILE${N}"
echo "     Update the selector(s) as recommended by the snapshot parser."
echo "     If the fix involves an a11y bug in the UI: file a bug and use the"
echo "     LOW-confidence fallback selector with a // A11Y BUG comment."
echo ""
read -p "  Press ENTER after fix is applied..."

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 5: Re-run Test to Verify Fix ────────────────────${N}"

if [ -f "$SPEC_FILE" ]; then
  echo "  Running: npx playwright test $SPEC_FILE --reporter=list"
  npx playwright test "$SPEC_FILE" --reporter=list 2>&1
else
  echo -e "  ${Y}Spec file not found. Manually run: npx playwright test <spec>${N}"
fi

# ═════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${G}╔══════════════════════════════════════════╗${N}"
echo -e "${G}║  SCENARIO C COMPLETE                     ║${N}"
echo -e "${G}╚══════════════════════════════════════════╝${N}"
echo "  Files produced:"
echo "    Failure log  : $FAILURE_LOG"
echo "    Snapshot     : $SNAPSHOT_FILE"
echo "    Debug report : $DEBUG_REPORT"
echo "    Fixed spec   : $SPEC_FILE"
