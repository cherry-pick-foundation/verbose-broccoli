# Research: Own-Code Limit per Feature

## R1. Line counter

- **Decision**: scc 4.1.0, installed from PyPI's `scc-bin` 4.1.0 in a uv
  project under `tools/scc/`, run as `uv run --project tools/scc --frozen
  --offline --no-sync scc --by-file --format json --no-complexity <files>`.
- **Rationale**: scc is maintained, fast, and reports per-file code, comment
  and blank lines as JSON with the language it detected, including shell
  scripts without an extension (by shebang). It counts files passed on the
  command line even when a `.gitignore` names them, and skips symbolic links,
  so Git alone decides which files exist (checked 2026-09-30 in a scratch
  directory). `scc-bin` packages scc's release binaries as PyPI wheels, the
  same way `shellcheck-py` packages ShellCheck, which `tools/shellcheck/`
  already pins. `scc-bin` is a third-party repackaging (justin-yan/pybin), not
  scc's own release; `uv.lock` pins its wheel hashes.
- **Alternatives considered**: The npm package `cloc` 2.11.0 bundles cloc
  1.96 from 2022 and needs Perl; its `latest` tag points to an older
  `2.6.0-cloc`. cloc's `--git --diff` would compare commits directly, but not
  the uncommitted worktree. PyPI's `tokei` 12.1.2 has wheels only up to
  CPython 3.10, and the repository's tools run on 3.14. `pygount` would work
  but brings Pygments and is slower, with no gain.

## R2. What counts as code

- **Decision**: A file counts as code when GitHub Linguist's language data
  (`linguist-languages` 9.5.0, MIT) gives scc's language name, or one of
  Linguist's aliases for it, compared without case, the type `programming`.
- **Rationale**: The user confirmed this definition on 2026-09-30. Linguist
  already classes every language as programming, data, markup or prose, so the
  check keeps no language list. On `develop` at 0bc0c63, scc names 14
  languages; Python, TypeScript, JavaScript, Shell and Powershell (Linguist's
  PowerShell) are programming, and Markdown, Plain Text (Text), JSON, JSONL
  (an extension of JSON), YAML, TOML, CSV and SVG are not. Linguist has no
  "License" language, so license files do not count.
- **Known limit**: The match is by name. The develop merge review found
  that scc names some languages differently from Linguist, for example
  "C Header", "JSX" and "Korn Shell", so files in them would not count. The
  repository has none; matching by Linguist's extensions or interpreters
  would need more code in the check, which is not justified until such a
  language appears.
- **Alternatives considered**: Counting every language scc recognizes would
  count about 36,800 lines of Markdown and 24,000 of JSON on `develop`,
  mostly specs and fixtures. A hand-kept list of languages would need editing
  whenever a new language appears.

## R3. Upstream copies

- **Decision**: Collect every 64-digit lowercase hexadecimal token from the
  tree's upstream records: files named `UPSTREAM.md` or `upstream.json`, and
  `.specify/integrations/*.manifest.json`. A file whose SHA-256 is in that set
  is an upstream copy. Each tree uses its own records.
- **Rationale**: The user chose this on 2026-09-30 (option A): a copy counts
  as upstream only while its bytes match a recorded upstream hash, so a
  patched copy counts in full. Hash matching needs no record-specific path
  mapping. It covers the backfire rebuild's
  `packages/backfire/src/jev_judge_mcp/UPSTREAM.md` table (414 rows, all
  `unchanged` at 8a1d2f0; the rebuild worktree then held two uncommitted
  patched files) and Spec Kit's six core scripts, which still match their
  install manifest. A hash in a record whose file is absent matches
  nothing, so the jev-mcp TypeScript hashes in
  `packages/backfire/src/backfire/UPSTREAM.md` do not exempt the Python port.
- **Alternatives considered**: Parsing each record's path table (the user's
  option B) needs format-specific code and trusts the table's statuses.
  Counting only patch lines (option C) needs the unpatched upstream bytes,
  which the repository does not keep. A hand-kept exclusion list is ruled out
  by the issue.
- **Review duty**: A branch could add an upstream record holding hashes of
  its own files and so exempt them. The check cannot tell, so the develop
  merge review checks every upstream record a branch adds or changes.
- **Known gap**: Ponytail's hook modules and Spec Kit's extension scripts
  under `.specify/extensions/` are upstream copies without per-file hashes,
  so they count as own code in the baseline. A branch pays for them only if
  it changes them. The extension scripts match the copies in the pinned Spec
  Kit package (`tools/spec-kit`), checked for `create-new-feature-branch.sh`.

## R4. Tests

- **Decision**: A path is a test when it has a `tests/` directory or its file
  name matches `_test.` or `.test.` followed by an extension.
- **Rationale**: The user confirmed this on 2026-09-30. It covers every test
  file in the layout: `packages/*/tests/`, `plugins/code/tests/`,
  `scripts/*_test.ts`, `scripts/doc_sources_test.py` and
  `plugins/code/skills/clean-code/scripts/clean_code_test.ts`.

## R5. Measuring the merge base

- **Decision**: `git merge-base HEAD develop`; `git archive` that commit and
  unpack it with `tar` into a temporary directory; list its files with
  `git ls-tree -r -z --name-only`. The worktree's files come from
  `git ls-files -z --cached --others --exclude-standard`. Both lists keep only
  regular files, so symbolic links and deleted files drop out. Net change is
  worktree size minus merge-base size.
- **Rationale**: Measuring whole trees lets a record change reclassify an
  unchanged file, and makes the merge-base number the own-code size of
  `develop` when the branch is up to date. `git archive` writes nothing to the
  repository.
- **Alternatives considered**: Counting only changed files misses a record
  that makes an unchanged file an upstream copy. `git worktree add` writes
  worktree metadata under `.git`.

## R6. Approval lines

- **Decision**: In both trees, read the files under `specs/`,
  `.specify/bugs/` and `.specify/assessments/`, and collect lines that start
  with `**Own-code limit**: ` followed by a number. A worktree line whose
  text appears in no such file at the merge base is one of the branch's
  approvals. The limit is the largest of 300 and their numbers; the output
  names the approval's file. The develop merge review found that comparing
  (path, line) pairs, the first design, let a renamed records file make an
  old approval count again, so the comparison uses the line text alone.
- **Rationale**: The user confirmed "a line the branch adds to its Spec Kit
  records naming the approved number". Comparing the two trees reuses the
  file lists from R5 and includes uncommitted records; an approval already on
  `develop` never raises another branch's limit.

## R7. The develop merge path

- **Decision**: No change to `scripts/git-flow-hooks/pre-flow-feature-finish`.
- **Rationale**: The hook ends with `(cd "${feature_worktree}" && npm run
  --silent verify)`, and `verify` runs `npm run check`, where the new task
  runs. The hook first requires `develop` to be an ancestor of the feature,
  so there the merge base is the `develop` tip.

## R8. Failure to measure

- **Decision**: Let Git's or uv's error end the run with a non-zero exit;
  add no extra handling.
- **Rationale**: `git merge-base` without `develop` and `uv run` without the
  `tools/scc` environment both exit non-zero with their own message, which is
  enough to fail the check (FR-011). `npm run doctor` names the sync command
  for a missing environment.
