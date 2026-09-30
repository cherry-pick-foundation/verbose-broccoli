# Bound PyModel stdio work and handle duplicate IDs efficiently

## Changes

- Keep the existing ID names and order while assigning duplicate suffixes in linear time by remembering the next suffix for each base ID. A regression test checks the output and order for 100,000 identical IDs.
- Limit stdio input lines to 10 MiB by default. The server constructor accepts a different positive byte limit. An oversized line is drained through its newline and reported as a parse error; the next line can still be read.
- Compile JSON Schema `exclusiveMinimum` and `exclusiveMaximum` into the existing number parser, with matching greater-than and less-than errors.
- Move synchronous line parsing, tool argument parsing and result serialization, the large verify/find preparation and finish steps, and response encoding off the event loop.

## Why

Backfire uses PyModel as a library and needs to send 10 MiB JSON-RPC lines. With 100,000 evidence items sharing one ID, the existing duplicate suffix search made `jev_verify` block the event loop for at least two seconds. Moving large synchronous steps to worker threads keeps unrelated async work responsive while preserving the protocol output.

This contribution was prepared for verbose-broccoli's Backfire integration, which uses PyModel as a library.

## Event-loop lag measurements

Each request body was 10,485,760 bytes. The `jev_verify` request contained 100,000 evidence items with the same ID and used a local stub provider. The lag monitor started on receipt of the request and sampled every 20 ms through response encoding. `16 yes` means 16 `nice -n 19 yes` processes were active; `pgrep -x yes` was checked before each loaded run, and the test processes were stopped afterward. Values are maximum measured event-loop lag, not total response time. `<20 ms` means the monitor did not observe a full 20 ms delayed tick.

| Tool | v0.6.0 idle | v0.6.0 with 16 `yes` | Patch idle | Patch with 16 `yes` |
|---|---:|---:|---:|---:|
| `jev_verify` | ≥2,000 ms (request timed out) | ≥2,000 ms (request timed out) | 5.8 ms | 8.3 ms |
| `jev_screen` | 8.3 ms | 3.0 ms | <20 ms | 4.6 ms |
| `jev_find` | 130.0 ms | 208.6 ms | 46.3 ms | 53.4 ms |
| `jev_classify` | 16.5 ms | 7.7 ms | <20 ms | 6.7 ms |
| `jev_decide` | <20 ms | <20 ms | <20 ms | <20 ms |
| `jev_rerank` | 17.6 ms | 15.6 ms | 0.7 ms | 10.5 ms |
| `jev_compare` | 3.0 ms | 11.1 ms | <20 ms | <20 ms |
| `jev_extract` | 2.8 ms | 18.2 ms | <20 ms | 8.1 ms |
| `jev_review` | 11.9 ms | 43.6 ms | 3.1 ms | 5.7 ms |
| `jev_gate` | 14.2 ms | 27.8 ms | 4.3 ms | 1.8 ms |
| `jev_score` | <20 ms | 2.4 ms | <20 ms | <20 ms |

The baseline `jev_verify` request did not return before the two-second probe timeout in either run. The patched call returned in 333.8 ms idle and 348.3 ms with 16 `yes` processes; its measured loop lag stayed below 9 ms.

## CHE-37 regex pool check

With 80 `nice -n 19 yes` processes, eight `jev_extract` runs mixed `!` and `\d+` with `(a+)+$` over a 50,000-character adversarial document. Each runaway pattern timed out at 1,002–1,009 ms as `invalid_pattern`. The simple pattern before it completed in 0.4–11.7 ms, and the simple pattern after it completed in 0.7–37.4 ms, including the run immediately after a worker was killed. None of the simple patterns timed out, so no regex timeout change was needed.

## Verification

- Offline PyModel suite: `4584 passed, 8 skipped, 17 deselected in 356.91s`.
- Focused tests for IDs, arguments, stdio, and Toolset: `51 passed in 0.73s`.
- `ruff check src/ tests/unit/`: passed.
- `ruff format --check src/ tests/unit/`: passed; 146 files already formatted.
- `pyright`: passed with 0 errors and 0 warnings.
- The patch was generated against v0.6.0 and checked with `git apply --check`.
