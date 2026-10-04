# Education privacy gate

The `jev-mcp` executable runs a FastMCP proxy. It applies the privacy gate to
every tool call before the hidden, unmodified `@jkudish/jev-mcp` child receives
it. Register only the proxy; keep the child hidden. No bypass or opt-out exists.
The console script and `python -m education_privacy_gate` start the proxy.

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

Run the repository's `mise run setup` to install the locked Python workspace
and this package's npm closure. `npm run education-privacy-gate:install`
installs only the reviewed npm lock with `npm ci --ignore-scripts` under this
package's `node_modules`. The proxy requires that local layout; do not hoist
or register the npm child directly. Python uses the root `.python-version`
and MCP 2.2.0 while the legacy PyModel dependency remains. Newly adopted
Python dependencies are wheel-only.

From the repository root, `npm run test:education-privacy-gate` runs the
synthetic suite, including all twelve actual pinned upstream schemas and
mocked provider responses. It reads no real registry or provider file and
makes no provider call. Upstream schemas are checked against the SHA-256 of
the reviewed 0.13.0 capture; no external scratch evidence is required.

At startup the proxy reads the existing protected OpenRouter configuration.
It fixes the upstream provider and model, suppresses logging and background
update/telemetry features, uses a neutral child directory and a 60-second
client timeout, and blocks resources, prompts and unsupported continuations.
External registration and real-list admission remain separately authorized
operations; passing synthetic tests does not activate either.
