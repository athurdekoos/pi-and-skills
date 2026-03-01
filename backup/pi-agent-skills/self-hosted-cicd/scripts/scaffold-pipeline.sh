#!/usr/bin/env bash
# scaffold-pipeline.sh — Generate a complete CI/CD pipeline for any Node.js project
# Usage: scaffold-pipeline.sh /path/to/project
set -euo pipefail

TARGET="${1:?Usage: scaffold-pipeline.sh /path/to/project}"
TARGET="$(cd "$TARGET" && pwd)"

echo "╔══════════════════════════════════════════════╗"
echo "║  Self-Hosted CI/CD Pipeline Scaffolder       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Detect project layout ──────────────────────────────────
if [ -f "$TARGET/package.json" ]; then
  SERVER_DIR="."
  CACHE_PATH="package-lock.json"
elif [ -f "$TARGET/server/package.json" ]; then
  SERVER_DIR="server"
  CACHE_PATH="server/package-lock.json"
else
  echo "❌ No package.json found in $TARGET or $TARGET/server"
  exit 1
fi

echo "   Project root:  $TARGET"
echo "   Node.js dir:   $SERVER_DIR/"
echo ""

# ── Create directories ─────────────────────────────────────
mkdir -p "$TARGET/.github/workflows"
mkdir -p "$TARGET/.github/runner"
mkdir -p "$TARGET/.github/scripts"

# ── 1. GitHub Actions CI Workflow ──────────────────────────
echo "==> Generating .github/workflows/ci.yml"
cat > "$TARGET/.github/workflows/ci.yml" << 'WORKFLOW_EOF'
name: CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: "🔍 Lint & Security Patterns"
    runs-on: [self-hosted, linux, x64]
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4.4.0
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: __CACHE_PATH__
      - run: cd __SERVER_DIR__ && npm ci
      - run: cd __SERVER_DIR__ && npm run lint
      - run: cd __SERVER_DIR__ && npm run lockfile:lint

  audit:
    name: "📦 Dependency Audit"
    runs-on: [self-hosted, linux, x64]
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4.4.0
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: __CACHE_PATH__
      - run: cd __SERVER_DIR__ && npm ci
      - name: npm audit
        run: cd __SERVER_DIR__ && npm audit --audit-level=high --omit=dev
      - name: Trivy FS scan
        run: |
          trivy fs __SERVER_DIR__/ \
            --severity HIGH,CRITICAL \
            --exit-code 1 \
            --format table \
            --ignore-unfixed
      - name: License check
        run: cd __SERVER_DIR__ && npm run license:check

  secrets-scan:
    name: "🔐 Secrets Scan"
    runs-on: [self-hosted, linux, x64]
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          fetch-depth: 0
      - name: Gitleaks scan
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            gitleaks detect --source . --log-opts "${{ github.event.pull_request.base.sha }}..${{ github.sha }}" --verbose
          else
            gitleaks detect --source . --verbose
          fi
      - name: Check for .env files
        run: |
          if git ls-files --cached | grep -E '\.env$' | grep -v '.env.example'; then
            echo "❌ .env file found in tracked files!"
            exit 1
          fi

  sast:
    name: "🛡️ SAST (CodeQL)"
    runs-on: [self-hosted, linux, x64]
    timeout-minutes: 15
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: github/codeql-action/init@v3
        with:
          languages: javascript
          queries: security-extended
      - uses: github/codeql-action/analyze@v3
        with:
          category: "/language:javascript"

  test:
    name: "🧪 Tests"
    runs-on: [self-hosted, linux, x64]
    timeout-minutes: 15
    needs: [lint]
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4.4.0
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: __CACHE_PATH__
      - run: cd __SERVER_DIR__ && npm ci
      - name: Run tests
        run: cd __SERVER_DIR__ && npm test
        env:
          NODE_ENV: test

  container-scan:
    name: "🐳 Container Security"
    runs-on: [self-hosted, linux, x64]
    timeout-minutes: 10
    if: hashFiles('**/Dockerfile') != ''
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - name: Hadolint
        run: |
          find . -name 'Dockerfile*' -not -path './node_modules/*' | while read f; do
            echo "==> Linting $f"
            hadolint "$f"
          done
      - name: Build image
        run: docker build -t ci-scan-target __SERVER_DIR__/
      - name: Trivy image scan
        run: |
          trivy image ci-scan-target \
            --severity HIGH,CRITICAL \
            --exit-code 1 \
            --format table \
            --ignore-unfixed
      - name: Cleanup
        if: always()
        run: docker rmi ci-scan-target 2>/dev/null || true

  scorecard:
    name: "📊 OSSF Scorecard"
    runs-on: [self-hosted, linux, x64]
    timeout-minutes: 10
    if: github.event_name == 'schedule' || github.ref == 'refs/heads/main'
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: ossf/scorecard-action@62b2cac7ed8198b15735ed49ab1e5cf35480ba46 # v2.4.0
        with:
          results_file: scorecard-results.sarif
          results_format: sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: scorecard-results.sarif

  ci-gate:
    name: "✅ CI Gate"
    runs-on: [self-hosted, linux, x64]
    timeout-minutes: 2
    needs: [lint, audit, secrets-scan, sast, test]
    if: always()
    steps:
      - name: Check all jobs passed
        run: |
          echo "lint:         ${{ needs.lint.result }}"
          echo "audit:        ${{ needs.audit.result }}"
          echo "secrets-scan: ${{ needs.secrets-scan.result }}"
          echo "sast:         ${{ needs.sast.result }}"
          echo "test:         ${{ needs.test.result }}"
          if [[ "${{ needs.lint.result }}" != "success" ]] || \
             [[ "${{ needs.audit.result }}" != "success" ]] || \
             [[ "${{ needs.secrets-scan.result }}" != "success" ]] || \
             [[ "${{ needs.sast.result }}" != "success" ]] || \
             [[ "${{ needs.test.result }}" != "success" ]]; then
            echo "❌ One or more required jobs failed."
            exit 1
          fi
          echo "✅ All gates passed."
WORKFLOW_EOF

# Patch paths for detected project layout
if [ "$SERVER_DIR" = "." ]; then
  sed -i 's|cd __SERVER_DIR__ && ||g' "$TARGET/.github/workflows/ci.yml"
  sed -i 's|__SERVER_DIR__/||g' "$TARGET/.github/workflows/ci.yml"
  sed -i 's|__SERVER_DIR__|.|g' "$TARGET/.github/workflows/ci.yml"
  sed -i "s|__CACHE_PATH__|package-lock.json|g" "$TARGET/.github/workflows/ci.yml"
else
  sed -i "s|__SERVER_DIR__|$SERVER_DIR|g" "$TARGET/.github/workflows/ci.yml"
  sed -i "s|__CACHE_PATH__|$CACHE_PATH|g" "$TARGET/.github/workflows/ci.yml"
fi

# ── 2. Self-Hosted Runner ─────────────────────────────────
echo "==> Generating .github/runner/ files"

cat > "$TARGET/.github/runner/Dockerfile" << 'DOCKERFILE_EOF'
FROM ghcr.io/actions/actions-runner:latest

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates build-essential python3 git jq \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Gitleaks
RUN curl -sSfL https://github.com/gitleaks/gitleaks/releases/download/v8.21.2/gitleaks_8.21.2_linux_x64.tar.gz \
    | tar xz -C /usr/local/bin gitleaks

# Trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.58.1

# Hadolint
RUN curl -sSL https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64 \
    -o /usr/local/bin/hadolint && chmod +x /usr/local/bin/hadolint

USER runner
DOCKERFILE_EOF

cat > "$TARGET/.github/runner/docker-compose.yml" << 'COMPOSE_EOF'
version: "3.8"
services:
  github-runner:
    build: .
    restart: unless-stopped
    env_file: .env
    environment:
      - RUNNER_NAME=${RUNNER_NAME:-project-runner}
      - RUNNER_WORKDIR=/tmp/runner-work
      - RUNNER_LABELS=self-hosted,linux,x64,security
      - EPHEMERAL=1
    volumes:
      - runner-work:/tmp/runner-work
    security_opt:
      - no-new-privileges:true
    tmpfs:
      - /tmp:exec
    mem_limit: 4g
    cpus: 2

volumes:
  runner-work:
COMPOSE_EOF

cat > "$TARGET/.github/runner/.env.example" << 'ENVEOF'
GITHUB_REPOSITORY=owner/repo
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RUNNER_NAME=my-runner
ENVEOF

cat > "$TARGET/.github/runner/setup-runner.sh" << 'SETUP_EOF'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "❌ docker compose required"; exit 1; }
[ -f .env ] || { echo "❌ Copy .env.example to .env and configure"; exit 1; }

echo "==> Building runner image..."
docker compose build

echo "==> Starting runner (ephemeral mode)..."
docker compose up -d

echo "✅ Runner started. Check: docker compose logs -f"
SETUP_EOF

cat > "$TARGET/.github/runner/teardown-runner.sh" << 'TEARDOWN_EOF'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
echo "==> Stopping runner..."
docker compose down --remove-orphans
echo "✅ Runner stopped."
TEARDOWN_EOF

chmod +x "$TARGET/.github/runner/setup-runner.sh" "$TARGET/.github/runner/teardown-runner.sh"

# ── 3. Gitleaks Config ────────────────────────────────────
echo "==> Generating .gitleaks.toml"
cat > "$TARGET/.gitleaks.toml" << 'GITLEAKS_EOF'
title = "Project gitleaks config"

[allowlist]
  description = "Known safe patterns"
  paths = [
    '''node_modules/''',
    '''\.env\.example$''',
    '''package-lock\.json$''',
    '''certs/'''
  ]

[[rules]]
  id = "telegram-bot-token"
  description = "Telegram Bot Token"
  regex = '''[0-9]{8,10}:[A-Za-z0-9_-]{35}'''
  tags = ["telegram", "bot"]

[[rules]]
  id = "hardcoded-password"
  description = "Hardcoded password in source"
  regex = '''(?i)(password|passwd|pwd)\s*[:=]\s*['"][^'"]{8,}'''
  tags = ["password"]
GITLEAKS_EOF

# ── 4. Dependabot ─────────────────────────────────────────
echo "==> Generating .github/dependabot.yml"
cat > "$TARGET/.github/dependabot.yml" << DEPBOT_EOF
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/$SERVER_DIR"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    labels: ["dependencies", "security"]
    groups:
      production:
        dependency-type: "production"
      dev:
        dependency-type: "development"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels: ["ci", "dependencies"]
DEPBOT_EOF

# Fix dependabot dir for root projects
if [ "$SERVER_DIR" = "." ]; then
  sed -i 's|directory: "/\."|directory: "/"|' "$TARGET/.github/dependabot.yml"
fi

# ── 5. SECURITY.md ────────────────────────────────────────
echo "==> Generating SECURITY.md"
cat > "$TARGET/SECURITY.md" << 'SECEOF'
# Security Policy

## Reporting a Vulnerability

Please report security vulnerabilities privately via GitHub's
[Security Advisories](../../security/advisories/new).

**Do NOT open a public issue for security vulnerabilities.**

## Security Measures

This project uses automated security scanning:
- Dependency scanning (Dependabot + npm audit + Trivy)
- Secret detection (Gitleaks)
- Static analysis (CodeQL + ESLint security plugins)
- Branch protection with required reviews
- Pinned GitHub Action versions (SHA-based)
SECEOF

# ── 6. Branch Protection Script ───────────────────────────
echo "==> Generating .github/scripts/setup-branch-protection.sh"
cat > "$TARGET/.github/scripts/setup-branch-protection.sh" << 'BPEOF'
#!/usr/bin/env bash
set -euo pipefail
OWNER="${GITHUB_OWNER:?Set GITHUB_OWNER}"
REPO="${GITHUB_REPO:?Set GITHUB_REPO}"
BRANCH="${1:-main}"
TOKEN="${GITHUB_TOKEN:?Set GITHUB_TOKEN}"

curl -sS -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/branches/$BRANCH/protection" \
  -d '{
    "required_status_checks": {"strict": true, "contexts": ["✅ CI Gate"]},
    "enforce_admins": true,
    "required_pull_request_reviews": {"required_approving_review_count": 1, "dismiss_stale_reviews": true},
    "restrictions": null,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "required_linear_history": true
  }'
echo "✅ Branch protection configured for $BRANCH"
BPEOF
chmod +x "$TARGET/.github/scripts/setup-branch-protection.sh"

# ── 7. ESLint Config ──────────────────────────────────────
echo "==> Generating ESLint flat config (eslint.config.js)"
ESLINT_DIR="$TARGET/$SERVER_DIR"
if [ "$SERVER_DIR" = "." ]; then
  ESLINT_DIR="$TARGET"
fi

cat > "$ESLINT_DIR/eslint.config.js" << 'ESLINTEOF'
import security from "eslint-plugin-security";
import noUnsanitized from "eslint-plugin-no-unsanitized";

export default [
  {
    ignores: ["node_modules/", "data/", "certs/"],
  },
  {
    files: ["src/**/*.js", "test/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        console: "readonly",
        process: "readonly",
        Buffer: "readonly",
        setTimeout: "readonly",
        setInterval: "readonly",
        clearTimeout: "readonly",
        clearInterval: "readonly",
        URL: "readonly",
      },
    },
    plugins: {
      security,
      "no-unsanitized": noUnsanitized,
    },
    rules: {
      "no-eval": "error",
      "no-implied-eval": "error",
      "no-new-func": "error",
      "security/detect-object-injection": "off",
      "security/detect-non-literal-fs-filename": "off",
      "security/detect-non-literal-require": "warn",
      "security/detect-possible-timing-attacks": "warn",
      "security/detect-child-process": "warn",
      "no-unsanitized/method": "error",
      "no-unsanitized/property": "error",
    },
  },
];
ESLINTEOF

# ── 8. Install Dev Dependencies ───────────────────────────
echo ""
echo "==> Installing security dev dependencies in $SERVER_DIR/"
cd "$ESLINT_DIR"

DEPS_NEEDED=""
for pkg in eslint eslint-plugin-security eslint-plugin-no-unsanitized lockfile-lint license-checker; do
  if ! node -e "require('$pkg')" 2>/dev/null; then
    DEPS_NEEDED="$DEPS_NEEDED $pkg"
  fi
done

if [ -n "$DEPS_NEEDED" ]; then
  echo "   Installing:$DEPS_NEEDED"
  npm install --save-dev $DEPS_NEEDED
else
  echo "   All security deps already installed."
fi

# Add scripts to package.json if missing
if ! grep -q '"lint"' package.json; then
  echo "   Adding lint/lockfile/license scripts to package.json..."
  node -e "
    const pkg = JSON.parse(require('fs').readFileSync('package.json', 'utf8'));
    pkg.scripts = pkg.scripts || {};
    if (!pkg.scripts.lint) pkg.scripts.lint = 'eslint src/ test/ --max-warnings 0';
    if (!pkg.scripts['lint:fix']) pkg.scripts['lint:fix'] = 'eslint src/ test/ --fix';
    if (!pkg.scripts['lockfile:lint']) pkg.scripts['lockfile:lint'] = 'lockfile-lint --type npm --path package-lock.json --allowed-hosts npm --validate-https';
    if (!pkg.scripts['license:check']) pkg.scripts['license:check'] = \"license-checker --failOn 'GPL-3.0;AGPL-3.0' --summary\";
    require('fs').writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');
  "
fi

# ── Done ──────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅ CI/CD Pipeline Scaffolded!                   ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║                                                  ║"
echo "║  Files created:                                  ║"
echo "║  • .github/workflows/ci.yml                      ║"
echo "║  • .github/runner/ (Docker self-hosted runner)    ║"
echo "║  • .github/dependabot.yml                        ║"
echo "║  • .github/scripts/setup-branch-protection.sh     ║"
echo "║  • .gitleaks.toml                                 ║"
echo "║  • .eslintrc.json                                 ║"
echo "║  • SECURITY.md                                    ║"
echo "║                                                  ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Next steps:                                      ║"
echo "║  1. Review the generated files                    ║"
echo "║  2. Run: npm run lint (fix any issues)            ║"
echo "║  3. Set up self-hosted runner:                    ║"
echo "║     cp .github/runner/.env.example .env           ║"
echo "║     bash .github/runner/setup-runner.sh           ║"
echo "║  4. Push to GitHub & enable branch protection:    ║"
echo "║     bash .github/scripts/setup-branch-protection.sh║"
echo "║  5. Verify pipeline runs green ✅                 ║"
echo "╚══════════════════════════════════════════════════╝"
