# Feature Specification: English Vaults

**Feature Branch**: `feature/english-vaults`

**Created**: 2026-09-29

**Status**: Draft

**Linear issue**: CHE-25

**Input**: Linear issue CHE-25, "Write all vault content in English", and the
develop session's task brief of 2026-09-29. The user decided on 2026-09-29
that all vault content is written in English and that the vault schema says
so. Three things stay as they are: raw evidence is never changed; student and
school names keep the roster's spelling, so backfire's pseudonymization still
replaces them; and a short direct quote may stay in its original language next
to an English translation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pages are written in English (Priority: P1)

An agent that writes or fixes pages in any vault reads the vault's schema
before it starts. The schema tells it to write in English, even when the raw
evidence is in another language.

**Why this priority**: It is the user's decision and the purpose of the
feature.

**Independent Test**: Read the schema template and each document that
describes how vault pages are written; each states the rule.

**Acceptance Scenarios**:

1. **Given** a vault whose raw evidence is in Korean, **When** an agent reads
   the schema before writing a page, **Then** the schema tells it to write the
   page in English and to leave the raw evidence unchanged.
2. **Given** a page that names a student or a school, **When** the agent
   writes it, **Then** the schema tells it to keep the roster's spelling of
   the name.
3. **Given** a short direct quote from a source, **When** the agent writes it,
   **Then** the schema lets it keep the original language next to an English
   translation.

---

### User Story 2 - Existing vaults get the rule (Priority: P2)

The `default`, `chat` and `code` vaults already hold a copy of the schema
template. They get the new wording, so agents working there follow it.

**Why this priority**: The rule only takes effect in a vault whose schema
states it.

**Independent Test**: Each of the three vaults' `AGENTS.md` equals the
template, its Git log has one new commit, and the offline `check` passes.

**Acceptance Scenarios**:

1. **Given** the feature is finished into `develop`, **When** the template is
   copied into the three vaults, **Then** each vault gets one commit and its
   `check` exits 0.

### Edge Cases

- Mechanical regions are generated, not written by the agent; a
  `source_provenance` region may show an original file name as it is.
- The `work` vault keeps its schema until CHE-21 has translated its pages;
  the develop session then updates it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The shared schema template
  `plugins/work/skills/wiki-raw-import/assets/AGENTS.md` MUST state that the
  agent writes the vault's Wiki in English, whatever the language of the raw
  evidence, which stays unchanged.
- **FR-002**: The template MUST say that student and school names keep the
  roster's spelling, so backfire still replaces them, and that a short direct
  quote may keep its original language next to an English translation.
- **FR-003**: Every other document that describes how vault pages are written
  MUST state the rule briefly: the `wiki-consistency` skill,
  `docs/architecture.md` and the example schema `docs/examples/wiki/AGENTS.md`.
  Earlier features' Spec Kit records, such as feature 010's page contract,
  record what those features built and stay as they are.
- **FR-004**: After the feature is finished into `develop`, the `default`,
  `chat` and `code` vaults MUST get the template's new wording, one vault
  commit each, with the offline `check` passing.
- **FR-005**: The `work` vault, every raw revision, the constitution and the
  tools' code MUST NOT change. The wording MUST stay short and add no other
  rule.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The four documents of FR-001 to FR-003 state the rule, and the
  merge review finds no other document outside earlier features' Spec Kit
  records that describes page writing without it.
- **SC-002**: Three vault commits exist, each vault's `AGENTS.md` is
  identical to the template, and `check` exits 0 in each vault.
- **SC-003**: `deno task verify` passes on the feature branch.

## Assumptions

- The page language is a page convention, which constitution VI puts in each
  vault's schema. The constitution's rule that repository prose is English
  covers the repository, not the vaults, so the constitution does not change.
- The `wiki-raw-import` skill admits raw documents and is not for writing
  pages, so its `SKILL.md` does not change; its template does.
- The `default`, `chat` and `code` vaults hold no pages yet, so nothing needs
  translating there.
