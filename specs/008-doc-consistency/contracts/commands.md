# Commands Contract

The package's console command is `doc-regions`. The repository runs it
through `deno.json` tasks with `uv run --project packages/doc-regions --frozen
--offline --no-sync`, and passes `scripts/doc_regions.toml` as the
configuration.

| Task | Command | Network | Writes |
| --- | --- | --- | --- |
| `doc-regions:check` (in `check`) | `doc-regions check <config>` | none | none |
| `doc-regions:update` | `doc-regions update <config>` | none | mechanical regions only |
| `doc-regions:prepare` | `doc-regions prepare <config> --base <ref> --max-claims <n> --max-evidence-chars <n>` | none | none |
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
- A request never has more claims or items than `--max-claims` (and never more
  than 64 items for `backfire_classify`), and no evidence item longer than
  `--max-evidence-chars`; longer file diffs are split into numbered items
  (`deno.json#2`). Every unit is in exactly one request per tool.
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

1. `deno task doc-regions:prepare -- --base develop ...` and
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
