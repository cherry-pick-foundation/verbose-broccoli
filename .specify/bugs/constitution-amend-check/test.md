# Bug Verification: Commit-message check rejects amending a constitution commit

- **Slug**: constitution-amend-check
- **Tested**: 2026-09-28
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The assessment's reproduction no longer fails: amending a breaking constitution
commit that keeps 1.0.0 is accepted and replaces `HEAD`. A new commit without a
bump is still refused, and the full repository check passes with the fix
(`2b0dd55`, on `develop` `969979d`).

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (post-fix) | The assessment's steps in a scratch repository holding `2b0dd55`'s `deno.json`, `deno.lock`, `scripts/commitlint.config.mjs`, `scripts/constitution_version.ts` and `scripts/git-hooks/commit-msg`, with `core.hooksPath = scripts/git-hooks` (git 2.53.0, Deno 2.9.6) | pass | `chore: seed` at 0.22.0, `docs!: break` at 1.0.0, then `git commit --amend --no-edit` with new text at 1.0.0 was accepted; the new commit's parent is the seed. A following `docs: follow up` without a bump was refused. |
| New / updated tests | `deno task test:commit-msg` | pass | 4 tests, including "commit-msg hook: amendments use the parent constitution version"; before the fix its first case failed with the reported message (implementing worker, Orca dispatch `ctx_6c1f978fb088`). |
| Regression suite, lint, type-check | `deno task verify --task CHE-15` on the tree committed as `2b0dd55` | pass | Workflow `VERIFIED`: "Configured checks passed for the current code state." |
| Formatting and lint | `deno task format:check`, `deno task lint` | pass | Biome checked 47 files with no fixes. |

## Output Excerpts

```text
[main 4714e21] docs!: break
 Date: Mon Sep 28 02:20:52 2026 +0900
 1 file changed, 2 insertions(+), 2 deletions(-)
Constitution version 1.0.0 with commit type 'docs' requires 1.0.1; found 1.0.0. [local/constitution-version]
```

The first block is the accepted amend; the last line is the refused follow-up
commit.

## Residual Risks

- The hook reads `/proc/$PPID/cmdline`. On a system without `/proc`, or when a
  program between `git` and the hook hides the arguments, an amend keeps the
  old refusal; it is never accepted wrongly.
- An abbreviated flag such as `--amen`, which git accepts, is not recognized
  and keeps the old refusal.

## Recommendation

Close the bug once the branch is merged into `develop`: the reported amend is
accepted, and new commits still need their own bump.
