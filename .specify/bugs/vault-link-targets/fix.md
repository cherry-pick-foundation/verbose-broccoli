# Bug Fix: Vault page checks flag file paths in link targets

- **Slug**: vault-link-targets
- **Fixed**: 2026-09-29
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The `english` and `school` page rules now skip link targets, as the `date`
rule already did: one mask of link destinations, autolinks and bare URLs
serves all three. The link-destination pattern also accepts CommonMark's
angle-bracket form, so a path holding spaces or `)` is masked whole. A time
may carry a decimal fraction after its seconds. The school rule flags only
roster school spans that hold a CJK letter, as the user decided: the
generic romanized school name check is gone.

## Changes

| File                                                        | Change        | Notes                                                                                                                                                      |
| ----------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `packages/wiki-consistency/src/wiki_consistency/rules.py`   | modified      | `_DATE_SKIP` becomes `_LINK_TARGETS`; `_mask_link_targets` builds the mask once per page for `english`, `school` and `date`; `_TIME` and `_OFFSET_PREFIX` accept `.` and digits after `:SS`; `_ROMANIZED_SCHOOL` removed. |
| `packages/wiki-consistency/tests/test_rules.py`             | tests         | Four new tests; the parametrized `school` case and the roster-school test now use only the Hangul roster school.                                          |
| `specs/017-vault-rule-checks/contracts/page-rules.md`       | contract      | New "Link targets" section; the `english` and `school` rows name the exception; the romanized school name section is removed; times take a fraction.      |
| `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`      | template      | The rule summary drops the romanized school name and says which rules skip link targets.                                                                   |
| `plugins/work/skills/wiki-consistency/SKILL.md`             | skill         | The same two changes in the skill's rule summary.                                                                                                          |
| `docs/architecture.md`                                      | documentation | The same two changes in the Wiki check's description.                                                                                                      |

## Tests Added or Updated

- `test_english_and_school_skip_link_targets`, four cases
  (`link-destination`, `angle-bracket-destination`, `autolink`,
  `bare-url`): Hangul, including the fixture's roster school, in each kind
  of link target passes `english` and `school`.
- `test_hangul_in_link_text_still_fails_english`: the roster school as link
  text still fails `english`.
- `test_fractional_seconds_with_zone_pass_time` (`utc`, `offset`):
  `2026-09-27T15:54:00.420Z` and `…:00.420+09:00` pass `time`.
- `test_fractional_seconds_without_zone_fails_time`: `15:54:00.420` with no
  zone fails `time`.
- `test_romanized_book_title_passes_school_rule`: the made-up title
  `Synthetic Words Middle School Basic` passes `school`.
- `test_roster_school_name_fails_school_rule` (was
  `test_roster_school_name_and_romanized_school_fail_school_rule`) and the
  parametrized `school` case of
  `test_page_rules_report_the_page_and_line_without_the_match` now check the
  Hangul roster school only.

## Local Verification

- The implementing Codex worker (gpt-6-luna, max effort; Orca dispatch
  `ctx_28ab151953f1`) wrote the tests first and reported them failing before
  each fix and passing after, `deno task test:wiki-consistency` (272
  passed), `deno task lint` and `deno task format:check` passing.
- The coordinator reviewed the diff and repeated the run with only
  `rules.py` restored from `6039981`:
  `PYTHONDONTWRITEBYTECODE=1 uv run --project packages/wiki-consistency --frozen --offline --no-sync pytest -p no:cacheprovider -q packages/wiki-consistency/tests/test_rules.py`
  ended `7 failed, 96 passed` (the four link-target cases, the two zoned
  fractional-second cases and the book title); with the fix, `103 passed`.
- `wiki-consistency check` from this worktree, read only, on the four
  vaults: `default`, `code` and `chat` exit 0; `work` exits 1 with the 2
  `date` problems that the assessment leaves to the pages, down from 273.

## Deviations from Assessment

- The assessment's preferred fix left the romanized school name check in
  place; the user's answer to its open question removed it.

## Follow-ups

- After the finish: rewrite the work vault's 2 slash-separated count lists
  as comma lists, and bring the four vaults' `AGENTS.md` to the updated
  template, keeping each vault's declared topics.
