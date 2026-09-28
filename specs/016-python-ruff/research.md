# Research: Python Ruff Check

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Measurements below were taken on `develop` at `df912f4` on 2026-09-29 with
Ruff 0.16.9 run from uv's cache, outside the repository.

## Pinning

- **Decision**: A uv project `tools/ruff/` whose `pyproject.toml` requires
  `ruff==0.16.9` and uv 0.11.32, with a committed `uv.lock`, like
  `tools/spec-kit/`. Orca's setup script syncs it, `deno task doctor` checks
  it with the existing `checkUvEnvironment`, and the tasks run it with
  `uv run --project tools/ruff --frozen --offline --no-sync ruff …`.
- **Rationale**: It is how the repository already pins a Python CLI tool
  (`docs/architecture.md`, Spec Kit section), and the lock pins the wheel
  hashes. Ruff 0.16.9 is the latest release on 2026-09-29.
- **Alternatives considered**: A `dev` dependency in each package's
  `pyproject.toml` would pin Ruff three times and leave the scripts outside
  any package. `uvx ruff@0.16.9` pins no hashes and needs a network or a
  warm cache. Ruff has no official npm package, so Biome's route through
  Deno's npm support does not apply.

## Sources of the rule set

- **Decision**: Two Google sources, applied in this order:
  1. The guide's text at
     [pyguide.md](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).
     A rule the text requires is selected when Ruff has a stable rule for it.
  2. Google's [`pylintrc`](https://google.github.io/styleguide/pylintrc),
     which the guide's section 2.1 tells readers to run. Its enabled pylint
     messages are mapped to stable Ruff rules. `disable=R` turns off every
     refactor message, so Ruff's `PLR` rules stay off. Where the text
     requires something the `pylintrc` disables, the text decides; for
     example the `pylintrc` disables `missing-function-docstring`, but
     section 3.8.3 makes docstrings mandatory for public API.
  Rules neither source asks for are not selected, and preview rules are not
  used.
- **Rationale**: The issue asks for a configuration "from the Google Python
  style guide"; the `pylintrc` is part of the guide's own instructions, and
  the text is the more specific of the two.
- **Mapping tool**: [`pylint-to-ruff`](https://github.com/akx/pylint-to-ruff)
  0.3.0 converts a `pylintrc` into Ruff rule codes. Run against Google's
  `pylintrc` with pylint 4.0.9 and Ruff 0.16.9, it fails on a Ruff rule
  whose code is null; skipping such rules in a scratch wrapper outside the
  repository gives about 60 selected codes. It maps only by pylint code,
  name and a small alias table, so it misses equivalents in other Ruff
  linters, such as `dangerous-default-value` → `B006`,
  `missing-module-docstring` → `D100`, `invalid-name` → `N8xx`,
  `undefined-variable` → `F821` and `wrong-import-position` → `E402`. Ruff's
  pylint tracking issue,
  [astral-sh/ruff#970](https://github.com/astral-sh/ruff/issues/970), lists
  those equivalents. The implementation completes the table below from both
  and records the result; neither tool enters the repository.

## Settings from the guide's text

| Guide section | Setting |
| --- | --- |
| 3.2 Line length | `line-length = 80`; `E501` stays on, as the `pylintrc` sets `max-line-length=80`. Ruff's own exemptions (URL-only lines, pragma comments) match the guide's listed exceptions. |
| 3.4 Indentation | `indent-width = 4`; `.editorconfig` gets a `[*.py]` section with `indent_size = 4`, since its default is 2. |
| Background; 3.2 | The guide names Black or Pyink as formatters; `ruff format` is Black-compatible. The user chose to run `ruff format --check` (Clarifications). |
| 3.8 Docstrings | `pydocstyle.convention = "google"`. |
| 3.8, `pylintrc` `no-docstring-rgx` | No docstring is required for names matching `(__.*__\|main\|test.*\|.*test\|.*Test)$`: test files are exempt from `D1`, and `D105` and `D107` (magic methods, `__init__`) stay off. |
| 3.13 Imports formatting | `isort`: one import per line (`force-single-line`), except `typing`, `collections.abc` and `typing_extensions`; sorted by full module path (`force-sort-within-sections`); groups future, standard library, third party, repository. |
| 3.16 Naming | `pep8-naming` (`N`), with the `pylintrc`'s exempt names where Ruff offers a setting. |

## Measurements before the change

With a trial configuration (the settings above plus broad rule groups, tests
exempt from `D1`):

- The formatter would reformat 99 of the 120 tracked Python files. After
  that reformat, 251 lines remain over 80 columns, mostly strings and
  comments.
- Outside tests, 137 public modules, classes and functions lack a
  docstring, including 102 functions.
- Without the formatter, 2,164 lines are over 80 columns.

The trial selected more rule groups than this research allows, so the final
counts will be lower for the lint rules; the formatter and line counts hold.

## Scope of checked files

- **Decision**: One root `ruff.toml` covers the repository. It excludes
  `.specify/` (Spec Kit's bundled extensions, vendored upstream) by path;
  `tools/` holds no Python today, and ignored folders such as `.venv/` are
  skipped by Ruff's `.gitignore` support. Each package's `pyproject.toml`
  extends the root file (`[tool.ruff] extend = "../../ruff.toml"`), so Ruff
  infers that package's target version from its own `requires-python`
  (3.11, 3.13, 3.14). Two files sit outside packages:
  `scripts/doc_sources.py` runs in the doc-regions environment (3.13), and
  `plugins/work/skills/wiki-raw-import/scripts/raw_import.py` declares 3.14
  in its script header. The implementation checks whether Ruff reads that
  header; for what it does not infer, the root file names the version with
  `per-file-target-version` for those paths only.
- **Rationale**: One source of truth for the rules, and no second copy of
  each package's Python version.
- **Alternatives considered**: `per-file-target-version` in the root file
  repeats every package's version, which can drift from `requires-python`.

## Rule table

The implementation fills this table: one row per selected Ruff rule or rule
group and one per left-out or exempted rule, with its source (guide section
or `pylintrc` message) and, for left-out rules, the reason. The `ruff.toml`
comments carry the same reasons in one line each.
