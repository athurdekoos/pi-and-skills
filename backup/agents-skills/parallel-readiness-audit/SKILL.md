---
name: parallel-readiness-audit
description: Audit all installed agent skills, workflows, and agents for parallel execution readiness. Scans structural validity, workflow patterns, and cross-skill conflicts, then generates a markdown report with findings grouped by severity. Use when asked to "audit skills", "check parallelization readiness", "scan for skill conflicts", "generate readiness report", "are my skills safe to parallelize", or "run parallel audit".
---

# Parallel Readiness Audit

Comprehensive audit of your agent ecosystem's readiness for parallel execution. Scans all installed skills, workflows, and agent definitions, then produces a single markdown report with actionable findings.

## What It Checks

1. **Structural Validation** — Verifies SKILL.md existence, required frontmatter fields, `@` file references resolve, and agent definitions are valid
2. **Workflow Analysis** — Extracts `Task()` and `subagent()` calls, classifies execution modes (sequential vs parallel), identifies parallelization and fan-out opportunities
3. **Conflict Detection** — Analyzes file I/O patterns across all skills, detects write-write and read-write conflicts, groups skills into safe-to-parallelize sets

## How to Run

```bash
cd ~/dev/parallel-readiness-audit
PYTHONPATH=src python3 -m parallel_readiness_audit
```

The report generator automatically runs all three upstream analysis modules in sequence. No manual step is needed — a single command produces the full audit.

### Options

- `--output PATH` — Override the default output location (default: `./parallel-readiness-report.md`)

## Output

A single markdown file (`parallel-readiness-report.md`) containing:

- **Executive Summary** — Total skills/workflows/agents scanned, error/warning/info counts, overall pass/fail status, top 3 findings
- **Detail Sections** — Findings grouped by source (Structural Validation, Workflow Analysis, Conflict Detection), then by severity (errors first, then warnings, then info)
- **Suppressed All-Clear** — Sections with zero findings are omitted for a clean report

### Status Levels

| Status | Meaning |
|--------|---------|
| 🟢 PASS | No errors or warnings — only informational findings |
| 🟡 WARN | Warnings found but no errors — review recommended |
| 🔴 FAIL | Errors found — action required before safe parallelization |

## Requirements

- Python 3.13+
- PyYAML (`pip install pyyaml`)

## Project Location

`~/dev/parallel-readiness-audit/`

## Orchestration Instructions

When invoked as a skill:

1. Run `PYTHONPATH=src python3 -m parallel_readiness_audit` from the project directory (`~/dev/parallel-readiness-audit/`)
2. Present the executive summary to the user (status badge, counts table, top findings)
3. If the user wants details, show the relevant section(s) from the generated report
4. All upstream modules (scan, analyzer, conflict_detector) are called directly by the report module — no subprocesses needed
