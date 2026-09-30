# T012 worker evidence

Assumption: `packages/wiki-consistency/pyproject.toml` keeps workspace sources
for root development; the built plugin copy needs sibling path sources.

## Changed files and selected rows

- `packages/backfire/src/backfire_tools/build.py`: rewrites both `doc-regions`
  and `backfire` workspace sources in the copied wiki-consistency project to
  editable sibling paths (`../doc-regions` and `../backfire`). It also fixes
  Ruff rows `RUFF:packages/backfire/src/backfire_tools/build.py:34`, `:37`,
  `:78`, `:194`, `:236` and `:241`.
- `packages/backfire/tests/test_build.py`: fixes
  `RUFF:packages/backfire/tests/test_build.py:129`; its build expectation now
  checks both rewritten sources. Its offline work-plugin case runs the
  install commands from the wiki-consistency skill with offline settings, then
  checks that `backfire` imports from the built sibling runtime.
- `packages/doc-regions/src/doc_regions/__main__.py`: fixes selected prose row
  `X136`. The npm probe
  `npm run args -- prepare config.yml -- --base HEAD` produced
  `["prepare", "config.yml", "--", "--base", "HEAD"]`.
- `pyproject.toml` and `uv.lock`: apply FR-013. Four packages use the newest
  develop versions; `typesafe-sdk` is pinned at 0.7.1 under the test exception
  below.
- `specs/019-turborepo/evidence/worker-T012.md`: records this evidence.

## Selected rows left unchanged

- `W2:packages/wiki-consistency/pyproject.toml#backfire-source`: the source
  manifest remains a workspace member for root development. The work build
  rewrites the copied manifest, which is the standalone artifact that needs
  `../backfire`.

All seven selected Ruff rows and `X136` changed. The W2 source manifest stays
unchanged for the reason above.

## Lock comparison and exception

The comparison used all three package locks at develop commit `8ce9b2a`.

| Package | Newest develop | Root lock | Result |
| --- | ---: | ---: | --- |
| openai | 3.20.0 | 3.20.0 | newest |
| starlette | 1.7.0 | 1.7.0 | newest |
| typesafe-sdk | 0.7.2 | 0.7.1 | exception |
| pyjwt | 2.15.1 | 2.15.1 | newest |
| sse-starlette | 3.5.0 | 3.5.0 | newest |

With the root constraint temporarily at 0.7.2, `uv lock` and
`uv export --package backfire --frozen --no-hashes --no-emit-workspace` both
resolved `typesafe-sdk` to 0.7.2 although
`packages/backfire/pyproject.toml` still constrains it to 0.7.1. The root
workspace resolution does not apply that member constraint. The full backfire
suite then failed only at
`packages/backfire/tests/test_package.py::test_package_dependency_versions`,
which asserts that `typesafe-sdk` is 0.7.1. The root constraint and lock now
keep 0.7.1; this is the FR-013 exception.

## Unselected sites

No unselected site needs a T012 edit. The final `deno task workflow` fails in
the concurrent clean-code conversion: its scope check cannot read the removed
`plugins/code/skills/clean-code/deno.json`. The changed scope caller is
`scripts/workflow_skills.ts`; the coordinator confirmed T008 is updating it and
asked that this remain with T008. This worker made no changes outside T012.

## Commands and results

- `uv lock` — exit 0; resolved the five requested newer versions.
- `uv sync --locked --all-packages --extra education` — exit 0 after the final
  lock.
- `uv lock --check` — exit 0.
- `npm run test:backfire` — final exit 0: 1,364 passed, 3 deselected. The
  earlier run at `typesafe-sdk` 0.7.2 exited 1: 1 failed, 1,363 passed,
  3 deselected, with the version assertion above.
- `npm run test:doc-regions` — exit 0: 107 passed, including
  `scripts/doc_sources_test.py`.
- `npm run test:wiki-consistency` — exit 0: 263 passed.
- `uv run --project tools/ruff --frozen --offline --no-sync ruff check --no-cache .`
  — final exit 0, `All checks passed!`; the baseline run reported exactly the
  seven selected Ruff findings.
- `uv run --project tools/ruff --frozen --offline --no-sync ruff format --check .`
  — exit 0, 117 files already formatted.
- `uv run --project tools/ruff --frozen --offline --no-sync ruff format packages/backfire/tests/test_build.py`
  — exit 0, formatted the test after adding the runtime import assertion.
- `git diff --check` — exit 0.
- Code plugin offline probe: `npm run backfire:build -- code
  /tmp/che32-t012-code-1wy_feee/code`, `uv sync --project
  /tmp/che32-t012-code-1wy_feee/code/backfire --frozen --offline --no-dev`,
  and `uv run --project /tmp/che32-t012-code-1wy_feee/code/backfire --frozen
  --offline --no-sync python -c 'import backfire; print(backfire.__file__)'`
  each exited 0. The work plugin build, documented uv sync commands, offline
  npm install, backfire import, and wiki check all passed inside the final
  `npm run test:backfire` run.
- `npm run workflow -- --task T012 --base 9bef254e64fc1fff5e67dfd6acd3998d5d194038 --graph impact --file packages/backfire/src/backfire_tools/build.py`
  — exit 1 because the graph does not support Python files.
- `npm run workflow -- --task T012 --base 9bef254e64fc1fff5e67dfd6acd3998d5d194038 --graph policy`
  — exit 1 during concurrent edits with `Invalid workflow evidence:
  data/context must have required property 'node_version', data/context must
  NOT have additional properties`.
- The final `deno task workflow` — exit 1 because the concurrent clean-code
  scope check reads the removed `plugins/code/skills/clean-code/deno.json`;
  the initial `deno task workflow` — exit 0.
