---
name: "gsd-quick"
description: "Execute a quick task with GSD guarantees (atomic commits, state tracking) but skip optional agents"
metadata:
  short-description: "Execute a quick task with GSD guarantees (atomic commits, state tracking) but skip optional agents"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<objective>
Execute small, ad-hoc tasks with GSD guarantees (atomic commits, STATE.md tracking).

Quick mode is the same system with a shorter path:
- Spawns gsd-planner (quick mode) + gsd-executor(s)
- Quick tasks live in `.planning/quick/` separate from planned phases
- Updates STATE.md "Quick Tasks Completed" table (NOT ROADMAP.md)

**Default:** Skips research, plan-checker, verifier. Use when you know exactly what to do.

**`--full` flag:** Enables plan-checking (max 2 iterations) and post-execution verification. Use when you want quality guarantees without full milestone ceremony.
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/quick.md
</execution_context>

<context>
{{GSD_ARGS}}

Context files are resolved inside the workflow (`init quick`) and delegated via `<files_to_read>` blocks.
</context>

<process>
Execute the quick workflow from @/home/mia/.agents/get-shit-done/workflows/quick.md end-to-end.
Preserve all workflow gates (validation, task description, planning, execution, state updates, commits).
</process>
