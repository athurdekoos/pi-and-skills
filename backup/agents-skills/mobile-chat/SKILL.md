---
name: mobile-chat
description: Optimize agent communication for users on mobile devices. Use this skill whenever the user mentions they're on their phone, says "mobile", "on my phone", "typing on mobile", asks for shorter messages, says "make it quick", "yes/no questions", "keep it brief", or when you detect short terse replies suggesting mobile input. Also use when building skills or workflows that will be used from a phone, chat app, or any small-screen touch interface. Applies to any conversational flow — discussions, decisions, reviews, approvals.
---

# Mobile Chat

Make agent conversations effortless on a phone. The user is tapping on glass with their thumbs — every word they type costs 10x what it costs on a keyboard. Respect that.

## Core Principle

**Propose, don't ask.** The agent does the thinking and suggests; the user confirms or rejects. A "yes" tap beats a typed paragraph every time.

## The Rules

### 1. Yes/No by Default

Transform every open-ended question into a proposal with a default.

```
❌ "How should errors be handled?"
❌ "What layout do you prefer — cards, list, or grid?"

✅ "I'd use card layout here. Good?" → y/n
✅ "On error: retry 3x then fail. OK?" → y/n
✅ "Errors: (1) retry 3x (2) fail fast (3) ask user" → 1/2/3
```

When you genuinely don't know the user's preference, offer max 3 numbered options. Never more.

### 2. One Question Per Message

Never stack questions. One decision per turn. Wait for the answer before moving on.

```
❌ "Should it retry on failure? And how many times? Also, what about timeouts?"

✅ "Retry on network failure?"
   → [user: y]
   "3 retries with 2s backoff?"
   → [user: y]
   "30s timeout?"
   → [user: make it 60]
```

### 3. Keep It Short

2-3 lines max per message. If you need to explain something, break it into:
- The decision (1 line) — this is the message
- The context (only if they ask "why?")

```
❌ "For the command queue, we need to decide how to handle the case where
    a command fails while other commands are waiting. There are several
    approaches: we could continue executing the remaining commands, we
    could pause and wait for user input, or we could flush the entire
    queue. Each has tradeoffs..."

✅ "If a queued command fails: keep running the rest of the queue?"
```

### 4. Smart Defaults First

Before asking anything, figure out the obvious answer. If 80% of users would choose X, propose X. Only surface genuinely ambiguous decisions.

**How to pick defaults:**
- Industry standard / common convention → propose it
- Only one option makes sense given context → propose it
- User already expressed a preference earlier → reuse it
- Genuinely 50/50 ambiguous → then ask (as numbered options)

### 5. Batch Confirm at the End

After a series of decisions, show a compact summary and ask for one confirmation.

```
"Here's what we landed on:
• Cards layout, infinite scroll
• Retry 3x on failure
• 60s timeout
• Queue max: 20 commands

All good, or anything to change?"
```

The user can say "good" or "change timeout to 30s" — one tap or one short correction.

### 6. Accept Terse Input

Mobile users give short answers. Interpret generously:

| User says | Means |
|-----------|-------|
| y, yes, yep, 👍, k, ok | Approve |
| n, no, nah, 👎 | Reject |
| 1, 2, 3 | Pick numbered option |
| A single word or phrase | Their preference — use it |
| "idk", "up to you", "whatever" | Use your best judgment, move on |
| "?" or "why" | They want context before deciding |

Never ask "could you elaborate?" on mobile. If the answer is ambiguous, propose your best interpretation: "I read that as [X]. Right?"

### 7. Progress Breadcrumbs

On mobile, users lose track of where they are. Drop quick markers:

```
"Queue behavior (3/5)..."
"Almost done — 2 more."
"Last one:"
```

## Applying to Multi-Decision Workflows

When a workflow (like gathering requirements or discussing a phase) involves many decisions:

1. **Group related decisions** — handle one topic at a time
2. **Start with the big fork** — the decision that changes everything else
3. **Cascade from there** — each answer narrows the next question
4. **Skip what you can infer** — if they said "keep it simple," don't ask about advanced options
5. **Offer an express lane** — "I'll pick sensible defaults for the rest. Review at the end?"

### Express Lane Pattern

For users who clearly want speed:

```
"I have 4 decisions for the queue. Want to:
(1) Go through each
(2) I'll pick defaults, you review at end"
```

If they pick 2, make all decisions, show the batch summary, let them override.

### Disagreement Is Easy Too

When the user rejects a proposal, offer the alternative immediately:

```
Agent: "Auto-execute queued commands when idle?"
User: "no"
Agent: "OK — manual trigger then. Tap 'next' to run each one?"
User: "y"
```

Don't ask "what would you prefer instead?" — propose the next-best option.

## Anti-Patterns

These kill mobile conversations:

- **Walls of text** — anything over 4 lines
- **Multiple questions in one message** — forces long typed response
- **Open-ended "what do you think?"** — requires a paragraph
- **Asking for elaboration** — "could you tell me more about that?"
- **Restating what they said back verbatim** — wastes screen space
- **Asking about things you could decide yourself** — technical details, implementation choices
- **Multi-select** — hard to tap on mobile; use sequential yes/no instead

## When NOT to Use This

- User is clearly at a keyboard (long detailed messages, code snippets)
- The topic genuinely requires nuanced discussion (architecture decisions)
- User explicitly asks for detailed options/explanation

Even then, keep messages as short as possible. Mobile habits are good habits.
