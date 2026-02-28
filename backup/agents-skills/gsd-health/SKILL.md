---
name: "gsd-health"
description: "Diagnose planning directory health and optionally repair issues"
metadata:
  short-description: "Diagnose planning directory health and optionally repair issues"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<objective>
Validate `.planning/` directory integrity and report actionable issues. Checks for missing files, invalid configurations, inconsistent state, and orphaned plans.
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/health.md
</execution_context>

<process>
Execute the health workflow from @/home/mia/.agents/get-shit-done/workflows/health.md end-to-end.
Parse --repair flag from arguments and pass to workflow.
</process>
