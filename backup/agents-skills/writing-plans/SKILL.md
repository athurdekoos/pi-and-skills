---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This should be run in a dedicated worktree (created by brainstorming skill).

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

## Plan Phases

Every plan MUST include these three quality gates alongside implementation tasks. They are not optional — they are part of the plan.

### Phase 1: Engineering Design (before coding)

Before writing any implementation tasks, include a design section:

- **Architecture decision** — Which components are involved, how they interact, what patterns to use
- **Data model** — Schema changes, API contracts, state management
- **Trade-off analysis** — Why this approach over alternatives, what we're optimizing for
- **Scale considerations** — Will this hold up? What breaks first?
- **Error handling strategy** — Failure modes, retry logic, graceful degradation
- **Edge cases enumeration** — List all boundary conditions, empty states, invalid inputs, concurrent scenarios that tests must cover
- **Observability** — Logging, metrics, alerting — how will you detect problems in production?

This phase should reference the system-design skill's framework: requirements → high-level design → deep dive → trade-offs.

### Phase 2: Implementation Tasks (TDD)

The bite-sized tasks described below in "Task Structure." This is the bulk of the plan.

**Task dependencies:** For each task, note if it depends on another task or can run in parallel:
- `Depends on: Task N` — must wait for that task to complete
- `Parallelizable with: Task N` — can run concurrently

### Phase 3: Integration Test (after implementation, before code review)

After all unit-level TDD tasks, include an integration test task:

```markdown
### Task N-1: Integration Test

**Purpose:** Verify components work together end-to-end.

**Step 1: Write integration test covering the full flow**

- Test realistic user scenarios, not isolated units
- Use realistic data (not trivial mocks)
- Cover the happy path AND at least one failure path

**Step 2: Run integration test**

Run: `[test command for integration tests]`
Expected: PASS

**Step 3: Commit**

```bash
git commit -m "test: add integration tests for [feature]"
```
```

### Phase 4: Code Review Gate (after implementation, before merge)

After all implementation tasks, include a code review task:

```markdown
### Task N: Code Review

**Run the code-review skill** against all files created/modified in this plan.

**Review dimensions (all required):**

**Security:**
- SQL injection, XSS, CSRF, SSRF
- Auth/authz flaws
- Secrets or credentials in code
- Insecure deserialization, path traversal

**Performance:**
- N+1 queries, unbounded loops
- Unnecessary allocations, resource leaks
- Algorithmic complexity in hot paths
- Missing indexes

**Correctness:**
- Edge cases (empty, null, overflow)
- Race conditions, concurrency
- Error handling, off-by-one

**Maintainability:**
- Naming, single responsibility, duplication
- Test coverage gaps
- Missing docs for non-obvious logic

**Step 1:** Review all new/modified files against the dimensions above
**Step 2:** Fix any issues found (create sub-tasks as needed)
**Step 3:** Re-review fixed code
**Step 4:** Commit fixes

```bash
git commit -m "fix: address code review findings"
```
```

### Phase 5: Security Audit (after implementation, before merge)

After code review, include a security audit task:

```markdown
### Task N+1: Security Audit

**Run the repo-security-review skill** scoped to the changes in this plan.

**Audit domains (check all that apply to this change):**

1. **Secrets Detection** — Scan new files for hardcoded keys, tokens, passwords
2. **Dependency & Supply Chain** — Audit any new dependencies added (CVEs, typosquatting, lockfile integrity)
3. **SAST** — Static analysis on new code for injection, XSS, SSRF, unsafe deserialization
4. **Infrastructure** — If Dockerfiles, CI/CD, or IaC changed: check misconfigurations
5. **Auth & Authz** — If auth touched: broken auth, missing authz, privilege escalation
6. **API Security** — If APIs added/changed: input validation, rate limiting, CORS, error leakage
7. **Data Protection** — If PII handled: encryption, logging, retention

**Step 1:** Run targeted security review on all files from this plan
**Step 2:** Classify findings by severity (🔴 CRITICAL, 🟡 HIGH, 🟢 MEDIUM, ℹ️ LOW)
**Step 3:** Fix all CRITICAL and HIGH findings (create sub-tasks as needed)
**Step 4:** Document accepted risks for MEDIUM/LOW findings
**Step 5:** Commit fixes

```bash
git commit -m "security: remediate audit findings"
```
```

### Phase 6: Rollback Plan

Every plan MUST end with a rollback strategy:

```markdown
### Task N+2: Rollback Plan

**Document how to undo this change if it breaks production:**

1. **Revert method:** [git revert, feature flag toggle, migration rollback]
2. **Data implications:** [Is rollback safe? Any data written in new format? Backfill needed?]
3. **Dependent services:** [What else breaks if this is reverted?]
4. **Rollback verification:** [How to confirm rollback succeeded]
```

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Done When:** [Measurable acceptance criteria — e.g., "API returns 200 for valid input, 422 for invalid, all tests pass, deployed to staging"]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Prerequisites:** [Branch to start from, env setup needed, services to run, env vars, DB migrations]

**Estimated Tasks:** [N tasks, ~X hours]
**Complexity:** [Low / Medium / High]

**Out of Scope:** [What this plan explicitly does NOT cover — prevents scope creep]

**Quality Gates:** Engineering Design → Implementation (TDD) → Integration Test → Code Review → Security Audit

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Remember
- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- Reference relevant skills with @ syntax
- DRY, YAGNI, TDD, frequent commits
- **Every plan ends with Integration Test → Code Review → Security Audit → Rollback Plan — no exceptions**

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use subagent-driven-development
- Stay in this session
- Fresh subagent per task + code review

**If Parallel Session chosen:**
- Guide them to open new session in worktree
- **REQUIRED SUB-SKILL:** New session uses executing-plans
