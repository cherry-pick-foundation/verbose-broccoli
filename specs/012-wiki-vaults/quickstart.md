# Quickstart: Validating Wiki Vaults

Run from the feature worktree's root with Deno on `PATH`
(`export PATH="$HOME/.deno/bin:$PATH"` if needed).

## Automated checks

```sh
deno task test:wiki-raw-import  # new paths, default work, chat admission
deno task verify                # everything, with recorded evidence
git grep -n wikis               # only records of this rename (SC-001)
```

## Document judgments

```sh
deno task doc-regions:prepare -- --base develop --max-evidence-chars 20000
```

Send the printed requests through backfire, as
[research R2](research.md#r2-checking-the-edited-documents-backfire-after-editing)
says; no changed unit may stay contradicted or flagged without a correction or
a recorded reason.

## After the merge (live data)

Follow [research R4](research.md#r4-moving-the-live-instance), then:

```sh
cd plugins/work/skills/wiki-raw-import   # in the develop worktree
for vault in default chat code work; do
  uv run --locked --script scripts/raw_import.py verify --wiki "$vault"
done
ls ~/.local/share/verbose-broccoli ~/.local/state/verbose-broccoli  # no wikis
git -C ~/.local/share/verbose-broccoli/vaults/work status --short   # as before
```
