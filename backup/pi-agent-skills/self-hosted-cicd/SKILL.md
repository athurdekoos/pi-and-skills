---
name: self-hosted-cicd
description: >
  Scaffold a complete self-hosted GitHub Actions CI/CD pipeline with hardened
  security scanning for Node.js projects. Use this skill whenever the user asks
  to "set up CI/CD", "add GitHub Actions", "create a pipeline", "security
  scanning", "add CI to my project", "self-hosted runner", "harden my repo",
  or mentions wanting automated testing, linting, secret scanning, dependency
  auditing, SAST, or container scanning in their GitHub workflow. Also trigger
  when someone says "make this repo production-ready" or "add DevSecOps".
---

# Self-Hosted CI/CD Pipeline Skill

**Announce at start:** "I'm using the self-hosted-cicd skill to scaffold a secure CI/CD pipeline."

## What This Builds

A multi-stage GitHub Actions pipeline running on a self-hosted Docker runner with 8 security gates:

| Stage | Tools | What It Catches |
|-------|-------|-----------------|
| Lint | ESLint + `eslint-plugin-security` + `no-unsanitized` | eval, prototype pollution, DOM injection |
| Audit | npm audit, Trivy FS, lockfile-lint, license-checker | CVEs, supply chain attacks, GPL contamination |
| Secrets | Gitleaks (custom rules) | API keys, tokens, passwords, Telegram bot tokens |
| SAST | GitHub CodeQL (security-extended) | Injection, XSS, broken auth, data flow bugs |
| Test | Project's existing test runner | Functional regressions |
| Container | Hadolint + Trivy image scan | Dockerfile misconfig, base image vulns |
| Scorecard | OSSF Scorecard | Overall open-source security posture |
| Gate | Aggregate check | Blocks merge if any stage fails |

## Quick Start

Run the scaffold script to generate all files for a Node.js project:

```bash
bash <skill-dir>/scripts/scaffold-pipeline.sh /path/to/project
```

The script auto-detects whether `package.json` is at root or in `server/`, generates all workflow files, installs security dev-deps, and prints next steps.

## How to Use This Skill

### For a new project
1. Run `scaffold-pipeline.sh` targeting the project root
2. Review generated files in `.github/`
3. Follow `references/runner-setup.md` if self-hosting
4. Push and verify pipeline runs green

### For an existing project with partial CI
1. Read `references/security-checklist.md` to identify gaps
2. Cherry-pick the stages you need from the generated `ci.yml`
3. Add missing dev dependencies (eslint-plugin-security, lockfile-lint, etc.)

## Key Security Decisions

These are the "why" behind each non-obvious choice in the pipeline:

1. **Pinned action SHAs** — Tags like `@v4` can be moved to point at malicious commits. SHA pins are immutable. Dependabot will still propose updates.

2. **Minimal `permissions`** — Default `contents: read` at workflow level. Only `sast` and `scorecard` jobs escalate to `security-events: write` because they need to upload SARIF results. This limits blast radius if the workflow is compromised.

3. **Ephemeral runners** — `EPHEMERAL=1` in docker-compose means the runner de-registers after each job. No state persists between runs, so a compromised job can't poison the next one.

4. **No `pull_request_target`** — This trigger runs workflow code from the *base* branch but with *write* permissions, which is a common vector for secret exfiltration from forks. We use plain `pull_request` instead.

5. **Full-depth checkout for secrets scan** — `fetch-depth: 0` lets Gitleaks scan the entire git history, not just the current commit. Secrets committed and "deleted" are still in history.

6. **Concurrency groups** — `cancel-in-progress: true` prevents resource waste when you push multiple times quickly. Each branch gets its own group so main and PR runs don't cancel each other.

7. **Weekly scheduled scans** — New CVEs are published daily. Even if you haven't pushed code, your dependencies might have new vulnerabilities. The Monday 6am cron catches these.

## File Layout Generated

```
.github/
├── workflows/ci.yml          # 8-stage pipeline
├── runner/                    # Self-hosted runner (Docker)
│   ├── Dockerfile            # Runner + Node.js + security tools
│   ├── docker-compose.yml    # Ephemeral container config
│   ├── .env.example          # Template for runner registration
│   ├── setup-runner.sh       # One-command runner start
│   └── teardown-runner.sh    # Clean shutdown
├── scripts/
│   ├── init-cicd.sh          # Full local bootstrap
│   └── setup-branch-protection.sh  # GitHub API branch rules
├── dependabot.yml            # Weekly dep + action updates
└── CODEOWNERS                # Require review for security files
.gitleaks.toml                # Custom secret patterns
SECURITY.md                   # Vulnerability reporting policy
server/.eslintrc.json         # Security-focused lint rules
```

## References

- `references/security-checklist.md` — Full threat model with 13 concerns, mitigations, and verification commands
- `references/runner-setup.md` — Step-by-step runner deployment guide with troubleshooting
