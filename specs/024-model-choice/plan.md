# Implementation Plan: Model Choice with Backfire

**Branch**: `feature/model-choice` | **Date**: 2026-09-30 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from `specs/024-model-choice/spec.md`

## Summary

Add the code-plugin skill `model-choice`, a copy of TypeSafe's agent skill
with a local reference that tells a coordinator how to choose each worker's
agent, model and effort with backfire, and point the repository rules to it:

- `plugins/code/skills/model-choice/SKILL.md` is upstream's
  `skills/typesafe-ai/SKILL.md`, changed only in the frontmatter `name` and
  `description`, one link to the reference, and what the security review
  requires. `LICENSE` is upstream's, unchanged.
- `references/model-choice.md` holds all local content: the live catalogs,
  the evidence, the call, acting on the answer, and calling backfire without
  its MCP tools.
- `upstream.json` records the source and every local change;
  `licenses/THIRD_PARTY_NOTICES.md` gains an entry.
- `AGENTS.md`'s model-choice line points to the skill;
  `.claude/rules/claude-code.md` drops the fixed roles and keeps the
  other-provider review; `docs/architecture.md`'s generated skill table and
  its sentence on model selection follow.

- CodexBar's command-line tool (steipete/CodexBar v0.69.0, MIT), unchanged,
  gives the usage limits and credit; `npm run doctor` pins its version like
  lychee's, and `.codex/config.toml` drops its fixed-role sentence.

Apart from the doctor pin, the change is prose, JSON and configuration.

## Research

### R1 - Upstream pin

TypeSafe's `typesafe-ai/skills` has one skill, `skills/typesafe-ai/`
(`SKILL.md` and an MIT `LICENSE`, "Copyright (c) 2026 TypeSafe AI"). Pin tag
`v0.5.7`, commit `65a39f393687675ce170e6094757de20370365b9`, the newest commit
on 2026-09-30. The upstream `SKILL.md` is 149 lines with SHA-256
`71ea90d7906c6554c4f4c460ef7361b2d26f59116ccdae986dc6d997b9389f52`.

### R2 - Security screen and review

Backfire's `jev_screen` on the upstream `SKILL.md` returned injection
probability 0.90, substance 1.0 and relevance 0.95, recommendation `block`.
A skill is imperative text for agents by nature, so the screen alone cannot
separate a risk from ordinary guidance; the skill's policy sends a `block` to
the user. A read-only security review (FR-012) gives evidence per finding; its
result and the user's decision are recorded in [tasks.md](tasks.md) under T001.

### R3 - Calling backfire without its MCP tools (FR-008)

- Backfire's only entry point is `backfire serve-mcp`
  (`packages/backfire/src/backfire/__main__.py`, `choices=("serve-mcp",)`),
  a stdio MCP server; a caller needs an MCP client.
- `jev-judge-mcp judge <tool>` in the locked jev-judge-mcp 0.6.0 calls one tool
  from stdin, but it builds `Runtime(load_settings())` without backfire's
  provider factory (`jev_judge_mcp/cli.py`, `_call`), so it would use
  jev-judge-mcp's own provider resolution instead of backfire's profile.
  Rejected.
- The `mcp` command in the uv environment needs the `mcp[cli]` extra (typer)
  and has no tool-call command. Rejected.
- MCP Inspector's CLI mode can call a tool on a stdio server, but it is a new,
  unlocked npm download for a fallback path. Rejected.
- Chosen: the Python `mcp` client library that the workspace already locks
  (`mcp` 2.2.0 in `uv.lock`, a dependency of jev-judge-mcp), in a short
  snippet in the reference that starts `backfire serve-mcp` over stdio and
  calls one tool with a JSON argument file. The coordinator saves it in its
  session scratch space and runs it with
  `uv run --frozen --offline --no-sync --package backfire python <file> <tool> <args.json>`
  from a worktree root. The develop session's working example used this
  pattern for `jev_decide`. The repository gains no program file.

### R4 - Live catalogs (FR-004)

- Codex: `~/.codex/models_cache.json` has `models[]` with `slug`,
  `display_name`, `description`, `supported_reasoning_levels[].effort`,
  `default_reasoning_level` and `visibility` (`list` or `hide`).
- Claude Code: `claude --help` documents `--model` (an alias such as `fable`,
  `opus` or `sonnet`, or a full model name) and `--effort` (`low`, `medium`,
  `high`, `xhigh`, `max`). Orca starts it with `worker-start --agent claude
  --model <model> --effort <effort>`.
- OMP: `omp models` prints one table per provider (for example `hive`,
  `openai-codex`, `tetrate`) with context, output limit and thinking levels;
  `~/.omp/agent/models.yml` defines the providers. OMP workers start through
  Orca's terminal path with `omp --model <provider>/<model-id>`.
- Launch limits: Orca's `worker-start` accepts only the efforts in its own
  model catalog and fails with `invalid_argument` otherwise;
  `~/.claude/rules/worker-dispatch.md` lists the current gaps and the
  terminal-path steps.

### R5 - Evidence (FR-005)

- Usage limits and credit: one `codexbar usage --format json` call (R7).
  Before CodexBar, the Codex weekly limit came from Codex's session logs
  (`rate_limits.primary.used_percent` in
  `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`; 36.0 on 2026-09-30,
  resetting 2026-10-04 02:28 KST); the user replaced that with CodexBar.
- Track records: the develop merge review records name each reviewer's agent,
  model and effort in a `Reviewed-by` trailer (`git log --grep='record develop
  merge review' --format='%h %(trailers:key=Reviewed-by,valueonly)'`), and each
  feature's `tasks.md` names its workers.
- Priorities: the user's instructions and the repository rules, for example
  `AGENTS.md`'s review timing (speed before `develop`, accuracy before
  `main`), the reuse order, and not wasting the Codex weekly limit.

### R6 - The call (FR-006)

`jev_decide` takes 2 to 6 candidates, a decision of at most 1,500 characters,
evidence of at most 12,000 and priorities of at most 2,000, up to three
requirements, and escape hatches `ask_user`, `investigate` and `none`.
`jev_rerank` takes up to 250 candidates of at most 2,000 characters. The
workers of this feature were chosen in two or three calls: `jev_rerank` over
the catalogs' models with the task as the query, `jev_decide` among the top
six agent and model pairs, then `jev_decide` among the chosen model's
efforts.

### R7 - CodexBar (FR-014 to FR-016)

- Release: tag `v0.69.0`, commit `48ded68da6932a4fe5de9037d06c4ac48bd36e90`,
  published 2026-09-28. The Linux glibc asset
  `CodexBarCLI-v0.69.0-linux-x86_64.tar.gz` has SHA-256
  `89a244a6713953719cc4211c147c0ff180a50e85776a742fc9013630b734e1d5`, which
  matches the release's `.sha256` asset. It holds the `CodexBarCLI` binary, a
  `codexbar` symlink to it, `VERSION` and `CodexBar_CodexBarCore.bundle`, whose
  JavaScript plugins implement providers such as OpenRouter; upstream's
  `docs/cli.md` says to extract it and run `./codexbar`. The laptop has glibc
  2.43.
- Source size: the Linux build compiles `CodexBarCLI` (about 16,000 lines)
  and `CodexBarCore` (about 182,000 lines, 107,000 of them in provider
  modules). The review is therefore split in two, each scoped by searching:
  A covers credential sources and destinations for Codex, Claude, OpenRouter
  and Vercel plus the plugin host; B covers telemetry, auto-update,
  subprocesses, listeners, files written and release provenance.
- Pinning: like lychee, a host tool whose version `scripts/doctor.ts` checks.
  The release keeps its bundle next to the binary, so it is extracted into
  `~/.local/opt/codexbar-0.69.0/`, the laptop's existing layout for versioned
  tools, with `~/.local/bin/codexbar` linking to it.
- Keys: `OPENROUTER_API_KEY` and `AI_GATEWAY_API_KEY` come from
  `~/.config/verbose-broccoli/providers/openrouter.env` and `vercel.env`
  through `uv run --no-project --env-file <file> ... -- codexbar usage`,
  the `--env-file` pattern the chat plugin uses; nothing is written to
  CodexBar's config file.
- Review result (T010): both reviews said "install with limits". No
  telemetry, auto-update or listener in `usage`; each credential goes only to
  its provider's host; the tarball matches the tag (all 77 plugin files, 785
  of 785 compiled source paths) but is not signed. The limits: one explicit
  `--provider` per call, never `all`, `both` or `--status` (`all` reads other
  tools' secrets); `--source oauth` for Claude and Codex (Claude's default
  path types `/usage` into a real interactive Claude session that could start
  a billed turn); only the call's own key, with the variables that reroute
  keys or switch sources unset; no CodexBar config file and an empty
  `~/.config/codexbar/providers/`; only the `usage` command; account identity
  stripped from the JSON before it is shared. Where review A preferred
  `--source cli` for Claude (OAuth may keep a hash of the token after a rate
  limit, low) and review B `--source oauth` (medium risk above), the lower
  risk wins.
- Checked on 2026-09-30 with those limits: all four calls succeed. Codex's
  extra-usage credit balance was 0 while its weekly window had room, so a zero
  credit balance alone does not mean Codex is exhausted. Review A's
  one-time check of the Codex login found no `chatgpt_base_url` in
  `~/.codex/config.toml` and no `OPENAI_API_KEY` in `~/.codex/auth.json`.
  Besides the files the reviews list, a Claude call left an empty
  `~/.codexbar/claude-oauth-cache.lock` (mode 600).

## Technical Context

**Language/Version**: Markdown, JSON and TOML; TypeScript for the doctor pin.

**Primary Dependencies**: backfire (`packages/backfire`), its locked `mcp`
client library; CodexBar 0.69.0 as a host tool; Orca's `orchestration
worker-start`.

**Storage**: None.

**Testing**: `npm run verify` (plugin packaging and skill checks, document
regions, formatting); one real `jev_decide` call through the reference's
snippet.

**Target Platform**: Claude Code and Codex CLI sessions that load the code
plugin; OMP where it loads the plugin's skills.

**Constraints**: no mapping from difficulty or risk to a model; no default
model; no student data or secrets in backfire evidence.

## Constitution Check

- Principle VII and the reuse order: the text is upstream's; the local
  reference is domain glue; CodexBar is used unchanged; the only program code
  is its version pin in `scripts/doctor.ts`, and the fallback call reuses the
  locked `mcp` client. Pass.
- Principle IX: the skill lives in its owning package, `plugins/code`.
  Pass.
- Principle V: acceptance calls backfire for real and starts a worker with
  the chosen settings. Pass.
- Development workflow: git flow feature finish after a fresh review by a
  provider other than the implementer's. Pass.

## Project Structure

### Documentation (this feature)

```text
specs/024-model-choice/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
plugins/code/skills/model-choice/
├── SKILL.md
├── LICENSE
├── upstream.json
└── references/model-choice.md
licenses/THIRD_PARTY_NOTICES.md
AGENTS.md
.claude/rules/claude-code.md
.codex/config.toml
docs/architecture.md
scripts/doctor.ts
scripts/doctor_test.ts
```

**Structure Decision**: One skill folder like `plugins/code/skills/backfire/`;
the reference folder is `references/`, as in the backfire skill's local
reference.

## Complexity Tracking

None.
