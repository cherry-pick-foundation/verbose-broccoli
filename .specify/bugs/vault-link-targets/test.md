# Bug Verification: Vault page checks flag file paths in link targets

- **Slug**: vault-link-targets
- **Tested**: 2026-09-29
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: partial

## Summary

The code fix holds: the assessment's synthetic reproduction no longer
fails, except the slash-separated count list, which stays a `date` failure
by design; the new tests fail without the fix and pass with it; and the
full repository check passes. The issue's expected result, the check
passing on all four vaults, is not reached yet: read only, the work vault's
273 problems drop to the 2 count lists, which the page fix after the
finish removes, and the other three vaults still pass.

## Checks Performed

| Check                        | Command / Action                                                                                                                                                                             | Result | Notes                                                                                                                                             |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reproduction (post-fix)      | The assessment's eight synthetic lines, each in `overview.md` of an instance built with the package's test fixtures, checked with `wiki_consistency.lint.check`                              | pass   | The four link-target lines, the two fractional-second times and the book title fail no page rule; `Batches of 30/30/30/30/30/25.` still fails `date`. |
| New tests, without fix       | `PYTHONDONTWRITEBYTECODE=1 uv run --project packages/wiki-consistency --frozen --offline --no-sync pytest -p no:cacheprovider -q packages/wiki-consistency/tests/test_rules.py` with `rules.py` from `6039981` | fail   | `7 failed, 96 passed`: the four link-target cases, the two zoned fractional-second cases and the book title.                                    |
| New tests, with fix          | The same command at `104c7d0`                                                                                                                                                                | pass   | `103 passed`.                                                                                                                                     |
| Review guard tests           | The same command at `9aebec6`                                                                                                                                                                | pass   | `106 passed`; the three added cases pass without code changes.                                                                                    |
| Mask narrowing, without      | The same command at `b82681d` with `rules.py` from `bcffef4`                                                                                                                                | fail   | `8 failed, 107 passed`: link-like text in code (three cases), a bare URL in a code span and four link titles.                                    |
| Mask narrowing, with         | The same command at `b82681d`                                                                                                                                                                | pass   | `115 passed`.                                                                                                                                     |
| Second review fixes, without | The same command at `ea34d9a` with `rules.py` from `b82681d`                                                                                                                                | fail   | `3 failed, 119 passed`: a code span across paragraphs, balanced parentheses in a destination, and text after a URL destination.                   |
| Second review fixes, with    | The same command at `ea34d9a`                                                                                                                                                                | pass   | `122 passed`.                                                                                                                                     |
| Regression suite and checks  | `deno task verify --task che-35 --base 8ce9b2a --plan /tmp/che-35-plan.json`, with the JSON below the table in that file, at `0a1f400` with this record's changes | pass   | Exit 0, workflow phase `VERIFIED`; it runs `deno task check`, which includes `test:wiki-consistency`. Earlier runs with the same task and base, the plan in the coordinator's scratch directory, passed at `aba3ea1` and `bcffef4` (the plan still without `spec.md`), `b82681d` (with record changes then pending) and `0a1f400`. |
| The four vaults, read only   | `uv run --project packages/wiki-consistency --frozen --offline --no-sync wiki-consistency check --wiki <name>` from this worktree at `aba3ea1`, `b82681d` and `ea34d9a`                     | partial | `default`, `code` and `chat` exit 0. `work` exits 1 with 2 `date` problems (the count lists), down from 273; the page fix follows the finish.     |

`/tmp/che-35-plan.json` held this JSON, which lists each task's files for
`deno task workflow` and `deno task verify`; to repeat the run, save it
there:

```json
{
  "tasks": [
    {
      "id": "che-35-rules",
      "files": [
        "packages/wiki-consistency/src/wiki_consistency/rules.py",
        "packages/wiki-consistency/tests/test_rules.py"
      ]
    },
    {
      "id": "che-35-docs",
      "files": [
        ".specify/bugs/vault-link-targets/assessment.md",
        ".specify/bugs/vault-link-targets/fix.md",
        ".specify/bugs/vault-link-targets/test.md",
        "specs/017-vault-rule-checks/spec.md",
        "specs/017-vault-rule-checks/contracts/page-rules.md",
        "plugins/work/skills/wiki-raw-import/assets/AGENTS.md",
        "plugins/work/skills/wiki-consistency/SKILL.md",
        "docs/architecture.md",
        "docs/examples/wiki/AGENTS.md"
      ]
    }
  ]
}
```

## Output Excerpts

```text
# test_rules.py without the fix
FAILED …::test_romanized_book_title_passes_school_rule
FAILED …::test_fractional_seconds_with_zone_pass_time[utc]
FAILED …::test_fractional_seconds_with_zone_pass_time[offset]
FAILED …::test_english_and_school_skip_link_targets[link-destination]
FAILED …::test_english_and_school_skip_link_targets[angle-bracket-destination]
FAILED …::test_english_and_school_skip_link_targets[autolink]
FAILED …::test_english_and_school_skip_link_targets[bare-url]
7 failed, 96 passed

# test_rules.py with the fix
103 passed

# after the two review rounds, at ea34d9a
122 passed

# wiki-consistency check, work vault, before (develop 8ce9b2a) and after
165 english, 86 school, 20 time, 2 date   ->   2 date
```

## Residual Risks

- Text in a link target outside code is no longer tested by the
  `english`, `school` and `date` rules; code spans, code blocks, link text
  and link titles are still checked.
- A school written in Latin letters other than its domain ID is left to the
  judgment step.

## Recommendation

Merge the fix. Keep CHE-35 open until, after the finish, the work vault's 2
count lists are rewritten, the four vaults' `AGENTS.md` follow the updated
template with one vault commit each, and the check passes on all four.
