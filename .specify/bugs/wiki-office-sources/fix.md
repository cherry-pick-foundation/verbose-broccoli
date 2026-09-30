# Bug Fix: Wiki check cannot convert XLSX, HWP and HWPX sources

- **Slug**: wiki-office-sources
- **Fixed**: 2026-09-30
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The Wiki check's evidence conversion now installs markitdown's own `xlsx`
extra, so markitdown's `XlsxConverter` reads workbooks, and reads HWP 5.0 and
HWPX sources through python-hwpx 6.6.0, the converter the user chose. A small
markitdown converter class passes `.hwp` and `.hwpx` payloads to python-hwpx
and returns its Markdown export; python-hwpx does all parsing. An HWP source
whose conversion emits `Hwp5ConversionWarning` keeps its text and is reported
as a partial conversion. A Codex worker (`gpt-6-luna`, effort `max`)
implemented the change in `c935ad3`; the coordinator reviewed it.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/wiki-consistency/pyproject.toml` | modified | `markitdown[docx,pdf,pptx,xlsx]==0.1.8` and `python-hwpx==6.6.0`. |
| `uv.lock` | modified | Adds python-hwpx 6.6.0, pandas 3.0.6, openpyxl 3.1.5 and their dependencies et-xmlfile 2.0.0, python-dateutil 2.9.0.post0 and tzdata 2026.4; lxml and numpy were already locked. |
| `packages/wiki-consistency/src/wiki_consistency/evidence.py` | modified | `HwpxConverter` (glue, registered beside `JsonConverter`); `convert` records `Hwp5ConversionWarning` as a `partial` entry and a `<revision>.partial.json` mark written before the text; `CONVERTER_VERSION` is now `0.1.8-hwpx-6.6.0-json-2`. |
| `packages/wiki-consistency/tests/test_evidence.py` | modified, added tests | See below. |
| `docs/architecture.md` | modified | markitdown reads XLSX and python-hwpx reads HWP and HWPX; of the formats CHE-34 names, only scanned PDFs stay unreadable. A payload no converter accepts is still `unsupported_format`. `8a63bf0` adds the partial-conversion mark after the code review. |
| `packages/wiki-consistency/tests/test_evidence.py` (`8a63bf0`) | modified | After the code review: the new conversion test asserts that its `.hwp` fixture starts with the compound-file signature. |
| `plugins/work/skills/wiki-consistency/SKILL.md` | modified | Step 2 reports `partial` revisions from `convert`; step 5 no longer names HWP as unreadable. |
| `licenses/THIRD_PARTY_NOTICES.md` | modified | markitdown's `xlsx` extra; a new python-hwpx entry (Apache-2.0). |

## Diff Highlights (optional)

```python
CONVERTER_VERSION = (
    f"{version('markitdown')}-hwpx-{version('python-hwpx')}-json-2"
)

class HwpxConverter(DocumentConverter):
    def accepts(self, file_stream, stream_info, **kwargs):
        return (stream_info.extension or "").lower() in {".hwp", ".hwpx"}

    def convert(self, file_stream, stream_info, **kwargs):
        document = HwpxDocument.open(file_stream.read())
        try:
            return DocumentConverterResult(document.text.markdown())
        finally:
            document.close()
```

Conversion runs inside `warnings.catch_warnings(record=True)` with
`Hwp5ConversionWarning` set to `always`, so the warning is captured even when
it repeats. The `partial` mark sits beside the text as
`<revision>.partial.json` and, like `.unreadable.json`, is written once and
never updated.

## Tests Added or Updated

- `test_evidence.py::test_convert_xlsx_hwp_and_hwpx_sources` — builds an XLSX
  workbook with openpyxl and an HWPX and an HWP 5.0 file with python-hwpx
  (the coordinator checked that python-hwpx writes the `.hwp` file with the
  compound-file signature, so the HWP 5.0 path is exercised), converts them
  with sockets blocked, and finds each file's synthetic text in the evidence.
- `test_evidence.py::test_unreadable_revisions_record_the_reason` — a `.foo`
  payload is now the `unsupported_format` case; the 8-byte `.hwp` file with
  only the compound-file signature is a `conversion_failed` case.
- `test_evidence.py::test_hwp5_conversion_warning_is_marked_and_reused` — a
  warning while opening an HWP payload keeps the text, writes the mark before
  the text, and lists the revision under `partial` on the first and the second
  run; its revision name contains a dot.
- `test_evidence.py::test_evidence_cache_path_uses_a_local_converter_revision`
  — also pins `CONVERTER_VERSION` to the markitdown and python-hwpx versions.

## Local Verification

- The worker ran `test_convert_xlsx_hwp_and_hwpx_sources` after adding the
  dependencies and before changing `evidence.py`: it failed with the HWP and
  HWPX revisions `unsupported_format`, and passed after the change.
- `npm run test:wiki-consistency` → 293 passed (worker; rerun by the
  coordinator on `c935ad3`, 293 passed in 90 s).
- `npm run verify -- --task che-34-office-sources --base f8ee808` → phase
  `VERIFIED`, exit code 0 (worker, on `c935ad3`).
- `npm run lint`, `npm run format:check`, `npm run docs:check` and
  `npm run doc-regions:check` passed (worker).

## Deviations from Assessment

- None in substance. The cache key's form is `<markitdown>-hwpx-<python-hwpx>-json-2`.
- Conversion now records every warning raised during a conversion and keeps
  only `Hwp5ConversionWarning`, so other warnings from converters are no longer
  printed on stderr during `convert`. Nothing reads them.

## Follow-ups

- The user added to CHE-34 on 2026-09-30 a check of python-hwpx's HWP-to-HWPX
  conversion against Hancom's official converter, for Exam4You files only; its
  result and any supplement are recorded in this folder when done.
- The old cache folder `markitdown-0.1.8-json-1` can be deleted by the user; it
  only counts toward the evidence budget.
