# Quickstart: Validating the Clean Architecture Tool Collection

Run these from a worktree root after the slice named in each scenario. Start
batch commands with the laptop's low-priority prefix
(`systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7`)
and run one `npm run verify` at a time.

## 1. Skills are the same set, once each (S2a and S2b; SC-001, FR-002, FR-003)

Before S2a, on `develop`, keep the list in the feature's state folder,
because it must survive until S2b. The first three lines find that folder,
ignoring a relative `XDG_STATE_HOME` as the XDG specification requires; they
are repeated after S2b because that runs in a later shell:

```sh
state=${XDG_STATE_HOME:-}
case "$state" in /*) ;; *) state="$HOME/.local/state" ;; esac
evidence="$state/verbose-broccoli/workspaces/feature-clean-architecture/skills-inventory"
mkdir -p "$evidence"
ls .agents/skills | sort > "$evidence/skills-before.txt"
```

After S2b:

```sh
state=${XDG_STATE_HOME:-}
case "$state" in /*) ;; *) state="$HOME/.local/state" ;; esac
evidence="$state/verbose-broccoli/workspaces/feature-clean-architecture/skills-inventory"
ls .agents/skills | sort | diff "$evidence/skills-before.txt" -
for skill in skills/*/*/ tools/ponytail/skills/*/ plugins/work/skills/*/; do
  uv run --project tools/skills-ref --frozen --offline --no-sync skills-ref validate "$skill"
done
```

Expected: no difference in names; every skill validates; the skills link
check in `npm run verify` passes. Then open a fresh Claude Code session and a
fresh Codex session in the worktree and ask each for its skill list: both
show the same names, each once, with no `code:` or `work:` plugin copies.
Report any old installed plugin copy in user folders to the user instead of
removing it (spec Edge Cases).

## 2. MCP servers come from user settings only (S2a; FR-003, FR-004, FR-005)

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

## 5. Settings fall back safely (S4; FR-009, FR-010)

Only `credit-offers` reads user settings among the slices that can start now;
`doc-regions` reads the repository's own `scripts/doc-regions.toml` and
`workflow` reads none.

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
state=${XDG_STATE_HOME:-}
case "$state" in /*) ;; *) state="$HOME/.local/state" ;; esac
python3 "$state/verbose-broccoli/workspaces/feature-clean-architecture/code-size/measure.py"
```

Expected: `VERIFIED`; the measured owned-code change is reported to the user
with the slice (SC-006, SC-008).
