# Quickstart: Validate Backfire for Education Work

Run from the repository root of the feature worktree. Steps 1 to 4 are
offline; steps 5 and 6 make billed provider calls and need the user's
go-ahead.

## 1. Environment and offline checks

```sh
deno task backfire:install
deno task test:backfire
deno task check
```

Expected: every suite passes, including the new pseudonymization, build and
end-to-end tests and the plugin layout test.

## 2. Build both plugins outside the repository

```sh
out=$(mktemp -d)
deno task backfire:build -- code "$out/code"
deno task backfire:build -- work "$out/work"
```

Expected ([build.md](contracts/build.md)):

- `$out/code/backfire/src/` has only `backfire/`, and its `config.toml` equals
  `packages/backfire/src/backfire/config.toml`.
- `$out/work/backfire/src/` has `backfire/` and `backfire_education/`; its
  `backfire/config.toml` equals
  `packages/backfire/src/backfire_education/config.toml`, and no other
  `config.toml` exists in the build.
- `deno task backfire:build -- chat "$out/chat"` fails and writes nothing.

## 3. Install the work build

```sh
(cd "$out/work/backfire" && uv sync --frozen --no-dev --extra education)
```

## 4. Pseudonymization against a recording provider

The end-to-end suite covers this automatically. It starts the built work
server with a temporary `XDG_CONFIG_HOME` and `XDG_DATA_HOME`, a synthetic
roster, and feature 005's scripted OpenAI-compatible provider through
`BACKFIRE_TEST_PROVIDER_BASE_URL`. It checks:

- no roster value, given name, phone number or email address in any recorded
  provider request, with and without particles (SC-001);
- the same pseudonym for the same identifier across two sessions and a
  restart, and distinct pseudonyms for distinct identifiers (SC-002);
- requests equal to the unpseudonymized ones except at the replaced spans
  (SC-003);
- results that carry the agent's own labels and no pseudonym (SC-001);
- each failure in [configuration.md](contracts/configuration.md#failures) and
  `pseudonym_conflict`, with no recorded provider request (SC-004).

## 5. Client check (live, with the user's go-ahead)

Register `$out/work` per invocation in Codex CLI and in Claude Code as feature
005's client registration does, with a temporary configuration: an
`education.toml` pointing at `scripts/backfire/fixtures/education-roster-v1.csv`,
an `education.env` link to the operator's `hive.env`, and an empty data
directory. Expected: each client lists the eleven tools and answers one
`backfire_classify` call on a synthetic observation (SC-006). Saved client
settings stay unchanged.

## 6. Education measurement (live, with the user's go-ahead)

```sh
uv run --project packages/backfire --frozen --offline --no-sync \
  python -m backfire_tools.acceptance.measure_education --runs 3
```

Expected: one line per case, run and arm, then a summary per tool and arm
([measurement.md](contracts/measurement.md)). Record it in
[research.md](research.md#results).

Remove `$out` afterwards.
