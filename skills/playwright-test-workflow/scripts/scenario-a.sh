#!/bin/bash
# =============================================================================
# SCENARIO A: Test-First Development
# Requirements → Manual Test Cases → UI Snapshot → Automation with verified selectors
#
# Usage:
#   bash scenario-a.sh <feature-name> <url> [--auth=<auth-json>] [--selector=<css>]
#
# Example:
#   bash scenario-a.sh "login" "https://exchange.fccx.io/signin"
#   bash scenario-a.sh "exchange-table" "https://exchange.fccx.io" --selector="section"
# =============================================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(pwd)"

# ── Colors ──────────────────────────────────────────────────────────────────
B='\033[0;34m'; G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; N='\033[0m'

# ── Args ─────────────────────────────────────────────────────────────────────
FEATURE=${1:-"feature"}
URL=${2:-""}
shift 2 2>/dev/null || true

AUTH_ARG=""; SELECTOR_ARG=""
for arg in "$@"; do
  [[ "$arg" == --auth=* ]]     && AUTH_ARG="$arg"
  [[ "$arg" == --selector=* ]] && SELECTOR_ARG="$arg"
done

DATE=$(date +%Y%m%d)
OUTPUT_DIR="$ROOT_DIR/data/outputs"
SNAPSHOT_DIR="$OUTPUT_DIR/snapshots"
TEST_CASES_FILE="$OUTPUT_DIR/test-cases-${FEATURE}-${DATE}.md"
SNAPSHOT_FILE="$SNAPSHOT_DIR/${FEATURE}-snapshot.txt"
SPEC_FILE="$ROOT_DIR/tests/${FEATURE}.spec.ts"

mkdir -p "$OUTPUT_DIR" "$SNAPSHOT_DIR" "$ROOT_DIR/tests"

# ── Header ───────────────────────────────────────────────────────────────────
echo -e "${B}╔══════════════════════════════════════════════╗${N}"
echo -e "${B}║  SCENARIO A: Test-First Development          ║${N}"
echo -e "${B}╚══════════════════════════════════════════════╝${N}"
echo -e "  Feature : ${Y}${FEATURE}${N}"
echo -e "  URL     : ${Y}${URL:-'(will ask)'}${N}"
echo ""

# ── GATE TRACKING ────────────────────────────────────────────────────────────
GATE_FILE="$OUTPUT_DIR/.scenario-a-${FEATURE}.gates"
load_gates() { [[ -f "$GATE_FILE" ]] && source "$GATE_FILE" || true; }
save_gate()  { echo "${1}=done" >> "$GATE_FILE"; }
gate_done()  { load_gates; [[ "${!1}" == "done" ]]; }

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 1: Generate Manual Test Cases ──────────────────${N}"

if gate_done "step1"; then
  echo -e "  ✅ Already completed. Output: ${TEST_CASES_FILE}"
else
  echo ""
  echo -e "  ${Y}👉 Invoke skill: qa-test-generation${N}"
  echo "     Fill in the requirements template, then paste this prompt into Claude:"
  echo ""
  echo "  ┌────────────────────────────────────────────────────────────┐"
  echo "  │ Generate test cases for: ${FEATURE}"
  echo "  │ Requirements: [paste your filled requirements.md here]"
  echo "  │ Save output to: ${TEST_CASES_FILE}"
  echo "  └────────────────────────────────────────────────────────────┘"
  echo ""
  echo "  Template: $SCRIPT_DIR/../templates/requirements.md"
  echo ""
  read -p "  Press ENTER after manual test cases are reviewed and confirmed..."
  save_gate "step1"
fi

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 2: Capture UI Snapshot ──────────────────────────${N}"

if gate_done "step2"; then
  echo -e "  ✅ Already captured. File: ${SNAPSHOT_FILE}"
else
  if [ -z "$URL" ]; then
    read -p "  Enter the URL to snapshot: " URL
  fi

  SNAPSHOT_CMD="npx ts-node $SCRIPT_DIR/take-snapshot.ts \"$URL\" \"$SNAPSHOT_FILE\""
  [[ -n "$AUTH_ARG" ]]     && SNAPSHOT_CMD="$SNAPSHOT_CMD $AUTH_ARG"
  [[ -n "$SELECTOR_ARG" ]] && SNAPSHOT_CMD="$SNAPSHOT_CMD $SELECTOR_ARG"

  echo "  Running: $SNAPSHOT_CMD"
  eval "$SNAPSHOT_CMD"
  save_gate "step2"
fi

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 3: Parse Snapshot → Selector Map ────────────────${N}"

if gate_done "step3"; then
  echo -e "  ✅ Already parsed."
else
  echo ""
  echo -e "  ${Y}👉 Invoke skill: playwright-snapshot-parser${N}"
  echo "     Paste this prompt into Claude:"
  echo ""
  echo "  ┌────────────────────────────────────────────────────────────┐"
  echo "  │ Parse this accessibility snapshot and export the selector  │"
  echo "  │ map for test generation.                                   │"
  echo "  │                                                            │"
  echo "  │ [paste contents of: ${SNAPSHOT_FILE}]"
  echo "  └────────────────────────────────────────────────────────────┘"
  echo ""
  echo "  Snapshot contents preview (first 40 lines):"
  echo "  ───────────────────────────────────────────"
  head -40 "$SNAPSHOT_FILE" 2>/dev/null || echo "  (file not found)"
  echo "  ───────────────────────────────────────────"
  echo ""
  echo "  Save the ### SELECTOR MAP block to: $OUTPUT_DIR/selector-map-${FEATURE}.md"
  read -p "  Press ENTER after you have the Selector Map from Claude..."
  save_gate "step3"
fi

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 4: Generate Automation Code ─────────────────────${N}"

if gate_done "step4"; then
  echo -e "  ✅ Already generated. File: ${SPEC_FILE}"
else
  echo ""
  echo -e "  ${Y}👉 Invoke skill: qa-test-generation Phase 2 Path A${N}"
  echo "     Paste this prompt into Claude:"
  echo ""
  echo "  ┌────────────────────────────────────────────────────────────┐"
  echo "  │ Phase 2: Write Playwright automation for the test cases in │"
  echo "  │ ${TEST_CASES_FILE}"
  echo "  │                                                            │"
  echo "  │ Use Path A (Selector Map provided):                        │"
  echo "  │ [paste the ### SELECTOR MAP block from Step 3]             │"
  echo "  │                                                            │"
  echo "  │ Save spec to: ${SPEC_FILE}"
  echo "  └────────────────────────────────────────────────────────────┘"
  echo ""
  read -p "  Press ENTER after automation code is generated..."
  save_gate "step4"
fi

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 5: Run Tests & Verify ────────────────────────────${N}"

if [ -f "$SPEC_FILE" ]; then
  echo "  Running: npx playwright test $SPEC_FILE"
  npx playwright test "$SPEC_FILE" --reporter=list 2>&1 || true
else
  echo -e "  ${Y}Spec file not found yet: $SPEC_FILE${N}"
  echo "  Generate it in Step 4, then re-run this script to execute tests."
fi

# ═════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${G}╔══════════════════════════════════════════╗${N}"
echo -e "${G}║  SCENARIO A COMPLETE                     ║${N}"
echo -e "${G}╚══════════════════════════════════════════╝${N}"
echo ""
echo "  Files produced:"
echo "    Manual tests : $TEST_CASES_FILE"
echo "    Snapshot     : $SNAPSHOT_FILE"
echo "    Spec file    : $SPEC_FILE"
