# Upstream source

The tools and pure helpers are a Python port of
[jkudish/jev-mcp](https://github.com/jkudish/jev-mcp), release 0.9.0, revision
`a1fcc1e47fc696614f081e23a66ff48a890f22fd`.

These are the original source hashes, checked against that checkout and the
Feature 005 research record:

| File | SHA-256 |
| --- | --- |
| `src/index.ts` | `10ae5eee5fbe0de52a4e5e8240b550585a12bab953235d511d550b3decccaac7` |
| `src/lib.ts` | `6b96ab62448b4154a7e4a25ff6ca064b43d5df3fa0e087f6b02fa25e767067d2` |

The server is named `backfire`; tool names, descriptions, results and errors
map `jev_` to `backfire_` and `jev-mcp` to `backfire`. The tools preserve the
release's descriptions, input schemas, question design, decision logic, result
formats and error texts except for the recorded differences below.
`ensure_unique_ids` keeps the next suffix per base ID, giving linear work
while preserving the original IDs and order.

## Recorded differences

These are the four differences recorded under “Tools” in Feature 005's
research.md, “Python package — 2026-09-27”:

1. `backfire_extract` uses Python `re` patterns, and its argument description
   says so. It documents differences from JavaScript instead of emulating
   them. Named groups use `(?P<name>...)` and named backreferences use
   `(?P=name)`; `\w` and `\d` use Python's Unicode rules unless ASCII mode
   is selected. Flags `a`, `i`, `m`, `s`, `u` and `x` select Python modes;
   `g` is unnecessary because matching always scans the document. Non-lowercase
   letters are dropped, as in the upstream caller. Repeated mode flags have
   no additional effect; unsupported letters, including JavaScript's `d`,
   `v` and `y`, fail. Pattern syntax errors use Python's error text.
   Each field runs in its own child process, in field order, with a 1,000 ms
   parent timeout and a child timer whose default signal action ends it.
   Cancellation kills the child, and waiting never blocks the asyncio loop.
   Candidate order, deduplication, caps and the worker result fields
   (`candidates`, `truncated`, `tooLong`, and `error` on failure) are preserved.
2. A failed judgment raises the backend's fixed `<type>: <message>` error
   instead of `Jev-compatible endpoint <status>: <body>`; there is no HTTP
   judgment transport.
3. The tools call an in-process judge instead of the upstream provider layer.
   `src/provider.ts` is not ported.
4. Invalid arguments keep the prefix `MCP error -32602: Input validation error:
   Invalid arguments for tool <name>: `; the details after it come from JSON
   Schema validation with `jsonschema` against the published input schema,
   not from zod.

## License

The following is the unchanged text of
[LICENSE at the source revision](https://raw.githubusercontent.com/jkudish/jev-mcp/a1fcc1e47fc696614f081e23a66ff48a890f22fd/LICENSE).

```text
MIT License

Copyright (c) 2026 Joey Kudish

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
