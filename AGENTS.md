# verbose-broccoli

A personal Deno workspace of three agent plugins for education and knowledge
work. `.specify/memory/constitution.md` governs; this file is the short map and
the rules every change follows. Detailed procedures live in skills. Claude-only
additions are in `.claude/rules/`; Codex-only additions are the
`developer_instructions` in `.codex/config.toml`.

## Map

- `plugins/code/`, `plugins/work/`, `plugins/chat/`: Agent Plugins packages
  (`plugin.json`, optional `skills/` and `mcp.json`).
- `specs/<feature>/`: Spec Kit ledgers (`spec.md`, `plan.md`, `research.md`,
  `tasks.md`).
- `scripts/`: repository tooling behind the tasks in `deno.json`.
- `tools/`: standalone tool packages with their own locks; none exist yet.
- `docs/`: architecture notes, brand assets and examples; `docs/reference/` is
  generated.

## Every change

- Do not claim that a function, behavior, or convention exists without an exact
  file and line, a source excerpt, or a reproducible command. If evidence is
  unavailable, say so.
- Read files in full before wide-ranging changes or before editing an unfamiliar
  file. Inspect the surrounding code instead of copying remembered APIs or
  commands.
- Preserve unrelated worktree changes. Never revert or rewrite changes you did
  not make.
- Make the smallest change that satisfies the request. Add tests for code
  changes; a bug fix needs a case that fails without the fix.
- Run the narrowest relevant checks first, then broader ones.
- Write comments and documents for a reader at HEAD who has not seen the
  conversation, issue, or diff.

## Reuse Before Implementing

Minimize code owned by this repository. Prefer, in order:

1. Existing repository, runtime, standard-library, or dependency functionality.
2. A stable upstream implementation used as a dependency.
3. An unstable upstream implementation with the smallest necessary patch.
4. Minimal glue code required to connect existing implementations.

Do not reimplement functionality that can reasonably be reused.

Prefer reducing locally owned implementation over reducing dependency count.

Judge upstream implementations by actual fit, compatibility, maintenance, tests, security, and license - not popularity alone.

Patches must preserve the upstream implementation and remain narrowly scoped. Do not turn a patch into a locally maintained rewrite.

Custom implementation is not a fallback. Locally authored code should be limited to necessary integration, adaptation, and domain-specific glue.

If the requirement cannot be met without substantial new local implementation, stop and report the missing capability and available upstream options instead of implementing it.

## Workflow and verification

- Before editing, after scope changes, and before completion, run
  `deno task workflow` and follow the execution instructions it prints.
- Before completion, `deno task verify` must pass; it runs all checks and
  records evidence.

## Review

- The provider that implemented a change does not give its final review. Use a
  fresh reviewer from the other provider (Claude Code or Codex) and give it only
  the review scope and the requirements, not suspected defects, prior findings,
  or expected outcomes.
- Resolve actionable findings, rerun the affected verification, and repeat the
  review when fixes change the implementation materially.

## Records

- Development memory is the Spec Kit ledger plus code and Git. Do not keep a
  separate memory system or development wiki.
- When a session ends or a task moves to another provider, the coordinator adds
  one or two lines under that task in `tasks.md`: what was done, what blocked,
  and what comes next. Main owns task-ledger updates.
- Record decisions in `research.md` as decision, rationale, and alternatives
  considered.
- Commit with Conventional Commits and one `Spec-Kit-Task: Txxx` trailer per
  covered implementation task.
- Lessons that hold across features belong in this file or in
  `plugins/<name>/AGENTS.md`.
