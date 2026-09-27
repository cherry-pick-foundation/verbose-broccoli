# Education Measurement Contract

## Set

`scripts/backfire/fixtures/education-v1.jsonl`: one JSON object per line in
feature 005's known-answer format:

| Field | Meaning |
| --- | --- |
| `id` | Unique case ID. |
| `tool` | One of `backfire_classify`, `backfire_verify`, `backfire_compare`, `backfire_noul`, `backfire_find`, `backfire_rerank`, `backfire_decide`, `backfire_extract`. |
| `language` | `ko`. |
| `kind` | `normal` or `boundary`. |
| `arguments` | The tool arguments. |
| `expect` | `{"result": {"<dotted path in the tool's JSON result>": <value>, ...}}`. |

- At least three cases per listed tool. The code-review tools
  (`backfire_gate`, `backfire_review`) and `backfire_screen` are not part of
  the education set.
- Every case is synthetic Korean education content: observations, lesson
  notes, progress claims, answers to compare, score reports. Every case names
  at least one student of the synthetic roster; at least one case per tool
  uses student names in option or candidate labels; at least three cases carry
  a synthetic phone number or email address and a school name; at least three
  write a student by given name alone with a particle.
- `scripts/backfire/fixtures/education-roster-v1.csv` is the synthetic roster
  in the [roster format](pseudonymization.md#roster), with at least eight
  students, their schools and at least two guardian names, and two students
  who share a given name.
- The set and roster are committed before the first measured run and are not
  changed afterwards; a changed set is `education-v2`.

## Runner

`uv run --project packages/backfire --frozen --offline --no-sync python -m
backfire_tools.acceptance.measure_education [--runs 3]`:

- Uses the repository's development environment and its shipped development
  profile, which has the same provider, model and request settings as the
  education profile.
- Makes a temporary directory that serves as `XDG_CONFIG_HOME` and
  `XDG_DATA_HOME` for the run. It holds `education.toml` pointing at the
  synthetic roster, a symbolic link `verbose-broccoli/backfire/hive.env` to the
  operator's `hive.env` (the key is never copied), and the mapping table. The
  directory is removed at the end, also on failure or interruption.
- For each run and each case, calls the tool in process with the real judge
  twice: with `pseudonymize=False` (arm `plain`) and with `pseudonymize=True`
  (arm `pseudonymized`).
- A case is correct when every `expect.result` path holds the expected value; a
  failed call counts as wrong and keeps its error type.
- Prints one JSON line per case, run and arm (`id`, `tool`, `arm`, `run`,
  `correct`, `error_type`), then a summary with the accuracy per tool and arm
  and the IDs of cases whose outcome differs between the arms.
- Writes no file outside its temporary directory. It makes real provider
  requests and needs the user's go-ahead.

The summary goes into [research.md](../research.md#results). No accuracy is a
pass/fail condition.
