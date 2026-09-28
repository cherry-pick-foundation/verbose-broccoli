# Data Model: Backfire for Education Work

The rules live in the contracts; this file names the entities and their
relations.

## Roster (operator's file, read only)

- Fields per row: `name` (required), `school`, `guardians` (list).
- Owner: the operator and the system the list comes from (EduOK for now).
- Read at every judgment of a work build; never copied or written.
- Source of the identifiers of kinds `student`, `given`, `guardian` and
  `school` ([pseudonymization.md](contracts/pseudonymization.md#identifiers-and-their-kinds)).

## Identifier (in memory, one judgment)

- Fields: kind, normalized value, the text spans it matched.
- Derived from the roster (exact match, given names) or from format rules
  (phone, email).
- Lives only for one call.

## Pseudonym

- Fields: prefix (by kind) and number (at least two digits).
- One per identifier digest, assigned once, never changed or reused.

## Mapping table (data file)

- Fields: `version`, `key` (random, per machine), `counters` (per prefix),
  `entries` (identifier digest to pseudonym).
- Grows only. Written under a lock, all or nothing, at most 1 MiB, mode `0600`.
- Holds no names, schools or contact details.

## Restoration map (in memory, one judgment)

- From each changed question key, option label and level description to the
  agent's original string.
- Built during replacement; a collision there is `pseudonym_conflict`.
- Used once on the answers, then dropped.

## Plugin build

- Fields: plugin name, plugin files, packages, shipped profile source
  ([build.md](contracts/build.md)).
- Code: `backfire` and the development profile. Work: `backfire`,
  `backfire_education` and the education profile with `pseudonymize = true`.

## Provider profile

- As in feature 005. The development profile is `[providers.hive]`; the
  education profile is `[providers.education]` with the same values and the
  credential file `education.env`.

## Education measurement case

- Fields: `id`, `tool`, `language`, `kind`, `arguments`, `expect`
  ([measurement.md](contracts/measurement.md)).
- Outcome per run and arm: correct, wrong, or failed with an error type.
