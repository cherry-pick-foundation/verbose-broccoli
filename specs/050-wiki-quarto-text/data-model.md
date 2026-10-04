# Data Model: Persistent Text and Quarto Wiki

| Layer | Authority and language | Storage/history |
| --- | --- | --- |
| `raw/` | User-selected immutable BagIt originals; original bytes | Vault data, outside Git; create-only |
| `text/` | Full original-language extraction per raw revision | Vault-local Git with no remote; reviewed corrections are commits |
| `wiki/` | Single maintained English knowledge source, `.qmd`, topics | Same local Git; index/overview/log retained |
| `site/` | Korean derived delivery from chosen English versions, tags | Base role only here; F2 owns freshness and publishing |
| `AGENTS.md` | Vault schema | Same local Git, separate from repository rules |

An extraction is `text/<source-id>/<revision>.qmd`, with front matter
`source-id`, `revision`, `sha256`, `converter: {name, version}` and
`checked-against-original`. A known new unreviewed conversion records `false`;
`true` requires actual review evidence. Unknown legacy converter or review facts
are `null` and reported, never guessed. Raw bags remain the source registry.

A Wiki page retains `title`, `summary`, `topics`, `sources: [{id, revision}]`
and meaningful skill metadata. Citation keys are generated solely from the bag's source ID and revision:
`<source-id>/<revision>`. Pages have no alias registry. The derived bibliography
carries exact revision provenance. Folder defaults live in `_metadata.yml` and page values
have the documented merging precedence in the citation contract.

A locator is a stable heading/div marker such as `{#p-25}` or `{#sec-purpose}`.
It references only its bounded content in the extraction. Source/revision/hash,
marker uniqueness and range continuity are validated before preparing evidence.
Correction commits may change text, never its original source identity.

The three special pages are `wiki/index.qmd`, `wiki/overview.qmd` and
`wiki/log.qmd`. Rename transitions preserve the old committed log prefix. The
index remains one Cog catalog region with `wiki/**/*.qmd` inputs.
