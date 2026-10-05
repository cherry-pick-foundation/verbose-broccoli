# Feature Specification: Wiki container naming

**Feature Branch**: `feature/wiki-container-naming`
**Created**: 2026-10-05
**Status**: Approved for implementation
**Linear issue**: CHE-90
**Input**: Use `llm-wiki` for the shared container and wiki for each instance.

## User Scenarios & Testing

### User Story 1 - Use the renamed container (Priority: P1)

The user can select default, chat, code or work without depending on the
old container link, while keeping the same evidence and knowledge history.

**Why this priority**: The physical move is complete; repository tools still
select the former folder.

**Independent Test**: Synthetic instances exist only below llm-wiki; run
instance resolution and the import/check command paths for all four names.

**Acceptance Scenarios**:

1. **Given** four synthetic wikis below llm-wiki and no former link, **When**
   a named command runs, **Then** it selects that wiki and preserves its data.
2. **Given** no explicit selection, **When** a command runs, **Then** it uses work.
3. **Given** a raw evidence folder, **When** session staging selects it,
   **Then** staging is refused before any write.

### User Story 2 - Understand the names and readiness (Priority: P2)

The user sees one consistent current naming convention and knows which
installed or active consumers need updating before removing the old link.

**Why this priority**: Old instructions or copied tools can still depend on the link.

**Independent Test**: Inspect current repository wording and read-only consumer
metadata, separating historical and upstream wording from current Wiki usage.

**Acceptance Scenarios**:

1. **Given** current Wiki instructions, **When** the user reads them, **Then**
   the container is llm-wiki and each instance is a wiki.
2. **Given** installed or active consumers, **When** readiness is reported,
   **Then** remaining old builders and inspection limits are identified.

### Edge Cases

Unset, empty and relative XDG settings retain their HOME defaults. Invalid
instance names remain refused. Custom instance names remain supported.
An unchanged initialization preserves existing bytes. Historical records and
external password-vault terminology retain their meaning.

## Requirements

### Functional Requirements

- **FR-001**: Current tools MUST select data under `verbose-broccoli/llm-wiki/<name>`;
  the four supported names MUST work without the former container link.
- **FR-002**: Default selection MUST remain work; custom names and existing
  name validation and XDG fallback behavior MUST remain supported.
- **FR-003**: Session staging MUST refuse renamed Wiki raw folders before writing.
- **FR-004**: Current Wiki-domain instructions, schemas and documentation MUST
  use wiki for an instance and llm-wiki for the container, preserving historical
  records, upstream vocabulary and unrelated uses.
- **FR-005**: Consumer readiness MUST identify inspected active/installed paths
  and remaining old builders without reading protected contents.
- **FR-006**: The feature MUST preserve raw bytes, originals and all four Git
  histories; it MUST NOT move data, remove the link, change clients, admit or
  convert real sources, edit private wikis or publish anything.

### Key Entities

A container holds named Wiki instances. A consumer resolves those instances
through a live checkout, linked skill or installed copy. A temporary link
supports consumers awaiting updates; main alone owns its removal.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All four named synthetic wikis work with no former container link.
- **SC-002**: Focused regression checks fail against the previous builders and
  pass against the renamed builders; synthetic evidence stays unchanged.
- **SC-003**: Every in-scope current Wiki instruction uses the chosen terminology.
- **SC-004**: The readiness report identifies each inspected consumer and every
  known remaining old builder, with all unperformed live checks stated.

## Assumptions

The existing name selectors and XDG conventions suffice. No new compatibility
layer or registry is needed. Main already moved the real repositories and
retained their link. Consumer inspection is read-only and limited to paths,
public code and metadata. Root owns integration, Linear and final ledger ticks.
