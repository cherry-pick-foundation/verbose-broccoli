# Bug Verification: Commit-message check rejects amending a constitution commit

- **Slug**: constitution-amend-check
- **Tested**: 2026-09-28
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The assessment's reproduction no longer fails: amending a breaking constitution
commit that keeps 1.0.0 is accepted and replaces `HEAD`, also with the
abbreviation `--amen`. A second bump in an amend and a new commit without a bump
are still refused, and the full repository check passes with the fix
(`3b21ba9`, on `develop` `969979d`).

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (post-fix) | The assessment's steps in a scratch repository holding `3b21ba9`'s `deno.json`, `deno.lock`, `scripts/commitlint.config.mjs`, `scripts/constitution_version.ts` and `scripts/git-hooks/commit-msg`, with `core.hooksPath = scripts/git-hooks` (git 2.53.0, Deno 2.9.6) | pass | `chore: seed` at 0.22.0, `docs!: break` at 1.0.0, then `git commit --amend --no-edit` and `git commit --amen --no-edit` with new text at 1.0.0 were accepted; the commit's parent stayed the seed. `git commit --amen -m 'docs!: break again'` at 2.0.0 and a new `docs: follow up` without a bump were refused. |
| New / updated tests | `deno task test:commit-msg` | pass | 4 tests, including "commit-msg hook: amendments use the parent constitution version"; the hook took 182 ms in the runtime test. Its first case and its `--amen` case failed before their fixes (implementing workers, Orca dispatches `ctx_6c1f978fb088` and `ctx_0a6f80b132a7`). |
| Regression suite, lint, type-check | `deno task verify --task CHE-15` on `3b21ba9` | pass | Workflow `VERIFIED`: "Configured checks passed for the current code state." |
| Abbreviations git accepts | `git commit --am`, `--ame`, `--amen`, `--no-am`, `--no-ame`, `--no-amen` in a scratch repository (git 2.53.0) | pass | The first three amend and the last three make a new commit, as the hook assumes. |

## Output Excerpts

```text
amend --no-edit keeping 1.0.0: accepted
amen --no-edit keeping 1.0.0: accepted
Constitution version 0.22.0 with commit type 'docs' requires 1.0.0; found 2.0.0. [local/constitution-version]
Constitution version 1.0.0 with commit type 'docs' requires 1.0.1; found 1.0.0. [local/constitution-version]
```

The two refusals are the amend with a second bump, now compared with the
seed, and the new commit without a bump.

## Residual Risks

- The hook reads `/proc/$PPID/cmdline`. On a system without `/proc`, or when a
  program between `git` and the hook hides the arguments, the amend goes
  undetected and is compared with the commit it replaces, as before this fix:
  it can then be refused wrongly or accepted wrongly (see fix.md, Deviations
  from Assessment).
- `git rebase -i` `fixup` and `squash` do not run the `commit-msg` hook, so a
  combined commit can raise the version more than once. This is outside this
  bug and was true before it; the develop merge review reported it.

## Recommendation

Close the bug once the branch is merged into `develop`: the reported amend is
accepted, and second bumps and new commits without a bump are still refused.
