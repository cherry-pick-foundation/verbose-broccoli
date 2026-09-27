# Quickstart: Validating Wiki Storage and Raw Documents

Run from the feature worktree's root with Deno and uv on `PATH`.

## Automated checks

```sh
deno task test:wiki-raw-import   # script against synthetic fixtures
deno task test:plugin-skills     # the new skill's resources package cleanly
deno task docs:check             # generated reference is current
deno task verify                 # everything, with recorded evidence
```

Expected: all pass. The tests set `HOME` and every XDG root to a temporary
folder and cover the guarantees in
[contracts/raw-import-cli.md](contracts/raw-import-cli.md).

## Manual check with a scratch home

```sh
export HOME="$(mktemp -d)" XDG_DATA_HOME= XDG_STATE_HOME= XDG_CACHE_HOME= XDG_CONFIG_HOME=
script=plugins/work/skills/wiki-raw-import/scripts/raw_import.py
uv run --locked --script "$script" init
printf 'synthetic\n' > "$HOME/doc.txt"
printf '{"path":"%s","kind":"files"}\n' "$HOME/doc.txt" > "$HOME/selection.jsonl"
uv run --locked --script "$script" admit --selection "$HOME/selection.jsonl"   # admitted
uv run --locked --script "$script" admit --selection "$HOME/selection.jsonl"   # already_admitted
printf 'changed\n' >> "$HOME/doc.txt"
uv run --locked --script "$script" admit --selection "$HOME/selection.jsonl"   # admitted, second revision
uv run --locked --script "$script" verify                                       # 2 valid revisions
git -C "$HOME/.local/share/verbose-broccoli/wikis/default" status --ignored --short  # raw/ ignored
```

## Real import (implementation phase only)

Follow `plugins/work/skills/wiki-raw-import/SKILL.md`. Nothing is copied
before the user has decided on every location in tasks.md Phase 6 and approved
each file list. Afterwards `verify` passes, originals are unchanged, and
tasks.md records counts per location only.
