---
name: "gsd-execute-phase"
description: "Execute all plans in a phase with wave-based parallelization"
metadata:
  short-description: "Execute all plans in a phase with wave-based parallelization"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<objective>
Execute all plans in a phase using wave-based parallel execution.

Orchestrator stays lean: discover plans, analyze dependencies, group into waves, spawn subagents, collect results. Each subagent loads the full execute-plan context and handles its own plan.

Context budget: ~15% orchestrator, 100% fresh per subagent.
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/execute-phase.md
@/home/mia/.agents/get-shit-done/references/ui-brand.md
</execution_context>

<context>
Phase: {{GSD_ARGS}}

**Flags:**
- `--gaps-only` — Execute only gap closure plans (plans with `gap_closure: true` in frontmatter). Use after verify-work creates fix plans.

Context files are resolved inside the workflow via `gsd-tools init execute-phase` and per-subagent `<files_to_read>` blocks.
</context>

<process>
Execute the execute-phase workflow from @/home/mia/.agents/get-shit-done/workflows/execute-phase.md end-to-end.
Preserve all workflow gates (wave execution, checkpoint handling, verification, state updates, routing).
</process>
