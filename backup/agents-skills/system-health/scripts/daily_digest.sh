#!/bin/bash
# Daily health digest — runs at 06:00 UTC via cron
# Always sends full report (healthy or not)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="/tmp/system-health-digest.log"

echo "[$(date)] Starting daily health digest" >> "$LOG"

python3 "$SCRIPT_DIR/health_check.py" \
    --email "${SYSTEM_HEALTH_EMAIL:-}" \
    --no-cooldown \
    >> "$LOG" 2>&1

echo "[$(date)] Digest complete (exit: $?)" >> "$LOG"
