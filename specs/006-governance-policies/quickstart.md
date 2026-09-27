# Quickstart: Validating the Governance Policies

Run from the feature worktree's root with Deno on `PATH` (`export
PATH="$HOME/.deno/bin:$PATH"` if needed).

## Automated checks

```sh
deno task test:git-flow      # finish hook
deno task test:worktree-branch  # branch-naming script
deno task test:commit-msg    # commit-message check and version rule
deno task test:doctor        # core.hooksPath check
deno task test:workflow      # REVIEW guidance
deno task docs:check         # generated reference is current
deno task verify             # everything, with recorded evidence
```

Expected: all pass. The finish tests compare refs and worktrees before and
after each refusal ([contracts/review-record.md](contracts/review-record.md));
the commit tests make real commits in temporary repositories with the hook
installed through `core.hooksPath`
([contracts/commit-message.md](contracts/commit-message.md)); the
branch-naming tests cover every case in
[contracts/worktree-branch.md](contracts/worktree-branch.md) and a second run.

## Manual checks in this repository

1. Installation: `git config --get core.hooksPath` prints
   `scripts/git-hooks`, and `deno task doctor` passes.
2. A bad header is refused: `git commit --allow-empty -m 'Update files'`
   fails with commitlint's `type-empty` and `subject-empty` problems.
3. The constitution amendment commit of this feature is accepted only with the
   version its type calls for (planned: `feat`, 0.21.0 → 0.22.0).
4. Timing: `time git commit --allow-empty -m 'test: time hook'` in a scratch
   clone takes under 2 seconds; drop the commit afterwards.
5. REVIEW guidance: a change to `AGENTS.md` makes `deno task workflow` choose
   REVIEW, and its instructions describe self-review before each commit and
   the independent review at merge time.

## Finish

1. Merge review by fresh reviewers from the other provider; resolve findings.
2. `git commit --allow-empty` with `Reviewed-by` and `Reviewed-commit: <tip>`.
3. From the `develop` worktree: `git flow feature finish governance-policies`.
