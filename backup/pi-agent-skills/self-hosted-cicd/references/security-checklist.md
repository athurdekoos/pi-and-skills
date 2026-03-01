# Security Checklist — CI/CD Pipeline Threat Model

## The 13 Concerns

### 1. Dependency Vulnerabilities (Known CVEs)
**Risk:** Your npm packages ship with publicly known exploits.
**Mitigation:** `npm audit --audit-level=high` + Trivy filesystem scan.
**Verify:** `cd server && npm audit --omit=dev && trivy fs server/`
**Stage:** `audit` job

### 2. Secret Leaks in Code/History
**Risk:** API keys, tokens, passwords committed to git — even if "deleted".
**Mitigation:** Gitleaks with full-depth checkout scans entire history.
**Verify:** `gitleaks detect --source . --verbose`
**Stage:** `secrets-scan` job

### 3. Static Analysis / Code Bugs
**Risk:** Injection flaws, XSS, broken auth patterns that tests miss.
**Mitigation:** CodeQL with `security-extended` query suite (broader than default).
**Verify:** Runs as GitHub SARIF upload — results in Security tab.
**Stage:** `sast` job

### 4. Insecure Code Patterns
**Risk:** `eval()`, `new Function()`, prototype pollution, unsanitized DOM writes.
**Mitigation:** ESLint + `eslint-plugin-security` + `eslint-plugin-no-unsanitized`.
**Verify:** `cd server && npm run lint`
**Stage:** `lint` job

### 5. Supply Chain Attacks
**Risk:** Typosquatted packages, lockfile manipulation, registry hijacking.
**Mitigation:** `lockfile-lint` validates all deps come from npm over HTTPS. `npm ci` uses frozen lockfile.
**Verify:** `cd server && npm run lockfile:lint`
**Stage:** `audit` job

### 6. Container Image Vulnerabilities
**Risk:** Base images with unpatched CVEs, outdated system packages.
**Mitigation:** Trivy image scan on built image.
**Verify:** `docker build -t test . && trivy image test`
**Stage:** `container-scan` job (conditional — only runs if Dockerfile exists)

### 7. Dockerfile Misconfiguration
**Risk:** Running as root, using `latest` tag, missing health checks.
**Mitigation:** Hadolint static analysis.
**Verify:** `hadolint Dockerfile`
**Stage:** `container-scan` job

### 8. CI Pipeline as Attack Surface
**Risk:** Compromised GitHub Actions, malicious PR workflows, tag hijacking.
**Mitigation:**
- All actions pinned to full SHA (not `@v4` tags)
- Minimal `permissions:` block — `contents: read` default
- No `pull_request_target` trigger (prevents fork secret exfiltration)
- Dependabot updates action versions weekly
**Verify:** `grep -r 'uses:' .github/workflows/ | grep -v '@[a-f0-9]\{40\}'` (should be empty)

### 9. Hardcoded Credentials in Environment
**Risk:** `.env` files committed, tokens in config files.
**Mitigation:** Gitleaks custom rules + explicit `.env` file check in pipeline.
**Verify:** `git ls-files --cached | grep -E '\.env$' | grep -v '.env.example'` (should be empty)

### 10. Runner Isolation
**Risk:** Compromised job leaves malware/creds for next job on same machine.
**Mitigation:**
- Docker-based runner with `EPHEMERAL=1` (de-registers after each job)
- `no-new-privileges` security option
- tmpfs for /tmp (wiped on container stop)
- Memory and CPU limits
**Verify:** Check `docker-compose.yml` for security settings.

### 11. Branch Protection Bypass
**Risk:** Direct push to main, force push that rewrites history.
**Mitigation:** GitHub branch protection rules set via API script:
- Required status checks (CI Gate must pass)
- Required PR reviews
- No force push
- Linear history (no merge commits that hide changes)
**Verify:** `bash .github/scripts/setup-branch-protection.sh`

### 12. License Compliance
**Risk:** GPL/AGPL dependency contaminates your project's license.
**Mitigation:** `license-checker --failOn 'GPL-3.0;AGPL-3.0'`
**Verify:** `cd server && npm run license:check`
**Stage:** `audit` job

### 13. Overall Security Posture
**Risk:** Unknown unknowns — are we following OSS security best practices?
**Mitigation:** OSSF Scorecard evaluates 20+ security dimensions.
**Verify:** Runs on main branch + weekly schedule, uploads SARIF.
**Stage:** `scorecard` job

---

## Quick Audit Sequence

Run these locally to check all 13 concerns:

```bash
# 1-5: Lint + Audit + Supply Chain
cd server && npm run lint && npm audit --audit-level=high --omit=dev && npm run lockfile:lint && npm run license:check

# 2+9: Secrets
gitleaks detect --source . --verbose
git ls-files --cached | grep -E '\.env$' | grep -v '.env.example'

# 8: Action pinning
grep -r 'uses:' .github/workflows/ | grep -v '@[a-f0-9]\{40\}'

# 6-7: Container (if applicable)
hadolint Dockerfile
docker build -t scan-target . && trivy image scan-target
```
