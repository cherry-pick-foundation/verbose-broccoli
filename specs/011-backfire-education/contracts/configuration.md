# Work Build Configuration Contract

Paths use feature 005's XDG rules: `$XDG_CONFIG_HOME` defaults to `~/.config`
and `$XDG_DATA_HOME` to `~/.local/share`; a relative value fails with
`backend_not_configured` naming the variable.

## Shipped `config.toml` (in the build)

The work build's `backfire/src/backfire/config.toml`, copied from
`packages/backfire/src/backfire_education/config.toml`:

```toml
pseudonymize = true
provider = "education"

[providers.education]
# The same values as the development profile's [providers.hive]:
# api, base_url, model, credential = "HIVE_API_KEY", rate_limit_per_second,
# request, thinking and statuses.
```

- `pseudonymize` is a boolean accepted only at the top level of the shipped
  file. When it is `true`, every judgment of that build goes through
  [pseudonymization](pseudonymization.md). An operator `config.toml` that
  contains `pseudonymize` fails with `backend_not_configured` naming that
  file, so an operator cannot turn it on or off.
- The code build's shipped file is feature 005's, without `pseudonymize`.

## Operator files

| File | Owner | Content |
| --- | --- | --- |
| `$XDG_CONFIG_HOME/verbose-broccoli/backfire/config.toml` | operator, optional | Feature 005's selection and provider tables, shared by both builds. Replace `[providers.education]` to change only the work build's provider, or `[providers.hive]` for only the code build. A top-level `provider` line selects for both builds. |
| `$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.env` | operator, required for work | `HIVE_API_KEY=<key>`, with feature 005's rules: owned by the operator, mode `0600`, non-empty. A symbolic link to `hive.env` is accepted, because the check inspects the opened file. |
| `$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.toml` | operator, required for work | `roster = "<absolute path to the roster CSV>"`, and no other key. |
| the roster CSV named there | operator (for now, the EduOK student list saved as a file) | [Roster format](pseudonymization.md#roster). Read at every judgment, never copied. |

## Data files

| File | Written by | Content |
| --- | --- | --- |
| `$XDG_DATA_HOME/verbose-broccoli/backfire/pseudonyms.json` | the work build's judge | [Mapping table](pseudonymization.md#mapping-table), mode `0600`, at most 1 MiB. |
| `$XDG_DATA_HOME/verbose-broccoli/backfire/pseudonyms.lock` | the same | Empty lock file, mode `0600`. |

The directory is created with mode `0700` when missing. Deleting the table
resets pseudonyms: calls stay correct, but new pseudonyms no longer match
earlier ones.

## Failures

Each of these fails the judgment before any provider request, with
`backend_not_configured` and the named path as its only detail:

- `education.toml` missing, unreadable, not TOML, with a key other than
  `roster`, or with a `roster` that is not an absolute path;
- the roster file missing, not a regular file, not UTF-8, without a header
  row, without a `name` column, or with an empty `name` cell;
- the table or its lock unreadable, unwritable, malformed, not mode `0600`, not
  owned by the operator, or over 1 MiB after the change;
- `pseudonymize = true` but `backfire_education` or `phonenumbers` not
  importable (the detail is the shipped `config.toml`).
