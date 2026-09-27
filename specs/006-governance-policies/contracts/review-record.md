# Contract: Review Record and Feature Finish

## Review-record commit

Created on the feature branch after the merge review, with no staged changes.
Both trailers go in one final paragraph, so Git reads them as one trailer
block:

```sh
git commit --allow-empty -m 'chore(review): record develop merge review' \
  -m "Reviewed-by: Claude Code (claude-opus-5-5)
Reviewed-commit: $(git rev-parse HEAD)"
```

The header is any valid Conventional Commits header; the hook does not check
it (the commit-message check does).

## `pre-flow-feature-finish` checks, in order

Existing checks are unchanged and come first:

1. git-flow gave a branch and a base branch.
2. The current worktree is on the base branch (`develop`) and clean.
3. `develop` is an ancestor of the feature.
4. The feature is checked out in a worktree, and that worktree is clean.

New checks, before verification:

5. The feature tip has exactly one parent.
6. The tip's tree equals its parent's tree.
7. The tip has exactly one `Reviewed-by` trailer with a non-empty value.
8. The tip has exactly one `Reviewed-commit` trailer, and its value resolves to
   a commit equal to the tip's parent.

Then, unchanged:

9. `deno task --quiet verify` passes in the feature worktree.

## Refusal output

Each refusal exits non-zero and prints one line to standard error:

```text
Feature finish refused: <condition>; <what to do next>.
```

The messages for checks 5 to 8 name the feature branch and tell the agent to
run the merge review on the current tip and add a review-record commit whose
`Reviewed-commit` is that tip. A refusal changes no ref, worktree, index or
file.

## Success

git-flow creates the no-fast-forward merge with Git's default message; its
parents are `develop` and the review-record commit, and its tree equals the
reviewed commit's tree.
