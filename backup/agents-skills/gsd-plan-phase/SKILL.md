---
name: "gsd-plan-phase"
description: "Create detailed phase plan (PLAN.md) with verification loop"
metadata:
  short-description: "Create detailed phase plan (PLAN.md) with verification loop"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<objective>
Create executable phase prompts (PLAN.md files) for a roadmap phase with integrated research and verification.

**Default flow:** Research (if needed) → Plan → Verify → Done

**Quality standards woven into plans:**
- Plans include code review steps after implementation (ref: code-review skill)
- Testing strategy specified per component — unit/integration/E2E (ref: testing-strategy skill)
- Documentation deliverables listed when APIs, config, or operations change (ref: documentation skill)
- Tech debt implications noted for shortcuts or workarounds (ref: tech-debt skill)
- Architecture decisions validated against system design principles (ref: system-design skill)

**Orchestrator role:** Parse arguments, validate phase, research domain (unless skipped), spawn gsd-planner, verify with gsd-plan-checker, iterate until pass or max iterations, present results.
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/plan-phase.md
@/home/mia/.agents/get-shit-done/references/ui-brand.md
</execution_context>

<context>
Phase number: {{GSD_ARGS}} (optional — auto-detects next unplanned phase if omitted)

**Flags:**
- `--research` — Force re-research even if RESEARCH.md exists
- `--skip-research` — Skip research, go straight to planning
- `--gaps` — Gap closure mode (reads VERIFICATION.md, skips research)
- `--skip-verify` — Skip verification loop
- `--prd <file>` — Use a PRD/acceptance criteria file instead of discuss-phase. Parses requirements into CONTEXT.md automatically. Skips discuss-phase entirely.

Normalize phase input in step 2 before any directory lookups.
</context>

<process>
Execute the plan-phase workflow from @/home/mia/.agents/get-shit-done/workflows/plan-phase.md end-to-end.
Preserve all workflow gates (validation, research, planning, verification loop, routing).
</process>
