---
name: session-migrate
description: Produce a copyable prompt that continues the current work in a new chat, or resume a selected task by checking its saved context against current sources. Use when the user asks to pause, migrate a session to a new chat, or continue identified work; not for transferring work to another running agent or for general questions about memory.
---

# Session Migrate

Create a handoff prompt for a new chat. Output it directly in chat as a copyable Markdown block. Do not write a document unless the user explicitly asks.

The prompt should let a fresh agent continue from the current point with minimal re-explaining.

## Workflow

1. Identify what the next session is meant to do.
   If the user gave a focus, tailor the handoff to that. Otherwise assume the next session should continue the current goal.

2. Summarize only durable context.
   Include decisions, current state, files, repos, URLs, commands, branches, commits, artifacts, and constraints that affect the next agent.

3. Include continuation instructions.
   Tell the next agent what has been done, what remains, what to verify first, and which skills or workflows may help.

4. Avoid duplication.
   Reference existing artifacts, commits, diffs, docs, issues, PRs, and URLs instead of copying their contents.
   If the recipient cannot access an artifact, include its essential permitted content or identify the missing input.

## Resume a Selected Task

Match the handoff to the intended task and workspace. Inspect the current sources,
Git state, and relevant runtime evidence before the next action. Reconcile stale
claims with those observations, keeping completed work whose evidence still holds.
Check uncertain external effects before retrying them. Continue the next authorized
step; a handoff does not grant new authority. Keep updates in chat unless the user
selected a durable record, then update that same record and read it back.

## Required Sections

Use this structure:

```markdown
Continue this session:

Role:
You are continuing an existing agent session. Use this context as a starting point; current sources and the user's latest instructions govern the work.

Goal:
...

Current state:
...

Completed:
...

Remaining work:
...

Constraints and preferences:
...

Important files and references:
...

Suggested skills:
...

First actions:
...
```

## Rules

- Make the output directly pasteable into a new chat.
- Keep it compact, but do not omit state the next agent would need to avoid redoing work.
- Preserve the user's wording when it contains important constraints or preferences.
- Include exact paths, URLs, branches, commits, PRs, and commands when relevant.
- Say what was verified and what was not.
- Do not invent completed work.
- Do not include secrets, tokens, credentials, or private data unless the user explicitly asks and it is safe.
- If the next agent should stay read-only, say that clearly.
