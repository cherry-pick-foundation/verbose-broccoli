# Education privacy gate

The `jev-mcp` executable is the only registered judgment server. Its FastMCP
proxy applies the privacy gate to every call before the hidden, unmodified
`@jkudish/jev-mcp` child receives it. No bypass or opt-out exists. Proxy wiring
is implemented separately; this package skeleton declares its entry point.

The operator-maintained list is
`<config>/verbose-broccoli/education-privacy-gate/registered-list.json`.
`<config>` is an absolute `XDG_CONFIG_HOME`, otherwise `HOME/.config`. The
containing directory must be user-owned mode 0700, and the regular file must
be user-owned mode 0600. Symlink components are refused. Only registered
person spellings and school spellings belong in this file; never scores,
student numbers, contacts or stand-ins. Admission is a separate authorized
operation. The gate only reads a bounded snapshot.

Each call draws one English Faker first name per matched person. Every form
of that person uses the same token; schools and covered identifier patterns
use numbered labels. Pairs exist only in memory and are cleared on every
exit. Unique complete echoed strings or keys restore exactly. Ambiguous
echoes and newly composed prose restore the registered Latin spelling, or
the Hangul name when no Latin spelling exists. Changed or truncated tokens
cannot reliably restore. Missing names and school variants, context and
uncovered identifier formats remain disclosure risks; an unregistered Korean
name can stand out among English fakes. EduOK detection covers isolated
ten-digit strings and `s-<ten digits>` components; accepted phone spans keep
the Phone label. Ten-digit JSON integers also become labels and restore as
decimal text; other numbers keep their types. Typed numeric fields then fail
unchanged upstream schema validation. Request bodies, results, deadlines and
concurrency use upstream/runtime controls; this gate
adds only a recursion guard, registry bounds and collision exhaustion bounds.
Grades, classes, school years and scores remain unchanged. Pattern-constrained
schema fields containing a covered identifier fail before forwarding.

Install the reviewed npm lock using `npm ci --ignore-scripts`. Python direct
dependencies are pinned; use the repository's root `.python-version` and MCP
2.2.0 lock during integration. Register the proxy entry point, never the npm
child directly. Follow the proxy's controlled environment, stderr, timeout,
result-type and tools-only policy before enabling it for real education data.
