---
name: pi-backup
description: "Back up and restore pi agent skills, prompts, settings, and registry to GitHub. Trigger with 'backup my skills', 'back up pi', 'save my agent config', 'restore my skills', 'push my skills to github', or when the user mentions backing up, snapshotting, or restoring their agent setup."
---

# pi-backup — Agent Configuration Backup & Restore

## Overview

Backs up all pi agent configuration to the GitHub repo at `git@github.com:athurdekoos/pi-and-skills.git`. Supports backup (snapshot + push) and restore (clone + apply).

**Repo:** https://github.com/athurdekoos/pi-and-skills
**Local clone:** `/tmp/pi-and-skills` (ephemeral; re-cloned as needed)

## What's Backed Up

| Source | Destination in Repo |
|--------|-------------------|
| `~/.agents/skills/` | `backup/agents-skills/` |
| `~/.agents/skill-registry.json` | `backup/skill-registry.json` |
| `~/.pi/agent/skills/` | `backup/pi-agent-skills/` |
| `~/.pi/agent/prompts/` | `backup/pi-agent-prompts/` |
| `~/.pi/agent/settings.json` | `backup/settings.json` |
| `~/.pi/agent/bin/` | `backup/pi-agent-bin/` |

**Excluded:** `~/.pi/agent/auth.json` (credentials), `~/.pi/agent/sessions/` (ephemeral)

## Mode 1: Backup

**Trigger:** "backup my skills", "back up pi", "snapshot my agent"

### Steps

```bash
# 1. Clone or pull latest
cd /tmp
rm -rf pi-and-skills
git clone git@github.com:athurdekoos/pi-and-skills.git
cd pi-and-skills

# 2. Run backup script
./bin/backup.sh --commit

# 3. Push
git push
```

Report the commit hash and summary of what changed.

## Mode 2: Restore

**Trigger:** "restore my skills", "set up my agent from backup"

### Steps

```bash
# 1. Clone latest
cd /tmp
rm -rf pi-and-skills
git clone git@github.com:athurdekoos/pi-and-skills.git
cd pi-and-skills

# 2. Dry run first
./bin/restore.sh --dry-run

# 3. Ask user for confirmation, then:
./bin/restore.sh
```

## Mode 3: npx Restore (on new machine)

Tell the user:

```bash
npx @athurdekoos/pi-and-skills          # restore everything
npx @athurdekoos/pi-and-skills --dry-run # preview first
```

> Note: npx restore requires the package to be published to npm. For now, clone-and-run works immediately.
