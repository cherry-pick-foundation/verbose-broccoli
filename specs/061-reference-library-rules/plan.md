# Plan

Write plugins/work/skills/reference-library/SKILL.md and references/sources.md;
link .agents/skills/reference-library using the existing relative-link convention.
Keep work skills in plugins/work/skills until the separate relocation feature.
Follow spec 058's compact spec, plan and tasks layout. Refresh the generated
skill table in docs/architecture.md with npm run doc-regions:update.

Use the source's primary contribution to distinguish the five selected homes.
An education result using AI belongs in education; an agent technique belongs
in agent tooling. Subject-specific standards follow their subject; knowledge
organization standards belong in knowledge management. Unclear items remain
unfiled for triage questions. This resolves the single-home requirement without
adding a collection, vocabulary namespace or library operation.

Keep each rule's supporting source nearby and distinguish user policy from
upstream capabilities. Cite all eight listed sources; the local API is reference
context, not an assertion that writes are available. Use existing skill validation
and link tests; prose review checks policy coverage and boundary examples.
No executable code or new dependencies are needed. Estimated prose: about 200
lines. The initial draft measures 270 prose lines plus one link; one coherent
rules skill stays together, below the 1,000-line split-review trigger.

Branch: feature/reference-library-rules from develop. Workflow task:
reference-library-rules; baseline: e5745d6330edee45d0e1613daf9a5fe9a1d3d017.
Run workflow policy before and after edits, focused checks, then npm run verify.
Commit with task trailers and push only to the local origin. Submit WHA-4 to its
configured CEO review stage. The CEO owns final review and its review-record commit;
Main owns the privacy gate and develop integration. No implementation self-approval.
