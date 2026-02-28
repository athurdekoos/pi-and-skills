#!/usr/bin/env bash
set -euo pipefail

# pi-restore — Restore pi agent skills, prompts, settings, and registry
# Usage: npx @athurdekoos/pi-and-skills
#        or: ./bin/restore.sh [--dry-run]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$REPO_DIR/backup"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "=== DRY RUN — no files will be modified ==="
fi

AGENTS_SKILLS="$HOME/.agents/skills"
AGENTS_REGISTRY="$HOME/.agents/skill-registry.json"
PI_SKILLS="$HOME/.pi/agent/skills"
PI_PROMPTS="$HOME/.pi/agent/prompts"
PI_SETTINGS="$HOME/.pi/agent/settings.json"
PI_BIN="$HOME/.pi/agent/bin"

restore_dir() {
  local src="$1" dst="$2" label="$3"
  if [[ ! -d "$src" ]]; then
    echo "⏭  Skip $label (not in backup)"
    return
  fi
  echo "📂 Restoring $label → $dst"
  if [[ "$DRY_RUN" == false ]]; then
    mkdir -p "$dst"
    rsync -a --delete "$src/" "$dst/"
  fi
}

restore_file() {
  local src="$1" dst="$2" label="$3"
  if [[ ! -f "$src" ]]; then
    echo "⏭  Skip $label (not in backup)"
    return
  fi
  echo "📄 Restoring $label → $dst"
  if [[ "$DRY_RUN" == false ]]; then
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
  fi
}

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   pi-and-skills restore                  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

restore_dir  "$BACKUP_DIR/agents-skills"      "$AGENTS_SKILLS"   "~/.agents/skills"
restore_file "$BACKUP_DIR/skill-registry.json" "$AGENTS_REGISTRY" "skill-registry.json"
restore_dir  "$BACKUP_DIR/pi-agent-skills"     "$PI_SKILLS"       "~/.pi/agent/skills"
restore_dir  "$BACKUP_DIR/pi-agent-prompts"    "$PI_PROMPTS"      "~/.pi/agent/prompts"
restore_file "$BACKUP_DIR/settings.json"       "$PI_SETTINGS"     "settings.json"
restore_dir  "$BACKUP_DIR/pi-agent-bin"        "$PI_BIN"          "~/.pi/agent/bin"

echo ""
if [[ "$DRY_RUN" == true ]]; then
  echo "✅ Dry run complete. Re-run without --dry-run to apply."
else
  echo "✅ Restore complete!"
fi
