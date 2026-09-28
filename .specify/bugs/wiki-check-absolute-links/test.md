# Bug Verification: Wiki check rejects links to existing absolute local paths

- **Slug**: wiki-check-absolute-links
- **Tested**: 2026-09-29
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The assessment's reproduction no longer fails: a link to an existing file by
absolute path passes, while a missing file and a root-relative link still fail.
The same holds end to end through `wiki-consistency check` on a synthetic Wiki
instance, which failed without the fix. The full repository check passes with
the fix (`aae7784`, on `develop` `2262815`).

## Checks Performed

| Check                              | Command / Action                                                                                                                                                                                                                                             | Result  | Notes                                                                                                                                                                                               |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reproduction (post-fix)            | The assessment's steps: `doc_regions.regions.check` on a scratch `doc.md` linking by absolute path, in the `<…>` form, to an existing file, a missing file, and `/docs/architecture.md`                                                                      | pass    | No problem for the existing file; `File not found` for the missing file (line 2) and for `file:///docs/architecture.md` (line 3).                                                                   |
| Wiki check end to end              | A scratch pytest file using `packages/wiki-consistency/tests`' own `ready_instance` and `run_check`: `wiki/concepts/alpha.md` links by absolute path to an existing `original document.pdf` or to a missing `missing.pdf` under pytest's temporary directory | pass    | With the fix: exit 0 and `{"orphans": [], "problems": [], "stale_citations": []}` for the existing file; exit 1 and `wiki/concepts/alpha.md:12: …/missing.pdf: File not found` for the missing one. |
| Wiki check end to end, without fix | The same scratch test with `regions.py` from `d40d458`                                                                                                                                                                                                       | fail    | Exit 1 for the existing file: `wiki/concepts/alpha.md:12: … Cannot resolve root-relative link`. `regions.py` was restored afterwards.                                                               |
| New test                           | `PYTHONDONTWRITEBYTECODE=1 uv run --project packages/doc-regions --frozen --offline --no-sync pytest -p no:cacheprovider packages/doc-regions/tests/test_regions.py`                                                                                         | pass    | 38 passed with the fix; with `regions.py` from `d40d458`, `test_lychee_absolute_local_links` fails its two existing-target cases.                                                                   |
| Regression suite and checks        | `deno task verify --task che-23 --base 2262815 --plan plan.json` at `aae7784`, with `plan.json` as shown below the table                                                                                                                                     | pass    | Exit 0, workflow phase `VERIFIED`; it runs `deno task check`, which includes `test:doc-regions`, `test:wiki-consistency`, and `doc-regions:check` on the repository's own documents.                |
| The work vault's 294 links         | Not run                                                                                                                                                                                                                                                      | not-run | This task does not touch the real vaults; CHE-21 runs the Wiki check on the work vault before its commit.                                                                                           |

`plan.json`, a temporary file outside the repository that lists each task's
files for `deno task workflow` and `deno task verify`:

```json
{
  "tasks": [
    {
      "id": "che-23-root-dir",
      "files": [
        "packages/doc-regions/src/doc_regions/regions.py",
        "packages/doc-regions/tests/test_regions.py"
      ]
    },
    {
      "id": "che-23-records",
      "files": [
        ".specify/bugs/wiki-check-absolute-links/assessment.md",
        ".specify/bugs/wiki-check-absolute-links/fix.md",
        ".specify/bugs/wiki-check-absolute-links/test.md"
      ]
    }
  ]
}
```

## Output Excerpts

```text
# test_regions.py without the fix
FAILED …::test_lychee_absolute_local_links[existing file.txt-False]
FAILED …::test_lychee_absolute_local_links[existing doc.md#existing-heading-False]
2 failed, 3 passed, 33 deselected

# test_regions.py with the fix
38 passed
```

## Residual Risks

- The fix is not yet exercised on the work vault's 294 links; every one reported
  in CHE-23 has an existing target, which the new cases cover in kind (absolute
  path, `<…>` form, a space in the name).
- As the assessment notes, the repository's documents can now hold an absolute
  link to a file that exists on this machine and pass the check.

## Recommendation

Close the bug: the reproduction is fixed, both at the function the assessment
named and through the Wiki check itself, and the repository check passes.
