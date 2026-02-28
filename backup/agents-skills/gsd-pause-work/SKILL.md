---
name: "gsd-pause-work"
description: "Create context handoff when pausing work mid-phase"
metadata:
  short-description: "Create context handoff when pausing work mid-phase"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<objective>
Create `.continue-here.md` handoff file to preserve complete work state across sessions.

Routes to the pause-work workflow which handles:
- Current phase detection from recent files
- Complete state gathering (position, completed work, remaining work, decisions, blockers)
- Handoff file creation with all context sections
- Git commit as WIP
- Resume instructions
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/pause-work.md
</execution_context>

<context>
State and phase progress are gathered in-workflow with targeted reads.
</context>

<process>
**Follow the pause-work workflow** from `@/home/mia/.agents/get-shit-done/workflows/pause-work.md`.

The workflow handles all logic including:
1. Phase directory detection
2. State gathering with user clarifications
3. Handoff file writing with timestamp
4. Git commit
5. Confirmation with resume instructions
</process>
