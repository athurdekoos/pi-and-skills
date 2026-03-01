# Skill Health Check Catalog

## Error Checks (🔴)

### STRUCT — Missing SKILL.md
- **What:** Skill directory exists but contains no SKILL.md
- **Why it matters:** Without SKILL.md, the skill cannot be discovered or triggered
- **Fix:** Create a SKILL.md with at minimum `name` and `description` frontmatter

### NAME — Missing name in frontmatter
- **What:** SKILL.md exists but YAML frontmatter has no `name` field
- **Why it matters:** The agent framework uses `name` to identify the skill
- **Fix:** Add `name: your-skill-name` to the YAML frontmatter

### ORPHAN — Directory without SKILL.md
- **What:** A directory exists under skills/ but has no SKILL.md
- **Why it matters:** Likely an incomplete or abandoned skill installation
- **Fix:** Either add a SKILL.md or remove the directory

### REF_BROKEN — Broken file reference
- **What:** SKILL.md references a file path that doesn't exist on disk
- **Why it matters:** The skill will fail when it tries to read the referenced file
- **Fix:** Create the missing file or update the reference path

## Warning Checks (🟡)

### DESC — Missing or too-short description
- **What:** Description field is missing or under 20 characters
- **Why it matters:** Description is the primary trigger mechanism — short descriptions cause poor triggering
- **Fix:** Write a descriptive, trigger-rich description (see skill-creator docs)

### SIZE — Oversized SKILL.md
- **What:** SKILL.md body exceeds 500 lines
- **Why it matters:** Large skill files consume excessive context window
- **Fix:** Move detailed content to references/ files

### CONFLICT — Near-duplicate skill names
- **What:** Two skills have names within edit distance ≤ 2
- **Why it matters:** May cause confusion in skill selection
- **Fix:** Rename one of the conflicting skills

### SCRIPT_ERR — Python script compilation error
- **What:** A .py file in scripts/ fails py_compile
- **Why it matters:** The script will crash at runtime
- **Fix:** Fix the syntax error in the script

## Info Checks (ℹ️)

### STALE — No modification in 90+ days
- **What:** No file in the skill directory has been modified in over 90 days
- **Why it matters:** May indicate an abandoned or forgotten skill
- **Fix:** Review whether the skill is still needed; update or remove

### EMPTY_DIR — Empty subdirectory
- **What:** scripts/, references/, or assets/ directory exists but is empty
- **Why it matters:** Empty dirs suggest incomplete setup
- **Fix:** Add content or remove the empty directory
