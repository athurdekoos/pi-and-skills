# Domain Checklists — Full Reference

Read this file when performing a full or targeted audit. Each domain has a checklist of things to
inspect, commands to run, and patterns to grep for. Not every check applies to every repo — use
the recon from Step 1 to determine relevance.

## Table of Contents
1. [Secrets Detection](#1-secrets-detection)
2. [Dependency & Supply Chain](#2-dependency--supply-chain)
3. [Static Application Security (SAST)](#3-static-application-security-sast)
4. [Infrastructure as Code (IaC)](#4-infrastructure-as-code-iac)
5. [CI/CD Pipeline Security](#5-cicd-pipeline-security)
6. [Authentication & Authorization](#6-authentication--authorization)
7. [API Security](#7-api-security)
8. [Data Protection & Privacy](#8-data-protection--privacy)

---

## 1. Secrets Detection

The single highest-impact domain. A leaked API key or database password can be exploited in minutes
by bots that scan public repositories.

### What to Look For

**Hardcoded credentials in source code:**
```bash
# High-entropy strings that look like secrets
rg -in '(api[_-]?key|api[_-]?secret|access[_-]?key|secret[_-]?key|private[_-]?key|auth[_-]?token|bearer)\s*[:=]\s*["\x27][A-Za-z0-9+/=_-]{16,}' \
  --glob '!*.lock' --glob '!*node_modules*' --glob '!*vendor*'

# AWS keys (AKIA pattern)
rg -n 'AKIA[0-9A-Z]{16}' --glob '!*.lock'

# Private keys
rg -rn 'BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY' .

# Connection strings
rg -in '(mongodb(\+srv)?|postgres(ql)?|mysql|redis|amqp)://[^\s"]+:[^\s"]+@' .

# Common password variable patterns
rg -in '(password|passwd|pwd|secret)\s*[:=]\s*["\x27][^"\x27]{4,}["\x27]' \
  --glob '!*.lock' --glob '!*.md' --glob '!*test*' --glob '!*mock*' --glob '!*example*'

# JWT tokens (they start with eyJ)
rg -n 'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}' .

# GitHub tokens
rg -n '(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}' .

# Slack tokens
rg -n 'xox[baprs]-[0-9a-zA-Z-]{10,}' .

# Generic "token" or "key" assignments with real-looking values
rg -in 'token\s*[:=]\s*["\x27][A-Za-z0-9_.-]{20,}["\x27]' --glob '!*.lock' --glob '!*node_modules*'
```

**Files that shouldn't be committed:**
```bash
# Env files with secrets
find . -name ".env" -o -name ".env.local" -o -name ".env.production" \
  -o -name "*.pem" -o -name "*.key" -o -name "*.p12" -o -name "*.pfx" \
  -o -name "*.jks" -o -name "*.keystore" -o -name "credentials.json" \
  -o -name "service-account*.json" -o -name "*secret*" 2>/dev/null | \
  grep -v node_modules | grep -v vendor | grep -v '.git/'
```

**Check .gitignore coverage:**
```bash
# These should ALL be in .gitignore
cat .gitignore 2>/dev/null
# Verify: .env*, *.pem, *.key, *.p12, *.pfx, credentials.json
```

**Git history (if git is available):**
```bash
# Check if secrets were ever committed (even if removed)
git log --all --diff-filter=D -- "*.env" "*.pem" "*.key" "credentials.json" 2>/dev/null
git log --all -p --follow -S 'AKIA' -- . 2>/dev/null | head -50
```

### Recommended Tools
- `gitleaks detect --source .` — Fast, comprehensive, low false positives
- `trufflehog filesystem .` — Entropy-based detection, catches unusual formats
- GitHub secret scanning (enable in repo settings) — Automated, covers 200+ providers

### Remediation
- Rotate any exposed credential immediately — assume it's compromised
- Use environment variables or a secrets manager (AWS SSM, Vault, 1Password)
- Add a pre-commit hook: `gitleaks protect --staged`
- If a secret was in git history, it's NOT enough to delete the file — you must rotate the credential

---

## 2. Dependency & Supply Chain

Third-party code is the largest attack surface in most applications. A single vulnerable transitive
dependency can compromise your entire application.

### What to Look For

**Known CVEs in dependencies:**
```bash
# Node.js
npm audit 2>/dev/null || true
cat package-lock.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Lock version: {d.get(\"lockfileVersion\",\"unknown\")}')" 2>/dev/null

# Python
pip-audit 2>/dev/null || pip install pip-audit && pip-audit 2>/dev/null
# Check for pinned vs unpinned
rg -c '==' requirements.txt 2>/dev/null
rg -vc '==' requirements.txt 2>/dev/null

# Go
go list -m -json all 2>/dev/null | head -100
govulncheck ./... 2>/dev/null

# Rust
cargo audit 2>/dev/null

# Ruby
bundle audit check 2>/dev/null

# General (works on most ecosystems)
# trivy fs --security-checks vuln .
```

**Dependency hygiene checks:**
```bash
# Check for lockfile presence (critical for reproducible, safe builds)
ls package-lock.json yarn.lock pnpm-lock.yaml Pipfile.lock poetry.lock \
  go.sum Cargo.lock Gemfile.lock composer.lock 2>/dev/null

# Check for wildcard/latest version specifiers (dangerous)
rg '"[*]"' package.json 2>/dev/null
rg '"latest"' package.json 2>/dev/null
rg '>=\s' requirements.txt 2>/dev/null

# Check dependency count (large dep trees = larger attack surface)
cat package.json 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
deps=len(d.get('dependencies',{}))
dev=len(d.get('devDependencies',{}))
print(f'Dependencies: {deps}, DevDependencies: {dev}, Total: {deps+dev}')
" 2>/dev/null

# Check for deprecated or unmaintained packages
npm outdated 2>/dev/null | head -20
```

**Supply chain attack indicators:**
```bash
# Postinstall scripts (common attack vector)
rg '"postinstall"' package.json 2>/dev/null
rg '"preinstall"' package.json 2>/dev/null

# Check if dependencies have install scripts
npm ls --all 2>/dev/null | head -50

# Look for typosquatting risk (manually review unusual package names)
cat package.json 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
deps=list(d.get('dependencies',{}).keys()) + list(d.get('devDependencies',{}).keys())
for dep in sorted(deps):
    print(dep)
" 2>/dev/null
```

### Recommended Tools
- Dependabot or Renovate for automated PRs
- `trivy fs .` for multi-ecosystem vulnerability scanning
- npm/pip/cargo built-in audit commands
- Socket.dev for supply chain attack detection

### Remediation
- Pin dependencies to exact versions in lockfiles
- Enable automated dependency update PRs (Dependabot/Renovate)
- Review and update critical/high CVEs within 48 hours
- Audit `postinstall` scripts before adding new dependencies
- Prefer well-maintained packages with active security response

---

## 3. Static Application Security (SAST)

Code-level vulnerabilities that allow attackers to inject, redirect, or otherwise abuse your application.

### What to Look For

**Injection vulnerabilities:**
```bash
# SQL injection (string concatenation in queries)
rg -n 'query\s*\(\s*[`"'"'"'].*\$\{' --glob '*.ts' --glob '*.js' .  # template literal in SQL
rg -n '(execute|query|raw)\s*\(.*[+].*\)' --glob '*.py' --glob '*.rb' --glob '*.java' .
rg -n 'f"(SELECT|INSERT|UPDATE|DELETE)' --glob '*.py' .  # Python f-string SQL
rg -n '\.format\(.*\).*(SELECT|INSERT|UPDATE|DELETE)' --glob '*.py' .

# Command injection
rg -n '(exec|spawn|system|popen|subprocess\.call|os\.system|child_process)\s*\(' \
  --glob '!node_modules' --glob '!vendor' .
rg -n 'shell\s*[:=]\s*True' --glob '*.py' .  # subprocess with shell=True

# Path traversal
rg -n '(readFile|readFileSync|open|fopen)\s*\(.*req\.(params|query|body)' .
rg -n '\.\./\.\.' .  # literal traversal (may be in tests, verify context)

# Server-Side Request Forgery (SSRF)
rg -n '(fetch|axios|request|urllib|http\.get|https\.get)\s*\(.*req\.' .
rg -n '(fetch|requests\.get|urllib)\s*\(.*user' --glob '*.py' --glob '*.js' --glob '*.ts' .
```

**Cross-Site Scripting (XSS):**
```bash
# Dangerous HTML rendering
rg -n 'dangerouslySetInnerHTML' .  # React
rg -n 'v-html' .  # Vue
rg -n '\[innerHTML\]' .  # Angular
rg -n '\.html\s*\(' --glob '*.py' .  # Flask/Django mark_safe
rg -n 'mark_safe|SafeString|Markup\(' --glob '*.py' .
rg -n '\|safe' --glob '*.html' .  # Django/Jinja2 safe filter
```

**Insecure cryptography:**
```bash
# Weak hashing algorithms
rg -in '(md5|sha1)\s*\(' --glob '!*.lock' --glob '!*node_modules*' .
rg -in 'createHash\s*\(\s*["\x27](md5|sha1)' .

# Weak encryption
rg -in '(DES|RC4|ECB)' --glob '*.py' --glob '*.java' --glob '*.go' --glob '*.ts' --glob '*.js' .

# Hardcoded IVs or salts
rg -in '(iv|salt|nonce)\s*[:=]\s*["\x27]' --glob '!*test*' --glob '!*mock*' .

# Math.random() for security-sensitive operations
rg -n 'Math\.random\(\)' --glob '*.js' --glob '*.ts' .
```

**Unsafe deserialization:**
```bash
rg -n '(pickle\.load|yaml\.load\s*\([^)]*$|yaml\.load\s*\([^)]*\)\s*$|Marshal\.load|unserialize|readObject)' .
rg -n 'yaml\.load' --glob '*.py' .  # Should be yaml.safe_load
rg -n 'eval\s*\(' --glob '*.py' --glob '*.js' --glob '*.rb' .  # eval() with any external input
rg -n 'JSON\.parse\(.*req\.' --glob '*.js' --glob '*.ts' .
```

**Error handling / information disclosure:**
```bash
# Stack traces in production
rg -in 'DEBUG\s*[:=]\s*True' --glob '*.py' .
rg -in 'stackTrace|stack_trace|printStackTrace' .
rg -in 'app\.use\(.*errorHandler.*{.*stack' --glob '*.js' --glob '*.ts' .
```

### Recommended Tools
- `semgrep --config auto .` — Rule-based, low false positive rate, multi-language
- `bandit` (Python), `gosec` (Go), `brakeman` (Ruby), `SpotBugs` (Java)
- GitHub CodeQL — Deep semantic analysis, free for public repos

### Remediation
- Use parameterized queries / prepared statements for all SQL
- Sanitize and validate all user input at the boundary
- Use safe APIs: `yaml.safe_load`, `subprocess.run(shell=False)`, etc.
- Enable Content-Security-Policy headers to mitigate XSS
- Use `crypto.randomBytes()` or `secrets` module, never `Math.random()` for security

---

## 4. Infrastructure as Code (IaC)

Misconfigurations are the #1 cause of cloud breaches (not sophisticated attacks). A single
`"0.0.0.0/0"` in a security group or a `privileged: true` container can undo months of work.

### What to Look For

**Docker:**
```bash
# Running as root (no USER directive)
for f in $(find . -name "Dockerfile*" 2>/dev/null); do
  echo "=== $f ==="
  grep -n 'USER' "$f" || echo "  ⚠️  No USER directive — runs as root"
  grep -n 'FROM.*:latest' "$f" && echo "  ⚠️  Using :latest tag"
  grep -n 'ADD ' "$f" && echo "  ⚠️  ADD used instead of COPY (ADD can fetch URLs)"
  grep -in 'SECRET\|PASSWORD\|API_KEY\|TOKEN' "$f" && echo "  ⚠️  Possible secret in Dockerfile"
done

# Docker Compose
for f in $(find . -name "docker-compose*" 2>/dev/null); do
  echo "=== $f ==="
  grep -n 'privileged: true' "$f" && echo "  🔴 Privileged container!"
  grep -n 'network_mode: host' "$f" && echo "  🟠 Host network mode"
  grep -n '\.env' "$f" && echo "  Check: env_file reference"
done
```

**Terraform:**
```bash
# Overly permissive security groups / firewall rules
rg -n '0\.0\.0\.0/0' --glob '*.tf' .
rg -n '::/0' --glob '*.tf' .
rg -n 'cidr_blocks\s*=\s*\["0' --glob '*.tf' .

# Public S3 buckets
rg -n 'acl\s*=\s*"public' --glob '*.tf' .
rg -n 'block_public_acls\s*=\s*false' --glob '*.tf' .

# Unencrypted storage
rg -n 'encrypted\s*=\s*false' --glob '*.tf' .
rg -n 'storage_encrypted\s*=\s*false' --glob '*.tf' .
rg -A5 'aws_s3_bucket\b' --glob '*.tf' . | grep -v 'server_side_encryption'

# Overpermissioned IAM
rg -n '"Effect"\s*:\s*"Allow".*"Action"\s*:\s*"\*"' --glob '*.tf' --glob '*.json' .
rg -n 'AdministratorAccess' --glob '*.tf' .
rg -n '"Resource"\s*:\s*"\*"' --glob '*.tf' --glob '*.json' .

# Hardcoded credentials in tfvars
rg -in '(password|secret|key|token)\s*=' --glob '*.tfvars' .

# Check state file exposure
find . -name "*.tfstate" -not -path '*/.git/*' 2>/dev/null
```

**Kubernetes:**
```bash
# Privileged containers
rg -n 'privileged:\s*true' --glob '*.yaml' --glob '*.yml' .

# Running as root
rg -A5 'securityContext' --glob '*.yaml' . | rg 'runAsNonRoot:\s*false'

# Containers without resource limits (DoS risk)
for f in $(find . -name "*.yaml" -o -name "*.yml" 2>/dev/null | xargs grep -l 'kind: Deployment' 2>/dev/null); do
  grep -q 'resources:' "$f" || echo "⚠️  $f: No resource limits"
done

# hostPath mounts (container escape risk)
rg -n 'hostPath:' --glob '*.yaml' --glob '*.yml' .

# hostNetwork
rg -n 'hostNetwork:\s*true' --glob '*.yaml' --glob '*.yml' .
```

### Recommended Tools
- `checkov -d .` — Multi-framework (Terraform, K8s, Docker, CloudFormation)
- `trivy config .` — IaC scanning built into Trivy
- `tfsec .` — Terraform-specific, excellent rules

### Remediation
- Pin base images to digests, not tags
- Add `USER nonroot` to all Dockerfiles
- Never open `0.0.0.0/0` except for public load balancers
- Use least-privilege IAM — never `Action: *` or `Resource: *`
- Always set resource limits on Kubernetes pods
- Never store .tfstate locally — use remote backends with encryption

---

## 5. CI/CD Pipeline Security

CI/CD pipelines run with elevated privileges and process untrusted input (PRs from forks,
branch names, commit messages). A compromised pipeline can exfiltrate secrets, modify builds,
or push malicious code.

### What to Look For

**GitHub Actions:**
```bash
# Workflow injection via untrusted input
for f in $(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null); do
  echo "=== $f ==="
  # Dangerous: using PR title/body/branch in run commands
  rg -n '\$\{\{\s*github\.event\.(pull_request\.(title|body|head\.ref)|issue\.title|comment\.body)' "$f"
  # Overpermissioned
  rg -n 'permissions:\s*write-all' "$f"
  rg -n 'permissions:.*contents:\s*write' "$f"
  # Using mutable action versions (should pin to SHA)
  rg -n 'uses:\s*[^@]+@(main|master|v[0-9]+\s*$)' "$f"
  # Pull request target trigger (runs with write access on PR from fork)
  rg -n 'pull_request_target' "$f" && echo "  🟠 pull_request_target — verify checkout safety"
  # Secrets in outputs or logs
  rg -n 'echo.*\$\{\{.*secrets\.' "$f"
done

# Self-hosted runners (higher risk — shared environment)
rg -rn 'runs-on:.*self-hosted' .github/ 2>/dev/null
```

**General CI/CD:**
```bash
# Secrets in CI config files
rg -in '(password|token|secret|key)\s*[:=]' \
  .github/workflows/*.yml .gitlab-ci.yml .circleci/config.yml Jenkinsfile 2>/dev/null

# Artifact upload without exclusion (might include .env, secrets)
rg -n 'upload-artifact' .github/workflows/ 2>/dev/null
rg -n 'artifacts:' .gitlab-ci.yml 2>/dev/null
```

### Key Risks
- **Workflow injection** (CWE-78): When `${{ github.event.pull_request.title }}` is used in a
  `run:` block, an attacker can craft a PR title with shell commands
- **Mutable action references**: `uses: actions/checkout@main` means a compromised upstream
  repo immediately compromises your pipeline. Pin to SHA: `uses: actions/checkout@8ade...`
- **pull_request_target**: Runs in the context of the base branch with write access but
  processes code from the PR — if it checks out PR code, it's RCE
- **Self-hosted runners**: Share the host OS, so one malicious job can access files, env vars,
  or credentials from other jobs

### Recommended Tools
- `actionlint` — Linter for GitHub Actions
- StepSecurity `harden-runner` — Runtime protection for Actions
- Pin actions to SHA with `pin-github-action` tool

### Remediation
- Never use `${{ }}` expressions in `run:` blocks — pass as env vars
- Pin all action versions to commit SHAs
- Set `permissions:` to minimum needed (default should be `read-all`)
- Use `pull_request` not `pull_request_target` unless you specifically need write access
- Use ephemeral self-hosted runners or prefer GitHub-hosted

---

## 6. Authentication & Authorization

Logic bugs in auth flows are the most dangerous class of vulnerabilities because they're invisible
to scanners. These require manual code review — understand the auth flow, trace the code paths,
and verify every endpoint checks the right thing.

### What to Look For

**Authentication weaknesses:**
```bash
# JWT configuration
rg -in 'algorithm.*none' --glob '!node_modules' --glob '!vendor' .  # alg:none attack
rg -in 'verify\s*[:=]\s*false' --glob '*.js' --glob '*.ts' .  # JWT verification disabled
rg -in 'expiresIn|exp\s*[:=]' --glob '*.js' --glob '*.ts' --glob '*.py' .  # Token expiry
rg -n 'ignoreExpiration' .  # Expired tokens accepted

# Password handling
rg -in 'bcrypt|argon2|scrypt|pbkdf2' .  # Good: secure hashing
rg -in 'md5|sha1|sha256' --glob '!*.lock' . | grep -i 'password'  # Bad: fast hash for passwords

# Session management
rg -in 'httponly|secure|samesite' --glob '*.js' --glob '*.ts' --glob '*.py' .
rg -in 'session.*secret' --glob '*.js' --glob '*.ts' .
```

**Authorization (the harder one — requires understanding the app):**
```bash
# Middleware/decorator patterns — look for routes WITHOUT auth
rg -n '@login_required|@authenticated|@auth_required|@require_auth' --glob '*.py' .
rg -n 'authenticate|isAuthenticated|requireAuth|authMiddleware' \
  --glob '*.js' --glob '*.ts' .

# Direct object reference — user ID from URL used to fetch data without ownership check
rg -n 'params\.(id|userId|user_id)' --glob '*.js' --glob '*.ts' .
rg -n 'request\.(args|form)\[.*(id|user)' --glob '*.py' .

# Role checks
rg -in 'role\s*[=!]=|isAdmin|is_admin|hasRole|has_permission|can\(' .
```

### Key Questions to Answer
1. Is every API endpoint/route protected with authentication?
2. Is there authorization on top of authentication? (knowing WHO you are ≠ having permission)
3. Are there IDOR (Insecure Direct Object Reference) vulnerabilities? (Can user A access user B's data?)
4. Is JWT `alg:none` rejected? Is token expiry enforced?
5. Are passwords hashed with bcrypt/argon2 (not MD5/SHA)?
6. Are sessions properly invalidated on logout?
7. Is there rate limiting on login/signup?

### Remediation
- Apply auth middleware at the router level, not per-endpoint (defense in depth)
- Always verify resource ownership, not just authentication
- Use established auth libraries (passport.js, Django auth, Spring Security)
- Enforce token expiry and rotation
- Implement account lockout after N failed attempts

---

## 7. API Security

APIs are the primary attack surface for most modern applications. Focus on input validation,
access control, and information leakage.

### What to Look For

**Input validation:**
```bash
# Look for validation libraries
rg -in '(joi|zod|yup|ajv|class-validator|marshmallow|pydantic|cerberus)' \
  package.json requirements.txt go.mod 2>/dev/null

# Routes/endpoints without validation
rg -n 'req\.body\.' --glob '*.js' --glob '*.ts' . | head -20
rg -n 'request\.(json|form|data)' --glob '*.py' . | head -20

# Mass assignment / over-posting
rg -n 'Object\.assign|spread.*req\.body|\{\.\.\.req\.body\}' --glob '*.js' --glob '*.ts' .
rg -n '\*\*request\.(json|data|form)' --glob '*.py' .  # Django/Flask **kwargs from request
```

**Rate limiting:**
```bash
rg -in 'rate.?limit|throttle|express-rate-limit|slowapi|bucket' . --glob '!node_modules' --glob '!vendor'
```

**CORS configuration:**
```bash
rg -in 'cors|access-control-allow-origin' --glob '*.js' --glob '*.ts' --glob '*.py' .
rg -in 'origin.*\*|allow_all_origins|AllowAllOrigins' .
```

**Error handling — information leakage:**
```bash
# Returning internal errors to users
rg -n 'res\.(status|json|send).*err\.(message|stack)' --glob '*.js' --glob '*.ts' .
rg -n 'return.*traceback|return.*str(e)' --glob '*.py' .
```

**File upload security:**
```bash
rg -n 'upload|multer|formidable|busboy|FileField|FileUpload' \
  --glob '*.js' --glob '*.ts' --glob '*.py' .
# Check: file type validation? size limits? storage location?
```

### Remediation
- Validate ALL input at API boundaries using a schema library
- Whitelist accepted fields — never spread request body directly into models
- Set up rate limiting on all public endpoints (especially auth)
- Configure CORS to specific origins, never `*` in production
- Return generic error messages to users, log details server-side
- Validate file uploads: type, size, and sanitize filenames

---

## 8. Data Protection & Privacy

Protecting user data is both a security and compliance requirement. PII in logs, unencrypted
databases, and missing data classification are common gaps.

### What to Look For

**PII in logs:**
```bash
# Logging sensitive data
rg -in 'log.*(password|ssn|social.security|credit.card|card.number|cvv|secret|token)' .
rg -in 'console\.(log|info|debug|warn).*password' --glob '*.js' --glob '*.ts' .
rg -in 'logger?\.(info|debug|warning|error).*password' --glob '*.py' .

# Logging full request/response bodies (may contain PII)
rg -in 'log.*req\.body|log.*request\.data|log.*response\.data' .
```

**Encryption:**
```bash
# Database connection strings — check for SSL/TLS
rg -in '(mongodb|postgres|mysql|redis)://' . | grep -iv 'ssl\|tls'

# Encryption at rest configuration
rg -in 'encrypt' --glob '*.tf' --glob '*.yaml' . | head -20
```

**Data retention and deletion:**
```bash
# Soft delete vs hard delete
rg -in 'soft.?delete|deleted_at|is_deleted|paranoid' .

# Data retention policies
rg -in 'retention|expir|ttl|purge' --glob '*.py' --glob '*.js' --glob '*.ts' --glob '*.yaml' .
```

**Privacy controls:**
```bash
# Cookie consent / privacy banners
rg -in 'cookie.?consent|gdpr|ccpa|privacy.?policy' --glob '*.js' --glob '*.ts' --glob '*.html' .

# Data export / deletion endpoints (GDPR right to erasure)
rg -in 'data.?export|data.?deletion|right.?to.?erasure|forget.?me|delete.?account' .

# Analytics and tracking
rg -in 'google.?analytics|gtag|mixpanel|segment|amplitude|hotjar' --glob '*.html' --glob '*.js' .
```

### Remediation
- Never log PII — use structured logging with field redaction
- Encrypt data at rest and in transit (TLS 1.2+ for all connections)
- Implement data classification (what's PII, what's sensitive, what's public)
- Build data deletion/export endpoints if handling EU user data (GDPR)
- Set database connection strings to require SSL
- Use field-level encryption for highly sensitive data (SSN, payment info)
- Review analytics/tracking for privacy compliance
