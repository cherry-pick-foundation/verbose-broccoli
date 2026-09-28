# Data Model: Wiki Vaults

`DATA`, `STATE` and `CACHE` are the `verbose-broccoli` folders under the XDG
data, state and cache roots, as in feature 009's
[data model](../009-wiki-storage/data-model.md), which this feature changes
only in the folder name and the default vault.

```text
DATA/vaults/
├── default/   # knowledge that belongs to no single plugin
├── chat/      # exported conversations and pages written from them
├── code/      # coding knowledge for work in any project
└── work/      # education work: raw imports and per-student pages
STATE/vaults/<name>/
├── raw-import.lock
└── selections/<selection>.jsonl
CACHE/raw-import/<name>/   # staging, unchanged
```

## Vault

One Wiki instance with feature 009's layout: the schema `AGENTS.md`,
`raw/{web,files,notes,assets}/`, `wiki/` with `index.md`, `overview.md` and
`log.md`, and its own Git repository that ignores `raw/`.

| Vault | Owner | Raw evidence it admits |
| --- | --- | --- |
| `default` | No single plugin | Originals the user confirms; not conversation records |
| `chat` | The chat plugin; its persistent state | Also exported conversations |
| `code` | The code plugin | Originals the user confirms; not conversation records |
| `work` | The work plugin | Originals the user confirms; not conversation records |

Rules:

- A plugin's Wiki skills use the vault named after the plugin unless the
  user selects another; `default` is always selected by name. The raw import,
  a work plugin skill, therefore defaults to `work`.
- Any plugin's Wiki tool may write a vault the user selects; vaults are the
  user's shared Wiki storage, not a plugin's private store.
- The code vault is not this repository's development memory, which stays in
  the Spec Kit records, code and Git.
- The tool accepts other vault names under the same rules as feature 009's
  `--wiki` names; the four above are the ones the user keeps.

## Transitions

The one-time move renames `DATA/wikis/default/` to `DATA/vaults/work/` and
`STATE/wikis/default/` to `STATE/vaults/work/`, then creates the other three
vaults ([research R4](research.md#r4-moving-the-live-instance)).
