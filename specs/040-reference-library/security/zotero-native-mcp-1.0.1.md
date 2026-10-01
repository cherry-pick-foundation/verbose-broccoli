# zotero-native-mcp 1.0.1 security review

- Version: `1.0.1` (npm), repository `dvdsosa/zotero-native-mcp`
- Commit: `fc560ea7262da01bbadc1d7cfc9da7165970be6a` (the tarball's `gitHead`
  and the commit named in its build provenance)
- Review date: 2026-10-01
- Verdict: **acceptable for the planned use with the three controls below**
- Findings: **high 0, medium 2, low 2**
- Difficulty: **medium**

## Scope and method

This was a read-only source, package and dependency review. The planned use is
the work plugin's `reference-library` stdio server: `node
plugins/work/node_modules/zotero-native-mcp/build/index.js`, installed with
`npm ci --ignore-scripts` from `plugins/work/package-lock.json`, talking to
Zotero's local API through the socket on `127.0.0.1:23190`. The library holds
the user's own references; no student data goes into it.

The review read all of the runtime's JavaScript (`build/`, 2,246 lines in 13
files; the TypeScript source is not published, the maps were not needed). The
tarball was fetched with `npm pack zotero-native-mcp@1.0.1` into a scratch
folder, never executed from there, and compared with the installed copy.
Nothing in the repository was executed from the tarball. The server was run
once with an empty standard input under `strace -f -e trace=openat` to list
the packages it loads. Its tools were not called during the review; the live
tests are in `../evidence/live-tests.md`.

The identity was verified before use:

```text
$ npm view zotero-native-mcp@1.0.1 gitHead dist.integrity license
gitHead = 'fc560ea7262da01bbadc1d7cfc9da7165970be6a'
dist.integrity = 'sha512-4OJpKrFRiAmxYhthHsIXcgQT1ia2v/PKT/P9HESqspaMubcAbFu+QINKbKF/J2J5OXcuSws3x3BlN9H4/FfVAQ=='
license = 'MIT'
$ sha512sum zotero-native-mcp-1.0.1.tgz | cut -d' ' -f1 | xxd -r -p | base64 -w0
4OJpKrFRiAmxYhthHsIXcgQT1ia2v/...   (same as the registry and the lock file)
$ diff -r package/build ~/.local/share/mcp-servers/zotero/1.0.1/node_modules/zotero-native-mcp/build
(no output)
```

## Verdict

The server is small and local. It makes HTTP requests to one configurable base
URL, reads one local file store and, for file attachments, reads files the
caller names. It has no install script, no telemetry, no update path, no shell
or process execution and no dynamic code loading. Its tarball is built by
GitHub Actions from the named commit and carries an npm SLSA provenance record;
all 95 packages in the lock have verified registry signatures. The tools that
can erase data permanently are separable and are blocked in the clients (see
control 1).

Two risks stay material: any file the agent can name may be copied into the
library (F-01), and ordinary write tools overwrite fields with no undo (F-02).

## Findings

### F-01 — Medium — `zotero_attach_file` reads any absolute path the caller names

The tool accepts any absolute path, checks only that it is a regular file, and
in `imported` mode reads the whole file into memory and uploads it to Zotero's
storage; in `linked` mode it records the path. There is no allow-list, size
limit below 4 GB, or sensitivity check. An agent that follows a malicious
instruction could copy a private file into the library, which then syncs to
zotero.org if the user turned sync on. `zotero_get_attachment_path` likewise
returns the local path of any attachment.

Evidence: `build/tools/attachments.js:56-69` (`describeFile`, absolute and
regular-file checks only), `:128` (call), `:179` (`readFile(filePath)`),
`:189-215` (upload to the loopback receiver).

Control: do not attach student or other private files; the plugin's guidance
and the user's review of writes are the boundary. Whether the user syncs the
library is unknown to this review.

### F-02 — Medium — Update tools replace fields and Zotero keeps no undo

`zotero_update_item` and `zotero_update_collection` send a PATCH with the
fields the caller gives; array fields such as `creators`, `tags` and
`collections` are replaced as a whole. The only guard is a version check
against concurrent edits. `zotero_update_item` also accepts `deleted: true`,
which moves an item to the trash; that is reversible and not a way around the
permanent-delete block.

Evidence: `build/tools/items.js:311-345` (`fields` passed through as the PATCH
body), `:118-153` (`setTrashed` uses the same PATCH).

Control: none beyond reviewing agent writes; Zotero's trash and sync history are
the only recovery.

### F-03 — Low — The write key sits in a plain file the user's own processes can read

The key that authorizes writes is stored as JSON, partitioned by Zotero's
server ID, in `~/.config/zotero-native-mcp/keys.json`, created with mode 0600
and forced back to 0600 on every write. Any process of the same user can read
it, including an agent with file-read access. The key is sent only as the
`Zotero-API-Key` header to the configured base URL, so it leaves the machine
only if `ZOTERO_LOCAL_BASE_URL` is pointed elsewhere, over plain HTTP.
`ZOTERO_LOCAL_API_KEY` and `ZOTERO_LOCAL_KEY_STORE` change where it comes from.

Evidence: `build/keystore.js:12-60` (store, `mode: 0o600` at `:52`, `chmod` at
`:54`, path from `XDG_CONFIG_HOME` at `:58`); `build/client.js:76-79` (header);
`build/config.js:16-24` (environment). On this machine the file is
`-rw-------`; this review did not read its contents.

Control: keep the base URL a loopback address in `mcp.json`; never print or
copy the file. Denying agents a `Read` of that path in the clients is a cheap
further step that this feature does not apply.

### F-04 — Low — Two moderate advisories in dependencies that the server does not load

`npm audit` on the lock reports `fast-uri` (3.0.0–3.1.7, GHSA-hrr3-gc8f-f4qj,
host case normalization) and `ip-address` (≤10.7.0, GHSA-j6r3-76f7-8jcv and
GHSA-h3mg-xc3c-68pw, subnet checks and an unbounded parse diagnostic). The
second is pulled in only by the SDK's `express-rate-limit`, which serves the
SDK's HTTP transports. The stdio server never imports Express, Hono or
`ip-address`; the start-up trace opened only `zod`, `ajv` (with `fast-uri`),
`ajv-formats`, `zod-to-json-schema`, the SDK's own files and the connector.
`fast-uri` is used by `ajv` to resolve schema references in tool schemas the
server itself defines, not on request data.

Control: no change; re-run `npm audit` when the pin moves.

## What the tools can change or delete

The server registers 28 tools (`build/tools/*.js`). Read-only: status, list
libraries, field metadata, search, get item, children, full text, export, list
collections, get collection, list tags, saved searches, run a saved search,
list trash, attachment path. Writes that add or edit data: authorize, create
items, update item, create and update collection, add and remove items from a
collection, restore items and collections, attach file. Destructive:

| Tool | Effect |
| --- | --- |
| `zotero_delete_items` | Trashes up to 50 items; with `permanent: true` erases them and their attachment files (`build/tools/items.js:348-408`, `DELETE` at `:394`). |
| `zotero_delete_collection` | Trashes up to 50 collections; with `permanent: true` erases them (`build/tools/collections.js:190-250`, `DELETE` at `:237`). |
| `zotero_empty_trash` | Erases every item in the trash and its files; refuses unless `expectedCount` equals the trash size (`build/tools/items.js:462-516`, `DELETE` at `:508`). |

These three are the planned block. Nothing else issues a `DELETE`
(`grep -n DELETE build/*.js build/tools/*.js` lists exactly these three plus
the method list at `build/client.js:24`).

## Network access

The only network calls are the three `fetch` calls in `build/client.js`
(`:88` requests, `:200` server ID, `:283` authorization), all to
`config.baseUrl`, which is `ZOTERO_LOCAL_BASE_URL` or
`http://127.0.0.1:${ZOTERO_LOCAL_PORT:-23119}`. Requests have a 60-second
timeout (the authorization call waits up to 5 minutes for the dialog). There is
no other `fetch`, `http`, `net` or `dns` use in the runtime. The upload URL
Zotero returns is reduced to its path before use (`build/tools/attachments.js`,
`new URL(url).pathname`), so a hostile reply cannot redirect the bytes to
another host.

## Install path and runtime effects

`package.json` has no `preinstall`, `install`, `postinstall` or `prepare`
script (only `postbuild`, which does not run on install). The lock has 95
packages, none with `hasInstallScript`, none from outside
`registry.npmjs.org`. Licenses: MIT 85, ISC 7, BSD-3-Clause 2, BSD-2-Clause 1.
Process-wide effects of the server: the
network calls above, reads of the key store and of attachment paths, and writes
only to the key store. It spawns no process and uses no `eval` or
`new Function` (`grep` over `build/` finds none).

## Provenance and license

The tarball's registry signature verifies with `npm audit signatures`. Its
provenance record (`https://registry.npmjs.org/-/npm/v1/attestations/zotero-native-mcp@1.0.1`,
SLSA provenance v1) names the builder `github-hosted` runner, the workflow
`.github/workflows/publish.yml` on `refs/heads/main` of
`https://github.com/dvdsosa/zotero-native-mcp`, commit
`fc560ea7262da01bbadc1d7cfc9da7165970be6a`, and the subject digest equals the
lock's integrity. The package has one maintainer, so a compromised account
would still publish a new version; the lock pins this exact one.

The project is MIT licensed (`LICENSE`, "Copyright (c) 2026 David Sosa",
`package.json` `license: "MIT"`). The repository does not copy the code: the
lock fetches it at install, so no redistribution notice is needed. If the
package is ever copied into the repository, keep the license text.

## Required controls

1. Block `zotero_delete_items`, `zotero_delete_collection` and
   `zotero_empty_trash` in every client's own settings (Claude Code permission
   deny rules, Codex `disabled_tools`), and keep the block shown by a test.
2. Keep `ZOTERO_LOCAL_BASE_URL` a loopback address and the lock file the only
   source of the package; treat a changed version, resolved URL or integrity as
   a new review.
3. Put no student data and no private file into the library; agents attach only
   files the user names for this purpose.

## Verification record

Completed checks: tarball identity against the registry, lock and installed
copy; full read of the runtime JavaScript; `grep` for file, network, process
and dynamic-code use; the three destructive tools and their `DELETE` calls;
`npm audit signatures` and `npm audit` on the lock; the provenance record;
a start-up trace of the packages loaded; lock review for scripts, sources and
licenses.

Intentionally not run: the connector's tools (the live tests do that), the
repository workflow and verification (`npm run verify` runs later), and any
read of `keys.json`.
