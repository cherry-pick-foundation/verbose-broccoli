# Bug Fix: Wiki check rejects links to existing absolute local paths

- **Slug**: wiki-check-absolute-links
- **Fixed**: 2026-09-29
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The lychee call in `doc_regions.regions.process` now passes lychee's own
`--root-dir /`, so a Markdown link to an absolute path resolves to that path on
the local filesystem. A link to an existing file or heading passes; a link to a
missing file or heading still fails, as feature 010's contract says. The
repository's document check uses the same call: a root-relative link such as
`/docs/x.md` still fails, now as a missing file.

## Changes

| File                                              | Change     | Notes                                                                  |
| ------------------------------------------------- | ---------- | ---------------------------------------------------------------------- |
| `packages/doc-regions/src/doc_regions/regions.py` | modified   | The lychee arguments gain `--root-dir /`.                              |
| `packages/doc-regions/tests/test_regions.py`      | added test | `test_lychee_absolute_local_links`, five cases, with its own fixtures. |

## Tests Added or Updated

- `packages/doc-regions/tests/test_regions.py::test_lychee_absolute_local_links`
  — a document links, by absolute path in the `[text](<path>)` form, to files
  under pytest's temporary directory but outside the check root, in a folder
  whose name has a space. An existing file and an existing heading pass; a
  missing file and a missing heading fail; the root-relative link
  `/missing-root-relative.md` fails.

## Local Verification

- The implementing Codex worker (gpt-6-luna, max effort; Orca dispatch
  `ctx_3c9287386309`) wrote the test first. Before the fix,
  `PYTHONDONTWRITEBYTECODE=1 uv run --project packages/doc-regions --frozen --offline --no-sync pytest -p no:cacheprovider packages/doc-regions/tests/test_regions.py`
  ended `2 failed, 36 passed`; after it, `38 passed`. The worker also reported
  `deno task test:doc-regions` (107 passed), `deno task test:wiki-consistency`
  (112 passed) and `deno task doc-regions:check` (`{"problems":[]}`) passing.
- The worker's `deno task verify` stopped at `test:plugin-skills` with
  `mise ERROR No version is set for shim: node`, a setting of its shell; the
  coordinator's `deno task verify` passed (see test.md).
- The coordinator reviewed the diff and repeated the before-and-after run at
  `aae7784` by restoring only `regions.py`: the two existing-target cases failed
  without the fix and all 38 tests passed with it.

## Deviations from Assessment

- None.

## Follow-ups

- None.
