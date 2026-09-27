# Data Model: Linear Usage Through Orca

## Linear issue

One to-do entry in team `CHE` (workspace `verbose-broccoli`).

| Field | Rule |
| --- | --- |
| ID | `CHE-<n>`, assigned by Linear |
| Title | The feature's or bug's name; no private data |
| Body | One or two sentences and the record location it will have (for example `specs/007-linear-usage/` on `feature/linear-usage`); no private data |
| Type label | Exactly one of Feature, Bug, Improvement |
| Plugin labels | Zero or more of `code`, `work`, `chat`: the plugins the work concerns; none for repository-wide tooling |
| Parent | Always empty (no sub-issues) |
| Comments | At most one completion comment written by the main agent |

### States

```text
Backlog / Todo ──start──▶ In Progress ──record committed──▶ In Review
                                                               │
                                          finish into develop  ▼
                                                             Done ──(1 month)──▶ archived
Any open state ──abandoned──▶ Canceled      Any open state ──same as another──▶ Duplicate
```

- Only the main agent changes a state.
- A state never moves backward from Done, Canceled or Duplicate.
- Nothing is deleted; Linear archives closed issues after the team's
  auto-archive period, and `orca linear list-issues --include-archived` still
  finds them.

## Worktree link

Orca metadata (`linkedLinearIssue`) that ties one worktree to one issue. Set
by `orca worktree create --linear-issue CHE-<n>` or, when missed, by `orca
worktree set --worktree <selector> --linear-issue CHE-<n>`. `orca linear issue
--current` reads it inside the worktree.

## Spec line

Exactly one line in a feature's `spec.md`, in the header after `**Status**`:

```text
**Linear issue**: CHE-<n>
```

## Record

The repository's durable account, citing the issue ID: `specs/<NNN>-<name>/`
for a feature, `.specify/bugs/<slug>/` for a bug (its `assessment.md` holds the
issue URL), and a lesson line in `AGENTS.md` or `plugins/<name>/AGENTS.md` when
it holds across features.

## Completion comment

One comment on the issue after the finish into `develop`; see
[contracts/linear-lifecycle.md](contracts/linear-lifecycle.md) for its form.
