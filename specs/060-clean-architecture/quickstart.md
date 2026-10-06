# Quickstart: Validating the Clean Architecture Tool Collection

Run these from a worktree root after the slice named in each scenario. Start
batch commands with the laptop's low-priority prefix
(`systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7`)
and run one `npm run verify` at a time.

## 1. Skills are the same set, once each (S2; SC-001, FR-002, FR-003)

Before S2, on `develop`:

```sh
ls .agents/skills | sort > /tmp/skills-before.txt
```

After S2:

```sh
ls .agents/skills | sort | diff /tmp/skills-before.txt -
uv run --project tools/skills-ref --frozen --offline --no-sync skills-ref validate skills/*/*/
```

Expected: no difference in names; every skill validates; the skills link
check in `npm run verify` passes. Then open a fresh Claude Code session and a
fresh Codex session in the worktree and ask each for its skill list: both
show the same names, each once, with no `code:` or `work:` plugin copies.
Report any old installed plugin copy in user folders to the user instead of
removing it (spec Edge Cases).

## 2. MCP servers come from user settings only (S2; FR-003, FR-004, FR-005)

```sh
test ! -e .mcp.json && ! grep -q 'BEGIN' .codex/config.toml && echo clean
claude mcp list
codex mcp list
```

Expected: `clean`; both agents list `jev-mcp` and `reference-library` once,
from user scope. `~/.claude/settings.json` still denies the reference
library's delete and empty-trash tools, and `~/.codex/config.toml` still
lists them in `disabled_tools` ([delivery contract](contracts/delivery.md)).

## 3. Each dependency rule fails on its fixture (S3; SC-004, FR-007)

```sh
npm run clean-architecture
npm run python:imports
npm run test:clean-architecture
```

Expected: the first two pass on the real tree; the test runs each fixture of
rules D1 to D6 ([dependency rules](contracts/dependency-rules.md)) and
asserts that the checker fails on it in one run.

## 4. A moved component keeps its behavior (S4–S6; SC-003, FR-013)

```sh
base=$(git merge-base HEAD develop)
git diff -M --stat "$base" -- packages/<name>/tests
git diff -M "$base" -- packages/<name>/tests | grep -E '^[-+][[:space:]]*(assert|expect|t\.)' || echo "no assertion changed"
```

Expected: only renames and import lines change; `no assertion changed`; the
package's tests pass in `npm run verify`.

## 5. Settings fall back safely (S4–S6; FR-009, FR-010)

Run a migrated command with an empty absolute configuration folder, then with
a relative one:

```sh
XDG_CONFIG_HOME=$(mktemp -d) <command> --help
XDG_CONFIG_HOME=relative/path <command> --help
```

Expected: both start with defaults. A command that needs a missing
credential exits as an execution failure naming the file and variable, never
the value ([settings contract](contracts/settings.md)).

## 6. Judgments by configuration (H1 slice; SC-007, FR-019 to FR-023)

After hold H1 is released: one counted live request through each gated
server returns a result naming its provider and model; a request with
`[judgment] server` set to the GLM server and a 90-second answer completes;
`npm run verify` makes no live model call ([judgment
contract](contracts/judgment.md)).

## 7. Every slice

```sh
pgrep -af "turbo run" || systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7 npm run verify
python3 "$XDG_STATE_HOME/verbose-broccoli/workspaces/feature-clean-architecture/code-size/measure.py"
```

Expected: `VERIFIED`; the measured owned-code change is reported to the user
with the slice (SC-006, SC-008).
