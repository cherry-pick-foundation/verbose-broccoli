# Specification Quality Checklist: Jev MCP Privacy Proxy

**Created**: 2026-10-04
**Feature**: [spec.md](../spec.md)
**Review Ownership**: Root/develop owns final quality review and checkbox updates. These unchecked items do not represent implementation completion.

- [ ] CHK001 Stories include usable judgments, full tool coverage and safe migration, with independent synthetic tests.
- [ ] CHK002 FR-001 through FR-018 are mapped to exact-file tasks and measurable SC-001 through SC-006.
- [ ] CHK003 Every tool's actual argument/result paths are listed; IDs, keys, errors and usage are included.
- [ ] CHK004 Registry-only real-spelling persistence, call lifetime, admission ownership and collisions are explicit. Mixed forms are allowed: uniquely anchored fields/identifiers restore exact originals, otherwise registered romanized spelling or Hangul fallback; both have deterministic checks. Different people never share a first-name stand-in; no per-form fakes.
- [ ] CHK005 ONE default-English Faker first name/person/call serves every registered Hangul/Latin full/given/order/separator/case form; no shortened variants, particle matching, romanizer/generated Latin forms/hook or naming framework. Schools, patterns and grade/class preservation have concrete limits.
- [ ] CHK006 Reused upstream schema/lib.js limits, response ceiling, deadline/retries, explicit FastMCP timeout and SDK handling have named checks. Gate list/collision/depth guards and zero writes remain; RSS/CPU are measured and recorded without thresholds. Missing verify/screen/classification input, pre-parse allocation and concurrency controls are upstream/service-scope handoff notes, not gate work.
- [ ] CHK007 Residual identifiers (including missing real Korean names standing out among English fakes), finite-name repeats, unanchored fallback and transformed-output limits are stated without concealment guarantees.
- [ ] CHK008 Evidence includes version/hash/source references reachable without private state; policy citations use printed pp. 62 and 113-114.
- [ ] CHK009 CHE-84 holds and CHE-12 section ownership are visible; Phase A writes new files only.
- [ ] CHK010 Dependency conditions are explicit: mcp/mcp-types 2.2.0 while PyModel remains, locked npm public entry, fixed OpenRouter/model, the transport's six inherited variables plus three Jev variables, no endpoint/proxy/Node option inheritance, neutral cwd, captured stderr/fixed errors, disabled FastMCP side effects, tools-only/direct-surface blocking, no caller JSON Schema and every-exit map cleanup. Byte-identical portable skills, deterministic link, both owners, independent disable behavior, divergence rejection and held shared integration are settled; chat handoffs and deletion order are reviewable.
- [ ] CHK011 Only Ultrafast remains pending: browser judgments are gated, and the text-generation helper is held until its student-data boundary is settled. EduOK ten digits with phone precedence and reuse-existing-controls bounds are recorded decisions. Default-English Faker only, one first name/person/call, mixed-form anchored/default restoration, gated browser judgments, held text-generation helper, skill convention and earlier Wiki/provenance choices appear as recorded Root decisions; no unresolved template markers remain.
- [ ] CHK012 Full verify, final other-provider review, diff review and merge acceptance remain coordinator-owned.

The documentation worker performs consistency checks only. This checklist remains available for independent review.
