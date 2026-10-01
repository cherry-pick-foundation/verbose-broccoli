# Bug Fix: Document judgment step fails on Hangul in docs/backfire.md

- **Slug**: doc-judgment-refusals
- **Fixed**: 2026-10-01
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

`doc-regions prepare` now spells every Hangul run of the unit text and of the
evidence diffs in Latin letters (lowercase, anyascii 0.3.3) before it builds
the requests, so no request holds Hangul and every unit is judged. The printed
`units` still hold the original text.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `packages/doc-regions/src/doc_regions/requests.py` | modified | `latin` replaces each Hangul run; `prepare` applies it to unit text for the requests, and to evidence ids and diffs before chunking. |
| `packages/doc-regions/pyproject.toml`, `uv.lock` | modified | Adds `anyascii==0.3.3`. |
| `packages/doc-regions/tests/test_requests.py` | modified, added test | `test_prepare_sends_hangul_in_latin_letters`. |
| `docs/architecture.md` | modified | The judgment-step bullet says requests spell Hangul in Latin letters. |

## Tests Added or Updated

- `test_requests.py::test_prepare_sends_hangul_in_latin_letters` — a unit and
  a changed file name and text with Hangul (composed syllables and a Jamo);
  no sent string holds Hangul, the spelled forms appear, and the printed
  units keep the Hangul. It fails without the change.
