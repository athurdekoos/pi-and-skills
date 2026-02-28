---
name: "gsd-progress"
description: "Check project progress, show context, and route to next action (execute or plan)"
metadata:
  short-description: "Check project progress, show context, and route to next action (execute or plan)"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<objective>
Check project progress, summarize recent work and what's ahead, then intelligently route to the next action - either executing an existing plan or creating the next one.

Provides situational awareness before continuing work.
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/progress.md
</execution_context>

<process>
Execute the progress workflow from @/home/mia/.agents/get-shit-done/workflows/progress.md end-to-end.
Preserve all routing logic (Routes A through F) and edge case handling.
</process>
