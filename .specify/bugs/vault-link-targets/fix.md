# Bug Fix: Vault page checks flag file paths in link targets

- **Slug**: vault-link-targets
- **Fixed**: 2026-09-29
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The `english` and `school` page rules now skip link targets, as the `date`
rule already did: one mask of link destinations, autolinks and bare URLs
serves all three. A destination may use CommonMark's angle-bracket form,
which holds spaces and `)`, or the bare form with one level of balanced
parentheses. After the develop merge reviews, the mask follows CommonMark
more closely: link targets inside code spans and code blocks stay checked,
a code span ends at a blank line, a link title is not part of the
destination, and a bare URL does not run past a destination's closing `)`.
A time may carry a decimal fraction after its seconds. The school rule
flags only roster school spans that hold a CJK letter, as the user decided:
the generic romanized school name check is gone.

## Changes

| File                                                        | Change        | Notes                                                                                                                                                      |
| ----------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `packages/wiki-consistency/src/wiki_consistency/rules.py`   | modified      | `_DATE_SKIP` becomes `_LINK_TARGETS`; `_mask_link_targets` builds the mask once per page for `english`, `school` and `date`, outside code blocks (markdown-it-py, `_MARKDOWN`) and code spans (`_CODE_SPANS`), and without link titles, with the helper `_blank`; `_TIME` and `_OFFSET_PREFIX` accept `.` and digits after `:SS`; `_ROMANIZED_SCHOOL` removed. |
| `packages/wiki-consistency/tests/test_rules.py`             | tests         | Five new test functions, then seven more and four cases from the merge reviews; the parametrized `school` case and the roster-school test now use only the Hangul roster school. |
| `specs/017-vault-rule-checks/spec.md`                       | specification | An amendment note; User Story 2, FR-009, FR-011, FR-012 and FR-013 follow the fix.                                                                         |
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
- Added after the develop merge review of the code (`9aebec6`), passing
  without code changes: `test_page_rules_check_time_and_phone_in_link_targets`
  (`time`, `phone`), a time and a phone number in a link destination still
  fail their rules; and the case
  `angle-bracket-destination-with-parenthesis` of
  `test_page_rules_skip_autolinks_and_link_destinations_for_dates`.
- Added after the develop merge review of the records (`b82681d`), failing
  before the change: `test_link_destinations_inside_code_fail_english`
  (`inline-code`, `fenced-code`, `indented-code`),
  `test_bare_url_inside_code_span_fails_english`, and
  `test_link_titles_are_checked_but_destinations_are_not` (`double-quoted`,
  `single-quoted`, `parenthesized`, `url-in-title`); plus the case
  `escaped-parenthesis-destination` of
  `test_english_and_school_skip_link_targets`.
- Added after the second review of the code (`ea34d9a`):
  `test_inline_code_span_does_not_cross_paragraphs`,
  `test_bare_url_pass_keeps_text_after_a_link_destination_visible` and the
  case `balanced-parentheses-in-destination`, which fail before the
  change; and, as guards, `test_page_rules_check_non_iso_date_inside_link_like_code`
  and the `email`, `id-number` and `address` cases of
  `test_page_rules_check_privacy_and_time_in_link_targets` (renamed from
  `test_page_rules_check_time_and_phone_in_link_targets`).
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
- For the mask narrowing, the Codex worker (dispatch `ctx_cdf799150898`)
  reported the same pytest command ending `8 failed, 107 passed` before the
  change and `115 passed` after, and `deno task test:wiki-consistency` (284
  passed), `deno task lint` and `deno task format:check` passing.
- For the second review's fixes, the Codex worker (dispatch
  `ctx_b86edca612df`) reported `3 failed, 119 passed` before and `122
  passed` after, and `deno task test:wiki-consistency` (291 passed), `deno
  task lint` and `deno task format:check` passing. The coordinator repeated
  both narrowing runs with `rules.py` restored from `bcffef4` (`8 failed,
  107 passed`) and from `b82681d` (`3 failed, 119 passed`); at `ea34d9a`,
  `122 passed`.
- `wiki-consistency check` from this worktree, read only, on the four
  vaults at `aba3ea1`, `b82681d` and `ea34d9a`: `default`, `code` and `chat`
  exit 0; `work` exits 1 with the 2 `date` problems that the assessment
  leaves to the pages, down from 273.

## Deviations from Assessment

- The assessment's preferred fix left the romanized school name check in
  place; the user's answer to its open question removed it.
- The assessment shared the date rule's mask as it was; the reviews then
  limited it to link targets outside code and without titles, and made it
  follow CommonMark's code spans and destinations more closely, which
  changes the date rule the same way.
- Left as they are after the second code review: a reference-style link
  definition (`[label]: <path>`) and a destination on the line after `](`
  are not link targets, so they still fail as ordinary text.

## Follow-ups

- After the finish: rewrite the work vault's 2 slash-separated count lists
  as comma lists, and bring the four vaults' `AGENTS.md` to the updated
  template, keeping each vault's declared topics.
