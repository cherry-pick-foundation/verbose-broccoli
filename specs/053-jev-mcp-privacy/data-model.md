# Data Model: Jev MCP Privacy Proxy

Assumption: one versioned UTF-8 JSON list file is the minimum format. Bounds below are proposed acceptance defaults, not results of W1/W2. Authority: Design, D5-D7 and constitution VI/VII; evidence labels are in [research.md](research.md#evidence-register).

## Persisted registered list

Location contract: `<config>/verbose-broccoli/education-privacy-gate/registered-list.json`, where config is absolute XDG_CONFIG_HOME or HOME/.config for unset, empty or relative values. Keep it outside Git. CHE-86 owns one narrow seam: a single function returns this registry config directory; do not migrate Backfire path code or author another shared helper. The separate future VERBOSE_BROCCOLI_HOME feature will own shared path resolution per language and later integrate this seam. Unset preserves today's XDG behavior; when set, config/data/state/cache sit below that root with the same application-relative paths. No global XDG override, file move or agent CLI home change is part of CHE-86. Its parent is user-owned mode 0700; the file is user-owned regular mode 0600. Refuse symlink components and unsafe ownership/modes before forwarding. Credentials remain in existing protected provider configuration; they are not a new gate data store.

Proposed format:

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

`full` is required; `given` is an optional admitted/validated part. `romanized` stores full-name spellings in surname-first order; flexible reverse/separator forms are derived in memory using existing matcher semantics. `aliases` holds explicit full-name variants. Romanizer adoption is PENDING: namefyi is a candidate, pending decision, alongside korean-romanizer and koroman (research.md). Without adoption, use explicitly registered real romanized spellings and forms derivable from registered name parts only; with adoption, reviewed library-generated aliases supplement them in memory and map to the same fake parts. Short Latin aliases are derived only when the surname/given split is known; do not guess a split for an arbitrary preferred spelling. Compound Hangul surname handling follows current roster.py:17-21. Unknown name structures need explicit given parts. Schools require a non-empty `spellings` array. Empty strings, unknown fields and duplicate raw JSON member keys reject.

Exact duplicate entries may deduplicate during admission. Conflicting aliases reject an update. A given form shared by multiple people is an ambiguous given-name match with its own per-call stand-in; it must not resolve to one person. The full name is authoritative. Search normalization never becomes an identity key (constitution III). Canonical normalization for matching may use NFC; retain the exact request substring for restoration.

Only authorized source-owning Claude Code/Codex sessions and the local gate process may read the actual list. Other-provider reviewers use synthetic fixtures. During confirmed raw admission, the admission owner derives source-backed names and school variants, validates the entire list and atomically publishes mode-0600 bytes in the existing config tree. Readback verifies count/shape/permissions without exposing values. Interrupted updates retain the prior valid list; no source-admission log or second private table is added by the gate. Each call reads a bounded snapshot; no mid-call list change alters its map. Real population/migration is held for main and is not performed by this feature worker (Design; plugins/work/AGENTS.md:22-26).

## In-memory per-call mapping

Create registry matchers, an isolated Faker generator, matched-span replacements, reverse spellings and school/pattern counters for one call. The map lifetime is preflight through restoration, then discard in finally on return, cancellation or error. Never write originals, pairs, fake seeds or request/result bodies to files, traces, caches or exception logs. Release references; Python does not promise physical RAM erasure.

One person draws separate surname/given parts. Full, given and generated Latin forms refer to those same parts. Each exact original substring is remembered so case, spaces, hyphens and Unicode bytes can restore. If distinguishable originals collapse to one stand-in, allocate a distinct collision-free spelling or reject rather than guessing. Same-person full/given parts may overlap when longest-first restoration is unambiguous. Different matched original spellings must never share an indistinguishable reverse token. Same-school variants need distinguishable reversible spellings if both occur together; School NN labels increment per distinct matched spelling while grouping remains call-local. Pattern labels remain `Phone NN`, `Email NN`, `EduOK NN`, `Resident number NN`.

Reject/redraw stand-ins overlapping registered originals, any original request string/key or another stand-in in either replacement direction. Check full/given/Latin variants and masks, not just full fake names. Check key uniqueness after forward and reverse walks. Prefer longest span; resolve ties as [privacy contract](contracts/privacy-gate.md) states. At most 128 distinct matched identities/spellings and 256 candidate attempts per identity; exhaustion rejects before forwarding. Old persisted fake names have no special meaning. Random repeats across calls are allowed, since no history is kept (Design; W2 Faker findings).

## Positive bounds

All byte sizes use UTF-8 serialized JSON, including keys and envelopes. Measure original and masked request and upstream and restored result. Limits apply to the whole request, not only claims. Tests below are planned under `packages/education-privacy-gate/tests/`; no measurements are claimed here.

| Bound            | Proposed limit/expectation                                                                                    | Proving check                                                                                                               |
| ---------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Request          | 262,144 bytes before and after masking                                                                        | test_privacy_gate.py: exact-boundary accepts, one-byte-over rejects; upstream capture is empty on refusal                   |
| Result           | 2,097,152 bytes before and after restoration                                                                  | test_privacy_gate.py: expansion over limit returns generic error; no partial result escapes                                 |
| List             | 1,048,576 bytes and 4,096 total explicit/derived match spellings, each <=256 characters                       | test_registry.py: byte/count/alias-expansion boundary and failed update retain old bytes                                    |
| Tree work        | depth 64; 50,000 visited values/keys                                                                          | test_privacy_gate.py: deepest/one-over and many-short-value requests avoid recursion overflow                               |
| Per call         | 60 seconds including connection/call/restore; cancellation propagates                                         | test_proxy.py: clock-controlled timeout and next valid call; fixture stays <=10 seconds                                     |
| Draws/map        | 128 identities/spellings, 256 draws each                                                                      | test_privacy_gate.py: forced collisions exhaust at the bound with zero forwarding                                           |
| Concurrency      | two active calls; excess calls reject generically, no unbounded queue                                         | test_proxy.py: three simultaneous calls, both active maps remain isolated                                                   |
| Memory           | peak combined proxy+child RSS <=768 MiB at these bounds                                                       | test_proxy.py: synthetic maximum request/result/list under OS resource observation, record actual peak                      |
| CPU              | local masking/restoration <=2 CPU seconds per maximum-size call; batch checks stay on cores 4-7, CPUWeight=20 | test_proxy.py: process-tree CPU delta excluding provider wait, record worst fixture and hardware                            |
| Per-call storage | zero regular files or persistent bytes written by proxy/child                                                 | test_proxy.py: filesystem snapshots plus syscall/write observation, including failure/cancellation; disable bytecode writes |

Use upstream deadlines and FastMCP timeout; do not implement another transport, retry engine or scheduler. The result limit is checked after FastMCP materializes a decoded message, not a hard stdio frame/allocation ceiling. RSS and CPU are measured acceptance expectations, not claims of a pre-parse sandbox. If a large child frame violates them, stop adoption acceptance and report a supported upstream/native limit option to Root. Do not add custom framing. An authorized OS memory/CPU scope can bound controlled tests; production service changes belong to main.

The only persistent writer here is admission. It enforces the list budget before publication, removes its own failed temporary stage, and preserves the prior list on interruption. Tool calls write nothing. Required immutable aggregate test receipts use task state, not the registry. See quickstart.md for the synthetic integration route.
