---
name: "gsd-new-project"
description: "Initialize a new project with deep context gathering and PROJECT.md"
metadata:
  short-description: "Initialize a new project with deep context gathering and PROJECT.md"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<context>
**Flags:**
- `--auto` — Automatic mode. After config questions, runs research → requirements → roadmap without further interaction. Expects idea document via @ reference.
</context>

<objective>
Initialize a new project through unified flow: questioning → research (optional) → requirements → roadmap.

**Quality standards integrated from project start:**
- System design principles guide architecture decisions during questioning (ref: system-design skill)
- Testing strategy is considered when scoping requirements (ref: testing-strategy skill)
- Documentation deliverables are planned alongside features (ref: documentation skill)
- Tech debt awareness informs scope decisions (ref: tech-debt skill)
- Security review criteria shape requirements (ref: code-review skill)

**Creates:**
- `.planning/PROJECT.md` — project context
- `.planning/config.json` — workflow preferences
- `.planning/research/` — domain research (optional)
- `.planning/REQUIREMENTS.md` — scoped requirements
- `.planning/ROADMAP.md` — phase structure
- `.planning/STATE.md` — project memory

**After this command:** Run `/skill:gsd-plan-phase 1` to start execution.
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/new-project.md
@/home/mia/.agents/get-shit-done/references/questioning.md
@/home/mia/.agents/get-shit-done/references/ui-brand.md
@/home/mia/.agents/get-shit-done/templates/project.md
@/home/mia/.agents/get-shit-done/templates/requirements.md
</execution_context>

<process>
Execute the new-project workflow from @/home/mia/.agents/get-shit-done/workflows/new-project.md end-to-end.
Preserve all workflow gates (validation, approvals, commits, routing).
</process>
