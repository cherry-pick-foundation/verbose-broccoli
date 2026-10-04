# Data Model: Jev MCP Privacy Proxy

Assumption: one versioned UTF-8 JSON list file is the minimum format. Bounds below record Root's reuse-existing-controls decision, not runtime acceptance or resource measurements. Authority: Design, D5-D7 as superseded by Root's latest English-first-name/mixed-form amendment, and constitution VI/VII; evidence labels are in [research.md](research.md#evidence-register).

## Persisted registered list

Location contract: `<config>/verbose-broccoli/education-privacy-gate/registered-list.json`, where config is absolute XDG_CONFIG_HOME or HOME/.config for unset, empty or relative values. Keep it outside Git. CHE-86 owns one narrow seam: a single function returns this registry config directory; do not migrate Backfire path code or author another shared helper. The separate future VERBOSE_BROCCOLI_HOME feature will own shared path resolution per language and later integrate this seam. Unset preserves today's XDG behavior; when set, config/data/state/cache sit below that root with the same application-relative paths. No global XDG override, file move or agent CLI home change is part of CHE-86. Its parent is user-owned mode 0700; the file is user-owned regular mode 0600. Refuse symlink components and unsafe ownership/modes before forwarding. Credentials remain in existing protected provider configuration; they are not a new gate data store.

Built format (the example is entirely fictional):

```json
{
  "version": 1,
  "entries": [
    {
      "kind": "person",
      "full": "가라온",
      "given": "라온",
      "romanized": ["Ga Raon"],
      "aliases": []
    },
    {
      "kind": "school",
      "spellings": ["가상별빛고등학교", "가상별빛고", "synthetic-school"]
    }
  ]
}
```

These are invented fixtures. Person entries store only real-source name spellings and their name-part grouping, needed for consistent stand-ins. School entries store spelling variants of one school, including website IDs. `kind` is person or school; no role, source path, student number, score, contact, date or pseudonym is stored. Student, teacher and source-backed guardian names use the same person kind. Admission includes teacher names from existing admitted teacher columns and guardian names only where an admitted source supplies them. Do not invent a teacher/guardian source when absent. JSON's strict shape catches typos; a version supports explicit migrations without a new database.

`full` is required; `given` is an optional admitted/validated part. `romanized` stores full-name spellings in surname-first order; flexible reverse/separator forms are derived in memory using existing matcher semantics. `aliases` holds explicit full-name variants. Faker only: no romanizer dependency, generated Latin spellings or optional romanize hook. The list keeps only registered real spellings; matching order, separator and case variants of a REGISTERED Latin spelling follow existing roster semantics in memory and are not new spellings. Every registered Hangul/Latin full/given form and matching order/separator/case variant uses the SAME single default-English Faker first name for that person per call. Short Latin aliases are derived only when the surname/given split is known; do not guess a split for an arbitrary preferred spelling. Compound Hangul surname handling follows current roster.py:17-21. Unknown name structures need explicit given parts. Schools require a non-empty `spellings` array. Empty strings, unknown fields and duplicate raw JSON member keys reject.

Exact duplicate entries may deduplicate during admission. Conflicting aliases reject an update. A given form shared by multiple people is an ambiguous given-name match with its own per-call stand-in; it must not resolve to one person. The full name is authoritative. Search normalization never becomes an identity key (constitution III). Canonical normalization for matching may use NFC; retain the exact request substring for restoration.

Only authorized source-owning Claude Code/Codex sessions and the local gate process may read the actual list. Other-provider reviewers use synthetic fixtures. During confirmed raw admission, the admission owner derives source-backed names and school variants, validates the entire list and atomically publishes mode-0600 bytes in the existing config tree. Readback verifies count/shape/permissions without exposing values. Interrupted updates retain the prior valid list; no source-admission log or second private table is added by the gate. Each call reads a bounded snapshot; no mid-call list change alters its map. Real population/migration is held for main and is not performed by this feature worker (Design; plugins/work/AGENTS.md:22-26).

## In-memory per-call mapping

Create registry matchers, an isolated Faker generator, matched-span replacements, reverse spellings and school/pattern counters for one call. The map lifetime is preflight through restoration, then discard in finally on return, cancellation or error. Never write originals, pairs, fake seeds or request/result bodies to files, traces, caches or exception logs. Release references; Python does not promise physical RAM erasure.

One real person draws ONE Faker 40.40.0 default-English first name per call. All registered Hangul/Latin full/given forms and matching order/separator/case variants use that SAME first name; no shortened variants, per-form fakes or naming framework. Mixed forms are allowed. Where an echoed field/identifier uniquely anchors an original spelling, restore that exact original; otherwise restore the person's registered romanized spelling, or the Hangul name if no romanized spelling is registered. Preserve within-call identity and test both anchored and default restoration. Keep exact matched substrings and only the call-local field/identifier anchors needed to restore them; do not persist anchors, pairs or defaults. Different people never share a stand-in. Same-school variants use separate School NN labels per distinct matched spelling while grouping remains call-local. Pattern labels remain `Phone NN`, `Email NN`, `EduOK NN`, `Resident number NN`.

EduOK detection uses isolated ten-digit strings and `s-<ten digits>` page IDs. phonenumbers runs first: accepted phone spans stay `Phone NN`, otherwise an isolated ten-digit span uses `EduOK NN`. Numeric boundaries exclude nine/eleven-digit runs and ten digits inside longer runs. Resident numbers remain 13 digits with an optional separator after digit six. Ten-digit JSON integers (excluding booleans/floats) become `EduOK NN` strings; decimal digits are retained for text restoration. A typed numeric field fails unchanged upstream schema validation before forwarding. Other numeric learning values and grades/classes remain unchanged (`masking.py:111-112`; `test_privacy_gate.py:384-413`).

Reject/redraw when a candidate occurs in an original request string/key. Registered spellings and other stand-ins are checked in both substring directions (`masking.py:179-201`). Check the single first-name stand-in and masks; check any shortened form actually used without adding such forms to this design. Check key uniqueness after forward and reverse walks. Prefer longest span; resolve ties as [privacy contract](contracts/privacy-gate.md) states. At most 128 distinct matched identities/spellings and 256 candidate attempts per identity; exhaustion rejects before forwarding. Old persisted fake names have no special meaning. Random repeats across calls are allowed, since no history is kept (Design; W2 Faker findings).

## Positive bounds

Reuse the actual controls of the selected tools, runtime and schemas. Tests below exist under `packages/education-privacy-gate/tests/`; no measurements are claimed here. Do not impose a new whole-request/result byte budget, provider deadline, CPU/memory threshold or concurrency scheduler.

| Owner                        | Control reused or kept                                                                                                                                                                                                            | Proving check                                                                                                                       |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Upstream tool schemas/lib.js | Preserve each tool's existing limits; `jev_noul` keeps 64 propositions of 2,000 characters each. Other per-tool limits remain as shipped, not a new uniform input ceiling (W1:174,183-203; dist/server.js:282-298; dist/lib.js).  | test_upstream_tools.py: boundary/over-bound cases for actual limited fields, unchanged captured schemas and upstream behavior       |
| Upstream response            | 1,000,000 bytes streamed on the selected OpenRouter route; this limits the provider response, not every decoded MCP/restored result (W1:167-181; dist/provider.js:31,94-136,261-305).                                             | test_upstream_tools.py: synthetic streamed boundary/over-bound response and recovery                                                |
| Upstream deadline/retries    | `JEV_MCP_REQUEST_TIMEOUT_MS` defaults to 60,000 ms; `JEV_MCP_MAX_ATTEMPTS` defaults to 3, clamped 1-6. Reuse them without another retry engine (W1:71; dist/provider.js:20-29,168-193).                                           | test_upstream_tools.py: controlled deadline/retry evidence and generic outward error                                                |
| FastMCP/MCP SDK              | The FastMCP client timeout is explicitly 60 seconds (`__main__.py:214-237`). Reuse SDK message handling, without claiming a pre-parse allocation ceiling.                          | test_proxy.py: explicit client configuration, controlled timeout/cancellation and next-call recovery                                |
| Gate list storage            | 1 MiB (1,048,576 bytes), 4,096 registered explicit spellings (full, explicit given, aliases, romanized forms and schools; repeats count), and 256 characters per spelling. Derived/Unicode-variant patterns have a separate ceiling of 65,536 (16 times the registered bound). Positive storage limits apply before atomic publication; failed updates keep the old file.                                                              | test_registry.py: byte/count/spelling boundaries, failed/interrupted update retains old bytes                                       |
| Gate collision exhaustion    | 256 draws per identity, 128 identities.                                                                                                                                                                                           | test_privacy_gate.py: forced collisions exhaust at the bound with zero forwarding                                                   |
| Gate tree walk               | Recursion-safety depth guard for argument/result keys, values and nested JSON decoding; reject with the fixed generic error before recursion overflow. The built depth guard rejects depths above 64; no extra node/work budget (`masking.py:71-73`). | test_privacy_gate.py: depth boundary/one-over and next-call recovery                                                                |
| Gate per-call storage        | Zero files written per call; no persistent mapping, seed or payload store.                                                                                                                                                        | test_proxy.py: filesystem/syscall observation on success, failure and cancellation, with bytecode writes disabled                   |
| Fixture observation          | Record peak proxy+child resident set size (RSS) and CPU for a large synthetic call, including large restored output. These are MEASURED, not enforced by the gate.                                                                | test_proxy.py: retain actual peak RSS, CPU, fixture shape and hardware; no pass/fail threshold other than recording the measurement |

Missing controls are handoff notes, not gate work:

| Missing control                             | Evidence/limit                                                                              | Upstream or service-level option to ask for                                                                                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `jev_verify` claims/evidence input ceilings | Unbounded by schema in stdio (W1:174; dist/server.js:95-97; independent security review).   | Ask upstream for schema input ceilings, or main for an operating-system resource scope at the service level.                                          |
| `jev_screen` text/purpose input ceilings    | Unbounded by schema in stdio (W1:174; dist/server.js:216-220; independent security review). | Ask upstream for schema input ceilings, or main for an operating-system resource scope at the service level.                                          |
| Classification context input ceiling        | Unbounded by schema in stdio (W1:174; dist/server.js:443-446; independent security review). | Ask upstream for a context schema limit, or main for an operating-system resource scope at the service level.                                         |
| Pre-parse stdio frame/allocation ceiling    | FastMCP decoded-result limits do not bound raw frame allocation.                            | Ask FastMCP/MCP SDK upstream for a supported pre-parse limit, or main for an operating-system resource scope at the service level; no custom framing. |
| Concurrency cap                             | No gate-owned cap or queue is built; call maps still stay isolated.                         | Ask upstream for supported concurrency control, or main for an operating-system resource scope at the service level.                                  |

Do not file upstream issues or change service scopes as part of this feature's documentation work. Main owns any service-level resource change. Measurements do not establish bounded production memory/CPU or complete concealment.

The only persistent writer here is admission. It enforces the list budget before publication, removes its own failed temporary stage, and preserves the prior list on interruption. Tool calls write nothing. Required immutable aggregate test receipts use task state, not the registry. See quickstart.md for the synthetic integration route.
