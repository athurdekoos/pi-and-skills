# Self-Hosted Runner Setup Guide

## Prerequisites

- Docker Engine 24+ with `docker compose` plugin
- A GitHub Personal Access Token (PAT) with `repo` scope
- A machine with at least 4GB RAM and 2 CPU cores

## Step-by-Step

### 1. Generate a GitHub PAT

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Create a token with:
   - **Repository access:** Only the target repo
   - **Permissions:** Actions (Read & Write), Administration (Read & Write)
3. Copy the token — you'll only see it once

### 2. Configure the Runner

```bash
cd .github/runner
cp .env.example .env
```

Edit `.env`:
```
GITHUB_REPOSITORY=your-username/your-repo
GITHUB_TOKEN=github_pat_xxxxxxxxxxxx
RUNNER_NAME=my-project-runner
```

### 3. Start the Runner

```bash
bash setup-runner.sh
```

This will:
1. Build the Docker image (Node.js 20 + Gitleaks + Trivy + Hadolint)
2. Start the container in ephemeral mode
3. Register with GitHub

### 4. Verify Registration

Go to your repo → Settings → Actions → Runners

You should see your runner listed as "Idle" with labels: `self-hosted, linux, x64, security`

### 5. Test the Pipeline

Push a commit or open a PR — the CI pipeline should trigger and run on your self-hosted runner.

## Ephemeral Mode

The runner is configured with `EPHEMERAL=1`, which means:
- After completing one job, the runner de-registers itself
- Docker's `restart: unless-stopped` spins up a fresh instance
- No state persists between jobs

This is the most secure configuration because a compromised job cannot affect future runs.

## Troubleshooting

### Runner doesn't appear in GitHub
- Check logs: `docker compose logs -f`
- Verify your PAT has the correct scopes
- Ensure the GITHUB_REPOSITORY format is `owner/repo` (not a URL)

### Build fails on native modules (node-pty, better-sqlite3)
- The Dockerfile includes `build-essential` and `python3` for this
- If you still get errors, check that your Dockerfile has `USER root` before the apt-get section

### Runner runs out of memory
- Increase `mem_limit` in `docker-compose.yml`
- Default is 4GB which handles most Node.js projects

### DNS resolution issues inside container
- Add to docker-compose.yml:
  ```yaml
  dns:
    - 8.8.8.8
    - 8.8.4.4
  ```

## Stopping the Runner

```bash
bash teardown-runner.sh
```

This stops the container and removes the work volume.

## Fallback to GitHub-Hosted Runners

If your self-hosted runner is down, you can temporarily switch `runs-on` in `ci.yml`:

```yaml
# From:
runs-on: [self-hosted, linux, x64]

# To:
runs-on: ubuntu-latest
```

Note: `ubuntu-latest` won't have Gitleaks/Trivy/Hadolint pre-installed, so those steps will need action-based alternatives or will be skipped.
