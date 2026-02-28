# pi-and-skills

Backup and restore for pi coding agent configuration: skills, prompts, settings, and skill-sync registry.

## Quick Restore (npx)

```bash
npx @athurdekoos/pi-and-skills          # restore all agent files
npx @athurdekoos/pi-and-skills --dry-run # preview what would be restored
```

## Manual Restore

```bash
git clone https://github.com/athurdekoos/pi-and-skills.git
cd pi-and-skills
./bin/restore.sh
```

## Create a New Backup

```bash
cd pi-and-skills
./bin/backup.sh           # snapshot current state
./bin/backup.sh --commit  # snapshot + git commit
git push                  # push to GitHub
```

## What's Backed Up

| Source | Backup Location | Contents |
|--------|----------------|----------|
| `~/.agents/skills/` | `backup/agents-skills/` | All installed agent skills (GSD, code-review, etc.) |
| `~/.agents/skill-registry.json` | `backup/skill-registry.json` | Skill-sync tracking registry |
| `~/.pi/agent/skills/` | `backup/pi-agent-skills/` | Pi-specific skills (openteams-pptx) |
| `~/.pi/agent/prompts/` | `backup/pi-agent-prompts/` | Prompt templates (architecture, debug, etc.) |
| `~/.pi/agent/settings.json` | `backup/settings.json` | Pi agent settings (model, provider) |
| `~/.pi/agent/bin/` | `backup/pi-agent-bin/` | Agent binaries (fd) |

### Excluded (intentionally)

- `~/.pi/agent/auth.json` — contains credentials
- `~/.pi/agent/sessions/` — ephemeral session data
