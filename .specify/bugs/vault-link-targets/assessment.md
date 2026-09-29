# Bug Assessment: Vault page checks flag file paths in link targets

- **Slug**: vault-link-targets
- **Created**: 2026-09-29
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-35> (Linear CHE-35,
  read with `orca linear issue CHE-35 --json`; host `linear.app`, allowlisted)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

CHE-35, "Vault page checks flag file paths in link targets; work vault check
fails": after feature 017's page-rule checks (CHE-26) merged into `develop`
at `07ebf47`, `wiki-consistency check` fails on the work vault with 273
problems, so no commit can land there. The develop session found that most
come from link targets, the file paths of originals under the user's
documents folders, whose folder and file names are Korean. The user decided
in CHE-28 that link targets stay unchanged, and CHE-26's approved defaults
covered link text, not targets. The rest, 20 `time` and 2 `date` problems by
the develop session's count, are in page text outside link targets: fix the
pages, or the pattern if it is wrong. Separately, all four vaults'
`AGENTS.md` lack lines the schema template gained in feature 017.

## Symptom

The `english` and `school` page rules fail on Hangul in link destinations,
autolinks and bare URLs, which a page cannot change without breaking the
link. Expected: those rules skip link targets, as the `date` rule already
does, and the work vault's check passes once its remaining page text follows
the rules.

## Reproduction

On 2026-09-29 at `develop` `8ce9b2a`, with the develop worktree's
`packages/wiki-consistency` environment:

1. `uv run --project packages/wiki-consistency --frozen --offline --no-sync
   wiki-consistency check --wiki <name>` exits 0 on the `default`, `code`
   and `chat` vaults and exits 1 on `work` with 273 problems: 165 `english`,
   86 `school`, 20 `time` and 2 `date`.
2. With the link targets that `_dates` already skips blanked out before the
   check, and with the link-destination pattern extended to the `<…>` form
   (see below), the work vault keeps 31 problems: 20 `time`, 9 `school` and
   2 `date`. So 242 problems (165 `english`, 77 `school`) come only from link
   targets, not 251 as the report says.
3. A synthetic instance built with the package's own test fixtures
   (`tests/conftest.py`, `tests/test_rules.py`'s roster helper), whose
   `overview.md` holds one line each, gives:

   | Line                                                           | Rules that fail    |
   | -------------------------------------------------------------- | ------------------ |
   | `[Original](</home/user/Documents/가상별학교/기록 (1).pdf>)`   | `english`, `school` |
   | `[Original](/home/user/Documents/가상별학교/기록.pdf)`         | `english`, `school` |
   | `<file:///home/user/Documents/가상별학교/기록.pdf>`            | `english`, `school` |
   | `See https://example.invalid/가상별학교/기록 for it.`          | `english`, `school` |
   | ``Retrieved `2026-09-27T15:54:00.420Z`.``                      | `time`             |
   | `Retrieved 2026-09-27T15:54:00.420+09:00.`                     | `time`             |
   | `Batches of 30/30/30/30/30/25.`                                | `date`             |
   | `Word Master Middle School Basic.`                             | `school`           |

The remaining 31 work-vault problems, by cause:

- 20 `time`: ISO 8601 date-times with fractional seconds, in the form
  `2026-09-27T15:54:00.420Z`, in one page.
- 2 `date`: slash-separated count lists such as `30/30/30/30/30/25`, whose
  first three numbers match the `M/D/YY` date form.
- 9 `school`: a vocabulary book series title, romanized as `Word Master
  Middle School Basic` (also `Proficiency`, `Advanced`) and `Word Master High
  School COMPLETE`, which matches the romanized school name form.

## Suspected Code Paths

- `packages/wiki-consistency/src/wiki_consistency/rules.py:506-531` — the
  `english` loop skips only name spans and allowed quotes, and the `school`
  loop only allowed quotes; neither skips link targets.
- `packages/wiki-consistency/src/wiki_consistency/rules.py:85-94`
  (`_DATE_SKIP`) and `:304` (`_dates`) — the date rule's mask of link
  destinations, autolinks and bare URLs, which the other two rules could
  share. Its destination pattern, `(?:\\.|[^)\n])*`, ends at the first `)`,
  so a `<…>` destination whose path holds `(1)` is only partly masked.
- `packages/wiki-consistency/src/wiki_consistency/rules.py:95-110` (`_TIME`,
  `_OFFSET_PREFIX`) and `:353` (`_has_zone`) — `:SS` may not be followed by
  a decimal fraction, so in `15:54:00.420Z` the zone check sees `.420Z`
  instead of `Z`.
- `specs/017-vault-rule-checks/contracts/page-rules.md:99` — "Link text and
  code spans get no other exception"; `:108` limits the link-target skip to
  dates; `:130` defines a time without fractional seconds.

## Root Cause Hypothesis

Feature 017 gave only the date rule a link-target exception. Its spec
(`specs/017-vault-rule-checks/spec.md:240-241`) skipped link destinations
for dates because "the page cannot change" them, and the same holds for
Hangul folder and file names in the targets of links to originals. The
`time` form omits the decimal fraction that ISO 8601 and RFC 3339 allow
after seconds, so an ISO date-time with milliseconds and `Z` counts as a
time without a zone. Confidence: high; the reproduction isolates both.

## Proposed Remediation

**Preferred**: Build one mask of link targets per page from the date rule's
existing `_DATE_SKIP` patterns, and apply it to the `english` and `school`
rules as well as to `date`. Extend the link-destination pattern to
CommonMark's `<…>` form, which may hold `)`, so the whole destination is
masked. Let `:SS` in `_TIME` and `_OFFSET_PREFIX` take an optional `.`
and one or more digits. Link text stays checked, and the contact rules
(`phone`, `email`, `id-number`, `address`) and `time` keep checking link
targets.

The two count lists are page text, not dates, and the contract's `M/D/YY`
form has no calendar check, so the pages change: write them as comma lists.

For the 9 book-title lines the user chose, through the develop session on
2026-09-29, to change the pattern and keep the real titles: the school rule
flags only real school names, the roster's schools and their official
names, which the roster holds in Hangul. So the generic romanized school
name check (`_ROMANIZED_SCHOOL`) goes, and a roster school span holding a
CJK letter outside allowed quotes and link targets stays the rule. A
romanized name of a real school is left to the judgment step, which the
schema template already gives "school names in other forms".

**Alternatives**:

- Use a Markdown parser such as `markdown-it-py`, already in the
  environment, to find link destinations. Its inline tokens carry no source
  offsets, so mapping them back to page lines would need new local code;
  the existing patterns are smaller.
- Rewrite the work vault's links instead. CHE-28 decided that link targets
  stay unchanged, and the links must keep pointing at the originals.

**Files likely to change**:

- `packages/wiki-consistency/src/wiki_consistency/rules.py`
- `packages/wiki-consistency/tests/test_rules.py`
- `specs/017-vault-rule-checks/contracts/page-rules.md`, the schema template
  `plugins/work/skills/wiki-raw-import/assets/AGENTS.md`,
  `plugins/work/skills/wiki-consistency/SKILL.md` and
  `docs/architecture.md`, where they describe the rules

**Tests to add or update**:

- Hangul in a `(…)` destination, a `<…>` destination holding `)`, an
  autolink and a bare URL passes `english` and `school`; the same Hangul in
  link text still fails.
- A time with fractional seconds and `Z`, or with `+09:00`, passes `time`;
  one with fractional seconds and no zone still fails.
- A made-up title ending in `Middle School`, such as `Synthetic Words
  Middle School Basic`, passes `school`; a Hangul roster school name still
  fails.
- Each test fails without its fix.

## Risks & Considerations

- Hangul hidden in a link target is no longer reported. That is the intent:
  the target names an original the user keeps, and the page cannot change
  it. The judgment step still reads the page.
- A bare URL runs to the next space, so a URL followed directly by Korean
  text would hide that text; English pages make this rare.
- Once the fix lands, the vaults' `AGENTS.md` copy the updated template, so
  the template's rule summary must describe the new exception.
- Without the romanized pattern, `check` no longer catches a school written
  as an invented English name; only the judgment step can.

## Open Questions

- Resolved on 2026-09-29, relayed by the develop session: the user chose
  the time pattern fix and the page fix for the count lists as proposed, and
  for the book title a school rule that flags only real school names, with
  the titles unchanged.
