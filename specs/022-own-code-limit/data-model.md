# Data Model: Own-Code Limit per Feature

The check keeps no data between runs. These are the values one run derives.

## Tree

One of two file sets: the **merge base** (the commit `git merge-base HEAD
develop` names, unpacked into a temporary directory) or the **worktree**
(tracked files plus untracked files Git does not ignore). Only regular files
take part; symbolic links and files missing on disk drop out.

## File classification

Each regular file of a tree is exactly one of:

| Class | Rule | Counts? |
| --- | --- | --- |
| Not code | scc gives no language, or Linguist's type for scc's language is not `programming` | No |
| Test | Path has a `tests/` directory, or the name has `_test.` or `.test.` before an extension | No |
| Upstream copy | The file's SHA-256 is one of the tree's recorded upstream hashes | No |
| Own code | Any other code file | Yes, scc's code lines |

## Upstream hash set

All 64-digit lowercase hexadecimal tokens in the tree's upstream records:
files named `UPSTREAM.md` or `upstream.json` anywhere, and
`.specify/integrations/*.manifest.json`.

## Own-code size

The sum of scc's code lines (neither blank nor comment) over the tree's
own-code files.

## Approval line

A (path, line) pair: a file under `specs/`, `.specify/bugs/` or
`.specify/assessments/`, and a line in it that starts with
`**Own-code limit**: ` followed by a whole number. The branch's approvals are
the pairs in the worktree that are not in the merge base.

## Result

- `base`: own-code size of the merge base.
- `worktree`: own-code size of the worktree.
- `net`: `worktree - base`.
- `limit`: the largest of 300 and the numbers in the branch's approvals.
- Pass when `net <= limit`; otherwise fail.
