# Contract: Dependency Rules

Repository verification (`npm run verify`) enforces these rules with the
checkers the repository already pins: dependency-cruiser 18.2.0 and ESLint
(gts) for TypeScript, import-linter 2.15 for Python. No new checker is added
(root `AGENTS.md` "Reuse Before Implementing"). Brown ranks compiler
enforcement above checkers and checkers above discipline; neither language
here has a compile-time package-private check, so the checkers stand in
(R-CA-03).

Each rule has a fixture that breaks it and a test asserting that the checker
fails on that fixture in a single run (SC-004); a rule without a failing
fixture is not counted as enforced (R-EX-11). Every new dependency-cruiser
rule has severity `error`, because only `error` makes the run fail
(R-ARCH-12).

## Rules

| ID | Rule | TypeScript check | Python check | Source |
| --- | --- | --- | --- | --- |
| D1 | Rings point inward: `domain` imports nothing from `application`, `adapters`, `entrypoints` or `bootstrap`; `application` imports nothing from `adapters`, `entrypoints` or `bootstrap`; `adapters` import nothing from `entrypoints` or `bootstrap`; `bootstrap` imports nothing from `entrypoints`. | `domain-dependency-direction` and `application-dependency-direction` with the new ring names, plus `adapters-dependency-direction` and `bootstrap-dependency-direction` | one `layers` contract with every component as a container and the layers `(entrypoints)`, `(bootstrap)`, `(adapters)`, `(application)`, `(domain)`; parentheses mark optional layers | R-CA-01, R-ARCH-04, R-ARCH-07 |
| D2 | Domain code has no input or output: no file, process, network, clock or environment access. | `no-node-in-inner-layers` (Node core modules) and `no-io-packages-in-inner-layers`; ESLint `no-restricted-globals` for `domain/` | `forbidden` contract with `include_external_packages = true`: `*.domain` and `*.application` may not import the input or output libraries `os`, `sys`, `subprocess`, `socket`, `shutil`, `tempfile`, `urllib`, `http`, `httpx`, `mcp` or `fastmcp`, directly or indirectly | R-CA-01, R-GG-12, R-ARCH-11 |
| D3 | Application code does no input or output either; it reaches the outside only through its ports. | the same two dependency-cruiser rules, which already cover `application/` | the same `forbidden` contract, covering `*.application` | R-CA-01, R-CA-02 |
| D4 | No package imports another package's unpublished modules. | `public-api:<package>` rules (exist for today's packages; one per new package); the package's `exports` map hides private folders with `null` targets | one `protected` contract per package: its modules may be imported only by itself, except the modules its `AGENTS.md` lists as published | R-CA-03, R-REPO-10, R-ARCH-11, R-EX-11 |
| D5 | No import cycles. | `no-cycles` (exists); `circular` with `scope: folder` if folder cycles appear | `acyclic_siblings` within each root package; the `Workspace package layers` contract across all five roots, with independent siblings separated by ` \| ` | R-CA-01, R-ARCH-10, R-ARCH-12 |
| D6 | No package reaches into another with `../`; it depends on the package by name. | `no-cross-package-local-imports`, a group-matching rule that forbids `local` imports leaving the importing package's folder; `no-unresolved-local-imports` only catches imports that do not resolve | the `src` layout and uv workspace sources; D4 covers the rest | R-REPO-01, R-REPO-06, R-ARCH-12 |

D1 to D3 cover a package from the slice that moves it into rings; packages
not yet moved, including held ones, keep today's checks until then. D4 to D6
cover every package from the start.

`forbidden_modules` names root-level external packages (`urllib`, not
`urllib.request`) with `include_external_packages = true`. D2 and D3 use
one built-in `forbidden` contract, because `protected` cannot safely list
libraries absent from the graph in import-linter 2.15 (see Probe). It is still
a list of named libraries: one added later is not refused until listed.
When Pydantic AI is adopted, `pydantic_ai`, `openai` and `httpx2` join the list
(R-PAI-08).

D4's published modules are listed in `pyproject.toml` beside the contracts,
because import-linter reads only its own configuration; a package's
`AGENTS.md` points to that list instead of repeating it. Slice S3 writes the
list for all five Python packages, including the held ones, from the imports
that exist today (for example `wiki_consistency` uses `doc_regions.config`,
`regions`, `requests` and `units`), which edits no held path.

## Probe

On 2026-10-06 a throwaway pair of Python packages under session scratch
showed import-linter 2.15 reporting a domain module importing an adapter
(D1), importing `subprocess` and `httpx` (D2), and importing another
package's domain (D4). A `layers` contract with `containers` requires every
layer in every container unless the layer is written in parentheses.

On 2026-10-07 the S3 fixtures settled both open questions:

- `acyclic_siblings` with separate root packages as ancestors kept a cycle
  between them (exit 0). The same cycle fails `Workspace package layers`
  (exit 1). Reproduce with `npm run test:python-imports`, test
  `test_d5_cross_root_cycle_needs_root_layers`.
- An npm workspace symlink and an `exports` entry resolve a by-name import to
  the real source path, not a `node_modules` path. In dependency-cruiser
  18.2.0 a root script sees `aliased-workspace`; a source under its own
  package manifest sees `undetermined` and `import`. Neither is `local`, so
  the D6 rule permits both while public-API rules see the resolved source.
  A `null` export fails resolution. Reproduce with
  `npm run test:clean-architecture`, the D6 workspace-import test.

The protected-library proposal proved unworkable in 2.15: a literal
`protected_modules` entry absent from the graph aborts (`socket` on the real
tree), while `**.<library>` misses a bare root library in Grimp 3.14 (all
eight initial inner-I/O fixtures passed incorrectly). The built-in
`forbidden` implementation skips absent external targets instead
(`importlinter/contracts/forbidden.py`, lines 117–119 in the installed 2.15
package). The coordinator approved that replacement on 2026-10-07.
Probe receipts: `$XDG_STATE_HOME/verbose-broccoli/workspaces/
feature-clean-architecture/slices/s3/ctx_daf7215cf651/`, files
`cross-root-probe.txt`, `python-imports-attempt-1.txt`,
`python-fixtures-attempt-1.txt` and the final fixture logs.

## Known limits

- Python D1 to D3 cover only modules inside `domain` and `application`
  rings, with D1 also covering the outer rings. Flat modules in un-moved
  packages are outside these ring checks until their moving slice adds rings.
- `acyclic_siblings` checks children within an ancestor, not separate roots.
  The root-package layers catch cross-root cycles and also restrict direction;
  every new root package must be added to that list in `pyproject.toml`.
- With `containers`, each component is layered on its own; the layers
  contract does not police imports between components, so D4 does
  (R-ARCH-07).
- `entrypoints` may import `adapters`: a layers contract allows any higher
  layer to import a lower one, and no rule here forbids it (R-ARCH-07).
- One adapter calling another inside the same component is not checked; it is
  a review item. Across components D4 applies, which prevents Brown's
  Périphérique problem (R-CA-03).
- The dependency-cruiser direction rules see direct imports only, while
  import-linter also follows indirect chains; `reachable` rules accept only
  `path` and `pathNot` (R-ARCH-12). A domain module reaching an adapter
  through a shared module passes in TypeScript.
- Clock reads (`datetime.now()`, `time.time()`) are not detected: `datetime`
  stays allowed in domain code for date values, so a use case passes "now"
  in as a value, and a clock read in domain code is a review item.
- `pathlib` stays allowed in domain code for pure path values; calls of
  `Path` methods that touch the disk are not detected and remain a review
  item.
- The checks see imports, not runtime behavior: a domain function that
  receives an open file object from an adapter is not flagged.
- Both tools check source files only; generated or vendored upstream code is
  excluded where the existing configuration already excludes it. Tests and
  entry points are roots: they import the packages and are not imported by
  them (R-FMCP-07, R-FMCP-08).
