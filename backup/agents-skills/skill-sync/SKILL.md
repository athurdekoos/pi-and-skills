---
name: skill-sync
description: "Track and update skills sourced from GitHub repositories. Use when the user says 'register skill', 'track skill', 'update skills', 'sync skills', 'check skill updates', 'list tracked skills', 'untrack skill', or mentions keeping skills in sync with upstream repos. Also triggers when user asks about skill versions, outdated skills, or managing skills installed from GitHub. Has four modes: register (track a new skill), update (check and apply upstream changes), list (show registry), and untrack (remove from registry)."
---

# Skill Sync — GitHub Skill Tracker & Updater

## Overview

This skill maintains a registry of pi-coding-agent skills that were sourced from GitHub repositories. It tracks what adaptations were made to each skill for pi compatibility and keeps them in sync with upstream changes.

**Registry location:** `~/.agents/skill-registry.json`
**Scripts location:** `~/.agents/skills/skill-sync/scripts/`

All scripts have CLI entrypoints. Run with `python3 <script> --help` for usage.

---

## Mode 1: Register a Skill

**Trigger phrases:** "register skill", "track skill", "add skill to sync"

When the user wants to register a skill they've installed (or are about to install) from a GitHub repo:

### Step 1: Gather Information

Ask the user for:
1. **GitHub repo URL** — e.g., `https://github.com/user/repo`
2. **Subpath within repo** — if the skill isn't at repo root (e.g., `skills/my-skill/`)
3. **Local skill name** — the directory name under `~/.agents/skills/`

If the user provides a GitHub URL, infer what you can from it.

### Step 2: Capture the Baseline

```bash
cd ~/.agents/skills/skill-sync/scripts
python3 upstream_check.py check --repo <REPO_URL> --last-sha 0 --subpath <SUBPATH>
```

This clones the repo and returns the current HEAD SHA. Record it as both `last_checked_commit` and `baseline_commit`.

### Step 3: Diff Local vs Upstream

Compare the locally installed skill against the upstream original:

```bash
cd ~/.agents/skills/skill-sync/scripts
python3 diff_generator.py dir --local <LOCAL_SKILL_PATH> --upstream <UPSTREAM_CLONE_PATH> --json
```

### Step 4: Document Adaptations

Review the diff and write a human-readable summary of what was changed and **why** — pi compatibility, tool differences, path adjustments, etc. This becomes the `adaptation_notes` field. The diff output becomes `adaptation_diff`. Together they explain what was changed (machine-readable) and why (human-readable).

### Step 5: Add to Registry

```bash
cd ~/.agents/skills/skill-sync/scripts
python3 registry.py add \
  --name <SKILL_NAME> \
  --repo <REPO_URL> \
  --subpath <SUBPATH> \
  --local-path <LOCAL_SKILL_PATH> \
  --sha <HEAD_SHA> \
  --notes "<ADAPTATION_NOTES>"
```

For the `adaptation_diff` (which can be large), use the Python API:

```bash
cd ~/.agents/skills/skill-sync/scripts
python3 -c "
from registry import Registry
r = Registry()
r.update('<SKILL_NAME>', adaptation_diff='''<DIFF_OUTPUT>''')
"
```

Confirm to the user: "Skill registered. I'll check for upstream updates whenever you ask."

---

## Mode 2: Update Skills

**Trigger phrases:** "update skills", "sync skills", "check skill updates", "are my skills up to date"

### Step 1: Check for Updates

**Check all skills:**
```bash
cd ~/.agents/skills/skill-sync/scripts
python3 upstream_check.py check-all --registry ~/.agents/skill-registry.json
```

**Check one skill:**
```bash
cd ~/.agents/skills/skill-sync/scripts
python3 registry.py get --name <SKILL_NAME>
# Then use the repo URL and last_checked_commit from the output:
python3 upstream_check.py check --repo <REPO_URL> --last-sha <LAST_SHA> --subpath <SUBPATH>
```

### Step 2: Report Status

Present a summary table:

| Skill | Status | Details |
|---|---|---|
| skill-name | ✅ Up to date | — |
| other-skill | 🔄 Updates available | `feat: add new command` / `fix: path bug` |
| broken-skill | ❌ Error | Could not reach repo |

The `commit_log` field in the check result contains the actual commit messages since last check — use these for the Details column.

If everything is up to date, stop here.

### Step 3: For Each Skill with Updates — Review

For each skill that has upstream changes, **stop and present the changes to the user before making any modifications**:

1. **Show the upstream commit log** — what commits were made since last check
2. **Show the file-level diff** between the upstream clone and the local skill:
   ```bash
   python3 diff_generator.py dir --local <LOCAL_PATH> --upstream <CLONE_SKILL_PATH>
   ```
3. **Show the local adaptation notes** — remind what was customized for pi
4. **Show the local adaptation diff** — the specific changes that were made

Ask: "Upstream has changes for `<skill-name>`. Here's what changed upstream and here are your current pi adaptations. Should I update this skill? I'll preserve your pi adaptations."

### Step 4: Apply Updates (with user approval only)

For each approved update:

1. **Backup the local skill:**
   ```bash
   cd ~/.agents/skills/skill-sync/scripts
   python3 patch_applier.py backup --local <LOCAL_PATH> --backup-dir /tmp/skill-sync-backups
   ```

2. **Review the changes intelligently.** Read:
   - The upstream diff (what changed in the GitHub repo)
   - The current local skill files
   - The adaptation notes and diff (what was customized for pi)

3. **Apply changes file-by-file:**
   - **Upstream changed file, NO local adaptations** → copy upstream version directly
   - **Upstream changed file, HAS local adaptations** → manually merge: apply the upstream improvement while keeping the pi-specific changes. Read both versions, understand the intent of each change, produce a merged result.
   - **Upstream added new file** → copy it in, adapt for pi if needed
   - **Upstream deleted file** → remove locally unless it's a pi-specific addition

4. **Update the adaptation records:**
   ```bash
   # Re-diff to capture new adaptation state
   python3 diff_generator.py dir --local <LOCAL_PATH> --upstream <CLONE_SKILL_PATH> --json

   # Update registry
   python3 registry.py update --name <SKILL_NAME> \
     --set last_checked_commit <NEW_SHA> \
     --set adaptation_notes "<UPDATED_NOTES>"
   ```
   Also update `adaptation_diff` via the Python API if the diff is large.

5. **Verify the updated skill** — read the final SKILL.md and confirm it looks correct. If something looks wrong, rollback:
   ```bash
   python3 patch_applier.py restore --backup <BACKUP_PATH> --local <LOCAL_PATH>
   ```

6. **Report to user:** "Updated `<skill-name>`. Changes: [summary]. Your pi adaptations have been preserved. Backup at: [path]."

### Step 5: Cleanup

Temp clone directories are cleaned up automatically by `upstream_check.py` CLI commands. If you used the Python API directly, call:
```bash
python3 -c "from upstream_check import cleanup; cleanup('<CLONE_PATH>')"
```

---

## Mode 3: List Tracked Skills

**Trigger phrases:** "list tracked skills", "show registered skills", "what skills am I tracking"

```bash
cd ~/.agents/skills/skill-sync/scripts
python3 registry.py list
```

Present the results in a readable table:

| Skill | GitHub Repo | Last Checked | Adaptations |
|---|---|---|---|
| my-skill | github.com/user/repo | 2026-02-28 | Changed tool refs for pi |

For more detail on a specific skill:
```bash
python3 registry.py get --name <SKILL_NAME>
```

---

## Mode 4: Untrack a Skill

**Trigger phrases:** "untrack skill", "stop tracking skill", "remove skill from sync"

```bash
cd ~/.agents/skills/skill-sync/scripts
python3 registry.py remove --name <SKILL_NAME>
```

This only removes the skill from the registry — it does NOT delete the locally installed skill files. Confirm to user: "Removed `<skill-name>` from tracking. The skill itself is still installed at `<path>`."

---

## Error Handling

- **Registry file missing:** Created automatically with empty skills list on first access
- **Git clone fails:** Report error, skip that skill, continue with others. If the error mentions authentication, advise: "Make sure `git clone <url>` works from your terminal — you may need SSH keys or a credential helper configured for private repos."
- **Merge conflict (can't cleanly merge):** Present both the upstream version and the local adapted version side-by-side. Ask the user to choose or specify how to merge.
- **Rollback on failure:** If anything goes wrong mid-update, restore from backup:
  ```bash
  python3 patch_applier.py restore --backup <BACKUP_PATH> --local <LOCAL_PATH>
  ```

---

## Quick Reference

| Action | What to Say |
|---|---|
| Register a skill | "register [skill-name] from [github-url]" |
| Check all skills | "check skill updates" or "sync skills" |
| Check one skill | "check updates for [skill-name]" |
| List tracked skills | "list tracked skills" |
| Remove from tracking | "untrack [skill-name]" |
