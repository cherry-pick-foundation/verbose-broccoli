# Privacy Gate Contract

Normative design contract for FR-003 through FR-012. Assumption: follow D2-D6 subject to Root's pending romanization decision, and the proposed bounds in [data-model.md](../data-model.md). This defines planned behavior; it does not certify implementation.

## Surface and ordering

Expose only tools/list and tools/call plus required MCP initialization/lifecycle. Tool descriptions/schemas are trusted pinned upstream metadata; verify all 12 at discovery. Resources, templates and prompts are hidden and direct access rejects. Use a disconnected plain Client, no automatic ProxyClient relays. Reject sampling, elicitation, roots and InputRequired continuation; suppress untrusted progress/logging. `provider_error_strategy='raise'` and explicit timeout are mandatory (D3; FastMCP 4.0.10 proxy.py:173-212,479-655,724-818,1528-1779).

1. Validate bounded shape, registry snapshot and tool schema. Reject application request `_meta` before any forwarding, including values outside arguments. Allow only protocol-required fields proven value-free; do not forward arbitrary client/session identifiers.
2. Detect constrained-field violations. Build spans for registered spellings and the agreed patterns across every other string/key, including nested classification context.
3. Resolve overlaps on original text, draw collision-free replacements and swap in one pass. Revalidate the masked arguments against the unchanged upstream schema; reject key collisions or invalid syntax.
4. Forward through upstream transport; restore all result text/keys in one pass, check reverse collisions and the restored size, preserve types/status, then discard maps.

Overlap order: select longest span first, then resident number, EduOK, phone, e-mail, registered full person, explicit person alias, school, given alias. Numeric boundaries prevent partial pattern matches. Latin names use case-insensitive letter boundaries and known separators; Hangul given/full forms permit attached particles. Apply admitted school variants exactly with deliberate Latin boundaries. Do not infer organizations or arbitrary domains. Keep exact original substrings. Two different owners of the same full alias reject the registry; shared given forms remain ambiguous matches (current roster.py:78-99, pseudonymize.py:535-635; W3:60-68).

## Person and school stand-ins

Use Faker 40.40.0 ko_KR with independent `seed_instance(None)` per call. Full/given/Latin parts refer to one draw. Romanization adoption is PENDING: namefyi 0.1.3 is a candidate, pending decision, not an approved or complete Revised Romanization library. Main is asking the user; compare korean-romanizer and koroman in research.md and the [pending dependency review](../security/dependency-review.md). Without an adopted library, use only explicitly registered real romanized spellings and forms derivable from registered name parts; do not add local transliteration. If adopted, reviewed generated aliases supplement those spellings and use the same drawn parts. Explicit real aliases remain authoritative. For a Hangul ending, prefer the same coda class: none, rieul, other consonant. This supports 은/는, 이/가, 을/를 and 으로/로 without rewriting surrounding particles. Exhaustion of that compatible class fails closed within 256 draws. Non-Hangul endings have no guaranteed particle fit (D5-D6; W2).

Schools use numbered `School NN` labels, including registered website IDs, full Korean spellings and short variants. Numbering is call-local, starts at 01 and can repeat on later calls. Person aliases and school variants must remain reversibly distinguishable when different originals appear together. School labels do not promise particle fit. No stored stand-in list exists and encountering an old fake name does not refuse a call.

Reject/redraw any candidate whose full/given/Latin/mask spelling collides with any registered spelling, original request text/key, or another current stand-in. Check substring replacement ambiguity in both directions, not only equality. Same-person full/given parts may overlap only when longest-first replacement has an unambiguous reverse mapping. Check constraints after replacement. No silent best-effort fallback on exhaustion (Design; D5).

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

Upstream lib.js:22-43 sanitizes some IDs to ASCII, truncates to 64 and generates fallbacks. Swapping a Hangul stand-in may lose the reversible token. Validate this in the all-tool fixture; fail before forwarding when a sensitive ID's stand-in cannot survive known schema/sanitization behavior. Do not send its real spelling or invent a general ID translation layer. Non-sensitive IDs preserve upstream's normal behavior. This limitation is distinct from the D4 pattern fields.

JSON map keys are text. Swap both keys and values, reject duplicate keys after masking/restoration, and bound nested objects/lists. No opaque/base64/binary result content or unrecognized content subtype is relayed without an admitted contract. Unsupported result types return generic error, not unchanged payloads (D2-D3; W2).

## Result restoration and failure

For each text block, parse JSON when valid, restore all string values and keys recursively, then serialize. Apply the same decoding/restoration to nested JSON-encoded strings, within the same depth/work bounds; escaping must not hide a supported text field. Restore plain text/errors directly when not JSON. Outer `content[].text` is always covered; JSON escape sequences must not prevent restoration. Walk `structured_content` and allowed `meta` recursively if present, plus supported text-bearing model fields. Treat usage as unvalidated arbitrary data: do not assume token counts are numbers. Preserve fixed enums, numbers, booleans, null and `is_error` (D2; W1:133-153).

No outputSchema exists in the selected package. If an upgrade adds one, pause for compatibility review; do not drop it to accommodate restored text. Restoration covers unchanged stand-in spellings. Truncated, translated or otherwise altered names are a documented limit; no fuzzy reverse guess. If a known reverse collision/unsupported result prevents safe restoration, return generic error.

Return generic `isError=true` text for rejected input, backend error, unsafe result, cancellation or timeout. Do not return raw exception strings, original paths, list contents, pairs or stderr. Upstream error results may use the normal restoration walk only when their type/bounds are allowed. Malformed input never starts a provider request; cancellation releases maps and closes/reaps the request's supported client scope. A bad call must not poison the next valid call. Error category/count may be recorded without payloads; no persistent per-call ledger is added.
