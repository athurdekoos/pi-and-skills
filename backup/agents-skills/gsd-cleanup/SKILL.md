---
name: "gsd-cleanup"
description: "Archive accumulated phase directories from completed milestones"
metadata:
  short-description: "Archive accumulated phase directories from completed milestones"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<objective>
Archive phase directories from completed milestones into `.planning/milestones/v{X.Y}-phases/`.

Use when `.planning/phases/` has accumulated directories from past milestones.
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/cleanup.md
</execution_context>

<process>
Follow the cleanup workflow at @/home/mia/.agents/get-shit-done/workflows/cleanup.md.
Identify completed milestones, show a dry-run summary, and archive on confirmation.
</process>
