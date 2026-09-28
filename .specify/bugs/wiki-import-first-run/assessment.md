# Bug Assessment: Wiki raw import test fails when the script environment is missing

- **Slug**: wiki-import-first-run
- **Created**: 2026-09-28
- **Source**: <https://linear.app/verbose-broccoli/issue/CHE-18> (Linear CHE-18,
  read with `orca linear issue CHE-18 --json`; host `linear.app`, allowlisted)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

CHE-18, "Wiki raw import test fails on a fresh worktree's first verify: uv
install line on stderr": the first `deno task verify` in a fresh worktree can
fail in `test:wiki-raw-import`. The test "raw import: locked offline help and
missing-instance errors" fails at `assertEquals(help.stderr, '')`, because
stderr holds uv's `Installed 1 package in 3ms`. The test runs the Wiki tool with
`uv run --locked --offline --script <script> --help`, and on the first run uv
builds the script's environment and reports it on stderr. Running
`deno task test:wiki-raw-import` again passes 41 of 41. Expected: the test
passes on the first run too, without weakening what it checks about the tool's
own output. CHE-9's orchestrator reported it after merging `develop` into
`feature/backfire-education`; the test came from CHE-7
(`specs/009-wiki-storage/`).

## Symptom

When uv has no environment for the raw import script yet, the test file's first
`uv run` builds one and prints `Installed 1 package in …` on stderr, so the
first test that asserts an empty stderr fails. The tool's own stderr is empty;
the line comes from uv.

## Reproduction

Reproduced on 2026-09-28 in the worktree `feature-wiki-import-first-run` at
`develop` `7137315` (uv 0.11.32, Deno 2.9.6, CPython 3.14.6):

1. `uv python find --offline --script <worktree>/plugins/work/skills/wiki-raw-import/scripts/raw_import.py`
   names this worktree's script environment,
   `~/.cache/uv/environments-v2/raw-import-6ed63e8ca35edc30/`. uv keys the
   environment by the script's path, so every worktree has its own.
2. With that environment present (Orca's setup had built it), the test passes.
3. Remove that one folder. `uv python find --offline --script …` now names the
   base interpreter, so the script has no environment.
4. `deno test --frozen --cached-only --no-prompt --allow-read --allow-write --allow-env --allow-run scripts/wiki_raw_import_test.ts`
   gives `FAILED | 40 passed | 1 failed`:

   ```text
   raw import: locked offline help and missing-instance errors => ./scripts/wiki_raw_import_test.ts:223:6
   error: AssertionError: Values are not equal.
       [Diff] Actual / Expected
   -   Installed 1 package in 1ms\n
       at file:///…/scripts/wiki_raw_import_test.ts:227:5
   ```

Running the tool by hand from a missing environment with the test's variables
(`UV_PYTHON`, `UV_NO_CONFIG=1`, `UV_PYTHON_DOWNLOADS=never`) shows the same
line; `UV_NO_PROGRESS=1` still shows it, and `uv run --quiet …` shows nothing.

A fresh worktree created today does not fail, because Orca's setup runs
`uv sync --locked --script` for the script (`orca.yaml:42`). The failure needs a
worktree whose script environment is missing: one set up before `daa028d` added
that setup line, as CHE-9's was (its folder dates from 00:26 KST on 2026-09-28,
`daa028d` from 01:55), or one whose uv cache entry was removed.

## Suspected Code Paths

- `scripts/wiki_raw_import_test.ts:94-103` — `Fixture.command` runs
  `uv run --locked --offline --script`, so uv's own messages share stderr with
  the tool's.
- `scripts/wiki_raw_import_test.ts:223-227` — the first test asserts
  `help.stderr` is empty; `init()` at lines 111-117 and `report()` at line 182
  assert the same for the other tests.
- `scripts/wiki_raw_import_test.ts:1019-1027` — the US5 tests build their own
  `uv run` command, but their first call, `init`, checks only the exit code, so
  a missing environment is built there without failing them.
- `orca.yaml:42` — setup prepares the script environment, which the test
  silently relies on (`specs/009-wiki-storage/research.md` notes this setup step
  is there for offline test runs).

## Root Cause Hypothesis

The tests treat the whole stderr of `uv run` as the tool's stderr. uv writes its
own progress report there when it has to build the script environment, so the
empty-stderr checks hold only when the environment already exists. Confidence:
high; the reproduction shows the exact line from the report.

## Proposed Remediation

**Preferred**: add uv's `--quiet` flag to the `uv run` arguments in
`Fixture.command`. uv then stops writing its own informational lines, while its
errors and the tool's stdout, stderr and exit code pass through unchanged, so
every existing assertion about the tool's output keeps its meaning. uv 0.11.32
has no environment variable for quiet output (`uv run --help` lists none for
`--quiet`), so the flag is the uv setting to use.

**Alternatives**:

- Build the environment first, with `uv sync --locked --offline --script` at the
  top of the test file. It keeps uv's warnings visible to the assertions, but
  adds a setup step, and any later uv message on stderr would fail the tests
  again.
- Remove the `Installed … package` line from stderr before asserting. Rejected:
  it filters text and breaks when uv changes its wording.

**Files likely to change**:

- `scripts/wiki_raw_import_test.ts`

**Tests to add or update**:

- No new test. The existing test "raw import: locked offline help and
  missing-instance errors" is the case that fails without the fix when the
  script environment is missing, as the reproduction shows. A test that empties
  the environment itself would have to delete from or add to the user's shared
  uv cache, or download bagit, and the tests run offline on their own fixtures.

## Risks & Considerations

- `--quiet` also hides uv's warnings in the tests. uv errors, such as a lock
  that no longer matches under `--locked`, still print and fail the run.
- The skill's procedure (`plugins/work/skills/wiki-raw-import/SKILL.md`) still
  shows uv's line on a first run; exit codes and stdout are unaffected, and this
  bug is limited to the test.

## Open Questions

- None.
