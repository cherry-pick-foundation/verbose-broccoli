# Bug Verification: Rebase fixup or squash can raise the constitution version more than once

- **Slug**: constitution-squash-check
- **Tested**: 2026-09-28
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

A feature whose commits were combined by `git rebase -i` `fixup` or `squash`
into one commit that raises the constitution's version twice is now refused at
`git flow feature finish`, and so is an unsquashed `fixup!` commit that changes
the constitution. A feature with one correct bump still finishes. The new tests
fail without the fix, and `deno task verify` passes on the branch after merging
`develop` `7137315` (`fa2c2d1`).

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (post-fix) | The new `scripts/git_flow_test.ts` cases repeat the assessment's steps with a real `git rebase -i` (fixup and squash) and a real `git flow feature finish` | pass | The finish is refused and names the combined commit; no ref, worktree or file changes. |
| New tests fail without the fix | With `a89e26f`'s tests but `ae1cd7e`'s `pre-flow-feature-finish` and `commit-msg`: `deno task test:git-flow` and `deno task test:commit-msg` | fail, as expected | 3 of 20 and 1 of 5 failed; see Output Excerpts. |
| New / updated tests | `deno task test:git-flow`, `deno task test:commit-msg` on `a89e26f` | pass | 20 and 5 tests. |
| This branch's own constitution commit | For each commit from `git rev-list --no-merges --full-history develop..HEAD -- .specify/memory/constitution.md`, its message piped to `deno task commitlint` with `CONSTITUTION_VERSION_COMMIT` set, as the hook does | pass | `87be437` (`docs`, 1.0.0 to 1.0.1) passes. |
| Regression suite, lint, type-check | `deno task verify --task CHE-17` on `fa2c2d1`, after merging `develop` `7137315` | pass | Workflow `VERIFIED`. Two earlier runs failed on this new worktree's setup, not on the change: the `packages/doc-regions` environment was missing (`uv sync --locked --project packages/doc-regions`), and then `raw import: locked offline help and missing-instance errors` saw uv's one-time "Installed 1 package" message; it passed when run again. |

## Document Judgment Step

Run on `fa2c2d1` against `develop` `7137315`, as `deno task workflow`
requires before the develop merge review. `deno task doc-regions:prepare --
--base develop --max-evidence-chars 45000` gave three `backfire_verify`
requests (201 units) and one `backfire_classify` request. They went to
backfire's MCP server (`serve-mcp`, Hive `deepseek-ai/deepseek-v4.1-flash`)
through a scratch MCP client, because this session has no backfire MCP tools.
`deno task backfire:ready` reached the provider and passed its tool checks, but
its calibration sample answered 0.5. Two requests first failed with
`provider_error` and passed on a retry.

- No unit was `contradicted`.
- Target units flagged `review`, all standing: `docs/architecture.md:304-315`
  (this feature's finish-hook sentence), `333-338`, `340-345`, `353-364`,
  `371-375` and `382-384`. Each is `verified` at low confidence or
  `unsupported` because the feature's diff says nothing about it, and each
  still matches the code.
- `backfire_classify`: the one added target unit,
  `docs/architecture.md:365-370`, is an `agent_region` (0.98); no new
  mechanical region.
- Reported to the user, unchanged: `.specify/memory/constitution.md:169-198`,
  `199-200` and `244`, and `AGENTS.md:47` and `51-52`, flagged `review` with
  no contradiction; and 19 MemoryLint 1.5.1 `boundary` warnings
  (`deno task doc-regions:audit`) that suggest moving constitution lines,
  including the Sync Impact Report, into `AGENTS.md`.

## Output Excerpts

Without the fix, each refusal case fails because the finish succeeds:

```text
git-flow: fixup rebase that raises the constitution twice is refused ... FAILED
git-flow: squash rebase that raises the constitution twice is refused ... FAILED
git-flow: unsquashed fixup commit that changes the constitution is refused ... FAILED
error: AssertionError: Switched to branch 'develop'
Merging using strategy: merge
Successfully finished branch 'feature/flow-test' and updated 0 child base branches
```

Without the `unset` in the `commit-msg` hook, the commit with an inherited
`CONSTITUTION_VERSION_COMMIT` is accepted
(`scripts/commit_msg_test.ts:415`, `assert(!refused.success)` fails).

## Residual Risks

- The check runs from the `develop` worktree, where git-flow takes its hook,
  so it applies from the first finish after this fix is on `develop`.
- Merge commits are not checked (see fix.md, Follow-ups).

## Recommendation

Close the bug once the branch is merged into `develop`.
