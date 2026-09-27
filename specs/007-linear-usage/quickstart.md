# Quickstart: Validate Linear Usage Through Orca

Run inside Orca terminals. `<W>` is the `verbose-broccoli` workspace ID.

## Repository carriers

```sh
# SC-004: exactly the two approved lines
grep -n "Linear" AGENTS.md

# FR-004: the preset appends the issue line to the spec template
uv run --project tools/spec-kit specify preset resolve spec-template
.specify/scripts/bash/resolve-template.sh spec-template | tail -12

# FR-006: every workflow mode prints the completion order
deno task test:workflow
deno task --quiet workflow | grep -c "In Review"

# SC-005: no Linear integration besides Orca
grep -n -i linear .specify/extensions.yml || echo "no Linear extension"
grep -n -i 'linear@' ~/.codex/config.toml || echo "no Codex Linear plugin"
jq '.enabledPlugins // {} | keys' ~/.claude/settings.json
```

Expected: two `AGENTS.md` lines; the resolved template ends with the
`**Linear issue**: [CHE-###]` line; the workflow test passes and the count is
1; no Linear extension or plugin.

## Linear side

```sh
# SC-001: one issue per feature, linked worktrees, one spec line each
for n in 5 6 7 8; do orca linear issue CHE-$n --workspace <W> --json | jq -r '.result.issue | "\(.identifier) \(.state.name)"'; done
orca worktree list --json | jq -r '.result.worktrees[] | "\(.displayName) \(.linkedLinearIssue)"'
for d in feature-linear-usage feature-doc-consistency feature-wiki-storage feature-wiki-consistency; do
  grep -c '^\*\*Linear issue\*\*: CHE-[0-9]*$' ../$d/specs/0*/spec.md | grep -v ':0'
done

# SC-002, after this feature's finish
orca linear issue CHE-5 --full --workspace <W> --json | jq '.result.issue | {state: .state.name, comments: [.comments[]?.body]}'
```

Expected: CHE-5 to CHE-8 exist and each linked worktree names its issue; each
feature's spec has one line; after the finish CHE-5 is Done with one comment
naming the merge commit and `specs/007-linear-usage/`.

## SC-003 walkthrough

A fresh agent given only the repository at HEAD answers, for each moment, where
the rule is and what it says: start a feature (spec template and `AGENTS.md`),
report a bug as a worker (`AGENTS.md`), complete a feature (`deno task
workflow`), need archiving or labels (`deno task workflow`). Record the
answers and the agent in `tasks.md`.

## SC-006, after the user's setting

Linear UI: Team Settings > Issue statuses & automations shows auto-archive
after 1 month; labels `code`, `work` and `chat` exist
(`orca linear team labels --team CHE --workspace <W> --json`).
