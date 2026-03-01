---
name: repo-security-review
description: >
  Comprehensive security audit of a code repository covering secrets detection, dependency vulnerabilities,
  static analysis (SAST), infrastructure-as-code misconfigurations, CI/CD pipeline risks, authentication
  and authorization flaws, API security, and data protection. Use this skill whenever the user asks to
  "audit this repo for security", "check for vulnerabilities", "is this repo secure", "security review",
  "find secrets in code", "check dependencies for CVEs", "scan for security issues", "harden this repo",
  "security checklist", "pentest this codebase", "threat model", "supply chain risk", "check my Dockerfile",
  "is my GitHub Actions workflow safe", or any request related to finding security problems in a codebase.
  Also trigger when the user mentions OWASP, CVE, CWE, SAST, SCA, secret scanning, or security hardening.
---

# Repository Security Review

A structured, comprehensive security audit for any code repository. This skill covers 8 domains that
together represent the full attack surface of a modern software project. Most security incidents come
from things teams *forgot to check*, not things they checked poorly — so the primary value here is
**breadth of coverage** with actionable remediation steps.

## How to Use This Skill

When triggered, determine the scope:

1. **Full audit** — Run all 8 domains. Takes longer but gives complete coverage. Use when the user
   says "audit this repo" or "security review" without specifying a focus area.
2. **Targeted review** — Run 1-3 specific domains. Use when the user asks about something specific
   like "check my dependencies" or "is my Dockerfile secure".
3. **Quick scan** — Hit the highest-impact checks across all domains in ~5 minutes. Use when the
   user says "quick security check" or seems time-constrained.

For any scope, follow this process:

### Step 1: Reconnaissance

Before diving into checks, understand what you're looking at:

```bash
# Identify the tech stack
find . -maxdepth 3 -name "package.json" -o -name "requirements.txt" -o -name "go.mod" \
  -o -name "Cargo.toml" -o -name "pom.xml" -o -name "Gemfile" -o -name "*.csproj" \
  -o -name "composer.json" -o -name "pubspec.yaml" 2>/dev/null

# Identify infrastructure files
find . -maxdepth 4 -name "Dockerfile*" -o -name "docker-compose*" -o -name "*.tf" \
  -o -name "*.tfvars" -o -name "k8s*" -o -name "helm*" -o -name "*.yaml" -path "*deploy*" 2>/dev/null

# Identify CI/CD
find . -maxdepth 3 -path "*/.github/workflows/*" -o -path "*/.gitlab-ci*" \
  -o -path "*/.circleci/*" -o -name "Jenkinsfile" 2>/dev/null

# Check for security tooling already in place
find . -maxdepth 2 -name ".snyk" -o -name ".trivyignore" -o -name ".gitleaks.toml" \
  -o -name ".semgrepignore" -o -name "security.md" -o -name "SECURITY.md" 2>/dev/null

# Get a sense of repo size and structure
find . -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/vendor/*' \
  -not -path '*/__pycache__/*' | head -200
```

This tells you which domains are relevant. A pure Python API has different risks than a Terraform monorepo.

### Step 2: Run the Relevant Domain Checks

Read `references/domain-checklists.md` for the full checklist for each domain. The 8 domains are:

1. **Secrets Detection** — Hardcoded credentials, API keys, tokens, private keys in code or git history
2. **Dependency & Supply Chain** — Known CVEs, outdated packages, typosquatting, lockfile integrity
3. **Static Application Security (SAST)** — Injection, XSS, SSRF, path traversal, insecure crypto, unsafe deserialization
4. **Infrastructure as Code (IaC)** — Docker, Terraform, Kubernetes, cloud misconfigurations
5. **CI/CD Pipeline Security** — Workflow injection, overpermissioned tokens, untrusted input in scripts
6. **Authentication & Authorization** — Broken auth, missing authz, session management, privilege escalation
7. **API Security** — Input validation, rate limiting, CORS, mass assignment, error info leakage
8. **Data Protection & Privacy** — PII in logs, encryption at rest/transit, data classification, retention

### Step 3: Produce the Report

Structure findings using severity levels:

- 🔴 **CRITICAL** — Actively exploitable, data breach risk, needs immediate fix (secrets in code, RCE, SQLi)
- 🟠 **HIGH** — Exploitable with some effort, significant impact (auth bypass, SSRF, known CVE with exploit)
- 🟡 **MEDIUM** — Requires specific conditions to exploit, moderate impact (XSS, missing rate limiting, overpermissioned IAM)
- 🔵 **LOW** — Minor risk, defense-in-depth improvement (verbose error messages, missing security headers)
- ⚪ **INFO** — Best practice recommendation, no current risk (missing SECURITY.md, no SBOM)

For each finding, provide:

```
### [SEVERITY] Finding Title (CWE-XXX if applicable)

**Domain:** Which of the 8 domains
**Location:** file:line or pattern description
**Description:** What the issue is and why it matters
**Impact:** What an attacker could do
**Remediation:** Exact steps to fix, with code examples
**References:** Link to CWE, OWASP, or relevant documentation
```

### Step 4: Summary and Prioritization

End with:

1. **Executive Summary** — One paragraph: overall posture, most critical findings, biggest risk areas
2. **Findings by Severity** — Count of 🔴/🟠/🟡/🔵/⚪
3. **Priority Fix Order** — Numbered list, most urgent first, with estimated effort (quick fix / half-day / multi-day)
4. **Recommended Scan Cadence** — See the cadence table below, customized to their stack

## Recommended Scan Cadence

| Domain | When to Run | How | Why |
|--------|------------|-----|-----|
| Secrets Detection | **Every commit** (pre-commit hook + CI) | `gitleaks`, `trufflehog`, GitHub secret scanning | Secrets are the #1 cause of breaches; must catch before they hit history |
| Dependency/SCA | **Every PR** + **daily automated** | `npm audit`, `pip-audit`, `trivy fs`, Dependabot/Renovate | New CVEs are published daily; deps change with every PR |
| SAST | **Every PR** + **weekly full scan** | `semgrep`, `bandit`, `gosec`, CodeQL | Catches vulns at write-time; weekly catches drift |
| IaC Security | **Every infra PR** + **weekly** | `checkov`, `trivy config`, `tfsec` | Misconfigs are the #1 cloud breach vector |
| CI/CD Pipeline | **Every workflow change** + **monthly audit** | Manual review + `actionlint` | Low change velocity but high blast radius |
| Auth & Access | **Per auth feature** + **quarterly deep review** | Manual code review, this skill | Logic bugs that scanners miss |
| API Security | **Per endpoint change** + **quarterly** | Manual review, OWASP ZAP (DAST) | Business logic + config issues |
| Data Protection | **Quarterly** + **after data model changes** | Manual review, `detect-secrets`, grep patterns | Compliance-driven, changes infrequently |

### Quick-Start: Minimum Viable Security Pipeline

If the repo has *nothing* today, recommend this in order:

1. **Today** — Run `gitleaks detect` on the repo and fix any findings
2. **This week** — Add a pre-commit hook for secrets + enable Dependabot/Renovate
3. **This sprint** — Add `semgrep` or CodeQL to CI on PRs
4. **This month** — Add IaC scanning if applicable, do first full audit with this skill
5. **Ongoing** — Quarterly deep review using the full 8-domain audit

## Important Context

Security review is not about finding every theoretical issue — it's about **finding the things that
will actually get you breached**. Prioritize:

- Secrets in code (the easiest win for attackers)
- Known CVEs with public exploits (script-kiddie accessible)
- Auth/authz bypasses (business-critical)
- Injection vulnerabilities (high impact, often easy to exploit)

Don't overwhelm the user with 50 LOW findings when there are 3 CRITICALs. Lead with what matters.

When the user asks about security and you're unsure whether to use this skill or the `code-review`
skill: use `code-review` for reviewing a specific PR/diff/snippet. Use this skill when auditing
an entire repository or checking a broad security posture.
