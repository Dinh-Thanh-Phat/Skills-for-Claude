#!/bin/bash
# =============================================================================
# SCENARIO B: Snapshot-First Development
# UI Snapshot → Extract structure + selectors → Generate test logic
#
# Use when: UI is already built but requirements/tests don't exist yet.
# The snapshot tells you WHAT exists; test generation gives it meaning.
#
# Usage:
#   bash scenario-b.sh <feature-name> <url> [--auth=<auth-json>] [--selector=<css>]
#   bash scenario-b.sh <feature-name> --snapshot=<existing-file>   # skip capture
#
# Example:
#   bash scenario-b.sh "fccx-homepage" "https://exchange.fccx.io"
#   bash scenario-b.sh "login-page" --snapshot=data/outputs/snapshots/login-snapshot.txt
# =============================================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(pwd)"

B='\033[0;34m'; G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; N='\033[0m'

# ── Args ──────────────────────────────────────────────────────────────────────
FEATURE=${1:-"feature"}
URL=${2:-""}
shift 2 2>/dev/null || true

AUTH_ARG=""; SELECTOR_ARG=""; EXISTING_SNAPSHOT=""
for arg in "$@"; do
  [[ "$arg" == --auth=* ]]       && AUTH_ARG="$arg"
  [[ "$arg" == --selector=* ]]   && SELECTOR_ARG="$arg"
  [[ "$arg" == --snapshot=* ]]   && EXISTING_SNAPSHOT="${arg#--snapshot=}"
done

DATE=$(date +%Y%m%d)
OUTPUT_DIR="$ROOT_DIR/data/outputs"
SNAPSHOT_DIR="$OUTPUT_DIR/snapshots"
SNAPSHOT_FILE="${EXISTING_SNAPSHOT:-$SNAPSHOT_DIR/${FEATURE}-snapshot.txt}"
TEST_CASES_FILE="$OUTPUT_DIR/test-cases-${FEATURE}-${DATE}.md"
SELECTOR_MAP_FILE="$OUTPUT_DIR/selector-map-${FEATURE}.md"
SPEC_FILE="$ROOT_DIR/tests/${FEATURE}.spec.ts"

mkdir -p "$OUTPUT_DIR" "$SNAPSHOT_DIR" "$ROOT_DIR/tests"

GATE_FILE="$OUTPUT_DIR/.scenario-b-${FEATURE}.gates"
load_gates() { [[ -f "$GATE_FILE" ]] && source "$GATE_FILE" || true; }
save_gate()  { echo "${1}=done" >> "$GATE_FILE"; }
gate_done()  { load_gates; [[ "${!1}" == "done" ]]; }

echo -e "${B}╔══════════════════════════════════════════════╗${N}"
echo -e "${B}║  SCENARIO B: Snapshot-First Development      ║${N}"
echo -e "${B}╚══════════════════════════════════════════════╝${N}"
echo -e "  Feature  : ${Y}${FEATURE}${N}"
echo -e "  Snapshot : ${Y}${SNAPSHOT_FILE}${N}"
echo ""

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 1: Capture UI Snapshot ──────────────────────────${N}"

if gate_done "step1" || [[ -n "$EXISTING_SNAPSHOT" && -f "$EXISTING_SNAPSHOT" ]]; then
  echo -e "  ✅ Using existing snapshot: ${SNAPSHOT_FILE}"
else
  if [ -z "$URL" ]; then
    read -p "  Enter the URL to snapshot: " URL
  fi
  SNAPSHOT_CMD="npx ts-node $SCRIPT_DIR/take-snapshot.ts \"$URL\" \"$SNAPSHOT_FILE\""
  [[ -n "$AUTH_ARG" ]]     && SNAPSHOT_CMD="$SNAPSHOT_CMD $AUTH_ARG"
  [[ -n "$SELECTOR_ARG" ]] && SNAPSHOT_CMD="$SNAPSHOT_CMD $SELECTOR_ARG"

  echo "  Running: $SNAPSHOT_CMD"
  eval "$SNAPSHOT_CMD"
  save_gate "step1"
fi

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 2: Extract Structure + Selector Map ─────────────${N}"

if gate_done "step2"; then
  echo -e "  ✅ Already extracted. File: ${SELECTOR_MAP_FILE}"
else
  echo ""
  echo -e "  ${Y}👉 Invoke skill: playwright-snapshot-parser (full parse)${N}"
  echo "     Paste this prompt into Claude:"
  echo ""
  echo "  ┌────────────────────────────────────────────────────────────┐"
  echo "  │ Parse this accessibility snapshot. I need:                 │"
  echo "  │ 1. Full list of all interactive elements                   │"
  echo "  │ 2. Selector recommendations per element                    │"
  echo "  │ 3. Accessibility report (critical + warnings)              │"
  echo "  │ 4. Selector Map exported for test generation               │"
  echo "  │                                                            │"
  echo "  │ [paste contents of: ${SNAPSHOT_FILE}]"
  echo "  └────────────────────────────────────────────────────────────┘"
  echo ""
  echo "  Snapshot preview (first 50 lines):"
  echo "  ───────────────────────────────────"
  head -50 "$SNAPSHOT_FILE" 2>/dev/null || echo "  (file not found)"
  echo "  ───────────────────────────────────"
  echo ""
  echo "  Save the output to: $SELECTOR_MAP_FILE"
  echo "  Template: $SCRIPT_DIR/../templates/selector-map-output.md"
  read -p "  Press ENTER after Claude has parsed the snapshot and you have the Selector Map..."
  save_gate "step2"
fi

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 3: Generate Test Cases from Actual UI ───────────${N}"

if gate_done "step3"; then
  echo -e "  ✅ Already generated. File: ${TEST_CASES_FILE}"
else
  echo ""
  echo -e "  ${Y}👉 Invoke skill: qa-test-generation Phase 1${N}"
  echo "     The Selector Map from Step 2 tells you what elements ACTUALLY exist."
  echo "     Use it to generate realistic test cases (not assumptions)."
  echo ""
  echo "  ┌────────────────────────────────────────────────────────────┐"
  echo "  │ Generate manual test cases for: ${FEATURE}"
  echo "  │                                                            │"
  echo "  │ The actual UI has these interactive elements:              │"
  echo "  │ [paste the ### SELECTOR MAP block from Step 2]             │"
  echo "  │                                                            │"
  echo "  │ Generate test cases covering:                              │"
  echo "  │ - Happy path for each interactive flow                     │"
  echo "  │ - Validation / error states                                │"
  echo "  │ - Navigation flows                                         │"
  echo "  │                                                            │"
  echo "  │ Save to: ${TEST_CASES_FILE}"
  echo "  └────────────────────────────────────────────────────────────┘"
  echo ""
  read -p "  Press ENTER after manual test cases are reviewed and confirmed..."
  save_gate "step3"
fi

# ═════════════════════════════════════════════════════════════════════════════
echo -e "\n${G}── STEP 4: Generate Automation Code ─────────────────────${N}"

if gate_done "step4"; then
  echo -e "  ✅ Already generated. File: ${SPEC_FILE}"
else
  echo ""
  echo -e "  ${Y}👉 Invoke skill: qa-test-generation Phase 2 Path A${N}"
  echo "     Selector Map is already available from Step 2 — use it directly."
  echo ""
  echo "  ┌────────────────────────────────────────────────────────────┐"
  echo "  │ Phase 2: Write Playwright automation for the test cases in │"
  echo "  │ ${TEST_CASES_FILE}"
  echo "  │                                                            │"
  echo "  │ Selector Map (from Step 2, use exact selectors):           │"
  echo "  │ [paste the ### SELECTOR MAP block]                         │"
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
  echo "  Running: npx playwright test $SPEC_FILE --reporter=list"
  npx playwright test "$SPEC_FILE" --reporter=list 2>&1 || true
else
  echo -e "  ${Y}Spec not ready yet. Complete Step 4 first.${N}"
fi

echo ""
echo -e "${G}╔══════════════════════════════════════════╗${N}"
echo -e "${G}║  SCENARIO B COMPLETE                     ║${N}"
echo -e "${G}╚══════════════════════════════════════════╝${N}"
echo "  Files produced:"
echo "    Snapshot     : $SNAPSHOT_FILE"
echo "    Selector Map : $SELECTOR_MAP_FILE"
echo "    Manual tests : $TEST_CASES_FILE"
echo "    Spec file    : $SPEC_FILE"
