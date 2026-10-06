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
| D1 | Rings point inward: `domain` imports nothing from `application`, `adapters`, `entrypoints` or `bootstrap`; `application` imports nothing from `adapters`, `entrypoints` or `bootstrap`; `adapters` import nothing from `entrypoints` or `bootstrap`. | `domain-dependency-direction` and `application-dependency-direction` with the new ring names, plus `adapters-dependency-direction` | one `layers` contract with every component as a container and the layers `(entrypoints)`, `(bootstrap)`, `(adapters)`, `(application)`, `(domain)`; parentheses mark optional layers | R-CA-01, R-ARCH-04, R-ARCH-07 |
| D2 | Domain code has no input or output: no file, process, network, clock or environment access. | `no-node-in-inner-layers` (Node core modules) and `no-io-packages-in-inner-layers`; ESLint `no-restricted-globals` for `domain/` | `protected` contracts with `include_external_packages = True`: each input or output library (`os`, `sys`, `subprocess`, `socket`, `shutil`, `tempfile`, `urllib`, `http`, `httpx`, `mcp`, `fastmcp`) may be imported only by `adapters`, `entrypoints` and `bootstrap` of any component | R-CA-01, R-GG-12, R-ARCH-11 |
| D3 | Application code does no input or output either; it reaches the outside only through its ports. | the same two dependency-cruiser rules, which already cover `application/` | the same `protected` contracts, whose allow-list leaves `application` out | R-CA-01, R-CA-02 |
| D4 | No package imports another package's unpublished modules. | `public-api:<package>` rules (exist for today's packages; one per new package); the package's `exports` map hides private folders with `null` targets | one `protected` contract per package: its modules may be imported only by itself, except the modules its `AGENTS.md` lists as published | R-CA-03, R-REPO-10, R-ARCH-11, R-EX-11 |
| D5 | No import cycles. | `no-cycles` (exists); `circular` with `scope: folder` if folder cycles appear | `acyclic_siblings` (exists); whether it sees cycles between separate root packages is settled by a fixture before it is relied on | R-CA-01, R-ARCH-10, R-ARCH-12 |
| D6 | No package reaches into another with `../`; it depends on the package by name. | a group-matching rule that forbids `local` imports leaving the importing package's folder; `no-unresolved-local-imports` only catches imports that do not resolve | the `src` layout and uv workspace sources; D4 covers the rest | R-REPO-01, R-REPO-06, R-ARCH-12 |

D1 to D3 cover a package from the slice that moves it into rings; packages
not yet moved, including held ones, keep today's checks until then. D4 to D6
cover every package from the start.

`forbidden_modules` in import-linter takes only root-level external packages
(`urllib`, not `urllib.request`), which is why D2 uses `protected`
allow-lists: a library added later is refused in inner rings until a
contract allows it (R-ARCH-08, R-ARCH-11). When Pydantic AI is adopted,
`pydantic_ai`, `openai` and `httpx2` join the D2 list (R-PAI-08).

## Probe

On 2026-10-06 a throwaway pair of Python packages under session scratch
showed import-linter 2.15 reporting a domain module importing an adapter
(D1), importing `subprocess` and `httpx` (D2), and importing another
package's domain (D4). A `layers` contract with `containers` requires every
layer in every container unless the layer is written in parentheses.

## Known limits

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
- `pathlib` stays allowed in domain code for pure path values; calls of
  `Path` methods that touch the disk are not detected and remain a review
  item.
- The checks see imports, not runtime behavior: a domain function that
  receives an open file object from an adapter is not flagged.
- Both tools check source files only; generated or vendored upstream code is
  excluded where the existing configuration already excludes it. Tests and
  entry points are roots: they import the packages and are not imported by
  them (R-FMCP-07, R-FMCP-08).
