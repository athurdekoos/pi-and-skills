---
name: "gsd-help"
description: "Show available GSD commands and usage guide"
metadata:
  short-description: "Show available GSD commands and usage guide"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<objective>
Display the complete GSD command reference.

Output ONLY the reference content below. Do NOT add:
- Project-specific analysis
- Git status or file context
- Next-step suggestions
- Any commentary beyond the reference
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/help.md
</execution_context>

<process>
Output the complete GSD command reference from @/home/mia/.agents/get-shit-done/workflows/help.md.
Display the reference content directly — no additions or modifications.
</process>
