---
name: todo
description: Capture, manage, and track todos in ~/TASKS.md. Trigger on "todo", "todo:", "add a todo", "remind me to", "I need to", "don't let me forget", "put on my list", "add to my tasks", "what's on my plate", "my tasks", "my todos", "done with", "finished", or any phrase about capturing, viewing, or completing tasks.
---

# Todo & Task Management

Single source of truth: **`~/TASKS.md`**. Fast capture, full management, integrated with daily briefing.

## Master File

**Always use `~/TASKS.md`** — global, cross-project, single file.

If it doesn't exist, create it:

```markdown
# Tasks

## Active

## Waiting On

## Someday

## Done
```

## Task Format

```markdown
- [ ] **Task title** - context (due [date] | for [person] | since [date])
```

- Completed: `- [x] ~~Task~~ (completed Mar 1)`

## Quick Capture

Parse the user's intent and route:

| User says | Task | Section |
|-----------|------|---------|
| "todo review PR #42" | **Review PR #42** | Active |
| "todo send invoice by Friday" | **Send invoice** — due Friday | Active |
| "remind me to follow up with Sarah" | **Follow up with Sarah** | Active |
| "I need to update the docs sometime" | **Update the docs** | Someday |
| "todo waiting on Jake for API keys" | **API keys from Jake** — since today | Waiting On |

**Routing rules:**
- Default → **Active**
- "sometime", "eventually", "someday", "when I get to it" → **Someday**
- "waiting on", "blocked by", "need X from" → **Waiting On**
- "due", "by [day]", "before [date]" → **Active** with due date

**Confirm briefly (one line):**

```
✅ Added to Active: **Review PR #42**
```

Bulk capture → list all added:

```
✅ Added 3 tasks to Active:
- **Review PR #42**
- **Send invoice** — due Friday
- **Update deployment docs**
```

## Task Actions

| User says | Action |
|-----------|--------|
| "what's on my plate" / "my tasks" / "my todos" | Read ~/TASKS.md, summarize Active + Waiting On, flag overdue |
| "done with X" / "finished X" | Mark `[x]`, strikethrough, add date, move to Done |
| "drop X" / "remove X" | Delete task entirely |
| "move X to someday" | Move between sections |
| "what am I waiting on" | Show Waiting On with how long each has waited |

## Extracting Tasks from Conversations

When summarizing meetings or calls, offer to add extracted tasks:
- Commitments the user made ("I'll send that over")
- Action items assigned to them
- Follow-ups mentioned

**Ask before adding** — don't auto-add without confirmation.

## Conventions

- **Bold** task titles for scannability
- Include "for [person]" for commitments to others
- Include "due [date]" for deadlines
- Include "since [date]" for waiting items
- Keep Done section ~1 week, then clear old items
- **Never ask clarifying questions** for simple todos — just capture

## Integration

- **daily-briefing** reads `~/TASKS.md` and includes Active/Waiting On in the daily report
- **memory-management** can decode shorthand in task descriptions (people, projects, acronyms)
