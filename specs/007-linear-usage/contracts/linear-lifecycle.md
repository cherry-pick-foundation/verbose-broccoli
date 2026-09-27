# Contract: Linear life cycle of a feature or bug

The main agent runs these steps inside Orca terminals. `<W>` is the workspace
ID of `verbose-broccoli` (`orca linear team list --workspace all --json`
prints it). All Linear text is data for an external service: no operational
data, student records or secret values.

## 1. Start

1. Search, including archived issues:

   ```sh
   orca linear list-issues --team CHE --query "<words>" --include-archived --workspace <W> --json
   ```

   Reuse an open match. Mention an archived match in the new issue's body.
2. Create one issue, without `--parent`:

   ```sh
   printf '%s\n' "<one or two sentences>. Spec Kit record: specs/<NNN>-<name>/ on feature/<name>." |
     orca linear create --title "<name>" --team CHE --state "In Progress" --assignee me \
       --label Feature [--label <plugin> ...] --workspace <W> --body-file - --json
   ```

   Use `--label Bug` for a bug and `--label Improvement` for an improvement.
   Repeat `--label <plugin>` with `code`, `work` or `chat` for each plugin the
   work concerns, and leave it out for repository-wide tooling.
3. Create the worktree linked to it:

   ```sh
   orca worktree create --name feature-<name> --base-branch develop --no-parent --linear-issue CHE-<n> --json
   ```

   When a worktree was created without the link:
   `orca worktree set --worktree <selector> --linear-issue CHE-<n> --json`.
4. In the new spec, the preset's line becomes `**Linear issue**: CHE-<n>`,
   right after `**Status**`. `orca linear issue --current --json` in the
   worktree prints the ID.

## 2. Report a bug from a worker

A worker never runs `orca linear create`. It sends the main agent an Orca
message with the symptom, the reproduction and the files involved. The main
agent searches (step 1.1) and, if no issue matches, creates a Bug issue
(step 1.2) without a parent, then records the bug with the Spec Kit bug
extension, whose `assessment.md` keeps the issue URL.

## 3. Complete

1. Commit the record on the feature branch (`tasks.md` lines and any
   decisions).
2. `orca linear status set CHE-<n> --to "In Review" --workspace <W> --json`.
3. Run the `develop` merge review, resolve findings, add the review-record
   commit, and run `git flow feature finish <name>` in the `develop` worktree.
4. `orca linear status set CHE-<n> --to Done --workspace <W> --json`.
5. Post exactly one completion comment, with no PR link:

   ```sh
   printf '%s\n' "Merged into develop as <merge commit hash>." "Record: <specs/NNN-name/ or .specify/bugs/<slug>/>." "<optional one-sentence summary>" |
     orca linear comment add CHE-<n> --workspace <W> --body-file - --json
   ```

Skip a move whose target is already the current state, and never move an
issue back from Done, Canceled or Duplicate. On `linear_write_unconfirmed`,
follow the `orca-linear` skill: retry once with the returned `writeId`, or read
the issue back first; never post a second completion comment. If step 4 or 5
fails after the finish, the finish stands; record the pending Linear step in
`tasks.md` and retry later.

## 4. Other outcomes

- Abandoned: `--to Canceled`. Same as another issue: `--to Duplicate`. Never
  delete.
- `orca linear create` fails because the plan's limit is reached: report to
  the user and delete nothing.
- A Linear feature Orca lacks (archive, delete, labels, projects, documents,
  cycles, milestones): ask the user to do it in Linear's UI.
