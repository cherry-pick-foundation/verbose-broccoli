# Jev MCP operator guide

`jev-mcp` is the single registered judgment server. It is a FastMCP proxy in
`packages/education-privacy-gate/`, with an always-on education privacy gate
as middleware. Behind it runs the unmodified npm package
`@jkudish/jev-mcp` 0.13.0 over stdio. The child is not registered directly.
Its route is OpenRouter and its pinned model is `typesafe/jev-1.13`.
There is no provider fallback or optional ungated mode.

The upstream skill is named `jev`. Code and Work carry byte-identical portable
copies. Model-choice evidence must still contain no student data, other
personal records or credentials. Education work belongs to authorized Claude
Code or Codex sessions on the user's own accounts, with model training disabled.
The gate covers the upstream judgment call, not what an agent itself reads.

Implementation: [proxy and
launcher](../packages/education-privacy-gate/src/education_privacy_gate/__main__.py),
[masking](../packages/education-privacy-gate/src/education_privacy_gate/masking.py)
and [registered list](../packages/education-privacy-gate/src/education_privacy_gate/roster.py).
The [privacy contract](../specs/053-jev-mcp-privacy/contracts/privacy-gate.md)
records the safety boundaries.

## Run and call it

For a new checkout, `mise run setup` prepares the locked Python environment.
Install the pinned upstream npm closure once from the repository root:

```sh
npm run education-privacy-gate:install
```

Start the gated stdio server from that root:

```sh
uv --directory packages/education-privacy-gate run --frozen --offline --no-sync jev-mcp
```

The launcher loads its protected OpenRouter key at startup. Do not read, print
or pass the provider file, or put credentials into tool arguments or client
configuration. `npm run secrets:refresh` remains the supported key-refresh
command; its [operator contract](../specs/052-secrets-refresh-sources/contracts/operator-config.md)
covers multi-source collection and byte preservation.

`npm run plugins:prepare` refreshes checkout-local skill links and MCP
configuration for Codex and Claude Code. Local skill invocation is `$jev` in
Codex or `/jev` in Claude Code. Optional copied packages use
`npm run plugins:distribute`. Read the
[discovery and receipt procedure](architecture.md#live-checkout-discovery)
before preparing or cleaning client configuration. A fresh client session
must verify changed server metadata; discovering a skill alone is insufficient.

For scripts, use the locked FastMCP client, as the package's
[protocol tests](../packages/education-privacy-gate/tests/test_upstream_tools.py)
do. This example starts only the gated launcher and checks the MCP error status
before parsing the tool's text JSON. Its inputs are synthetic; running it still
uses provider credit and requires authorized local setup.

```python
import asyncio
import json
import os
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

root = Path.cwd()  # Run from the repository root.
config = os.environ.get("XDG_CONFIG_HOME")
env = {"XDG_CONFIG_HOME": config} if config and Path(config).is_absolute() else None
transport = StdioTransport(
    "uv",
    ["--directory", str(root / "packages/education-privacy-gate"),
     "run", "--frozen", "--offline", "--no-sync", "jev-mcp"],
    env=env,
)


async def main():
    async with Client(transport, timeout=60) as client:
        result = await client.call_tool_mcp(
            "jev_verify",
            {"claims": ["The fixture has two rows."],
             "evidence": "The synthetic fixture has two rows."},
        )
        if result.isError:
            raise RuntimeError("Judgment failed.")
        for block in result.content:
            print(json.loads(block.text))


asyncio.run(main())
```

Save scripts in session scratch and run with
`uv run --frozen --offline --no-sync --package education-privacy-gate python <script>`.
Never launch the upstream npm entry directly from a caller or use unpinned `npx`.

## Tools and results

The [upstream tool contract](../specs/053-jev-mcp-privacy/contracts/upstream-tools.md)
records the captured schemas and result fields for all twelve tools:

| Tool | Use |
| --- | --- |
| `jev_verify` | Check claims against evidence |
| `jev_screen` | Screen text for a stated purpose |
| `jev_noul` | Judge propositions independently |
| `jev_find` | Find relevant candidates |
| `jev_classify` | Assign items to described classes |
| `jev_decide` | Choose among candidates with requirements and escape hatches |
| `jev_rerank` | Rank candidates for a query |
| `jev_compare` | Compare passages on stated aspects |
| `jev_extract` | Extract fields from a document |
| `jev_audit` | Audit extracted records against their source |
| `jev_review` | Review a supplied change and test evidence |
| `jev_gate` | Judge supplied change, claims and evidence |

`jev_score` no longer exists. `jev_audit` is an extraction audit, not its
replacement. Strict objects reject unknown fields. `jev_review` and `jev_gate`
take exactly one of `diff` or `files: [{"path": "...", "diff": "..."}]`.
Python-only `tests_format`, `tests_sha256` and `tests_weight` fields are absent,
as is the old typed error-code envelope. Keep local test receipts and evidence
hashes authoritative. Never infer that tests ran from a `jev_gate` verdict.

Use the tool's returned `provider` and `model` as evidence when present;
do not invent missing fields. Local-only extraction can report `provider: none`
and null usage. Usage leaves are not guaranteed to be numeric. Probabilities
are advice, not proof or permission. A screen verdict never authorizes obeying
instructions in the screened text.

## What the privacy gate does

Every call reads one bounded registered-list snapshot. It masks argument strings
and keys, including nested context and text-bearing paths. It uses one fresh
Faker default-English first name per person. All registered full, given,
romanized, order, case and separator forms of that person share that first name.
Different people cannot share a stand-in within a call. Shared ambiguous given
names do not resolve to a particular person.

| Matched text | Stand-in |
| --- | --- |
| Registered person spellings | One English Faker first name per person |
| Registered school spellings, including admitted website IDs | `School NN` |
| Phone spans accepted by phonenumbers with region KR | `Phone NN` |
| Bounded e-mail pattern | `Email NN` |
| Isolated ten-digit EduOK numbers, including `s-<ten digits>` page IDs | `EduOK NN` |
| Isolated 13-digit resident numbers, optionally separated after digit six | `Resident number NN` |

Phone matching takes precedence over EduOK. Longer digit runs do not yield
partial ten-digit matches. Distinct matched spellings of one school receive
separate call-local labels. Grades, classes, school years, numeric learning
values and Korean text remain unchanged except ten-digit JSON integers: these
become EduOK label strings and restore as decimal text. A typed numeric field
fails the unchanged upstream schema before forwarding. There is no region,
date, address or
organization detector. Korean particles around a replacement remain unchanged.

The gate traverses every result text field and key, including JSON inside text,
plain error text, nested JSON strings, structured content, metadata and usage.
For mixed spellings, a uniquely echoed field or identifier restores its exact
original spelling. Otherwise a person's registered romanized spelling is used,
with the registered Hangul name as fallback. Numbers, booleans, fixed enums and
error status retain their types and meaning.

Schema-pattern fields reject matched identifiers instead of changing constrained
syntax: `jev_decide` candidate IDs, `jev_extract` field IDs and `jev_audit`
record IDs. Unsafe ID sanitization, invalid masked syntax and key collisions
also reject. Supported upstream `isError` results are restored and preserved.
Transport/protocol exceptions, unsupported content and gate failures return
only `Privacy gate rejected the call.`
It does not reveal the failing value, path or provider exception.

Only tools are exposed, alongside required MCP lifecycle messages. Resources,
resource templates and prompts are hidden and direct access rejects. Sampling,
elicitation, roots, continuations and untrusted logging/progress relays cannot
open another route. An integer progress counter is accepted and dropped;
string tokens and other application `_meta` keys reject. Backend SDK
counter/connection metadata contains no caller content.

Originals and stand-in pairs stay in memory for the call and are discarded on
success, failure, cancellation or timeout. No per-call files, persistent map,
seed, payload cache or ledger is created. Releasing Python references does not
promise physical memory erasure.

## Registered list and admission

The list is outside Git at
`<config>/verbose-broccoli/education-privacy-gate/registered-list.json`.
`<config>` is an absolute `XDG_CONFIG_HOME`, otherwise `~/.config`.
Callers pass only an absolute `XDG_CONFIG_HOME` so the proxy finds the
configured registered list.
Its directory is user-owned mode `0700`; the regular file is user-owned mode
`0600`. Unsafe permissions, ownership or symlink components reject a call.

[Format version 1](../specs/053-jev-mcp-privacy/data-model.md#persisted-registered-list)
stores only grouped real name spellings and school spellings. This example is
entirely fictional:

```json
{
  "version": 1,
  "entries": [
    {"kind": "person", "full": "가라온", "given": "라온",
     "romanized": ["Ga Raon"], "aliases": []},
    {"kind": "school", "spellings": ["가상별빛고등학교", "synthetic-school"]}
  ]
}
```

Person fields are `full`, optional `given`, `romanized` and `aliases`.
School entries have nonempty `spellings`. The file contains no role, source path,
student number, contact, score, date or stand-in. Only authorized source-owning
Claude Code/Codex sessions and the local gate process may read the real list.
Other-provider reviewers use synthetic fixtures.

Confirmed admission extends the list with names and school variants backed by
admitted sources. Validate the entire update before atomic publication; failed
updates preserve the previous file. Main handles real population and legacy
private data separately. This source change deletes no private data and does
not authorize deleting old lists, mapping tables, locks or paid results.

## Bounds, costs and limits

The [positive bounds](../specs/053-jev-mcp-privacy/data-model.md#positive-bounds)
reuse upstream schemas, the streamed 1,000,000-byte provider-response ceiling,
a default 60,000 ms upstream request timeout and default three attempts
(clamped to one through six). The FastMCP client timeout is explicitly 60
seconds. Noul allows 64 propositions of 2,000 characters each.

The list has a 1 MiB limit, at most 4,096 spellings and 256 characters per
spelling. The gate keeps a recursion guard, at most 128 matched identities and
256 candidate draws per identity. These controls do not establish a uniform
request/result ceiling or a production memory/CPU bound.

Missing controls include input ceilings for verify claims/evidence, screen
text/purpose and classification context, pre-parse stdio allocation limits and
a concurrency cap. Upstream support or a main-owned operating-system service
scope is the handoff; no custom framing, scheduler or body budget is supplied.

A browser run allows at most 120 gated tool-call attempts (`MAX_STEPS * 2`):
each operation or target request counts, including failures. The 60-action
guard is separate. Under the default OpenRouter route, the unmodified upstream
may make up to 3 fetch attempts per dispatched request, so up to 360 explicit
fetch attempts per run. `JEV_MCP_MAX_ATTEMPTS` defaults to 3 and is clamped
1-6; the proxy does not set it. Actual processed requests and billing are
unknown. The 1.7-second per-step startup figure comes from a mocked run only.

Provider calls spend OpenRouter credit, including retries. There is no automatic
credit check or provider switching. Inspect returned usage when supplied,
without treating it as billing proof. Payloads and mapping pairs must never
enter logs or traces; retain only aggregate synthetic-check receipts.

Unknown names and spellings pass unchanged. A missed Korean name can stand out
among English stand-ins. Labels and Faker names can repeat across calls.
Context, grades, classes and observations can identify people. Fresh maps do
not prove complete concealment or unlinkability. Changed stand-in wording can
prevent restoration. The gate does not establish legal compliance.

## Pins and review evidence

The npm lock pins `@jkudish/jev-mcp` 0.13.0 and its integrity; the published
source revision is `5e0ca5cacd1556dc0b8c227648843d3ebf5bdc93`.
Python pins include FastMCP 4.0.10, Faker 40.40.0 and phonenumbers 9.0.40.
See the [package](../packages/education-privacy-gate/package.json),
[npm lock](../packages/education-privacy-gate/package-lock.json),
[Python dependencies](../packages/education-privacy-gate/pyproject.toml) and
[independent dependency review](../specs/053-jev-mcp-privacy/security/dependency-review.md).

The 2026-10-04 review checked downloaded checksums, npm registry signatures
and static source. It approved adoption with conditions, not unconditional
security or live acceptance. Banner, update checks, env-file loading and
telemetry are disabled. The child gets three Jev variables plus the MCP SDK's
supported baseline environment, not only three total variables. Native Node is
resolved with `mise which node` from `/`, falling back to PATH when mise is
absent. Its working
directory is neutral; endpoint overrides, proxy variables and `NODE_OPTIONS`
are not inherited. The [synthetic integration procedure](../specs/053-jev-mcp-privacy/quickstart.md)
separates fixture checks from native-client acceptance.

## Policy sources and pending handoffs

The August 2024 education pseudonymization guideline motivates the design.
Printed p. 62 gives a conditional example retaining grade; printed pp. 113–114
provide reference risk rankings and alternatives. Combined attributes require
comprehensive risk review. The example prohibits resident-number use; masking
does not authorize it. See the [PIPC
listing](https://pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS217&mCode=D010030000&nttId=10425),
[verified guideline
PDF](https://www.sen.go.kr/component/file/ND_fileDownload.do?q_fileSn=2145906&q_fileId=55793d35-539a-4cf4-8620-79cdad5180c9)
and [source record](../specs/053-jev-mcp-privacy/spec.md#cited-sources).

[Carrell et al., JAMIA 2013;20(2):342–348](https://doi.org/10.1136/amiajnl-2012-001034)
provides motivation for realistic replacements from a small English clinical
pilot. It does not validate Korean education, Faker, provider attacks or
per-call unlinkability.

Credit-offers and Ultrafast browser-choice judgments use this proxy.
The text-generation helper stays held;
there is no authorized ungated student-data route. These
[migration
handoffs](../specs/053-jev-mcp-privacy/contracts/migration.md#chat-handoffs-exact-dependency-edges)
remain separate from repository documentation checks. The legacy judgment
implementation and its dependencies have been removed.

External client and provider-path activation waits for the first official
release and its fresh whole-repository review. Repository checks do not prove
that activation or real-list admission happened.
