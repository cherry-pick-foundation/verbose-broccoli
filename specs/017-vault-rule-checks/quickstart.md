# Quickstart: Vault Page Rule Checks

Run from the repository root after `deno task backfire:install` and
`deno task wiki-consistency:install`.

## Tests

```sh
deno task test:wiki-consistency
deno task test:backfire
```

`packages/wiki-consistency/tests/test_rules.py` builds synthetic vaults and
a synthetic roster in a temporary `XDG_CONFIG_HOME`; no test reads the
user's configuration, roster or vaults.

## A synthetic vault by hand

```sh
tmp=$(mktemp -d)
export XDG_DATA_HOME="$tmp/data" XDG_CONFIG_HOME="$tmp/config"
mkdir -p "$XDG_CONFIG_HOME/verbose-broccoli/backfire"
printf 'name,school,guardians\n가라온,가상별중학교,가보호\n' > "$tmp/roster.csv"
printf 'roster = "%s"\n' "$tmp/roster.csv" \
  > "$XDG_CONFIG_HOME/verbose-broccoli/backfire/education.toml"
```

Create a vault in `$XDG_DATA_HOME/verbose-broccoli/vaults/work/` from the
schema template (the `wiki-raw-import` skill's `assets/AGENTS.md`), add a
page with a synthetic phone number such as `010-0000-0000`, and run:

```sh
uv run --project packages/wiki-consistency --frozen --offline --no-sync \
  wiki-consistency check --wiki work
```

Expected: exit 1 and a line `wiki/<page>.md:<line>: page rule phone: pages
hold no phone numbers`, without the number. Remove the number and the check
passes the rule.

The names above are made up for this example and match no real record.
