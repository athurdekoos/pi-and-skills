#!/usr/bin/env bash
set -euo pipefail

# pi-backup — Snapshot current pi agent state into this repo's backup/ dir
# Usage: ./bin/backup.sh [--commit]
#
# Run from the repo root, then git push to persist.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$REPO_DIR/backup"

AUTO_COMMIT=false
if [[ "${1:-}" == "--commit" ]]; then
  AUTO_COMMIT=true
fi

sync_dir() {
  local src="$1" dst="$2" label="$3"
  if [[ ! -d "$src" ]]; then
    echo "⏭  Skip $label (source not found)"
    return
  fi
  echo "📂 Backing up $label"
  mkdir -p "$dst"
  rsync -a --delete "$src/" "$dst/"
}

sync_file() {
  local src="$1" dst="$2" label="$3"
  if [[ ! -f "$src" ]]; then
    echo "⏭  Skip $label (source not found)"
    return
  fi
  echo "📄 Backing up $label"
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
}

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   pi-and-skills backup                   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Core skills
sync_dir  "$HOME/.agents/skills"              "$BACKUP_DIR/agents-skills"      "~/.agents/skills"
sync_file "$HOME/.agents/skill-registry.json"  "$BACKUP_DIR/skill-registry.json" "skill-registry.json"

# Pi agent config
sync_dir  "$HOME/.pi/agent/skills"            "$BACKUP_DIR/pi-agent-skills"    "~/.pi/agent/skills"
sync_dir  "$HOME/.pi/agent/prompts"           "$BACKUP_DIR/pi-agent-prompts"   "~/.pi/agent/prompts"
sync_dir  "$HOME/.pi/agent/agents"            "$BACKUP_DIR/pi-agent-agents"    "~/.pi/agent/agents"
sync_dir  "$HOME/.pi/agent/bin"               "$BACKUP_DIR/pi-agent-bin"       "~/.pi/agent/bin"
sync_dir  "$HOME/.pi/agent/extensions"        "$BACKUP_DIR/pi-agent-extensions" "~/.pi/agent/extensions"
sync_file "$HOME/.pi/agent/settings.json"      "$BACKUP_DIR/settings.json"      "settings.json"

# User-level files (tasks, memory, CLAUDE.md)
sync_file "$HOME/TASKS.md"                     "$BACKUP_DIR/user/TASKS.md"      "~/TASKS.md"
sync_file "$HOME/CLAUDE.md"                    "$BACKUP_DIR/user/CLAUDE.md"     "~/CLAUDE.md"
sync_dir  "$HOME/memory"                       "$BACKUP_DIR/user/memory"        "~/memory"

echo ""
echo "✅ Backup snapshot written to $BACKUP_DIR"

# Show stats
SKILL_COUNT=$(find "$BACKUP_DIR/agents-skills" -name "SKILL.md" 2>/dev/null | wc -l)
echo "   Skills: $SKILL_COUNT"
echo "   Size:   $(du -sh "$BACKUP_DIR" | cut -f1)"

if [[ "$AUTO_COMMIT" == true ]]; then
  cd "$REPO_DIR"
  git add -A
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  CHANGES=$(git diff --cached --stat | tail -1)
  git commit -m "backup: snapshot $TIMESTAMP

$CHANGES
Skills: $SKILL_COUNT" || echo "Nothing to commit"
  echo "📦 Committed. Run 'git push' to persist remotely."
fi
