# Research: Governance Policies of 2026-09-27

Probes ran on 2026-09-27 with Deno 2.9.6, Git 2.53.0, git-flow-next 2.1.0 and
Orca 1.4.215 on Linux x86_64, in scratch repositories outside the checkout.

## R1. Commit-message linter

- **Decision**: Use commitlint 21.2.3 (`@commitlint/cli` and
  `@commitlint/config-conventional`, MIT) through Deno's npm support, with the
  Conventional Commits parser preset from
  `conventional-changelog-conventionalcommits` 10.4.0 (MIT). The only local
  code is a commitlint plugin rule for the constitution version and the hook
  that calls the CLI.
- **Rationale**: commitlint is the maintained reference linter for
  Conventional Commits. Probed under Deno with `--edit <file>`:
  - `feat!: …` with `Spec-Kit-Task`, `Reviewed-by`, `Reviewed-commit`,
    `Co-Authored-By` and `Signed-off-by` trailers passed; the parser reported
    the `!` as a `BREAKING CHANGE` note.
  - `fix: …` with a `BREAKING CHANGE:` footer produced the same note.
  - `Update files` failed with `subject-empty` and `type-empty`.
  - `Merge branch 'feature/x' into develop` passed: commitlint's default
    ignore list skips Git's default merge messages before any rule runs.
  - Comment lines left in the message file by an editor were stripped.
  - Each run took about 0.15 seconds after the first download.
  - A plugin rule may be async and receives the parsed commit (type, notes,
    footer), so the constitution rule fits commitlint's own extension point.
- **Constraints found**:
  - `config-conventional` names its parser preset as a package string, which
    commitlint resolves with `require.resolve` from the config file's folder.
    Without `node_modules` (`nodeModulesDir: "none"`) that fails, so the config
    imports the preset and passes `parserPreset: {parserOpts}` as an object.
  - A TypeScript config file fails: commitlint loads `.ts` configs through
    jiti, which cannot resolve `npm:` specifiers. An `.mjs` config loads
    through native `import()`, and from it Deno imports a `.ts` module, so the
    rule logic stays in TypeScript and is type-checked and unit-tested.
- **Alternatives considered**:
  - cocogitto (`cog verify`) or convco: Rust host binaries, a second host-tool
    install like git-flow, and no extension point for the constitution rule.
  - gitlint or commitizen: Python; possible through `tools/spec-kit`-style uv
    projects, but a second toolchain for one hook and weaker Conventional
    Commits defaults.
  - Using `@commitlint/lint` from a Deno script instead of the CLI: needs local
    code for message reading and comment stripping that the CLI already owns.
  - A hand-written header regex: rejected by the root `AGENTS.md` reuse order.

## R2. Installing the commit-message hook

- **Decision**: Commit the hook as `scripts/git-hooks/commit-msg` and set the
  repository's local Git setting `core.hooksPath` to the relative path
  `scripts/git-hooks`. Orca's setup script sets it; `deno task doctor` fails
  when it differs.
- **Rationale**: Git runs hooks from the top of the working tree, and a
  relative `core.hooksPath` resolves there, so each worktree runs the hook from
  its own checkout, as `gitflow.path.hooks = scripts/git-flow-hooks` already
  does for git-flow. `core.hooksPath` is unset today and `.git/hooks` holds only
  samples, so nothing is displaced. Git 2.24 and later run `commit-msg` for
  merge commits as well; the default merge message is ignored by commitlint
  (R1).
- **Consequences**: The setting lives in the shared repository config, so all
  worktrees get it at once. A worktree whose checkout has no
  `scripts/git-hooks/` (a branch that has not merged `develop` since this
  feature) runs no commit hook until it does.
- **Runtime lookup**: Git hooks inherit the caller's `PATH`, which may lack
  Deno (it is not on this session's `PATH`). The hook finds Deno the way Orca's
  setup does (`$HOME/.deno/bin/deno` first, then `PATH`) and refuses the commit
  with a message when neither exists.
- **Alternatives considered**: Putting `commit-msg` into
  `scripts/git-flow-hooks/` and pointing `core.hooksPath` there mixes two hook
  systems in one folder. Copying hooks into `.git/hooks` needs a per-worktree
  install step and drifts from the checkout.

## R3. The constitution version rule

- **Decision**: The plugin rule compares `.specify/memory/constitution.md` in
  `HEAD` with the same path in the index being committed (`git show
  HEAD:<path>` and `git show :<path>`). Git exports `GIT_INDEX_FILE` to hooks,
  so `git commit -a` and `git commit <paths>` are compared correctly.
- **Rules**: No `HEAD`, or the file missing on either side: not applied.
  Identical content: pass. Otherwise both sides need exactly one
  `**Version**: X.Y.Z` line; the expected version is `(X+1).0.0` for a breaking
  commit (any `BREAKING CHANGE` note, from `!` or a footer), else `X.(Y+1).0`
  for `feat`, else `X.Y.(Z+1)` for `docs` or `fix`; any other type is refused.
  A missing or malformed version line, or any other version, is refused with
  the expected version in the message.
- **Known limit**: `commit-msg` does not learn that a commit is an amend, so
  `git commit --amend` is compared with the commit being replaced (`HEAD`), not
  with its parent. An amend that only changes the header type is therefore not
  re-checked. The spec's edge case is narrowed to this behavior.

## R4. Review-record checks in the feature-finish hook

- **Decision**: Keep the POSIX shell hook and add Git plumbing checks before
  verification: the tip has one parent (`git rev-list --parents -n 1`), its
  tree equals the parent's tree, `git log -1
  --format='%(trailers:key=Reviewed-by,valueonly)'` and the same for
  `Reviewed-commit` each give exactly one non-empty line, and the
  `Reviewed-commit` value resolves with `git rev-parse --verify --quiet
  <value>^{commit}` to the parent. Git matches trailer keys without regard to
  case.
- **Rationale**: Git already parses trailers and resolves commit names; the
  hook only compares results. The checks read objects and refs and write
  nothing, so every refusal leaves the repository unchanged. They run before
  `deno task verify` so a missing record fails fast.
- **Alternatives considered**: A Deno script for the checks would add a
  runtime start and a second language to a hook that is shell today.

## R5. Branch names for new worktrees

- **Orca facts**: `orca worktree create --help` (1.4.215) offers `--name`,
  `--base-branch` and `--setup`, but no branch option. Orca runs
  `scripts.setup` from `orca.yaml` in the new worktree and exports
  `ORCA_ROOT_PATH`, `ORCA_WORKTREE_PATH` and `ORCA_WORKSPACE_NAME` (strings in
  the app bundle's setup environment builder and its settings help text: "Path
  to the worktree being created. Setup commands run from this directory.").
- **Decision**: A small POSIX shell script, `scripts/worktree-branch.sh`,
  called first by Orca's setup. The worktree name is the base name of `git
  rev-parse --show-toplevel`, which equals `ORCA_WORKTREE_PATH`'s base name and
  also works outside Orca and in tests. It renames the checked-out branch only
  when all of these hold: HEAD is a branch; the branch is not `main` or
  `develop` and not already `feature/…`, `release/…` or `hotfix/…`; it has no
  upstream; and its tip is already on another branch (`git for-each-ref
  --contains HEAD` lists a ref other than the branch itself), meaning it has no
  commits of its own. The target is checked with `git check-ref-format
  --branch` and must not exist; otherwise the script exits non-zero with a
  message, which stops Orca's setup.
- **Rationale**: Only Git commands are needed. `git branch -m` renames a
  branch that is checked out in the current worktree and updates its HEAD. A
  second run finds a git flow name and does nothing.
- **Alternatives considered**: Orca's internal `branchNameOverride` is not
  reachable from its command line. A Deno script would work but adds a runtime
  start and more code for a dozen Git calls.

## R6. Worker model choice

- **Decision**: Before dispatch, run the local advisor
  (`.local/jev-substitute/task_advisor.py` in the `develop` worktree, which
  sends each task line to the local System One endpoint) for each worker's
  tasks, and choose model, reasoning effort and time budget case by case from
  its difficulty, size and risk judgments. There is no mapping table. If the
  advisor is unavailable, record that and fall back to the Codex default
  (`gpt-6-luna` at `max`), which is what applies when no choice is made.
