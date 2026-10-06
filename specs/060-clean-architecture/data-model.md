# Data Model: Clean Architecture Migration

This migration introduces no database or parallel development-memory registry.
Existing application records remain authoritative. These shapes describe
boundaries and task evidence, not new persistence schemas.

## Capability Boundary

A capability has its existing distribution/import name, supported commands or
library entries, inner rules, required external ports, real adapters, one
composition entry and meaningful tests. The composition entry accepts the real
project/instance root and resolves private settings at the outer boundary.
Public package exports may forward to inner owners without duplicating behavior.

No business entity is invented for an integration-only capability. Existing
document units, problems, source revisions, offer records and workflow reports
keep their current field meanings and identity rules.

## Judgment Request and Reply

A request names an existing upstream tool and supplies its published arguments.
Its reply retains upstream JSON fields, probabilities, route evidence and
explicit errors. Inner use cases consume provider-neutral values; MCP envelopes,
process launch, credentials and environment fields belong to adapters.
Do not create a second schema/validator for all twelve upstream tools.

## Judgment Profile

The chosen general backend is Jev or GLM. Composition maps the selected profile
to existing upstream provider/model/endpoint/key/timeout settings. A profile
holds a credential-file reference, never a committed credential value.
The model-selection purpose permits only the Jev profile and verifies the
returned provider/model. Invalid or missing settings fail through the existing
entry's error contract; no profile is selected silently after a call fails.

The candidate configuration is documented in [contracts/judgments.md](contracts/judgments.md).
This feature does not write live operator settings or register another server.

## Migration Slice Evidence

Each slice records its scope, current source base, public contract, owners and
holds, measured source/test size, estimate, checks actually run, independent
review and integration result. Spec Kit plus Git and the existing Orca Run own
those facts; immutable attempt receipts live in approved XDG state.

A slice progresses from planned or held to implemented, verified, independently
reviewed and merged. Base drift invalidates prior final verification/review.
Develop alone records final merged task ticks. Planning or a collected test
inventory never advances an implementation task to complete.
