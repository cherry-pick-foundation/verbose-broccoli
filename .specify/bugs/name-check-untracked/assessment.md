# Bug Assessment: Name check fails on folders that Git ignores

- **Slug**: name-check-untracked
- **Created**: 2026-09-30
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-65> (Linear CHE-65,
  read with `orca linear issue CHE-65`)
- **Verdict**: valid
- **Severity**: high (`npm run verify` fails on `develop`, so every feature
  that merges `develop` is blocked)

## Report (summarized)

`npm run verify` fails at `//#lint:names` on `develop` (`4f12cb2`).
`.ls-lint.yml` skips a hand-kept list of cache folders, but ls-lint also
walks git-ignored `.venv` folders that uv creates on first use, such as
`packages/backfire/.venv`.

## Symptom

`npm run lint:names` reports names inside ignored folders, for example
non-kebab-case files under a `.venv`. Expected: only the repository's own
files are checked, meaning tracked files and untracked files that Git does not
ignore.

## Reproduction

1. In a worktree, create `mkdir -p packages/backfire/.venv/lib && touch
   packages/backfire/.venv/lib/Bad_Name.txt` (the path is in `.gitignore`'s
   `.venv/`).
2. `npm run lint:names` exits 1 and names the file.

The new test `scripts/lint-names-test.ts` reproduces it on a temporary Git
repository with an ignored `cache/` folder.

## Suspected Code Paths

- `.ls-lint.yml`, the `ignore:` list, and `package.json` `lint:names`
  (`timeout 60 ls-lint`). ls-lint 2.3.1 has no `.gitignore` support (its
  binary has no such string), so every ignored folder needs a list entry.

## Root Cause Hypothesis

The literal ignore list duplicates `.gitignore` and misses folders that appear
later. Confidence: high.

## Proposed Remediation

**Preferred**: ask Git for the ignored paths and pass them to ls-lint as
literal `ignore` entries through a second config read from standard input
(`-config .ls-lint.yml -config /dev/stdin`); ls-lint merges the two.
`git ls-files --others --ignored --exclude-standard --directory` lists each
ignored folder once. Then the `.ls-lint.yml` list keeps only `.git`.

**Alternative, rejected**: pass `git ls-files -z --cached --others
--exclude-standard` as file arguments. Tried on ls-lint 2.3.1 in a scratch
repository: with file arguments ls-lint does not check the names of the
folders that hold them (`Bad_Dir/a.txt` passes), so a non-kebab folder name
would go unchecked.

**Tests to add**: an ignored folder holding non-kebab names passes; an
untracked, unignored non-kebab file and folder fail. The first fails without
the fix.

## Risks & Considerations

- The security review's controls hold: the 60-second timeout stays, and the
  generated entries are literal names from Git, not wildcard patterns. A
  git-ignored path whose own name holds `*`, `?`, `[` or `{` would still be
  handed to ls-lint as an entry; ls-lint matched such a name literally in a
  scratch test (`[x]`), and no such name exists here.
- Git lists an ignored file in a non-ignored folder once by name; those files
  are skipped as well.

## Open Questions

None.
