# Bug Assessment: Wiki check rejects links to existing absolute local paths

- **Slug**: wiki-check-absolute-links
- **Created**: 2026-09-29
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-23> (Linear CHE-23,
  read with `orca linear issue CHE-23 --json`; host `linear.app`, allowlisted)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

CHE-23, "Wiki check rejects links to existing absolute local paths (lychee runs
without --root-dir)": the Wiki consistency check rejects Markdown links to
absolute local paths even when the file exists.
`packages/doc-regions/src/doc_regions/regions.py:193` runs
`lychee --offline
--include-fragments --no-progress --config /dev/null --format json --
<document>`
without `--root-dir`, so a link such as `[a](</home/user/Documents/a.pdf>)`
fails with "Cannot resolve root-relative link" although the file exists; a
`file:///home/user/Documents/a.pdf` link to the same file passes. Feature 010's
contract (`specs/010-wiki-consistency/contracts/commands.md:28`) says the check
fails on a link to a missing local file or heading. In the work vault (CHE-21),
294 check failures across 15 pages are such links, every target exists, and the
vault cannot be committed until the check passes. CHE-21's orchestrator reported
it.

## Symptom

`wiki-consistency check`, and `deno task doc-regions:check` for the repository's
own documents, report every Markdown link whose target is an absolute path as
broken, whether or not the file exists. Expected: a link to an existing file or
heading passes, and a link to a missing file or heading fails.

## Reproduction

Reproduced on 2026-09-29 in the worktree `feature-wiki-check-absolute-links` at
`develop` `2262815` (lychee 0.24.2, uv 0.11.32):

1. Create `exists.txt` in a scratch directory, and `root/doc.md` beside it
   containing `[a](<…/exists.txt>)` with the file's absolute path.
2. Call `doc_regions.regions.check(<root>, ['doc.md'], 'sources', <generators>)`
   through
   `uv run --project packages/doc-regions --frozen --offline --no-sync
   python`.
   It returns one problem for `doc.md` line 1:
   `Error building URL for
   "…/exists.txt" (Attribute: Some("href")): Cannot resolve root-relative link
   '…/exists.txt'`.
3. Running lychee directly with the same arguments on a file with nine links
   gives this, without and with `--root-dir /`:

   | Link                                                        | Without `--root-dir`              | With `--root-dir /`                             |
   | ----------------------------------------------------------- | --------------------------------- | ----------------------------------------------- |
   | absolute path to an existing file                           | Cannot resolve root-relative link | passes                                          |
   | absolute path with a space or Korean characters, `<…>` form | Cannot resolve root-relative link | passes                                          |
   | absolute path to an existing file, existing heading         | Cannot resolve root-relative link | passes                                          |
   | absolute path to a missing file                             | Cannot resolve root-relative link | File not found                                  |
   | absolute path to an existing file, missing heading          | Cannot resolve root-relative link | Cannot find fragment                            |
   | `/docs/architecture.md` (root-relative in a repository)     | Cannot resolve root-relative link | File not found (`file:///docs/architecture.md`) |
   | `file://` URL to an existing file                           | passes                            | passes                                          |
   | relative link to a missing file                             | File not found                    | File not found                                  |
   | relative link to an existing heading                        | passes                            | passes                                          |

## Suspected Code Paths

- `packages/doc-regions/src/doc_regions/regions.py:193-194` — the lychee
  arguments have no `--root-dir`. lychee 0.24.2's help says `--root-dir` "is
  required if absolute links appear in local files, otherwise those links will
  be flagged as errors", and that it resolves an absolute link by prefixing the
  root directory.
- `packages/wiki-consistency/src/wiki_consistency/lint.py:11` — the Wiki check
  imports `doc_regions.regions.check`, so it inherits the lychee arguments.
- `scripts/doc_regions.toml:5` — the same code checks the repository's targets,
  `README.md`, `docs/architecture.md` and `docs/backfire.md`.

## Root Cause Hypothesis

lychee treats a link that starts with `/` as root-relative and cannot resolve it
without a root directory, so it reports an error instead of checking the file.
Confidence: high; the reproduction shows the exact message from the report, and
adding `--root-dir /` alone makes existing targets pass while missing files and
headings still fail.

## Proposed Remediation

**Preferred**: add lychee's own `--root-dir /` to the arguments in `regions.py`.
An absolute link then resolves to the same path on the local filesystem, which
is what the Markdown means in a Wiki page. No new code is needed.

Effect on the repository's own documents, which the same call checks: a
root-relative link such as `/docs/architecture.md` still fails, now as "File not
found" for `file:///docs/architecture.md` instead of "Cannot resolve
root-relative link". None of the targets has such a link today (`grep -n
"](/"`
on them finds none). An absolute link to a file that exists on this machine,
such as a path under the home directory, now passes in those documents as it
does in a Wiki page.

**Alternatives**:

- Pass the root directory only from the Wiki check, through a new keyword of
  `regions.check`. It keeps absolute links failing in the repository's
  documents, at the cost of a parameter carried through `check` and `process`
  for one caller.
- Use the repository root as `--root-dir` for the repository's documents. It
  would accept root-relative links as GitHub renders them, which is a new
  feature, not this fix, and would break absolute paths in Wiki pages.

**Files likely to change**:

- `packages/doc-regions/src/doc_regions/regions.py`
- `packages/doc-regions/tests/test_regions.py`

**Tests to add or update**:

- A check of a document linking, by absolute path in the `<…>` form, to a file
  outside the root: an existing file and an existing heading pass; a missing
  file and a missing heading fail. The passing cases fail without the fix.
- A root-relative link such as `/missing.md` still fails.

## Risks & Considerations

- The repository's documents can now hold an absolute link to a file on this
  machine and pass the check, although such a link does not work for other
  readers. No check forbade it on purpose before; it failed only because lychee
  could not resolve it.
- The Wiki check still fails, as the contract says, when an absolute link's file
  or heading is missing; for CHE-21 that means a moved or deleted original
  document fails the vault's check.

## Open Questions

- None.
