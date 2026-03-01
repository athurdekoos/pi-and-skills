#!/bin/bash
# Emergency health check — runs every 5 minutes via cron
# Only emails if something is wrong (with 1-hour cooldown per check)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="/tmp/system-health-emergency.log"

python3 "$SCRIPT_DIR/health_check.py" \
    --emergency-only \
    --email "${SYSTEM_HEALTH_EMAIL:-}" \
    >> "$LOG" 2>&1
