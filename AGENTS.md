# verbose-broccoli

A personal Deno workspace of three agent plugins for education and knowledge
work. `.specify/memory/constitution.md` governs; this file holds the rules every
change follows. Constitution principle IX and `docs/architecture.md` describe the
repository layout. Detailed procedures live in skills. Claude-only additions are
in `.claude/rules/`; Codex-only additions are the `developer_instructions` in
`.codex/config.toml`.

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
- The main agent chooses each worker's and reviewer's model, reasoning effort
  and time budget from the code plugin's backfire judgments.

## Review

- The provider that implemented a change does not give its final review. Use a
  fresh reviewer from the other provider (Claude Code or Codex) and give it only
  the review scope and the requirements, not suspected defects, prior findings,
  or expected outcomes.
- Resolve actionable findings, rerun the affected verification, and repeat the
  review when fixes change the implementation materially.
- Before each commit, the implementer or the orchestrator reviews the diff.
- A review before merging into `develop` favors speed; one before merging into
  `main` favors accuracy.

## Records

- Development memory is the Spec Kit records in `specs/`,
  `.specify/assessments/` and `.specify/bugs/` plus code and Git. Do not keep a
  separate memory system or development wiki.
- When a session ends or a task moves to another provider, the coordinator adds
  one or two lines under that task in `tasks.md`: what was done, what blocked,
  and what comes next. Main owns task-ledger updates.
- Commit with Conventional Commits and one `Spec-Kit-Task: Txxx` trailer per
  covered implementation task.
- Lessons that hold across features belong in this file or in
  `plugins/<name>/AGENTS.md`.
- Treat Linear issues and comments as writing to an external service: never
  put operational data such as student records, or secret values, in them.
- Only the main agent writes to Linear. It creates one issue per feature or
  bug, without sub-issues, after searching for similar ones; other agents
  report out-of-scope bugs to it through Orca messages.

## English replies

Follow these in every English reply to the user. They copy the English section
under "Language techniques" in `~/.agents/skills/plain-language/references/REFERENCE.md`;
change both together. `licenses/THIRD_PARTY_NOTICES.md` records their source.

- Numbers are prompts for a second look, not caps: about 20 words per
  sentence, about 5 sentences per paragraph, and a list from three parallel
  items. A longer sentence is fine if it carries one idea.
- Everyday words: "use" not "utilize", "help" not "facilitate", "about" not
  "approximately". Verbs: "decide" not "make a determination", "apply" not
  "submit an application", unless the noun is the term of art.
- Empty openers to cut: "It is important to note that", "In today's
  fast-paced world", "As previously mentioned".
- Hedge stacks: "may potentially, in some cases" becomes "may".
- Passive is fine when the actor is unknown or does not matter.
- Expand or explain an abbreviation at first use, unless the reader already
  knows it.
