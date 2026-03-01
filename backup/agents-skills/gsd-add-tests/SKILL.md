---
name: "gsd-add-tests"
description: "Generate tests for a completed phase based on UAT criteria and implementation"
metadata:
  short-description: "Generate tests for a completed phase based on UAT criteria and implementation"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<objective>
Generate unit and E2E tests for a completed phase, using its SUMMARY.md, CONTEXT.md, and VERIFICATION.md as specifications.

Analyzes implementation files, classifies them into TDD (unit), E2E (browser), or Skip categories, presents a test plan for user approval, then generates tests following RED-GREEN conventions.

Output: Test files committed with message `test(phase-{N}): add unit and E2E tests from add-tests command`
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/add-tests.md
</execution_context>

<context>
Phase: {{GSD_ARGS}}

@.planning/STATE.md
@.planning/ROADMAP.md
</context>

<process>
Execute the add-tests workflow from @/home/mia/.agents/get-shit-done/workflows/add-tests.md end-to-end.
Preserve all workflow gates (classification approval, test plan approval, RED-GREEN verification, gap reporting).

When generating tests, apply quality skill guidance:
- **Testing strategy**: Follow the testing pyramid — many unit tests, some integration, few E2E. Match test type to component type (ref: testing-strategy skill)
- **Code review lens**: Tests should cover security boundaries, error handling, edge cases, and concurrency (ref: code-review skill)
- **Documentation**: Include test documentation explaining what each test validates and why (ref: documentation skill)
- **Tech debt coverage**: Prioritize tests for areas with known tech debt to prevent regressions (ref: tech-debt skill)
</process>
