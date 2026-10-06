# verbose-broccoli

A personal workspace of agent tools for education and knowledge work:
skills, command-line tools and MCP servers in three areas, `code`, `work` and
`chat`. `.specify/memory/constitution.md` governs; this file holds the rules
every change follows. Constitution principle IX and `docs/architecture.md`
describe the repository layout. Detailed procedures live in skills.
Claude-only additions are in `.claude/rules/`; Codex-only additions are the
`developer_instructions` in `.codex/config.toml`.

Before working on a plugin, read its rules, including when invoking its skills
from another directory: [code](plugins/code/AGENTS.md),
[work](plugins/work/AGENTS.md), or [chat](plugins/chat/AGENTS.md).

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

## Rule placement and reusable boundaries

Add an AGENTS.md rule only when an agent must exercise judgment every time.
Put mechanically enforceable behavior in a hook, check, workflow output or
configuration instead. Show that split when proposing rules.

Reusable packages keep provider facts in configuration or a narrow provider
profile. Keep modules, files, tasks and commands provider-neutral. The chosen
provider may remain the shipped default and acceptance target. This preference
permits abstraction for vendor choices; it does not permit unrelated flexibility.
Ask when the required abstraction depth is unclear.

Before adding a profile field, check whether a reused dependency already handles
it. Do not duplicate protocol selection, standard HTTP status mapping, retries
or finish-reason checks. Record unsupported unchosen providers as limits instead
of building for them.

Deliver capabilities as Agent Skills, command-line tools and MCP servers
(constitution IX). Do not add plugin packaging or an installer; document
`skills` and `add-mcp` for installing elsewhere.

## Necessary work and code size

Before dispatching planned work, check whether earlier decisions or measurements
already answer it. Raise redundant work with the user before starting, especially
large batches or paid runs. A task-ledger entry alone does not establish a need.

Estimate locally owned code when proposing or relaying a build, and show the
estimate to the user. Keep requested capabilities. Offer supporting tools,
records and defensive checks as removable when the component does not need them.
Name dependencies before deleting them.

Do not restore the abolished 300-net-line feature cap or invent a new budget.
Report measured size and the split decision under the existing split-review rule.
A line count alone does not stop work or require approval. Patches to upstream
files are locally maintained code; unchanged upstream copies are not.

## Upstream adoption and attribution

Before adopting third-party source, dependencies or tools, obtain a read-only
security review with evidence for every finding. The adopting feature's
orchestrator owns that review. Choose its model through model-choice.

Use adopted Spec Kit extensions to replace duplicated local hooks and
instructions. Removing or disabling one, or adding a local wrapper, needs a
reason tied to that reuse goal. If a review brief omits the change's purpose,
ask before recommending its removal or narrowing it.

`licenses/third-party-notices.md` lists upstream code actually copied, ported or
vendored into this repository. Name its source repository and exact revision,
and point to the license shipped with the copy. Installed dependencies do not
get an entry solely for being installed. Remove a notice in the same change
that removes the copy or replaces it with an installed dependency.

## Workflow and verification

- Before editing, after scope changes, and before completion, run
  `npm run workflow` and follow the execution instructions it prints.
- Before completion, `npm run verify` must pass; it runs all checks through
  Turborepo and passes on their exit status and the same run's summary.
- The agent, model and reasoning effort of each worker, reviewer and
  orchestrator come from the code plugin's `model-choice` skill; each time
  budget comes from the code plugin's jev-mcp judgments.

## Review

- The provider that implemented a change does not give its final review. Use a
  fresh reviewer from a provider other than the implementer's (Claude Code,
  Codex or Copilot; for a develop merge, also Antigravity, Grok or Cursor),
  preferring Copilot when Claude Code and Codex both implemented parts of a
  feature, and give it only the review scope and the requirements, not
  suspected defects, prior findings, or expected outcomes.
- Workers and reviewers that read student data (the work wiki's student
  pages, the gate's registered list or raw student sources) run only on Claude Code or
  Codex, the user's own Claude and ChatGPT accounts, never on another agent;
  this overrides the Copilot preference above.
- Resolve actionable findings, rerun the affected verification, and repeat the
  review when fixes change the implementation materially.
- Before each commit, the implementer or the orchestrator reviews the diff.
- If a feature's change against its merge base with `develop` reaches 1,000
  lines or more (`git diff --stat`; deleting a whole file counts as about one
  line), review whether to split it before the `develop` merge review.
- A review before merging into `develop` favors speed; one before merging into
  `main` favors accuracy.

## Coordinator messages

Develop messages main only with questions or user-relevant merges, user blocks and finished features.
Main answers by convention and relays user decisions; it does not re-verify develop evidence or reply to routine status.
Heartbeats need acknowledgment only.

## Records

- Development memory is the Spec Kit records in `specs/`,
  `.specify/assessments/` and `.specify/bugs/` plus code and Git. Do not keep a
  separate memory system or development wiki. The code plugin's `code` wiki
  holds coding knowledge for work in any project (libraries, patterns,
  decisions); it is not this repository's development memory.
- When a session ends or a task moves to another provider, the task coordinator
  adds one or two lines under that task in `tasks.md`: what was done, what
  blocked, and what comes next. The develop orchestrator owns final task-ledger
  ticks.
- Commit with Conventional Commits and one `Spec-Kit-Task: Txxx` trailer per
  covered implementation task.
- Lessons that hold across features belong in this file or in
  `plugins/<name>/AGENTS.md`.
- Treat Linear issues and comments as writing to an external service: never
  put operational data such as student records, or secret values, in them.
- Only the develop orchestrator writes to Linear. It creates one issue per
  feature or bug, without sub-issues, after searching for similar ones; other agents
  report out-of-scope bugs to it through Orca messages.
- The Opus session in the main worktree relays the user's decisions to the
  develop orchestrator.

## English replies

Follow these in every English reply to the user. They copy the English section
under "Language techniques" in `~/.agents/skills/plain-language/references/REFERENCE.md`;
change both together. `licenses/third-party-notices.md` records their source.

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
