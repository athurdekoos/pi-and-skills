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

# Core skills
restore_dir  "$BACKUP_DIR/agents-skills"      "$HOME/.agents/skills"              "~/.agents/skills"
restore_file "$BACKUP_DIR/skill-registry.json" "$HOME/.agents/skill-registry.json" "skill-registry.json"

# Pi agent config
restore_dir  "$BACKUP_DIR/pi-agent-skills"     "$HOME/.pi/agent/skills"            "~/.pi/agent/skills"
restore_dir  "$BACKUP_DIR/pi-agent-prompts"    "$HOME/.pi/agent/prompts"           "~/.pi/agent/prompts"
restore_dir  "$BACKUP_DIR/pi-agent-agents"     "$HOME/.pi/agent/agents"            "~/.pi/agent/agents"
restore_dir  "$BACKUP_DIR/pi-agent-bin"        "$HOME/.pi/agent/bin"               "~/.pi/agent/bin"
restore_dir  "$BACKUP_DIR/pi-agent-extensions" "$HOME/.pi/agent/extensions"        "~/.pi/agent/extensions"
restore_file "$BACKUP_DIR/settings.json"       "$HOME/.pi/agent/settings.json"     "settings.json"

# User-level files
restore_file "$BACKUP_DIR/user/TASKS.md"       "$HOME/TASKS.md"                    "~/TASKS.md"
restore_file "$BACKUP_DIR/user/CLAUDE.md"      "$HOME/CLAUDE.md"                   "~/CLAUDE.md"
restore_dir  "$BACKUP_DIR/user/memory"         "$HOME/memory"                      "~/memory"

echo ""
if [[ "$DRY_RUN" == true ]]; then
  SKILL_COUNT=$(find "$BACKUP_DIR/agents-skills" -name "SKILL.md" 2>/dev/null | wc -l)
  echo "✅ Dry run complete. Would restore $SKILL_COUNT skills."
  echo "   Re-run without --dry-run to apply."
else
  echo "✅ Restore complete!"
fi
