#!/bin/bash
# Daily skill health audit — run by cron
# Sends report via email; falls back to /tmp if msmtp fails

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="/tmp/skill-audit-cron.log"

echo "[$(date)] Starting daily skill audit" >> "$LOG"

python3 "$SCRIPT_DIR/audit_skills.py" \
    --email "${SKILL_AUDIT_EMAIL:-}" \
    >> "$LOG" 2>&1

echo "[$(date)] Audit complete (exit: $?)" >> "$LOG"
