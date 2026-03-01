---
name: system-health
description: >
  System health monitor daemon for VM environments. Checks RAM, disk, swap,
  CPU load, OOM kills, zombie processes, failed services, SSH brute force
  attempts, and node server availability. Runs every 5 minutes via cron —
  sends emergency emails immediately (with 1-hour cooldown) and a daily
  digest at 06:00 UTC. Use this skill when the user asks "is my system healthy",
  "check system health", "server status", "am I running low on disk",
  "is the server up", "system monitor", or when troubleshooting performance.
---

# System Health Monitor

## What This Does

Monitors critical system resources on this VM and alerts via email when
things go wrong. Two modes:

- **Emergency (every 5 min):** RAM critical, disk full, OOM kills, swap thrashing, server down
- **Daily digest (06:00 UTC):** Full status report with warnings and info

## Running Manually

```bash
# Full report
python3 ~/.agents/skills/system-health/scripts/health_check.py

# Emergency checks only (what cron runs every 5 min)
python3 ~/.agents/skills/system-health/scripts/health_check.py --emergency-only

# Email the report
python3 ~/.agents/skills/system-health/scripts/health_check.py --email skynetwasdumb@gmail.com

# JSON output
python3 ~/.agents/skills/system-health/scripts/health_check.py --json
```

## Send a Test Email

```bash
python3 ~/.agents/skills/system-health/scripts/send_test.py
```

Sends a test email with current status from both the skill auditor and
system health checker. Marked clearly as a test. Use this to verify
email is working or to get a snapshot of current status.

Add `--email other@example.com` to send to a different address.

## Health Checks

Read `references/check_reference.md` for the complete list of checks,
thresholds, and what to do when alerts fire.
