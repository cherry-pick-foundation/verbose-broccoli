# Quickstart: ChatGPT Export into the Chat Vault

Validation scenarios for the feature. Details are in the
[procedure contract](contracts/export-procedure.md) and the
[evidence contract](contracts/evidence-json.md).

## Prerequisites

- `deno task doctor` passes (uv, Deno, the `wiki-consistency` environment).
- `deno task wiki-consistency:install` has been run once.

## Automated checks

```sh
deno task test:wiki-raw-import      # US1-US3: fixed-file export, chat and work vaults
deno task test:wiki-consistency     # US4: escaped, direct and invalid JSON; export ZIP
deno task verify                    # whole repository
```

Expected: all pass. The raw import test builds a synthetic export ZIP at
`<temporary home>/Documents/chatgpt/chatgpt-export.zip`, admits it into the
`chat` and `work` vaults, saves a changed export over it and admits again (two
revisions of one source per vault), then admits once more (`already_admitted`
in both) and verifies both vaults.

## Manual walk-through with a synthetic export

In a temporary home folder (`HOME` and the four `XDG_*_HOME` variables pointing
inside it), follow the skill's "ChatGPT exports" section with a synthetic ZIP
in place of a real download. Expected: steps 4 to 6 succeed without other
instructions, and `verify` reports one revision per vault.

## After the merge (user's go-ahead required)

- Update the copies of the schema in the user's vaults so they state the new
  rule.
- When the user's real export arrives and the user says go, run the procedure
  on the real vaults. Report counts only.
