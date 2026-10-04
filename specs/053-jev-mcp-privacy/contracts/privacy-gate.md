# Privacy Gate Contract

Normative design contract for FR-003 through FR-012. Assumption: follow D2-D6 subject to Root's latest default-English Faker, single-first-name and mixed-form restoration amendment, and proposed bounds in [data-model.md](../data-model.md). This defines planned behavior; it does not certify implementation.

## Surface and ordering

Expose only tools/list and tools/call plus required MCP initialization/lifecycle. Tool descriptions/schemas are trusted pinned upstream metadata; verify all 12 at discovery. Resources, templates and prompts are hidden and direct access rejects. Use a disconnected plain Client, no automatic ProxyClient relays. Reject sampling, elicitation, roots and InputRequired continuation; suppress untrusted progress/logging. `provider_error_strategy='raise'` and explicit timeout are mandatory (D3; FastMCP 4.0.10 proxy.py:173-212,479-655,724-818,1528-1779).

1. Validate bounded shape, registry snapshot and tool schema. Reject application request `_meta` before any forwarding, including values outside arguments. Allow only protocol-required fields proven value-free; do not forward arbitrary client/session identifiers.
2. Detect constrained-field violations. Build spans for registered spellings and the agreed patterns across every other string/key, including nested classification context.
3. Resolve overlaps on original text, draw collision-free replacements and swap in one pass. Revalidate the masked arguments against the unchanged upstream schema; reject key collisions or invalid syntax.
4. Forward through upstream transport; restore all result text/keys in one pass, check reverse collisions and the restored size, preserve types/status, then discard maps.

Overlap order: select longest span first, then resident number, EduOK, phone, e-mail, registered full person, explicit person alias, school, given alias. Numeric boundaries prevent partial pattern matches. Latin names use case-insensitive letter boundaries and known separators; Hangul given/full forms permit attached particles. Apply admitted school variants exactly with deliberate Latin boundaries. Do not infer organizations or arbitrary domains. Keep exact original substrings. Two different owners of the same full alias reject the registry; shared given forms remain ambiguous matches (current roster.py:78-99, pseudonymize.py:535-635; W3:60-68).

## Person and school stand-ins

Use Faker 40.40.0 DEFAULT ENGLISH locale with independent `seed_instance(None)` per call; draw ONE `first_name()` per real person. Every registered Hangul full/given and Latin/romanized full/given form, including order/separator/case variants of a registered spelling, uses that SAME single fake first name. No shortened variants, per-form fakes, naming framework, romanizer dependency, generated Latin spellings or optional romanize hook. Persist only registered real spellings; matching variants follow existing roster semantics in memory and are not new spellings. Explicit real aliases remain authoritative; do not guess name-part splits. There is no final-consonant/particle rule and surrounding Korean particles remain unchanged (Root amendment 2026-10-04).

Schools use numbered `School NN` labels, including registered website IDs, full Korean spellings and short variants. Numbering is call-local, starts at 01 and can repeat on later calls. Mixed forms are allowed. Where an echoed field/identifier uniquely anchors an original spelling, restore that exact original; otherwise restore the person's registered romanized spelling, or the Hangul name if no romanized spelling is registered. Preserve within-call identity and test both anchored and default restoration. Do not reject mixed forms merely because they share one person's first-name stand-in. Deterministically anchored inputs/results must test each original spelling, along with unanchored registered romanized/Hangul fallback. School variants receive distinct call-local labels when different originals appear together. No stored stand-in list exists and encountering an old fake name does not refuse a call.

Reject/redraw a candidate whose single first-name stand-in or mask collides with any registered real full/given/Latin spelling, original request text/key or another current stand-in. Different people must never share a stand-in; include any shortened form actually used in checks, without adding shortened variants. Check substring replacement ambiguity in both directions, not only equality, and check masked/restored key uniqueness. Mixed forms of one person remain valid under the anchored/default restoration rule. Enforce 256 draws per identity and 128 identities; exhaustion fails before forwarding with fixed generic error. No silent best-effort fallback (Root amendment 2026-10-04; Design).

## Identifier patterns

| Kind            | Planned detection                                                                                                               | Label / limits                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Phone           | phonenumbers 9.0.40 PhoneNumberMatcher(text, 'KR'), exact returned spans, E.164 only for internal grouping                      | Phone NN; parser does not cover arbitrary digit strings                             |
| E-mail          | existing bounded e-mail pattern semantics from pseudonymize.py:16,696-699                                                       | Email NN; test boundaries and overlap, not an RFC-completeness claim                |
| EduOK           | provisional explicit EduOK/student-number labels and `s-<digits>` page components; proposed 1-12 digits with numeric boundaries | EduOK NN; Root must confirm lengths and bare/numeric forms before acceptance        |
| Resident number | isolated six digits + optional separator + seven digits, with numeric boundaries; no date/checksum requirement                  | Resident number NN; invalid-date shapes still mask; contiguous 13-digit shapes mask |

Do not persist student numbers to extend matching. Root question 1 is an admission-format release gate. A plain number is not identifiable as an EduOK ID without a format or source relation. All other numeric/boolean schema arguments stay unchanged. Numeric identifiers in open context must be rejected or masked under an agreed numeric-ID policy before real education rollout; do not claim string-only matching covers them.

Grades/classes, school years, scores, dates, regions, addresses and learning observations stay unchanged unless they overlap a registered spelling or covered pattern. Remove cohort/date/address/region/labeled-field/table-column detectors and blanket Hangul refusal. No new organization detector (Design; W3:66-70).

## Schema-sensitive inputs

D4: inspect inputSchema `pattern` at the exact field. Never swap such fields. If they contain a registered spelling or a covered identifier pattern, reject the whole call before upstream; otherwise preserve the original schema-valid string. In 0.13.0 this applies to `jev_decide.candidates[].id`, `jev_extract.fields[].id` and `jev_audit.records[].id` (W1 argument table; server.js:594,882-885,1079).

Other IDs, paths and regex literals are swapped. `fields[].pattern` is executable RegExp source, not a JSON Schema `pattern` constraint on that string. Rewriting it may change matches; test literal names and capture groups against the actual upstream engine, and reject invalid masked regex with a generic error. `flags` are preserved when enum/syntax-valid and free of a registered spelling, otherwise revalidation rejects. Never access or rewrite the file denoted by `files[].path`.

Upstream lib.js:22-43 sanitizes some IDs to ASCII, truncates to 64 and generates fallbacks. Sanitizing or truncating a first-name stand-in may lose the reversible token. Validate this in the all-tool fixture; fail before forwarding when a sensitive ID's stand-in cannot survive known schema/sanitization behavior. Do not send its real spelling or invent a general ID translation layer. Non-sensitive IDs preserve upstream's normal behavior. This limitation is distinct from the D4 pattern fields.

JSON map keys are text. Swap both keys and values, reject duplicate keys after masking/restoration, and bound nested objects/lists. No opaque/base64/binary result content or unrecognized content subtype is relayed without an admitted contract. Unsupported result types return generic error, not unchanged payloads (D2-D3; W2).

## Result restoration and failure

For each text block, parse JSON when valid, restore all string values and keys recursively, then serialize. Apply the same decoding/restoration to nested JSON-encoded strings, within the same depth/work bounds; escaping must not hide a supported text field. Restore plain text/errors directly when not JSON. Outer `content[].text` is always covered; JSON escape sequences must not prevent restoration. Walk `structured_content` and allowed `meta` recursively if present, plus supported text-bearing model fields. Treat usage as unvalidated arbitrary data: do not assume token counts are numbers. Preserve fixed enums, numbers, booleans, null and `is_error` (D2; W1:133-153).

No outputSchema exists in the selected package. If an upgrade adds one, pause for compatibility review; do not drop it to accommodate restored text. Restoration covers unchanged stand-in spellings. Truncated, translated or otherwise altered names are a documented limit; no fuzzy reverse guess. Use exact originals where a returned field/identifier uniquely anchors them; otherwise use the registered romanized spelling or Hangul fallback. Do not guess a mixed-form original without an anchor. If a different-person reverse collision, key collision or unsupported result prevents safe restoration, return generic error.

Return generic `isError=true` text for rejected input, backend error, unsafe result, cancellation or timeout. Do not return raw exception strings, original paths, list contents, pairs or stderr. Upstream error results may use the normal restoration walk only when their type/bounds are allowed. Malformed input never starts a provider request; cancellation releases maps and closes/reaps the request's supported client scope. A bad call must not poison the next valid call. Error category/count may be recorded without payloads; no persistent per-call ledger is added.

## Dependency-review acceptance conditions

These conditions implement the committed [independent review](../security/dependency-review.md), findings F1-F7, F14-F17 and Q1; the historical review is unchanged. T006/T007 must prove them with synthetic captured requests/results, launch parameters and stderr.

Use the locked npm public entry only: `node <absolute path>/dist/index.js`, from the reviewed closure installed with `npm ci --ignore-scripts`. Never use unpinned npx, deep imports, `--http` or a direct registered child. Force OpenRouter and `JEV_MCP_MODEL=typesafe/jev-1.13`; the recording fetch must observe only `https://openrouter.ai/api/alpha/decisions`.

Supply only three Jev variables through `env=`: `JEV_PROVIDER=openrouter`, `OPENROUTER_API_KEY` and `JEV_MCP_MODEL`. The REAL child environment bound also includes `HOME`, `LOGNAME`, `PATH`, `SHELL`, `TERM`, `USER`, inherited by the public MCP transport (review Q1, mcp 2.2.0 client/stdio.py:40-55,75-86,128). Do not claim exactly three total environment variables. Reject inheritance of endpoint/provider overrides, proxy variables or `NODE_OPTIONS`; do not reimplement transport to promise a stronger bound. Set a neutral cwd explicitly.

Capture child stderr with `log_file=` and proxy stderr in a controlled sink; planted synthetic identifiers must be absent. Raise and return fixed generic errors, never raw exceptions. Disable FastMCP update check (`FASTMCP_CHECK_FOR_UPDATES=off`), banner (`show_banner=False`), env-file loading (neutral startup directory or an empty `FASTMCP_ENV_FILE`) and telemetry (`FASTMCP_TELEMETRY_MODE=off`; no SDK/exporters). Observe zero per-call writes and no extra network target.

Expose tools only and block resources/templates/prompts on direct access as well as listing; callbacks, relays and continuations remain disabled. Never pass caller-supplied JSON Schema to the SDK. Clear call-local maps on every exit, including preflight refusal, success, backend failure, cancellation and timeout; prove next-call recovery and no cross-call restoration.

The acceptance Python environment uses `mcp==2.2.0` and `mcp-types==2.2.0` while `jev-judge-mcp` (PyModel) remains. Repeat synthetic protocol fixtures there. The earlier 2.3.0 prototype is research evidence, not integration acceptance. Faker 40.40.0 and phonenumbers 9.0.40 stay; no romanizer belongs in the dependency pins or test environment.
