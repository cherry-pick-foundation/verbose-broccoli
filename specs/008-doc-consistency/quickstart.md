# Quickstart: Validating Repository Document Consistency

Run from the feature worktree's root after implementation, with Deno on `PATH`
(`export PATH="$HOME/.deno/bin:$PATH"` if needed), lychee 0.24.2 installed and
`uv sync --locked --project packages/doc-regions` done by Orca's setup.

## Automated checks

```sh
deno task doctor             # lychee version and the doc-regions environment
deno task test:doc-regions   # package and generator tests
deno task doc-regions:check  # regions and links, offline
deno task test:workflow      # REVIEW text includes the judgment step
deno task docs:check         # generated reference, unchanged by this feature
deno task verify             # everything, with recorded evidence
```

Expected: all pass, and `git status --short` is empty after the check.

## Stale region by hand (User Story 1)

1. In a scratch worktree, add a skill folder under `plugins/work/skills/`
   with a `SKILL.md`.
2. `deno task doc-regions:check` fails, names `docs/architecture.md` and the
   skill table region, shows the diff and names `deno task doc-regions:update`;
   `git status --short` lists only the new skill.
3. `deno task doc-regions:update` changes only that region; running it again
   changes nothing; the check passes.

## Judgment step (User Stories 2 and 3)

1. On a scratch branch from `develop`, rename a task that
   `docs/architecture.md` describes in prose, without editing the document.
2. `deno task doc-regions:prepare -- --base develop --max-evidence-chars
   20000` prints requests; the describing paragraph is a claim, and
   `deno.json`'s diff is evidence.
3. Send the `backfire_verify` request through the agent's MCP client; the
   paragraph comes back `contradicted` or with `action` `review` (SC-005: in
   each of three runs).
4. `deno task doc-regions:audit` reports MemoryLint findings for `AGENTS.md`
   and the constitution; neither file changes.
