#!/usr/bin/env bash
# Skills-for-Claude — Mac/Linux/Git-Bash Setup Script
# Usage: bash setup.sh [--force] [--skip-settings]

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
FORCE=false
SKIP_SETTINGS=false

for arg in "$@"; do
  case $arg in
    --force) FORCE=true ;;
    --skip-settings) SKIP_SETTINGS=true ;;
  esac
done

step()  { echo; echo "==> $1"; }
ok()    { echo "    [OK] $1"; }
warn()  { echo "    [!!] $1"; }

echo
echo "Skills-for-Claude Setup"
echo "======================="

# 1. Skills
step "Installing skills to $CLAUDE_DIR/skills/"
mkdir -p "$CLAUDE_DIR/skills"
count=0
for skill_dir in "$REPO_ROOT/skills"/*/; do
  skill_name=$(basename "$skill_dir")
  dst="$CLAUDE_DIR/skills/$skill_name"
  if [ -d "$dst" ] && [ "$FORCE" != true ]; then
    warn "Skipping $skill_name (exists — use --force to overwrite)"
  else
    cp -r "$skill_dir" "$CLAUDE_DIR/skills/"
    ok "$skill_name"
  fi
  count=$((count + 1))
done
echo "    $count skills processed"

# 2. Hooks
step "Installing hooks to $CLAUDE_DIR/hooks/"
mkdir -p "$CLAUDE_DIR/hooks"
cp -f "$REPO_ROOT/hooks/fix-flat-skill.py" "$CLAUDE_DIR/hooks/"
ok "fix-flat-skill.py"

# 3. Shared context
step "Installing shared-context to $CLAUDE_DIR/shared-context/"

# memories/_shared.md
mkdir -p "$CLAUDE_DIR/shared-context/memories"
if [ -f "$CLAUDE_DIR/shared-context/memories/_shared.md" ] && [ "$FORCE" != true ]; then
  warn "_shared.md already exists — skipping (use --force to overwrite)"
else
  cp -f "$REPO_ROOT/shared-context/memories/_shared.md" "$CLAUDE_DIR/shared-context/memories/_shared.md"
  ok "memories/_shared.md"
fi

# knowledge/
mkdir -p "$CLAUDE_DIR/shared-context/knowledge"
for kfile in "$REPO_ROOT/shared-context/knowledge/"*.md; do
  [ -f "$kfile" ] || continue
  fname=$(basename "$kfile")
  dst="$CLAUDE_DIR/shared-context/knowledge/$fname"
  if [ -f "$dst" ] && [ "$FORCE" != true ]; then
    warn "knowledge/$fname exists — skipping"
  else
    cp -f "$kfile" "$dst"
    ok "knowledge/$fname"
  fi
done

# 4. Settings
if [ "$SKIP_SETTINGS" != true ]; then
  step "Settings configuration"
  if [ -f "$CLAUDE_DIR/settings.json" ]; then
    warn "settings.json exists. Review config/settings.template.json manually."
    echo "    Key things to add:"
    echo "      - hooks (PostToolUse, PreCompact, SessionStart)"
    echo "      - enabledPlugins"
    echo "      - extraKnownMarketplaces"
  else
    cp -f "$REPO_ROOT/config/settings.template.json" "$CLAUDE_DIR/settings.json"
    ok "settings.json created from template"
  fi
fi

# 5. Project example
step "Project-example skills"
echo "    project-example/.claude/skills/ contains:"
for d in "$REPO_ROOT/project-example/.claude/skills"/*/; do
  echo "      - $(basename "$d")"
done
echo "    Copy these to your project's .claude/skills/ as needed."

echo
echo "Setup complete!"
echo "Restart Claude Code to activate skills and hooks."
echo
