# Per-Plugin Build Contract

`deno task backfire:build -- <plugin> <output>` runs `python -m
backfire_tools.build <plugin> <output>` in `packages/backfire/`'s environment
and writes a complete plugin to `<output>`. `<plugin>` is `code` or `work`.

## Plugin table

`packages/backfire/src/backfire_tools/build.py` holds the only table of what
each plugin gets:

| Plugin | Plugin files | Packages from `packages/backfire/src/` | Shipped profile source |
| --- | --- | --- | --- |
| `code` | `plugins/code/` | `backfire` | `backfire/config.toml` |
| `work` | `plugins/work/` | `backfire`, `backfire_education` | `backfire_education/config.toml` |

Adding a package to a plugin's build means adding its directory name to that
plugin's row. A package listed here must live under `packages/backfire/src/`
and is copied whole, except `__pycache__/` and its own `config.toml`.

## Output

```text
<output>/                         # copy of plugins/<plugin>/
└── backfire/
    ├── pyproject.toml, .python-version, uv.lock
    └── src/
        ├── backfire/             # the shared core
        │   └── config.toml       # the plugin's shipped profile, from the table
        └── <each further package in the plugin's row>/
```

- Every package's own `config.toml` is skipped, and the row's profile source
  is written to `backfire/src/backfire/config.toml`. So a code build has no
  education profile and no `backfire_education/`, and a work build has no
  development profile.
- Everything else follows feature 005's
  [distribution build](../../005-jev-decision-backend/contracts/mcp-server.md#distribution-build):
  refusal of an existing output or one inside `plugins/` or `packages/`, the
  partial directory renamed at the end, no links, the 16 MiB budget with its
  test variable, and cleanup on failure, SIGINT and SIGTERM.
- An unknown `<plugin>`, including `chat`, fails before anything is written,
  with a message naming the known plugins.
- Usage without exactly two arguments fails with `Usage: deno task
  backfire:build -- <plugin> <output>`.

## Install and serve

In `<output>/backfire/`:

| Plugin | Install | Serve (from `plugins/<plugin>/mcp.json`) |
| --- | --- | --- |
| `code` | `uv sync --frozen --no-dev` | `uv --directory ${PLUGIN_ROOT}/backfire run --frozen --offline --no-sync backfire serve-mcp` |
| `work` | `uv sync --frozen --no-dev --extra education` | the same command |

A work build installed without `--extra education` cannot import
`phonenumbers`; its first judgment fails with `backend_not_configured` naming
the shipped `config.toml`, and nothing is sent.

The repository's `deno task backfire:install` runs `uv sync --project
packages/backfire --frozen --extra education`, so the development environment
can test both builds.
