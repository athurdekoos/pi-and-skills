---
name: pi-backup
description: "Back up and restore pi agent skills, prompts, settings, and registry to GitHub. Trigger with 'backup my skills', 'back up pi', 'save my agent config', 'restore my skills', 'push my skills to github', or when the user mentions backing up, snapshotting, or restoring their agent setup."
---

# pi-backup — Agent Configuration Backup & Restore

**Repo:** `git@github.com:athurdekoos/pi-and-skills.git`
**Local clone:** `/tmp/pi-and-skills` (ephemeral; re-cloned as needed)

## What's Backed Up

| Source | Destination in Repo |
|--------|-------------------|
| `~/.agents/skills/` | `backup/agents-skills/` |
| `~/.agents/skill-registry.json` | `backup/skill-registry.json` |
| `~/.pi/agent/skills/` | `backup/pi-agent-skills/` |
| `~/.pi/agent/prompts/` | `backup/pi-agent-prompts/` |
| `~/.pi/agent/agents/` | `backup/pi-agent-agents/` |
| `~/.pi/agent/extensions/` | `backup/pi-agent-extensions/` |
| `~/.pi/agent/bin/` | `backup/pi-agent-bin/` |
| `~/.pi/agent/settings.json` | `backup/settings.json` |
| `~/TASKS.md` | `backup/user/TASKS.md` |
| `~/CLAUDE.md` | `backup/user/CLAUDE.md` |
| `~/memory/` | `backup/user/memory/` |

**Excluded:** `~/.pi/agent/auth.json` (credentials), `~/.pi/agent/sessions/` (ephemeral)

## Backup

**Trigger:** "backup my skills", "back up pi", "snapshot my agent"

```bash
cd /tmp
rm -rf pi-and-skills
git clone git@github.com:athurdekoos/pi-and-skills.git
cd pi-and-skills
./bin/backup.sh --commit
git push
```

Report: commit hash, skill count, what changed.

## Restore

**Trigger:** "restore my skills", "set up my agent from backup"

```bash
cd /tmp
rm -rf pi-and-skills
git clone git@github.com:athurdekoos/pi-and-skills.git
cd pi-and-skills
./bin/restore.sh --dry-run   # preview first
./bin/restore.sh             # after user confirms
```
