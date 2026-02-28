---
name: "gsd-add-todo"
description: "Capture idea or task as todo from current conversation context"
metadata:
  short-description: "Capture idea or task as todo from current conversation context"
---

<pi_skill_adapter>
Pi coding agent mode:
- This skill is invoked via /skill:SKILL_NAME or when the task matches the description.
- Use the read tool to load referenced files (paths starting with @).
- Treat @ path references as files to read with the read tool.
- For subagent patterns, work inline in the current session.
</pi_skill_adapter>

<objective>
Capture an idea, task, or issue that surfaces during a GSD session as a structured todo for later work.

Routes to the add-todo workflow which handles:
- Directory structure creation
- Content extraction from arguments or conversation
- Area inference from file paths
- Duplicate detection and resolution
- Todo file creation with frontmatter
- STATE.md updates
- Git commits
</objective>

<execution_context>
@/home/mia/.agents/get-shit-done/workflows/add-todo.md
</execution_context>

<context>
Arguments: {{GSD_ARGS}} (optional todo description)

State is resolved in-workflow via `init todos` and targeted reads.
</context>

<process>
**Follow the add-todo workflow** from `@/home/mia/.agents/get-shit-done/workflows/add-todo.md`.

The workflow handles all logic including:
1. Directory ensuring
2. Existing area checking
3. Content extraction (arguments or conversation)
4. Area inference
5. Duplicate checking
6. File creation with slug generation
7. STATE.md updates
8. Git commits
</process>
