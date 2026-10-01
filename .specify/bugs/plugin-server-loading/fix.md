# Bug Fix: Plugin server loading

- **Slug**: plugin-server-loading
- **Fixed**: 2026-10-02
- **Assessment**: ./assessment.md
- **Status**: applied

## T001: Patch

Code declares `backfire-code`; Work declares `backfire-education` with
`--education`, alongside `reference-library`. Server implementations are unchanged.
`scripts/plugin-clients.ts` copies local resources with Node's filesystem API,
resolves checkout dependency paths, and generates a Claude manifest pointing
to the same `mcp.json` that Codex reads. `npm run plugins:prepare` first uses
the existing schema validation. Canonical manifests remain hand-maintained;
client packages and their marketplace are derived under ignored `.local/`.

Preparation rejects duplicate server identities, nonlocal resource links and
output above 16 MiB. Fixed staging and recovery paths prevent accumulation;
failure keeps the completed output, and the next invocation recovers an
interruption between directory renames. The distribution must be prepared
from the permanent `develop` checkout before saved-client installation.
Backfire and the connector are not repackaged or published.

Implementation choice supplied by develop: Jev on OpenRouter,
`typesafe/jev-1.13`, chose Codex (probability 0.74, confidence 0.69),
`gpt-6.1-sol` (0.95, 0.94), xhigh (0.91, 0.90); difficulty difficult.
The dispatch's usage snapshot was Codex weekly 69%, Claude session 23% and
weekly 56%, Copilot monthly 16.1%, with Antigravity unread, Cursor capped
until 16 October and Grok's rolling cap active. No usage reserve was imposed.

## T002: Validation and review

`scripts/plugin-skills-test.ts` now checks the two modes and the prepared
distribution. It checks source readback, copied-client paths, regeneration
after a source edit, malformed input, duplicate identities, interrupted
replacement, resource links and the storage budget. The mode regression was
run before the fix and failed on the old `backfire` name.

Architecture prose, the operator guide, Work's Wiki instruction and generated
references describe the resulting source and loading paths. Lint excludes the
ignored generated area; its fixture failed before this exclusion and passed
afterward. Review choice used one local Backfire
Jev call: Claude Code Sonnet, high effort, 600 seconds (probability 0.71,
confidence 0.63). Its live usage was session 28%, weekly 56%, Fable weekly 8%.
The choice names OpenRouter and `typesafe/jev-1.13` in its actual response.
The native launch uses the full `claude-sonnet-5-5` ID, as develop requires;
the reviewer receives scope and requirements only. Actual assistant model
metadata must be read back before accepting that review.

## Scope and remaining boundaries

Necessary consumer documentation, generated references and the generated-area
lint exclusion follow the loading change. No global client settings changed;
only selected saved-client server metadata was read. No credentials, vaults,
roster, raw material or saved sessions were changed or read. Saved settings
require a concrete preview and main's approval;
develop has authorized supported cache refresh after the distribution fix.
