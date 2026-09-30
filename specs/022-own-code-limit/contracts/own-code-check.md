# Contract: Own-Code Check

## Invocation

`npm run own-code` from the repository root, with no arguments. Turborepo runs
it as `//#own-code` inside `npm run check`, so `npm run verify` and the
feature finish hook run it too.

## Output

On success, one line on standard output with the merge base's short hash,
both own-code sizes, the signed net change and the limit, naming the approving
file when an approval raised the limit. For example:

```text
Own code: 18418 lines at 0bc0c63 (merge base with develop), 18480 in the worktree; net +62 of 300 allowed.
Own code: 18418 lines at 0bc0c63 (merge base with develop), 18818 in the worktree; net +400 of 450 allowed (specs/030-example/spec.md).
```

The exact wording is not an acceptance criterion; the numbers are.

## Failure

When `net` exceeds the limit: the same numbers, then a message on standard
error that the branch adds more own code than allowed and that the user's
approval of a larger number is recorded as a line
`**Own-code limit**: <number>, approved by the user on <date>` added to the
feature's records under `specs/`, `.specify/bugs/` or
`.specify/assessments/`. Exit code 1.

When the check cannot measure (no `develop`, no merge base, a missing
`tools/scc` environment, an scc error): a non-zero exit with the failing
command's message.

## Side effects

None in the repository or the Git index. One temporary directory in the OS
temporary directory, removed before the run ends, on success and on failure.
