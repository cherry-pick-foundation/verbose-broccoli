# Contract: Upstream Record

`packages/backfire/src/jev_judge_mcp/UPSTREAM.md` has these sections, in
this order.

1. **Source**: repository URL, release tag `v0.6.0`, commit
   `fd6829c3fd1c3eb244f0feb011b6ca55298459f8`, license (MIT, `LICENSE` in
   this directory), and the upstream's own notice for jev-mcp 0.5.0 text
   (`THIRD_PARTY_NOTICES.md` in this directory).
2. **Files**: a Markdown table with one row per vendored file (sources under
   `src/jev_judge_mcp/`, tests under `tests/`): upstream path, upstream
   SHA-256, and status `unchanged`, `changed` or `added`. The hash test reads
   this table.
3. **Not taken**: the upstream areas left out, each with the reason.
4. **Changes**: one entry per changed or added file: what changed, why, and
   the spec requirement (for example FR-005 for `ids.py`).
5. **Behaviour differences outside the vendored files**: what backfire's
   glue changes relative to the upstream server (tool names, `backfire_noul`,
   provider seam and provider name, `regex` executor, server name and
   boundary, settings from defaults only).

The hash test fails, naming the file, when:

- an `unchanged` file's SHA-256 differs from the table;
- a `changed` file has no entry under Changes;
- a file exists in the vendored directories without a table row, or a row
  names a missing file.
