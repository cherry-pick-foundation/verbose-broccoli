# Feature Specification: Clean Architecture Migration

**Feature Branch**: `feature/clean-architecture`

**Created**: 2026-10-06

**Status**: Draft for implementation planning

**Linear issue**: Awaiting the develop coordinator; none assigned at specification time.

**Input**: The user's 2026-10-06 decision to redesign the whole workspace as capability packages with inward dependencies, thin plugin delivery, configurable Jev and GLM judgments, and small separately reviewable migration slices.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Change a capability without changing its delivery (Priority: P1)

A maintainer changes the rules of one capability without needing a running
model server, filesystem, client application or other plugin. The same capability
remains available through its existing commands and library interfaces.

**Why this priority**: Separation must improve maintenance without losing working
behavior. An independently checked component is the smallest useful migration.

**Independent Test**: Migrate document-region checking alone. Run its existing
tests and existing command/library acceptance cases before and after; test its
rules without external processes, then test real delivery with synthetic files.

**Acceptance Scenarios**:

1. **Given** a working capability and its recorded contract, **When** its
   implementation is reorganized, **Then** its callers receive the same results,
   exit classifications, supported errors and storage effects.
2. **Given** an internal rule test, **When** external services and writable
   user storage are unavailable, **Then** the rule can still be exercised.
3. **Given** a forbidden dependency from an inner rule to delivery or storage,
   **When** repository checks run, **Then** the dependency fails validation.
4. **Given** a held consumer on another feature, **When** its dependency moves,
   **Then** the consumer's supported interface remains usable without editing
   that consumer's owned files.

### User Story 2 - Use either approved judgment backend (Priority: P1)

The operator chooses Jev or GLM for supported semantic judgments using private
configuration. Both are working options in the first judgment-backend slice.
Model and worker selection always uses Jev, regardless of the general setting.

**Why this priority**: The user explicitly chose both backends from the first
version; GLM is a requested capability, not an optional later experiment.

**Independent Test**: With synthetic, non-personal inputs, exercise the same
judgment operation on both configured backends and confirm the reported route.
Verify that model selection uses Jev when general judgments use GLM.

**Acceptance Scenarios**:

1. **Given** an approved Jev setting, **When** a supported judgment is requested,
   **Then** Jev answers and its provider/model evidence identifies that route.
2. **Given** an approved GLM setting, **When** the same judgment takes longer
   than the former 60-second limit, **Then** it can finish within the configured
   timeout and identifies GLM as the answering model.
3. **Given** a failed route or invalid answer, **When** the application handles
   it, **Then** it reports failure without changing backend silently.
4. **Given** synthetic identifying education content, **When** either backend
   is used, **Then** the existing privacy protection masks before transmission,
   restores supported returned text and retains no call-specific mapping.
5. **Given** GLM as the general backend, **When** a worker/model selection is
   requested, **Then** the answering model is Jev or the selection stops.

### User Story 3 - Finish the whole move in usable slices (Priority: P2)

The operator receives a sequence of small migrations, each usable, reviewed and
verified on its own. Packages under active development wait for their owners;
approved replacement trials are incorporated before the affected code is moved.

**Why this priority**: A whole-workspace change must remain understandable and
recoverable while other features continue development.

**Independent Test**: Inspect a slice's scope, baseline and resulting contracts,
run its checks and full verification, and confirm that held paths and live user
data have not changed. Repeat after the current integration base changes.

**Acceptance Scenarios**:

1. **Given** a ready migration slice, **When** it is presented for integration,
   **Then** its estimate, measured diff, behavior evidence and independent review
   are recorded without claiming completion of later slices.
2. **Given** another feature owns a component, **When** scheduling its migration,
   **Then** the component waits for that owner's release and current sources are
   reread before work starts.
3. **Given** an approved replacement trial for existing implementation, **When**
   planning its migration, **Then** that implementation is excluded until the
   trial outcome is known, and surviving replacement glue is planned explicitly.
4. **Given** the complete migration, **When** any one of the three plugins is
   selected, **Then** its declared capabilities resolve through its documented
   delivery route without deep imports of another plugin's private files.

### Edge Cases

- An installed dependency moves while an unmigrated consumer still imports its
  public interface or presently relied-on helper.
- A command runs from another working directory or as a copied plugin skill.
- A package contains only integration behavior; no empty business-rule layer or
  fake entity is created merely to match a diagram.
- A configuration variable is empty, relative or missing; supported storage
  defaults and error behavior must remain explicit.
- A provider times out, supplies malformed output or changes its tool schema.
- A rejected request must not disable continued service for valid requests.
- Develop changes between verification and integration, or an active feature
  changes the component originally inventoried.
- An interrupted write leaves user data or recovery ownership at risk; existing
  cleanup and recovery guarantees must remain covered.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Organize every surviving executable capability in a component
  package with inward source dependencies; delivery, settings and external
  effects must not be dependencies of business rules or use-case policy.
- **FR-002**: Keep exactly the `code`, `work` and `chat` Agent Plugins 1.0 roots.
  Plugins deliver and compose skills, server declarations and thin entries;
  reusable implementation belongs to capability packages.
- **FR-003**: Preserve each moved component's supported command, library,
  protocol, storage, error and recovery behavior, documented and tested against
  the pre-move baseline with synthetic fixtures.
- **FR-004**: Reject forbidden layer imports and package cycles mechanically in
  repository verification, including a deliberate violation test.
- **FR-005**: Keep rule, integration and complete-entry tests distinguishable
  within each capability, using real installed implementations where practical.
- **FR-006**: Add a shared package only for a demonstrated second consumer. Add
  ports only for required external conversations, with no general framework or
  package for each architecture ring.
- **FR-007**: Keep settings and credentials in their approved XDG locations;
  read them at composition boundaries and preserve supported defaults. Code
  restructuring must not move live data or change external client settings.
- **FR-008**: Provide one provider-neutral judgment boundary backed by the
  gated jev-mcp client; configuration chooses Jev on OpenRouter or GLM 5.3 Flash
  on Hive through TypeSafe's system-one-adapter-compatible endpoint.
- **FR-009**: Make both judgment routes operational in the first backend slice,
  using existing typed upstream tools rather than reimplementing their protocol,
  retry policy, status mapping or answer validation.
- **FR-010**: Keep worker/model selection Jev-only and verify returned route
  evidence; a different general backend cannot substitute for that decision.
- **FR-011**: Apply the existing education privacy gate before either backend
  sees education content; no direct ungated student-data route is introduced.
  Acceptance uses synthetic identities, never real student records.
- **FR-012**: Support an explicit GLM request timeout above the former 60-second
  limit and align transport timeouts so a valid slow answer is not cancelled
  earlier by the caller. Do not silently retry on another provider.
- **FR-013**: Obtain an evidence-backed read-only security review before adopting
  system-one-adapter or any other new third-party implementation.
- **FR-014**: Complete the whole specification, plan, task sequence and
  consistency analysis before implementation; publish the owned-code estimate
  before starting each planned build and update it from measured results.
- **FR-015**: Begin with document regions, credit offers, Clean Code, workflow
  and small-script slices. Wait for the gate bug's coordinated disposition and
  active work/wiki/browser owners before their respective migrations.
- **FR-016**: Exclude implementations undergoing the approved rulesync, chezmoi,
  session-scan and Jev Browser replacement trials until their outcomes are
  integrated or explicitly released by develop.
- **FR-017**: Run the required workflow and behavior checks for every slice;
  preserve earlier verification evidence, pass full verification on the current
  integration base and obtain a fresh review from another provider before merge.
- **FR-018**: Keep all existing license/provenance and portable resource
  requirements valid, update current documentation and delivery references, and
  avoid unrequested client distribution formats or release frameworks.

### Key Entities

- **Capability**: An existing user-facing or maintenance operation with owned
  rules, external conversations, public delivery and tests.
- **Judgment request/result**: A supported typed semantic question and its
  answer, route evidence, uncertainty and failure state.
- **Judgment profile**: Private backend, endpoint, credential reference and
  timeout settings; model-selection policy restricts which profile may be used.
- **Migration slice**: Bounded capabilities, current owners, prerequisite holds,
  baseline contract, code estimate, verification and review evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every migrated capability passes 100% of its preserved acceptance
  cases before and after the move. An unperformed required case prevents slice
  acceptance; each slice also records any unperformed optional check.
- **SC-002**: Every migrated capability has an isolated rule/use-case check and
  a real-entry acceptance check; deliberate forbidden dependencies fail checks.
- **SC-003**: Both selected backends complete representative non-personal
  judgments; a synthetic slow response beyond 60 seconds is accepted inside the
  selected timeout, and a response beyond that timeout fails explicitly.
- **SC-004**: Synthetic privacy cases preserve masking/restoration on both
  routes, and every accepted model-selection call reports Jev as its model.
- **SC-005**: All three plugins remain independently selectable through their
  declared portable route; moved implementations have no cross-plugin deep import.
- **SC-006**: Every slice has an estimate, measured change, passing full check
  result and independent merge review; zero held components or live data roots
  are modified without their owner releasing the boundary.

## Assumptions

The existing behavior is the migration baseline. This feature changes structure
and adds the two explicitly chosen judgment routes; it does not invent new
education workflows, alter retention, publish a site or migrate user data.

The 2026-10-06 backend choice supersedes the earlier OpenRouter-only and
no-GLM decisions. Model-choice remains Jev-only. Jev and GLM are important
working integrations; deterministic rules remain deterministic. No arbitrary
paid-call quota or line-count cap is added.

Use the user's supplied repo-convention and Google-guide captures as references,
with the current constitution and explicit user decisions governing conflicts.
These selected public guides and the 2026-10-06 structure trial are inputs to
this current redesign, not evidence or implementation from an earlier project.
Nested instruction files are added only for recurring judgments. Empty rings and
test directories are not committed without useful content.

Develop owns the issue, integration slots, merges and final task ticks. This
specification can be prepared while develop is unavailable; the missing issue
is an administrative dependency, not a missing user requirement.
