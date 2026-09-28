# Research: Python Ruff Check

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Measurements below were taken on `develop` at `df912f4` on 2026-09-29 with Ruff
0.16.9 run from uv's cache, outside the repository.

## Pinning

- **Decision**: A uv project `tools/ruff/` whose `pyproject.toml` requires
  `ruff==0.16.9` and uv 0.11.32, with a committed `uv.lock`, like
  `tools/spec-kit/`. Orca's setup script syncs it, `deno task doctor` checks it
  with the existing `checkUvEnvironment`, and the tasks run it with
  `uv run --project tools/ruff --frozen --offline --no-sync ruff …`.
- **Rationale**: It is how the repository already pins a Python CLI tool
  (`docs/architecture.md`, Spec Kit section), and the lock pins the wheel
  hashes. Ruff 0.16.9 is the latest release on 2026-09-29.
- **Alternatives considered**: A `dev` dependency in each package's
  `pyproject.toml` would pin Ruff three times and leave the scripts outside any
  package. `uvx ruff@0.16.9` pins no hashes and needs a network or a warm cache.
  Ruff has no official npm package, so Biome's route through Deno's npm support
  does not apply.

## Sources of the rule set

- **Decision**: Two Google sources, applied in this order:
  1. The guide's text at
     [pyguide.md](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).
     A rule the text requires is selected when Ruff has a stable rule for it.
  2. Google's [`pylintrc`](https://google.github.io/styleguide/pylintrc), which
     the guide's section 2.1 tells readers to run. Its enabled pylint messages
     are mapped to stable Ruff rules. `disable=R` turns off every refactor
     message, so Ruff's `PLR` rules stay off. Where the text requires something
     the `pylintrc` disables, the text decides; for example the `pylintrc`
     disables `missing-function-docstring`, but section 3.8.3 makes docstrings
     mandatory for public API. Rules neither source asks for are not selected,
     and preview rules are not used.
- **Rationale**: The issue asks for a configuration "from the Google Python
  style guide"; the `pylintrc` is part of the guide's own instructions, and the
  text is the more specific of the two.
- **Mapping tool**: [`pylint-to-ruff`](https://github.com/akx/pylint-to-ruff)
  0.3.0 converts a `pylintrc` into Ruff rule codes. Run against Google's
  `pylintrc` with pylint 4.0.9 and Ruff 0.16.9, it fails on a Ruff rule whose
  code is null; skipping such rules in a scratch wrapper outside the repository
  gives about 60 selected codes. It maps only by pylint code, name and a small
  alias table, so it misses equivalents in other Ruff linters, such as
  `dangerous-default-value` → `B006`, `missing-module-docstring` → `D100`,
  `invalid-name` → `N8xx`, `undefined-variable` → `F821` and
  `wrong-import-position` → `E402`. Ruff's pylint tracking issue,
  [astral-sh/ruff#970](https://github.com/astral-sh/ruff/issues/970), lists
  those equivalents. The implementation completes the table below from both and
  records the result; neither tool enters the repository.

## Settings from the guide's text

| Guide section                      | Setting                                                                                                                                                                                                                              |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 3.2 Line length                    | `line-length = 80`; `E501` stays on, as the `pylintrc` sets `max-line-length=80`. Ruff's own exemptions (URL-only lines, pragma comments) match the guide's listed exceptions.                                                       |
| 3.4 Indentation                    | `indent-width = 4`; `.editorconfig` gets a `[*.py]` section with `indent_size = 4`, since its default is 2.                                                                                                                          |
| Background; 3.2                    | The guide names Black or Pyink as formatters; `ruff format` is Black-compatible. The user chose to run `ruff format --check` (Clarifications).                                                                                       |
| 3.8 Docstrings                     | `pydocstyle.convention = "google"`.                                                                                                                                                                                                  |
| 3.8, `pylintrc` `no-docstring-rgx` | No docstring is required for names matching `(__.*__\|main\|test.*\|.*test\|.*Test)$`: test files are exempt from `D1`, and `D105` and `D107` (magic methods, `__init__`) stay off.                                                  |
| 3.13 Imports formatting            | `isort`: one import per line (`force-single-line`), except `typing`, `collections.abc` and `typing_extensions`; sorted by full module path (`force-sort-within-sections`); groups future, standard library, third party, repository. |
| 3.16 Naming                        | `pep8-naming` (`N`), with the `pylintrc`'s exempt names where Ruff offers a setting.                                                                                                                                                 |

## Measurements before the change

With a trial configuration (the settings above plus broad rule groups, tests
exempt from `D1`):

- The formatter reported 99 files to reformat. After that reformat, 251
  lines remained over 80 columns, mostly strings and comments.
- Outside tests, 137 public modules, classes and functions lack a docstring,
  including 102 functions.
- Without the formatter, 2,164 lines are over 80 columns.

The trial selected more rule groups than this research allows and did not yet
give each package its own Python version, so its counts differ from the final
configuration's. With the final configuration, the format-only commit
`d2c4e58` changed 106 of the 115 Python files outside `.specify/`, and 394
lines remained over 80 columns among 813 lint findings.

## Scope of checked files

- **Decision**: One root `ruff.toml` covers the repository. It excludes
  `.specify/extensions/` (Spec Kit's bundled extensions, vendored upstream) by path;
  `tools/` holds no Python today, and ignored folders such as `.venv/` are
  skipped by Ruff's `.gitignore` support. Each package's `pyproject.toml`
  extends the root file (`[tool.ruff] extend = "../../ruff.toml"`), so Ruff
  infers that package's target version from its own `requires-python` (3.11,
  3.13, 3.14). Two files sit outside packages: `scripts/doc_sources.py` runs in
  the doc-regions environment (3.13), and
  `plugins/work/skills/wiki-raw-import/scripts/raw_import.py` declares 3.14 in
  its script header. The implementation checks whether Ruff reads that header;
  for what it does not infer, the root file names the version with
  `per-file-target-version` for those paths only.
- **Rationale**: One source of truth for the rules, and no second copy of each
  package's Python version.
- **Alternatives considered**: `per-file-target-version` in the root file
  repeats every package's version, which can drift from `requires-python`.

## Rule table

| Ruff rule or group                                | Source                                                                                                                                |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `D` family, stable rules except `D105` and `D107` | Google guide §3.8; Pylint docstring messages `empty-docstring`, `missing-module-docstring`, and `missing-class-docstring`.            |
| `N` family, all stable rules                      | Google guide §3.16; Pylint naming messages `invalid-name`, `bad-classmethod-argument`, `no-self-argument`, and `non-ascii-file-name`. |
| `A001`                                            | Pylint: `redefined-builtin`.                                                                                                          |
| `A002`                                            | Pylint: `redefined-builtin` for arguments.                                                                                            |
| `A003`                                            | Pylint: `redefined-builtin` for attributes.                                                                                           |
| `A004`                                            | Pylint: `redefined-builtin` for imports.                                                                                              |
| `A006`                                            | Pylint: `redefined-builtin` for lambda arguments.                                                                                     |
| `ARG001`                                          | Pylint: `unused-argument` in functions.                                                                                               |
| `ARG002`                                          | Pylint: `unused-argument` in methods.                                                                                                 |
| `ARG003`                                          | Pylint: `unused-argument` in class methods.                                                                                           |
| `ARG004`                                          | Pylint: `unused-argument` in static methods.                                                                                          |
| `ARG005`                                          | Pylint: `unused-argument` in lambdas.                                                                                                 |
| `B002`                                            | Pylint: `nonexistent-operator`.                                                                                                       |
| `B006`                                            | Pylint: `dangerous-default-value`.                                                                                                    |
| `B007`                                            | Pylint: `unused-variable` for loop targets.                                                                                           |
| `B012`                                            | Pylint: `lost-exception`.                                                                                                             |
| `B014`                                            | Pylint: `duplicate-except` for duplicate exception types.                                                                             |
| `B018`                                            | Pylint: `expression-not-assigned`, `pointless-statement`, `pointless-string-statement`.                                               |
| `B019`                                            | Pylint: `method-cache-max-size-none`.                                                                                                 |
| `B023`                                            | Pylint: `cell-var-from-loop`.                                                                                                         |
| `B026`                                            | Pylint: `keyword-arg-before-vararg`.                                                                                                  |
| `B025`                                            | Pylint: `duplicate-except` for repeated exception handlers.                                                                           |
| `B030`                                            | Pylint: `catching-non-exception`.                                                                                                     |
| `B033`                                            | Pylint: `duplicate-value`.                                                                                                            |
| `B904`                                            | Pylint: `raise-missing-from`.                                                                                                         |
| `BLE001`                                          | Pylint: `broad-exception-caught`.                                                                                                     |
| `E401`                                            | Pylint: `multiple-imports`.                                                                                                           |
| `E402`                                            | Google guide §2.2; Pylint message `wrong-import-position`.                                                                            |
| `E501`                                            | Google guide §3.2; Pylint message `line-too-long`.                                                                                    |
| `E701`                                            | Pylint: `multiple-statements`.                                                                                                        |
| `E702`                                            | Pylint: `multiple-statements`.                                                                                                        |
| `E703`                                            | Pylint: `unnecessary-semicolon`.                                                                                                      |
| `E711`                                            | Pylint: `singleton-comparison` with `None`.                                                                                           |
| `E712`                                            | Pylint: `singleton-comparison`.                                                                                                       |
| `E713`                                            | Pylint: `unnecessary-negation` for membership tests.                                                                                  |
| `E714`                                            | Pylint: `unnecessary-negation` for identity tests.                                                                                    |
| `E721`                                            | Pylint: `unidiomatic-typecheck`.                                                                                                      |
| `E722`                                            | Pylint: `bare-except`.                                                                                                                |
| `E731`                                            | Pylint: `unnecessary-lambda-assignment`.                                                                                              |
| `F401`                                            | Pylint: `unused-import`.                                                                                                              |
| `F403`                                            | Pylint: `wildcard-import`.                                                                                                            |
| `F404`                                            | Pylint: `misplaced-future`.                                                                                                           |
| `F501`                                            | Pylint: `truncated-format-string`.                                                                                                    |
| `F502`                                            | Pylint: `format-needs-mapping`.                                                                                                       |
| `F504`                                            | Pylint: `unused-format-string-key`.                                                                                                   |
| `F506`                                            | Pylint: `mixed-format-string`.                                                                                                        |
| `F507`                                            | Pylint: `unused-format-string-argument`.                                                                                              |
| `F521`                                            | Pylint: `bad-format-string`.                                                                                                          |
| `F522`                                            | Pylint: `too-many-format-args`.                                                                                                       |
| `F524`                                            | Pylint: `missing-format-argument-key`, `missing-format-string-key`, `too-few-format-args`.                                            |
| `F525`                                            | Pylint: `format-combined-specification`.                                                                                              |
| `F541`                                            | Pylint: `f-string-without-interpolation`, `format-string-without-interpolation`.                                                      |
| `F601`                                            | Pylint: `duplicate-key`.                                                                                                              |
| `F622`                                            | Pylint: `too-many-star-expressions`.                                                                                                  |
| `F631`                                            | Pylint: `assert-on-tuple`.                                                                                                            |
| `F701`                                            | Pylint: `not-in-loop`.                                                                                                                |
| `F702`                                            | Pylint: `not-in-loop`.                                                                                                                |
| `F704`                                            | Pylint: `yield-outside-function`.                                                                                                     |
| `F706`                                            | Pylint: `return-outside-function`.                                                                                                    |
| `F811`                                            | Pylint: `function-redefined`, `reimported`.                                                                                           |
| `F821`                                            | Pylint: `undefined-variable`.                                                                                                         |
| `F822`                                            | Pylint: `undefined-all-variable`.                                                                                                     |
| `F823`                                            | Pylint: `used-before-assignment`.                                                                                                     |
| `F841`                                            | Pylint: `unused-variable`.                                                                                                            |
| `F842`                                            | Pylint: `unused-variable` for annotated locals.                                                                                      |
| `F901`                                            | Pylint: `notimplemented-raised`.                                                                                                      |
| `G001`                                            | Pylint: `logging-format-interpolation`.                                                                                               |
| `G002`                                            | Pylint: `logging-not-lazy`.                                                                                                           |
| `G004`                                            | Pylint: `logging-fstring-interpolation`.                                                                                              |
| `I001`                                            | Google guide §3.13; Pylint message `ungrouped-imports`.                                                                               |
| `PLC0105`                                         | Pylint: `typevar-name-incorrect-variance`.                                                                                            |
| `PLC0131`                                         | Pylint: `typevar-double-variance`.                                                                                                    |
| `PLC0132`                                         | Pylint: `typevar-name-mismatch`.                                                                                                      |
| `PLC0205`                                         | Pylint: `single-string-used-for-slots`.                                                                                               |
| `PLC0206`                                         | Pylint: `consider-using-dict-items`.                                                                                                  |
| `PLC0207`                                         | Pylint: `use-maxsplit-arg`.                                                                                                           |
| `PLC0208`                                         | Pylint: `use-sequence-for-iteration`.                                                                                                 |
| `PLC0414`                                         | Pylint: `useless-import-alias`.                                                                                                       |
| `PLC0415`                                         | Pylint: `import-outside-toplevel`.                                                                                                    |
| `PLC1802`                                         | Pylint: `use-implicit-booleaness-not-len`.                                                                                            |
| `PLC2401`                                         | Pylint: `non-ascii-name`.                                                                                                             |
| `PLC2403`                                         | Pylint: `non-ascii-module-import`.                                                                                                    |
| `PLC3002`                                         | Pylint: `unnecessary-direct-lambda-call`.                                                                                             |
| `PLE0100`                                         | Pylint: `init-is-generator`.                                                                                                          |
| `PLE0101`                                         | Pylint: `return-in-init`.                                                                                                             |
| `PLE0115`                                         | Pylint: `nonlocal-and-global`.                                                                                                        |
| `PLE0116`                                         | Pylint: `continue-in-finally`.                                                                                                        |
| `PLE0117`                                         | Pylint: `nonlocal-without-binding`.                                                                                                   |
| `PLE0118`                                         | Pylint: `used-prior-global-declaration`.                                                                                              |
| `PLE0237`                                         | Pylint: `assigning-non-slot`.                                                                                                         |
| `PLE0241`                                         | Pylint: `duplicate-bases`.                                                                                                            |
| `PLE0302`                                         | Pylint: `unexpected-special-method-signature`.                                                                                        |
| `PLE0303`                                         | Pylint: `invalid-length-returned`.                                                                                                    |
| `PLE0304`                                         | Pylint: `invalid-bool-returned`.                                                                                                      |
| `PLE0305`                                         | Pylint: `invalid-index-returned`.                                                                                                     |
| `PLE0307`                                         | Pylint: `invalid-str-returned`.                                                                                                       |
| `PLE0308`                                         | Pylint: `invalid-bytes-returned`.                                                                                                     |
| `PLE0309`                                         | Pylint: `invalid-hash-returned`.                                                                                                      |
| `PLE0604`                                         | Pylint: `invalid-all-object`.                                                                                                         |
| `PLE0605`                                         | Pylint: `invalid-all-format`.                                                                                                         |
| `PLE0643`                                         | Pylint: `potential-index-error`.                                                                                                      |
| `PLE0704`                                         | Pylint: `misplaced-bare-raise`.                                                                                                       |
| `PLE1132`                                         | Pylint: `repeated-keyword`.                                                                                                           |
| `PLE1142`                                         | Pylint: `await-outside-async`.                                                                                                        |
| `PLE1205`                                         | Pylint: `logging-too-many-args`.                                                                                                      |
| `PLE1206`                                         | Pylint: `logging-too-few-args`.                                                                                                       |
| `PLE1300`                                         | Pylint: `bad-format-character`.                                                                                                       |
| `PLE1307`                                         | Pylint: `bad-string-format-type`.                                                                                                     |
| `PLE1310`                                         | Pylint: `bad-str-strip-call`.                                                                                                         |
| `PLE1507`                                         | Pylint: `invalid-envvar-value`.                                                                                                       |
| `PLE1519`                                         | Pylint: `singledispatch-method`.                                                                                                      |
| `PLE1520`                                         | Pylint: `singledispatchmethod-function`.                                                                                              |
| `PLE1700`                                         | Pylint: `yield-inside-async-function`.                                                                                                |
| `PLE2502`                                         | Pylint: `bidirectional-unicode`.                                                                                                      |
| `PLE2510`                                         | Pylint: `invalid-character-backspace`.                                                                                                |
| `PLE2512`                                         | Pylint: `invalid-character-sub`.                                                                                                      |
| `PLE2513`                                         | Pylint: `invalid-character-esc`.                                                                                                      |
| `PLE2514`                                         | Pylint: `invalid-character-nul`.                                                                                                      |
| `PLE2515`                                         | Pylint: `invalid-character-zero-width-space`.                                                                                         |
| `PLW0108`                                         | Pylint: `unnecessary-lambda`.                                                                                                         |
| `PLW0127`                                         | Pylint: `self-assigning-variable`.                                                                                                    |
| `PLW0128`                                         | Pylint: `redeclared-assigned-name`.                                                                                                   |
| `PLW0129`                                         | Pylint: `assert-on-string-literal`.                                                                                                   |
| `PLW0131`                                         | Pylint: `named-expr-without-context`.                                                                                                 |
| `PLW0133`                                         | Pylint: `pointless-exception-statement`.                                                                                              |
| `PLW0177`                                         | Pylint: `nan-comparison`.                                                                                                             |
| `PLW0211`                                         | Pylint: `bad-staticmethod-argument`.                                                                                                  |
| `PLW0245`                                         | Pylint: `super-without-brackets`.                                                                                                     |
| `PLW0602`                                         | Pylint: `global-variable-not-assigned`.                                                                                               |
| `PLW0604`                                         | Pylint: `global-at-module-level`.                                                                                                     |
| `PLW0642`                                         | Pylint: `self-cls-assignment`.                                                                                                        |
| `PLW0711`                                         | Pylint: `binary-op-exception`.                                                                                                        |
| `PLW1501`                                         | Pylint: `bad-open-mode`.                                                                                                              |
| `PLW1507`                                         | Pylint: `shallow-copy-environ`.                                                                                                       |
| `PLW1508`                                         | Pylint: `invalid-envvar-default`.                                                                                                     |
| `PLW1509`                                         | Pylint: `subprocess-popen-preexec-fn`.                                                                                                |
| `PLW1510`                                         | Pylint: `subprocess-run-check`.                                                                                                       |
| `PLW2101`                                         | Pylint: `useless-with-lock`.                                                                                                          |
| `PLW3301`                                         | Pylint: `nested-min-max`.                                                                                                             |
| `PIE790`                                          | Pylint: `unnecessary-ellipsis`.                                                                                                        |
| `S102`                                            | Pylint: `exec-used`.                                                                                                                  |
| `S113`                                            | Pylint: `missing-timeout`.                                                                                                            |
| `S307`                                            | Pylint: `eval-used`.                                                                                                                  |
| `SIM118`                                          | Pylint: `consider-iterating-dictionary`.                                                                                              |
| `SIM107`                                          | Pylint: `return-in-finally`.                                                                                                          |
| `SIM201`                                          | Pylint: `unnecessary-negation` for equality tests.                                                                                    |
| `SIM202`                                          | Pylint: `unnecessary-negation` for inequality tests.                                                                                  |
| `SIM208`                                          | Pylint: `unnecessary-negation` for double negations.                                                                                  |
| `SLF001`                                          | Pylint: `protected-access`.                                                                                                           |
| `TID252`                                          | Google guide §2.2.4; Pylint message `relative-beyond-top-level`.                                                                      |
| `T100`                                            | Pylint: `forgotten-debug-statement`.                                                                                                  |
| `TRY002`                                          | Pylint: `broad-exception-raised`.                                                                                                     |
| `TRY203`                                          | Pylint: `try-except-raise`.                                                                                                           |
| `UP025`                                           | Pylint: `redundant-u-string-prefix`.                                                                                                  |
| `UP031`                                           | Pylint: `consider-using-f-string` for printf-style formatting.                                                                       |
| `UP032`                                           | Pylint: `consider-using-f-string` for `.format` calls.                                                                                |
| `UP034`                                           | Pylint: `superfluous-parens`.                                                                                                         |
| `RUF059`                                          | Pylint: `unused-variable` for unpacked values.                                                                                        |
| `W291`                                            | Pylint: `trailing-whitespace`.                                                                                                        |
| `W292`                                            | Pylint: `missing-final-newline`.                                                                                                      |
| `W605`                                            | Pylint: `anomalous-backslash-in-string`.                                                                                              |

The scratch conversion uses `pylint-to-ruff` 0.3.0 with Pylint 4.0.9 and Ruff
0.16.9; neither tool was added to the repository. The converter yields 137
distinct codes, including removed E999, and misses cross-linter equivalents. The
final selection supplements its output with Ruff issue
[#970](https://github.com/astral-sh/ruff/issues/970) and the guide text. Of the
297 messages enabled by Google’s pylintrc, 152 have a selected stable Ruff
counterpart, six have only preview candidates, E999 is removed, and 138 have no
stable equivalent. The mappings were rechecked against the stable rule list with
`ruff rule <code>`; preview rules remain excluded.

The following enabled Pylint messages have no selected stable Ruff equivalent.
The converter and Ruff issue #970 supplied candidates; the stable rule list was
checked separately so cross-linter mappings are not missed.

| Left-out Pylint message                                        | Reason                                                           |
| -------------------------------------------------------------- | ---------------------------------------------------------------- |
| `disallowed-name` (`C0104`)                                    | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-mcs-method-argument` (`C0203`)                            | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-mcs-classmethod-argument` (`C0204`)                       | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `too-many-lines` (`C0302`)                                     | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `mixed-line-endings` (`C0327`)                                 | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unexpected-line-ending-format` (`C0328`)                      | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `wrong-spelling-in-comment` (`C0401`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `wrong-spelling-in-docstring` (`C0402`)                        | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-characters-in-docstring` (`C0403`)                    | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `use-implicit-booleaness-not-comparison` (`C1803`)             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-file-encoding` (`C2503`)                                  | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unrecognized-inline-option` (`E0011`)                         | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-plugin-value` (`E0013`)                                   | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-configuration-section` (`E0014`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unrecognized-option` (`E0015`)                                | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `duplicate-argument-name` (`E0108`)                            | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `abstract-class-instantiated` (`E0110`)                        | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-reversed-sequence` (`E0111`)                              | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-star-assignment-target` (`E0113`)                     | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `star-needs-assignment-target` (`E0114`)                       | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `misplaced-format-function` (`E0119`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `method-hidden` (`E0202`)                                      | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `access-member-before-definition` (`E0203`)                    | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `no-method-argument` (`E0211`)                                 | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-slots-object` (`E0236`)                               | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-slots` (`E0238`)                                      | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `inherit-non-class` (`E0239`)                                  | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `inconsistent-mro` (`E0240`)                                   | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `class-variable-slots-conflict` (`E0242`)                      | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-class-object` (`E0243`)                               | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-enum-extension` (`E0244`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `declare-non-slot` (`E0245`)                                   | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `non-iterator-returned` (`E0301`)                              | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-repr-returned` (`E0306`)                              | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-length-hint-returned` (`E0310`)                       | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-format-returned` (`E0311`)                            | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-getnewargs-returned` (`E0312`)                        | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-getnewargs-ex-returned` (`E0313`)                     | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `possibly-used-before-assignment` (`E0606`)                    | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unpacking-non-sequence` (`E0633`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-except-order` (`E0701`)                                   | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `raising-bad-type` (`E0702`)                                   | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-exception-cause` (`E0705`)                                | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `raising-non-exception` (`E0710`)                              | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-super-call` (`E1003`)                                     | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `not-callable` (`E1102`)                                       | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `assignment-from-no-return` (`E1111`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `no-value-for-parameter` (`E1120`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `too-many-function-args` (`E1121`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unexpected-keyword-arg` (`E1123`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `redundant-keyword-arg` (`E1124`)                              | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `missing-kwoa` (`E1125`)                                       | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-sequence-index` (`E1126`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-slice-index` (`E1127`)                                | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `assignment-from-none` (`E1128`)                               | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `not-context-manager` (`E1129`)                                | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-unary-operand-type` (`E1130`)                         | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unsupported-binary-operation` (`E1131`)                       | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `not-an-iterable` (`E1133`)                                    | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `not-a-mapping` (`E1134`)                                      | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unsupported-membership-test` (`E1135`)                        | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unsubscriptable-object` (`E1136`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unsupported-assignment-operation` (`E1137`)                   | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unsupported-delete-operation` (`E1138`)                       | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-metaclass` (`E1139`)                                  | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unhashable-member` (`E1143`)                                  | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-slice-step` (`E1144`)                                 | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `async-context-manager-with-regular-with` (`E1145`)            | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `logging-unsupported-format` (`E1200`)                         | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `logging-format-truncated` (`E1201`)                           | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `not-async-context-manager` (`E1701`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bare-name-capture-pattern` (`E1901`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-match-args-definition` (`E1902`)                      | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `too-many-positional-sub-patterns` (`E1903`)                   | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `multiple-class-sub-patterns` (`E1904`)                        | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-unicode-codec` (`E2501`)                              | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-character-carriage-return` (`E2511`)                  | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `positional-only-arguments-expected` (`E3102`)                 | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-field-call` (`E3701`)                                 | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `modified-iterating-dict` (`E4702`)                            | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `fatal` (`F0001`)                                              | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `astroid-error` (`F0002`)                                      | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `parse-error` (`F0010`)                                        | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `config-parse-error` (`F0011`)                                 | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `method-check-failed` (`F0202`)                                | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unreachable` (`W0101`)                                        | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `confusing-with-statement` (`W0124`)                           | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `using-constant-test` (`W0125`)                                | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `missing-parentheses-for-call-in-test` (`W0126`)               | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `contextmanager-generator-missing-cleanup` (`W0135`)           | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `break-in-finally` (`W0137`)                                   | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `comparison-with-callable` (`W0143`)                           | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `implicit-flag-alias` (`W0213`)                                | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `super-init-not-called` (`W0231`)                              | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `non-parent-init-called` (`W0233`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-overridden-method` (`W0236`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `arguments-renamed` (`W0237`)                                  | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unused-private-member` (`W0238`)                              | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `overridden-final-method` (`W0239`)                            | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `subclassed-final-class` (`W0240`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `useless-parent-delegation` (`W0246`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `preferred-module` (`W0407`)                                   | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `shadowed-import` (`W0416`)                                    | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `global-variable-undefined` (`W0601`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unused-wildcard-import` (`W0614`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `redefined-outer-name` (`W0621`)                               | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `undefined-loop-variable` (`W0631`)                            | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unbalanced-tuple-unpacking` (`W0632`)                         | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `possibly-unused-variable` (`W0641`)                           | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `unbalanced-dict-unpacking` (`W0644`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `raising-format-tuple` (`W0715`)                               | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `wrong-exception-operation` (`W0716`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `arguments-out-of-order` (`W1114`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `non-str-assignment-to-dunder-name` (`W1115`)                  | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `isinstance-second-argument-not-valid-type` (`W1116`)          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `kwarg-superseded-by-positional-arg` (`W1117`)                 | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-format-string-key` (`W1300`)                              | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `missing-format-attribute` (`W1306`)                           | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `invalid-format-index` (`W1307`)                               | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `duplicate-string-formatting-argument` (`W1308`)               | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `anomalous-unicode-escape-in-string` (`W1402`)                 | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `inconsistent-quotes` (`W1405`)                                | Neither Google source requires one quote style; the formatter normalizes quotes. |
| `redundant-unittest-assert` (`W1503`)                          | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-thread-instantiation` (`W1506`)                           | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `using-f-string-in-unsupported-version` (`W2601`)              | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `using-final-decorator-in-unsupported-version` (`W2602`)       | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `using-exception-groups-in-unsupported-version` (`W2603`)      | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `using-generic-type-syntax-in-unsupported-version` (`W2604`)   | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `using-assignment-expression-in-unsupported-version` (`W2605`) | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `using-positional-only-args-in-unsupported-version` (`W2606`)  | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `bad-chained-comparison` (`W3601`)                             | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `modified-iterating-list` (`W4701`)                            | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `deprecated-module` (`W4901`)                                  | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `deprecated-method` (`W4902`)                                  | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `deprecated-argument` (`W4903`)                                | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `deprecated-class` (`W4904`)                                   | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `deprecated-decorator` (`W4905`)                               | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |
| `deprecated-attribute` (`W4906`)                               | No stable Ruff 0.16.9 equivalent in the converter or issue #970. |

### Preview-only and removed mappings

| Pylint message                          | Candidate | Reason                                                                               |
| --------------------------------------- | --------- | ------------------------------------------------------------------------------------ |
| `unnecessary-dunder-call` (`C2801`)     | `PLC2801` | Its only Ruff candidate is preview; preview is disabled by requirement.              |
| `dict-iter-missing-items` (`E1141`)     | `PLE1141` | Its only Ruff candidate is preview; preview is disabled by requirement.              |
| `modified-iterating-set` (`E4703`)      | `PLE4703` | Its only Ruff candidate is preview; preview is disabled by requirement.              |
| `redefined-slots-in-subclass` (`W0244`) | `PLW0244` | Its only Ruff candidate is preview; preview is disabled by requirement.              |
| `bad-indentation` (`W0311`)             | `E111`    | Its only Ruff candidate is preview; preview is disabled by requirement.              |
| `unspecified-encoding` (`W1514`)        | `PLW1514` | Its only Ruff candidate is preview; preview is disabled by requirement.              |
| `syntax-error` (`E0001`)                | `E999`    | Ruff removed the rule in 0.8.0; syntax errors are always reported without selection. |

### Exemptions and unsupported settings

| Rule or setting                                                                     | Source                                                       | Reason                                                                                                                                                                                                                                 |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PLR` family                                                                        | Google pylintrc `disable=R`.                                 | Keep the source configuration’s refactor exclusion; no preview or `PLR` rules are selected. FR-007 review: docstrings, line wraps, import sorting, and local renames are local fixes, so no other rule is excluded as a large rewrite. |
| `E999`                                                                              | Pylint `syntax-error` (`E0001`); Ruff 0.16.9 rule status.    | Ruff removed E999 in 0.8.0 and always reports syntax errors.                                                                                                                                                                           |
| `D105`, `D107`                                                                      | Google guide §3.8 and pylintrc `no-docstring-rgx`.           | Magic methods and `__init__` match the source exemption.                                                                                                                                                                               |
| `D1` in `*_test.py` and `test_*.py`                                                 | Google guide §3.8.2.1.                                       | Test modules, classes, and functions need no docstrings.                                                                                                                                                                               |
| `SLF001` in `*_test.py` and `test_*.py`                                             | Pylint `protected-access`.                                   | Tests may inspect protected state.                                                                                                                                                                                                     |
| `F401` in `__init__.py`                                                             | Pylintrc `[VARIABLES] init-import=no`.                       | Package initializer imports form the public module API.                                                                                                                                                                                |
| `D103` on `main` and test-named declarations                                        | Pylintrc `no-docstring-rgx`.                                 | Ruff has no name-based pydocstyle exemption; use a local directive only where the source exception applies.                                                                                                                           |
| `E501` on long import lines, URLs or paths in comments, flags, and string constants | Google guide §3.2.                                           | Ruff’s automatic exceptions do not cover every Google exception; use a local `# noqa: E501` only for these documented cases.                                                                                                           |
| `E402` after warning-filter initialization                                           | Python import-order requirement.                              | Keep warning filters active before importing the optional source package; the local directive explains this ordering.                                                                                                                |
| `BLE001` at failure-isolation boundaries                                             | Google guide §2.4.4.                                          | Broad catches are allowed at isolation points that record and suppress failures; each local comment names the boundary.                                                                                                               |
| `F401` on optional-dependency availability probes                                    | Optional dependency behavior.                                  | The import itself checks whether the optional package is installed.                                                                                                                                                                   |
| `N818` on `MessageTooLarge`                                                         | FR-007 behavior-preserving fixes.                             | Renaming the public class would change its name.                                                                                                                                                                                      |
| `PLC0415` on lazy, optional, or test-only imports                                    | Pylint `import-outside-toplevel`.                              | Keep deferred imports at their current boundary; each local comment gives the reason.                                                                                                                                                  |
| `SLF001` on same-package private helper calls                                        | Pylint `protected-access`.                                    | Preserve the private helper names and identify their same-package use at each call.                                                                                                                                                   |
| Naming exemptions in `extend-ignore-names`                                          | Pylintrc `[BASIC]` and `[CLASSES]`.                          | Preserve the source’s `main`, `_`, test, assertion, setup/teardown, and `class_`/`mcs` conventions where Ruff exposes matching name exemptions.                                                                                        |
| `dummy-variable-rgx`                                                               | Pylintrc `[VARIABLES]` and Pylint's default `ignored-argument-names`. | Ruff uses one setting for both source patterns.                                                                                                                                                                                        |
| `docstring-min-length=12`                                                           | Pylintrc `[BASIC]`.                                          | Ruff pydocstyle has no matching minimum-length setting.                                                                                                                                                                                |
| Fenced Python in Clean Code reference Markdown                                      | Vendored upstream references; Markdown is not Python source. | Exclude these documents from Ruff formatting so their examples retain upstream form.                                                                                                                                                   |
| `.specify/extensions/`                                                              | FR-005; vendored Spec Kit extensions.                        | Keep vendored upstream code unchanged.                                                                                                                                                                                                 |
