---
name: "gsd-new-milestone"
description: "Start a new milestone cycle — update PROJECT.md and route to requirements"
metadata:
  short-description: "Start a new milestone cycle — update PROJECT.md and route to requirements"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<objective>
Start a new milestone: questioning → research (optional) → requirements → roadmap.

Brownfield equivalent of new-project. Project exists, PROJECT.md has history. Gathers "what's next", updates PROJECT.md, then runs requirements → roadmap cycle.

**Quality dimensions carried forward:**
- Review tech debt from previous milestone and plan remediation (ref: tech-debt skill)
- Assess testing coverage gaps to address in new milestone (ref: testing-strategy skill)
- Update documentation plan for new features (ref: documentation skill)
- Validate architecture can support planned changes (ref: system-design skill)
- Apply code review lessons learned from previous phases (ref: code-review skill)

**Creates/Updates:**
- `.planning/PROJECT.md` — updated with new milestone goals
- `.planning/research/` — domain research (optional, NEW features only)
- `.planning/REQUIREMENTS.md` — scoped requirements for this milestone
- `.planning/ROADMAP.md` — phase structure (continues numbering)
- `.planning/STATE.md` — reset for new milestone

**After:** `/skill:gsd-plan-phase [N]` to start execution.
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/new-milestone.md
@/home/mia/.agents/get-shit-done/references/questioning.md
@/home/mia/.agents/get-shit-done/references/ui-brand.md
@/home/mia/.agents/get-shit-done/templates/project.md
@/home/mia/.agents/get-shit-done/templates/requirements.md
</execution_context>

<context>
Milestone name: {{GSD_ARGS}} (optional - will prompt if not provided)

Project and milestone context files are resolved inside the workflow (`init new-milestone`) and delegated via `<files_to_read>` blocks where subagents are used.
</context>

<process>
Execute the new-milestone workflow from @/home/mia/.agents/get-shit-done/workflows/new-milestone.md end-to-end.
Preserve all workflow gates (validation, questioning, research, requirements, roadmap approval, commits).
</process>
