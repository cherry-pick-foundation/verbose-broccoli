# Bug Verification: Wiki check cannot convert XLSX, HWP and HWPX sources

- **Slug**: wiki-office-sources
- **Tested**: 2026-09-30
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The assessment's reproductions no longer fail: the synthetic workbook converts,
and every XLSX, HWP and HWPX revision the work vault's pages cite is now
readable evidence. The package's tests, lint and format checks pass. Only the
image-only PDFs stay unreadable, which is out of scope.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction, synthetic XLSX, before the fix | The assessment's scratch script (hand-built one-cell workbook, `evidence.convert`) in a `git archive` copy of `f8ee808` with its own environment | fail, as expected | `converted: 0`, reason `conversion_failed` |
| Reproduction, synthetic XLSX, after the fix | The same script on the fix, `c935ad3` | pass | `converted: 1`, no unreadable entry |
| New test before the fix | `f8ee808` plus the new `test_evidence.py`, `pytest packages/wiki-consistency/tests/test_evidence.py` | fail, as expected | Collection error: `ModuleNotFoundError: No module named 'hwpx'`; the fix's dependencies are missing |
| New test with dependencies but the old `evidence.py` | The worker's run of `test_convert_xlsx_hwp_and_hwpx_sources` before its source change | fail, as expected | HWP and HWPX revisions `unsupported_format` |
| Reproduction, work vault, after the fix | A scratch script outside the repository runs `convert --scope lint` on the work vault and counts cited revisions by payload type and status | pass | Counts below; no content or paths leave the machine |
| New and updated tests | `uv run --frozen --offline --no-sync --package wiki-consistency pytest packages/wiki-consistency/tests/test_evidence.py -q` | pass | 16 passed |
| Regression suite | `npm run test:wiki-consistency` | pass | 293 passed in 90 s |
| Lint and format | `npm run lint`; `npm run format:check` | pass | gts and ruff clean; 117 files formatted |
| Full verification | `npm run verify -- --task che-34-office-sources --base f8ee808` | pass | Worker's run on `c935ad3`: phase `VERIFIED`, exit 0; rerun on the merged result before the finish |

## Output Excerpts

Work vault, cited revisions by payload type, converter
`0.1.8-hwpx-6.6.0-json-2`:

| Payload type | Cited revisions | Page citations | Before the fix | After the fix |
| --- | --- | --- | --- | --- |
| XLSX | 1 | 2 | `conversion_failed` | readable |
| HWP | 4 | 8 | `unsupported_format` | readable |
| HWPX | 8 | 16 | `unsupported_format` | readable |
| PDF, image-only | 4 | 8 | `empty_text` | `empty_text` (out of scope) |
| PDF with text, DOCX, TSV | 78 | 105 | readable | readable |

13 previously unreadable cited revisions, cited 26 times by pages, are now
readable. The run converted 91 revisions into the new cache folder and found
4 unreadable, all image-only PDFs; no revision was listed under `partial`.

```text
converter: 0.1.8-hwpx-6.6.0-json-2
convert result: {'converted': 91, 'present': 0, 'unreadable': 4}
```

## Residual Risks

- python-hwpx reads HWP 5.0 and HWPX only; an HWP 3.x, encrypted or
  distribution-restricted file is recorded as `conversion_failed`. None of the
  work vault's 26 HWP files failed.
- Readable text is not a claim that python-hwpx's HWPX equals Hancom's own
  conversion. The user's goal of an exact match for Exam4You files is tracked
  separately as Linear CHE-40.
- The judgment step (backfire) was not run: readability is measured offline,
  and no paid call was needed to confirm the fix.

## Recommendation

Close CHE-34 after the develop merge review and the finish: the reproduction
is verified end to end on the work vault, and the remaining unreadable sources
are image-only PDFs, which the issue leaves out of scope.
