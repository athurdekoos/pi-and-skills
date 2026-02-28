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

sync_dir  "$HOME/.agents/skills"        "$BACKUP_DIR/agents-skills"   "~/.agents/skills"
sync_file "$HOME/.agents/skill-registry.json" "$BACKUP_DIR/skill-registry.json" "skill-registry.json"
sync_dir  "$HOME/.pi/agent/skills"      "$BACKUP_DIR/pi-agent-skills" "~/.pi/agent/skills"
sync_dir  "$HOME/.pi/agent/prompts"     "$BACKUP_DIR/pi-agent-prompts" "~/.pi/agent/prompts"
sync_file "$HOME/.pi/agent/settings.json" "$BACKUP_DIR/settings.json"  "settings.json"
sync_dir  "$HOME/.pi/agent/bin"         "$BACKUP_DIR/pi-agent-bin"    "~/.pi/agent/bin"

echo ""
echo "✅ Backup snapshot written to $BACKUP_DIR"

if [[ "$AUTO_COMMIT" == true ]]; then
  cd "$REPO_DIR"
  git add -A
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  git commit -m "backup: snapshot $TIMESTAMP" || echo "Nothing to commit"
  echo "📦 Committed. Run 'git push' to persist remotely."
fi
