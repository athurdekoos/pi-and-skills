---
name: lessons-learned
description: >
  Daily health auditor for installed agent skills. Detects structural problems
  (missing SKILL.md, broken references, empty frontmatter), quality warnings
  (oversized skills, stale skills, near-duplicate names), and compilation errors
  in bundled scripts. Runs automatically via cron daemon and emails a report.
  Use this skill when the user asks "are my skills healthy", "audit my skills",
  "check skill problems", "skill health check", "lessons learned", "what skills
  have issues", or when troubleshooting why a skill isn't triggering properly.
---

# Lessons Learned — Skill Health Auditor

## What This Does

Scans all installed skills in `~/.agents/skills/` and checks for common
problems that cause skills to malfunction, fail to trigger, or degrade
agent performance.

## Running Manually

```bash
python3 ~/.agents/skills/lessons-learned/scripts/audit_skills.py
```

Add `--email user@example.com` to send the report via msmtp.
Add `--json` for machine-readable output.

## Automated Mode

A cron job runs this daily and emails results. See the daemon setup
in `references/check_catalog.md` for the full list of checks and
severity levels.

## Health Checks

Read `references/check_catalog.md` for the complete catalog of checks,
their severity levels, and remediation guidance.

## What To Do With Results

- 🔴 **ERROR** — Skill is broken or non-functional. Fix immediately.
- 🟡 **WARN** — Skill works but has quality issues. Fix when convenient.
- ℹ️ **INFO** — Minor housekeeping. Fix at your leisure.

When reviewing results, start with ERRORs — they indicate skills that
are definitely not working as intended.
