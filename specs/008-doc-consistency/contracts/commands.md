# Commands Contract

The package's console command is `doc-regions`. The repository runs it
through `deno.json` tasks with `uv run --project packages/doc-regions --frozen
--offline --no-sync`, and passes `scripts/doc_regions.toml` as the
configuration.

| Task | Command | Network | Writes |
| --- | --- | --- | --- |
| `doc-regions:check` (in `check`) | `doc-regions check <config>` | none | none |
| `doc-regions:update` | `doc-regions update <config>` | none | mechanical regions only |
| `doc-regions:prepare` | `doc-regions prepare <config> --base <ref> --max-evidence-chars <n>` | none | none |
| `doc-regions:audit` | `doc-regions audit <config>` | downloads MemoryLint 1.5.1 once | the cache directory only |
| `test:doc-regions` (in `test`) | pytest on `packages/doc-regions/tests` and `scripts/doc_sources_test.py` | none | temporary directories |

## Exit and output

As the repository's other commands: 0 with one JSON object on stdout on
success; 2 with an error on stderr for invalid arguments; 1 for a failed check
or execution failure, with each problem on stderr.

## `prepare` output

```json
{
  "base": "<merge-base commit id>",
  "units": [{"id": "docs/architecture.md:12-15", "document": "docs/architecture.md", "heading_path": ["Three-plugin workspace", "Current skeleton"], "kind": "paragraph", "first_line": 12, "last_line": 15, "added": false, "report_only": false}],
  "requests": [
    {"tool": "backfire_verify", "units": ["docs/architecture.md:12-15"], "arguments": {"claims": ["..."], "evidence": [{"id": "deno.json", "text": "<diff of deno.json>"}]}},
    {"tool": "backfire_classify", "units": ["docs/architecture.md:40-41"], "arguments": {"items": [{"id": "docs/architecture.md:40-41", "text": "..."}], "classes": [{"id": "mechanical_candidate", "description": "..."}, {"id": "agent_region", "description": "..."}], "purpose": "..."}}
  ]
}
```

- `base` is `git merge-base <ref> HEAD`; the evidence is `git diff <base>`
  of the working tree, one item per changed file.
- Units of every target and report-only document are included; the output is
  sorted by document, then line, so the same inputs give byte-identical output.
- A `backfire_verify` request stays within backfire's fixed limits
  (`packages/backfire/src/backfire/validate.py`: 250 options per Choice, 672
  answer cells per request): with `E` evidence items it has at most 224
  claims when `E` is 1 and at most `672 // (E + 4)` otherwise. With more than
  249 evidence items the command fails, naming the limit
  ([research.md](../research.md) R6). A `backfire_classify` request has at
  most 64 items. No evidence item is longer than `--max-evidence-chars`;
  longer file diffs are split into numbered items (`deno.json#2`). Every unit
  is in exactly one request per tool, except that an empty feature diff gives
  no `backfire_verify` request: with no change, nothing can be contradicted.
- Each `arguments` object validates against the tool's input schema as
  published by backfire.

## `audit` output

```json
{"memorylint": {"version": "1.5.1", "sha256": "df4b3104...", "findings": [{"id": "ML-022", "drift_type": "reality", "source": "AGENTS.md:100", "evidence": "...", "suggested_action": "rewrite"}]}}
```

It keeps only findings whose source is a report-only document, unchanged
otherwise. A hash mismatch fails without running the script. The cache
directory stays within 1 MiB, checked before each write; the download and
extraction go to a temporary sibling directory that is renamed into place
only after the hash check and removed on failure, SIGINT or SIGTERM; a run
first removes leftovers of killed runs. The audit never
edits files; MemoryLint's `apply` script is never run.

## The judgment step

Run by the main agent before each `develop` merge review, never by `verify`
or the finish hook:

1. `deno task doc-regions:prepare -- --base develop --max-evidence-chars <n>` and
   `deno task doc-regions:audit`.
2. Send each request to backfire's tool named in it, through the agent's MCP
   client. If backfire is unavailable, stop and report that the step could not
   run.
3. For target units with `contradicted` or `review`: fix the text in this
   feature, or record why it stands in the feature's `tasks.md` note.
4. For report-only units with `contradicted` or `review`, and for MemoryLint
   findings: report them to the user; change nothing.
5. For `mechanical_candidate` suggestions: decide whether to add a generator
   and region in this feature.

## Library interface

Feature 010 calls the package's modules directly, with a Wiki instance as the
root and its own evidence ([research.md](../research.md), "For feature 010").
The commands above are thin wrappers over these functions, with the
repository as root. No function uses the network, and only `update` writes.

- `config.load(config_path, root)` reads the TOML. Entries of `targets` and
  `report_only` are root-relative paths or globs (`wiki/**/*.md`); each must
  match at least one file, and a file matched by both lists fails. It returns
  both lists as sorted, root-relative paths, the generator module name, and
  `generator_path` resolved against `root` when relative (it may lie outside
  `root`).
- `regions.check(root, targets, generators, generator_path)` returns the
  problems of the check in [regions.md](regions.md), each with document and
  line; `regions.update(...)`, with the same arguments, regenerates regions.
  Sources and targets resolve against `root`.
- `units.split(document, text, base_text=None)` returns the units of `text`
  outside mechanical regions, in line order. `added` is true when every line
  of the unit is inserted relative to `base_text` by `difflib`; with `None`
  every unit has `added` false, and `""` (a new file) makes every unit added.
  `prepare` passes `git show <merge-base>:<path>`, or `""` for a new file.
- `requests.verify_requests(groups)` takes a list of `(units, evidence)`
  groups, `evidence` being a list of `{id, text}`, and returns requests in
  input order, splitting each group's claims within the limits above. It
  never drops, trims or truncates a unit or evidence item, and passes
  evidence ids and texts through unchanged; it raises `ValueError` naming the
  limit when a group's evidence alone does not fit, and for a group with no
  evidence. `prepare` passes one
  group: all units, with the feature diff split into items of at most
  `--max-evidence-chars`.
- `requests.classify_requests(units, purpose)` returns requests of at most 64
  items with the two classes above, in input order.

Each request is `{"tool", "units", "arguments"}` as in the `prepare` output,
`units` listing the unit ids in claim or item order.
