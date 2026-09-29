# Bug Assessment: Wiki check cannot convert XLSX, HWP and HWPX sources

- **Slug**: wiki-office-sources
- **Created**: 2026-09-30
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-34> (Linear issue
  CHE-34, read with `orca linear issue CHE-34 --json`; host `linear.app`,
  allowlisted)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

CHE-34, "Wiki check cannot convert XLSX (and HWP) sources, leaving statements
unverifiable": Excel (XLSX) files admitted as raw evidence cannot be converted
for the Wiki consistency check, so every statement that cites one stays
unverifiable. It was seen on 2026-09-29 in CHE-21 and CHE-28 on the work vault,
where HWP, HWPX and image-only PDF sources were also unreadable. Expected: the
check's source conversion reads XLSX and, where an existing converter allows,
HWP and HWPX, so statements citing them can be judged. An existing converter
the repository already uses, such as markitdown, is preferred over new code,
per the reuse order in `AGENTS.md`. A format that no existing tool can read is
recorded as unsupported, with its reason.

The user's decision of 2026-09-30, relayed by the develop session: start with
HWP and adopt python-hwpx (PyPI `python-hwpx` 6.6.0, Apache-2.0, pure Python,
depends only on lxml) to read HWP 5.0 files, which it converts to HWPX, and to
read HWPX files, unless an existing converter in the repository already reads
HWPX; then fix XLSX. python-hwpx emits `Hwp5ConversionWarning` for HWP parts it
does not convert (for example master pages); such a source is recorded as a
partial conversion, not as a failure. The user rejected hwpforge (two weeks
old) and the Java hwp2hwpx (needs a Java runtime). Image-only PDFs stay out of
scope, because no converter the repository uses reads them without OCR.

Feature 010 left this open on purpose: its spec lists "Converting HWP files or
scanned PDFs, and adding Docling, until the user decides a source needs it" as
out of scope (`specs/010-wiki-consistency/spec.md:511`), and research R3 found
that markitdown refuses HWP (`specs/010-wiki-consistency/research.md:81-89`).
This issue is that decision for XLSX, HWP and HWPX.

## Symptom

`wiki-consistency convert` records a cited XLSX revision as
`conversion_failed` and a cited HWP or HWPX revision as `unsupported_format`,
so `prepare` treats every unit resting only on them as unverifiable. Expected:
these revisions convert to Markdown text in the evidence cache, and only
formats that no dependency can read stay unreadable.

## Reproduction

Reproduced on 2026-09-30 in the worktree `feature-wiki-office-sources` at
`develop` `ae8cadf` (markitdown 0.1.8, Python 3.14):

1. A scratch script outside the repository builds a one-cell XLSX workbook
   by hand (the five OOXML parts, cell text "Synthetic XLSX evidence"), puts it
   in a synthetic bag as `data/source.xlsx`, and calls
   `wiki_consistency.evidence.convert` through `uv run --frozen --offline
   --no-sync --package wiki-consistency python`.
2. The result is `converted: 0` and one unreadable entry with reason
   `conversion_failed` and detail "XlsxConverter threw
   MissingDependencyException ... the dependencies needed to read .xlsx files
   have not been installed. To resolve this error, include the optional
   dependency [xlsx] or [all] when installing MarkItDown."
3. In the same environment `openpyxl`, `pandas`, `xlrd` and `olefile` are not
   installed (`importlib.metadata.version` raises for each).

On the work vault, a scratch script ran `convert --scope lint` with the
current code and counted the cited revisions by payload type and status. It
read the vault and the evidence cache locally; only these counts leave them:

| Payload type | Cited revisions | Page citations | Status today |
| --- | --- | --- | --- |
| XLSX | 1 | 2 | `conversion_failed` (missing dependency) |
| HWP | 4 | 8 | `unsupported_format` |
| HWPX | 8 | 16 | `unsupported_format` |
| PDF, image-only | 4 | 8 | `empty_text` (out of scope) |
| PDF with text, DOCX, TSV | 78 | 105 | readable |

python-hwpx 6.6.0, installed in a scratch environment outside the repository,
opened every HWP (26) and HWPX (12) payload in the work vault's `raw/`, cited
or not, and exported Markdown with letters from each, with no error and no
`Hwp5ConversionWarning`, in 5.3 s in total.

## Suspected Code Paths

- `packages/wiki-consistency/pyproject.toml:13` — the dependency is
  `markitdown[docx,pdf,pptx]==0.1.8`, without the `xlsx` extra that installs
  `pandas` and `openpyxl`.
- `markitdown/converters/_xlsx_converter.py` (markitdown 0.1.8, installed
  package) — `XlsxConverter` accepts `.xlsx` and raises
  `MissingDependencyException` when `pandas` or `openpyxl` cannot be imported.
- `packages/wiki-consistency/src/wiki_consistency/evidence.py:210-211` — the
  converter is `MarkItDown()` plus the local `JsonConverter`; markitdown 0.1.8
  has no HWP or HWPX converter, so these payloads raise
  `UnsupportedFormatException` and get `unsupported_format` at
  `evidence.py:247-249`.
- `packages/wiki-consistency/src/wiki_consistency/evidence.py:22` —
  `CONVERTER_VERSION` is `f"{version('markitdown')}-json-1"` and names the
  cache folder. Marks are immutable (`evidence.py:225-232`), so while this value
  stays `0.1.8-json-1`, the `.unreadable.json` marks already written for the
  vault's XLSX, HWP and HWPX revisions would be reused after a fix.

## Root Cause Hypothesis

The Wiki check converts every non-text payload with markitdown, which was
installed without its `xlsx` extra, so its own XLSX converter cannot load
`pandas` and `openpyxl`. HWP and HWPX were never covered: markitdown has no
converter for them, and feature 010 deferred them to the user's decision.
Confidence: high; the reproduction shows markitdown's own message naming the
missing `[xlsx]` extra.

## Proposed Remediation

**Preferred**:

- XLSX: add markitdown's own `xlsx` extra, `markitdown[docx,pdf,pptx,xlsx]
  ==0.1.8`, so markitdown's `XlsxConverter` reads workbooks. No new code.
- HWP and HWPX: add `python-hwpx==6.6.0`, as the user decided, and register
  one small markitdown converter in `evidence.convert`, beside
  `JsonConverter`, that accepts `.hwp` and `.hwpx` payloads, opens them with
  python-hwpx's `HwpxDocument.open` (which reads HWP 5.0 by converting it to
  HWPX in memory, and HWPX directly) and returns python-hwpx's own Markdown
  export. The class is glue: python-hwpx does all parsing.
- Partial conversion: when opening an HWP file emits `Hwp5ConversionWarning`,
  keep the converted text and record the warning as a partial conversion.
  `convert` reports it in a new `partial` list (`id`, `revision`, `detail`),
  and a `<revision>.partial.json` mark beside the text keeps it for later runs,
  in the same way `.unreadable.json` marks keep unreadable reasons.
- Cache key: change `CONVERTER_VERSION` so that it includes python-hwpx's
  version and a new local revision. Revisions marked unreadable under the old
  key then convert again, and a later python-hwpx release converts again too.
  `search.index` already moves qmd's evidence collection to the new folder, and
  `search` refuses a collection built from the old one
  (`search.py:320-340`), so the next `index` run follows.
- Formats that still cannot be read keep today's reasons: an image-only PDF is
  `empty_text`, and a payload no converter accepts is `unsupported_format`.

**Alternatives**:

- Other HWP readers on PyPI, such as unhwp (MIT, a Rust library behind a
  pure-Python wheel), syhwp, hwpkit, hwp-hwpx-parser and hwp2md: the user chose
  python-hwpx; unhwp's wheel carries no native library, so how it obtains one
  was not checked.
- The markitdown plugin `markitdown-hwp` 0.1.0: it depends on `docpler`, which
  is under the Business Source License 1.1, is deprecated in favour of a
  package under the Elastic License v2, and publishes no Python 3.14 wheel.
  Rejected.
- pyhwp: AGPL-3.0, last released 2020, HWP only. Rejected.

**Files likely to change**:

- `packages/wiki-consistency/pyproject.toml`
- `uv.lock`
- `packages/wiki-consistency/src/wiki_consistency/evidence.py`
- `packages/wiki-consistency/tests/test_evidence.py`
- `licenses/THIRD_PARTY_NOTICES.md` (markitdown's extras; a new python-hwpx
  entry)
- `docs/architecture.md` (lines 233-238 and 259-262 say HWP files are
  unreadable)
- `plugins/work/skills/wiki-consistency/SKILL.md` (line 97 names HWP as
  unreadable; the new `partial` report)

**Tests to add or update**:

- A test that builds an XLSX workbook (with openpyxl), an HWPX file and an HWP
  5.0 file (with python-hwpx, which writes both) in the test's temporary
  folder, converts them offline and finds each file's synthetic text in the
  evidence. It fails without the fix: the XLSX revision is
  `conversion_failed` and the HWP and HWPX revisions are `unsupported_format`.
- `test_unreadable_revisions_record_the_reason`
  (`tests/test_evidence.py:241-285`) uses an 8-byte file named `.hwp` as its
  `unsupported_format` case. After the fix that file reaches python-hwpx and
  fails as damaged, so the test needs a payload type that nothing accepts for
  `unsupported_format`, and the short HWP file becomes a `conversion_failed`
  case.
- A test that an `Hwp5ConversionWarning` while opening an HWP payload keeps the
  text and lists the revision under `partial`, on the first run and, from the
  mark, on the next one.
- The cache folder name changes when python-hwpx's version changes.

## Risks & Considerations

- New dependencies: pandas and openpyxl through markitdown's extra, and
  python-hwpx with lxml. lxml 6.1.3 and numpy 2.5.3 are already in the root
  `uv.lock`. The lock changes in the root `uv.lock`, which CHE-39 may also
  change in parallel; the merge keeps both.
- The old cache folder `markitdown-0.1.8-json-1` stays on disk and counts
  toward the 1 GiB evidence budget until the user deletes it; deleting it only
  costs reconversion.
- python-hwpx reads HWP 5.0 and HWPX. An older HWP 3.x file, or an encrypted
  or distribution-restricted one, fails and is recorded as `conversion_failed`
  with python-hwpx's reason; none of the work vault's files failed.
- python-hwpx's source has no network client imports (a scratch `grep` for
  `requests`, `urllib.request`, `socket`, `http.client` and `httpx` in the
  installed package found none); the tests block sockets during conversion.
- Converted HWP text holds operational data, as other converted evidence does;
  it stays in the cache, never in the repository.

## Open Questions

- None. The user decided the converter on 2026-09-30.
