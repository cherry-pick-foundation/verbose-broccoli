# Session selection

Offer the local Claude Code and Codex sessions to the Wiki vaults. The
sessions are rendered to Markdown, filtered, scanned for secrets and
classified by backfire; the user approves the lists, and the raw import
(steps 5 to 9 of [SKILL.md](../SKILL.md)) admits the rendered Markdown as
`files`. Exported Claude Code and Codex sessions are raw evidence in any
vault they belong to, but a session that names a student, guardian or school
goes only to `work`.

## Scope

- Claude Code sessions: `~/.claude/projects/<project>/<session-id>.jsonl`.
- Codex sessions: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`.
- Orca worker sessions are included and classified from their task and final
  report.
- Sessions of other agents, such as OMP, are out of scope. A session whose
  file changed in the last hour is still running; it waits for a later run.

## Folders and tools

`STAGE` is the absolute path of `CACHE/sessions/` (by default
`~/.cache/verbose-broccoli/sessions/`), mode `0700`, because it holds student data and may hold secrets. Everything in
it can be rebuilt from the original session files. Nothing in it goes into a
repository, a Linear issue or an Orca message; reports there give counts only.

The repository's `mise.toml` pins the two tools, and `mise.lock` holds their
reviewed checksums:

- SpecStory's command-line tool 2.15.1 (Apache-2.0) renders sessions to
  Markdown and redacts secrets it recognizes. It is used unchanged. By
  default it sends usage analytics, checks for updates, syncs to its cloud
  when logged in and copies full session text into a search index in its
  home folder; step 1 turns all of that off and runs it without network.
- betterleaks 1.9.0 (MIT) scans the rendered Markdown for secrets that
  SpecStory's redaction missed. It makes no network requests in `dir` mode.

Install them from the lock with `mise install --locked
github:specstoryai/getspecstory@2.15.1 github:betterleaks/betterleaks@1.9.0`
in a worktree whose `mise.toml` is trusted.

Run the commands from the repository root. `SELECT` stands for the line
below; the script's path is absolute because `--directory` changes the
working folder:

```sh
uv --directory packages/backfire run --frozen --offline --no-sync \
  python "$PWD/plugins/work/skills/wiki-raw-import/scripts/session_select.py"
```

## Procedure

1. **Render.** Run SpecStory with no network at all, inside bubblewrap:

   ```sh
   SELECT render --stage STAGE \
     --specstory "bwrap --unshare-net --dev-bind / / $(mise which specstory)"
   ```

   It calls SpecStory once per session with `sync -s <id> --print`, skips
   sessions still running and those already rendered from an unchanged
   file, and writes `STAGE/rendered/<claude|codex>/<session-id>.md` and
   `STAGE/sessions.jsonl`. SpecStory runs from `STAGE` with its home, cache
   and configuration inside `STAGE/specstory/`, with cloud sync, usage
   analytics, the version check and OpenTelemetry off, and with its own
   secret redaction on. Claude Code projects are mirrored into `STAGE` with
   hard links, because SpecStory finds no Claude Code sessions for a
   project folder that no longer exists; the originals are only read.
2. **Scan.** Run betterleaks from `STAGE`, without inherited configuration:

   ```sh
   scanner="$(mise which betterleaks)"
   (cd STAGE && env -u BETTERLEAKS_CONFIG -u GITLEAKS_CONFIG \
     -u BETTERLEAKS_CONFIG_TOML -u GITLEAKS_CONFIG_TOML \
     XDG_CACHE_HOME=STAGE/specstory/cache \
     "$scanner" dir STAGE/rendered -i STAGE/rendered \
     --no-banner --redact=100 -f json -r STAGE/scan.json)
   ```

   Exit 1 means it found secrets. Never add `--validation`, which sends
   found secrets to provider APIs. A session with a finding is held back in
   the next step and never sent to backfire. Tell the user how many sessions
   were held; do not show findings in any message.
3. **Digest.** Run `SELECT digest --stage STAGE --scan STAGE/scan.json`. It
   holds back sessions without a user message, those with a finding, and
   Codex's own approval reviews, which Codex starts by itself to judge an
   agent's action (`auto_review`); it tags
   Orca worker sessions and sessions in which backfire's roster finds a
   student, guardian or school (`student_data`), and writes one digest of at
   most 2,000 characters per session to `STAGE/digests.jsonl`. The roster check
   runs on this machine; an empty roster stops the step. It also stops when
   the scan report is missing or older than a rendered file, so run step 2
   again after every render. A roster match counts only at a word start, and a
   Latin-letter match only as a whole word, so a short given name inside a
   longer word does not tag a session; backfire still replaces every match
   before sending.
4. **Sample.** Before the first full run, run `SELECT classify --stage STAGE
   --catalog CATALOG --limit 64`, where `CATALOG` is
   `"$PWD/plugins/work/skills/wiki-raw-import/references/session-catalog.json"`.
   Report the backfire call count and the input and output tokens it prints,
   with an estimate for all digests, and wait for the user's go.
5. **Classify.** Run `SELECT classify --stage STAGE --catalog CATALOG`.
   Backfire runs in education mode, so
   names are replaced with pseudonyms before a digest leaves the machine.
   Sessions tagged `student_data` are classified only as `work` or `none`.
   Each result in `STAGE/labels.jsonl` has a label, its confidence and a
   decision: `auto`, or `review` when backfire is not sure.
6. **Decide with the user.** Show the counts per label and decision. Every
   `review` result is open: show its label, confidence and project path, and
   let the user choose a vault or `none`. The user may also change any `auto`
   result. Read a rendered session only when the user asks.
7. **Write the selections.** For each vault with approved sessions, write
   `STATE/vaults/<vault>/selections/sessions.jsonl` with one line per session:
   `{"path": "<absolute path of STAGE/rendered/...md>", "kind": "files"}`.
   Then follow steps 5 to 9 of [SKILL.md](../SKILL.md) for that vault. A
   rendered file keeps its path when it is rendered again, so a session that
   continued becomes a new revision of the same source.
8. **Clean up.** After every approved vault passes `verify`, delete `STAGE`'s
   contents. They are rebuilt by the next run.

## Catalog

[session-catalog.json](session-catalog.json) gives backfire the purpose and
the five labels: `work`, `code`, `default`, `chat` and `none` (no lasting
value). Its descriptions carry the decision: each says what belongs, what
does not and which label wins where they overlap. Change them only with the
user's agreement, and rerun the sample before a full run after a change.
