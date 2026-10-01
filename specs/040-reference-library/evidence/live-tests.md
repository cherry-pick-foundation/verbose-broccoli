# Live tests, 2026-10-01

Run on the user's machine (Zotero 10.0.5, systemd 259, Node 24.19.0, Claude Code
2.1.286, Codex 0.159.2) after the develop session recorded the user's approval
(install the units and the shortcut; edit the two client settings files with
dated backups; run these tests). Times are KST. The units are the final design:
socket on `127.0.0.1:23190`, then `systemd-socket-proxyd`, then Caddy on
`127.0.0.1:23191` (Host rewrite), then Zotero on `127.0.0.1:23119`.

## 0. Findings that changed the design

1. First live test, units without Caddy: the first request started Zotero in
   1 s, but every proxied request got `400 Bad Request`. Zotero's web server
   (Mozilla httpd.js) accepts only a Host header whose port is its own:

   ```text
   Host: 127.0.0.1:23119  200      Host: localhost:23119  200
   Host: 127.0.0.1:23190  400      Host: localhost:23190  400
   Host: [::1]:23119      400      Host: 127.0.0.2:23119  400
   ```

   Also ruled out: Node's `NODE_USE_ENV_PROXY` (it tunnels with CONNECT and
   Zotero answers 404), `localhost` (resolves to 127.0.0.1 only here), and a
   changed Zotero port (the browser extension would start Zotero on every
   ping). The user chose Caddy (`../security/caddy-2.11.4.md`).
2. With the first unit design (`ExecCondition` skips the app unit when an open
   app answers), a request that arrived while the app was open left the proxy
   running; after the app closed, requests got `502 Bad Gateway`, and each
   failed request kept the proxy alive. The app unit now holds one idle
   connection to an open app (`socat`), and the proxy is `BindsTo` the app unit,
   so the chain ends when the app closes (test D). Zotero keeps an idle
   connection open (45 s checked) and `socat` exits with status 0 when Zotero
   stops.
3. The first shortcut quoting passed `desktop-file-validate` but GLib refused
   it (`gio launch`: "Unable to load application information"), so
   `gtk-launch zotero` ran the package's shortcut and the background copy was
   not stopped. A literal quote inside the quoted argument is `\\"` in the
   file. `scripts/reference-library-test.ts` now runs the shortcut through GLib.
4. One idle test was spoiled by this session's own mistake: a shell command
   with an unquoted here-document ran `gtk-launch zotero` from a backtick in
   its text at 20:01:07. The shortcut stopped the chain (as designed) and a
   window opened; it was closed with SIGTERM and the idle test was repeated
   from a single request (test E).

## A. On-demand start and reads through the socket

```text
units before: active inactive inactive inactive      (socket, proxy, gateway, app)
zotero processes: 0
HTTP/1.1 200 OK
first request took 1.108428350 s
units after: active active active active
1052349 /usr/lib/zotero/zotero-bin -app /usr/lib/zotero/app/application.ini --headless
127.0.0.1:23191 127.0.0.1:23190 127.0.0.1:23119
```

Reads, through the server exactly as `plugins/work/mcp.json` declares it
(`node` from `plugins/work/node_modules`, base URL `http://127.0.0.1:23190`,
app name "Agent reference library"), driven over stdio with the MCP client
library:

```text
tools: 28
status: connected true, baseUrl http://127.0.0.1:23190, zoteroVersion 10.0.5,
        writeAccess true, appName Agent reference library, library user
collections: totalResults 2 returned 2
search: totalResults 0 returned 0
```

Write on a throwaway item (run on the first unit design, over the same socket
port; the connector and the tool calls are unchanged by the later unit
changes): `zotero_create_items` made a `book` titled "reference-library live
test 2026-10-01 (throwaway)" (key `7Q8JDQRA`, tag `reference-library-test`);
`zotero_update_item` with `{"deleted": true}` moved it to Zotero's trash
(library version 19); `zotero_list_trash` listed it; `zotero_get_item` showed
`"deleted": true`. `zotero_delete_items` is blocked, so the trash move uses
`zotero_update_item`. No permanent delete and no empty trash were run. The
trash held 3 other items before; they were not touched. The throwaway item
stays in the trash for the user to empty.

## C. The app opened over the background copy

```text
before: active active active                            (proxy, gateway, app)
1052349 ... zotero-bin ... --headless
t+3s windowed=1 headless=0 app-unit=inactive            (same at t+6 .. t+15)
after: inactive inactive inactive
1052752 /usr/lib/zotero/zotero-bin -app /usr/lib/zotero/app/application.ini --url
api on 23119: 200
```

`gtk-launch zotero` runs the replaced shortcut: the background copy stopped
before the window opened, one Zotero main process remained, and the API
answered on 23119. A window showed on the user's desktop and was closed with
SIGTERM afterwards.

## B. A request through the socket while the app is open

```text
before: active inactive inactive inactive               (socket, proxy, gateway, app)
HTTP/1.1 200 OK        request took .080756423 s
after: active active active active
zotero main processes: 1
1053200 socat -u TCP:127.0.0.1:23119 /dev/null
connected: true, baseUrl: 'http://127.0.0.1:23190', collections: totalResults 2
```

No second copy started: the app unit holds one idle connection to the open
app. With the first design the journal showed `Skipped due to 'exec-condition'`
instead.

## D. The open app closes while the proxy is up

```text
t+2s .. t+8s zotero=0 units(proxy,gateway,app)=inactive inactive inactive
socket: active
HTTP/1.1 200 OK        next request took 1.194362697 s
1053896 /usr/lib/zotero/zotero-bin -app /usr/lib/zotero/app/application.ini --headless
units: active active active
```

## E. Idle stop

See the end of this file.

## Client blocks

Claude Code (`claude -p`, `--output-format stream-json`; the `system/init`
event lists the tools). The server is the plugin's, loaded through a probe
plugin named `work` whose `.mcp.json` holds the same entry as
`plugins/work/mcp.json` (Claude Code 2.1.286 reads `.mcp.json`, not Agent
Plugins' `mcp.json`, so the repository's `mcp.json` is not loaded by it):

```text
--- user settings apply (~/.claude/settings.json)
server tools visible: 25 | delete/empty tools visible: []
server: plugin:work:reference-library connected
--- project settings only (--setting-sources project: the repository's .claude/settings.json)
server tools visible: 25 | delete/empty tools visible: []
--- control, no settings source (--setting-sources local)
server tools visible: 28 | visible: mcp__plugin_work_reference-library__zotero_delete_collection,
  ..._zotero_delete_items, ..._zotero_empty_trash
--- a server added by the user under the same name (--mcp-config), user settings apply
server tools visible: 25 | delete/empty tools visible: []
server: reference-library connected
```

Codex (`codex exec`, the user's `reference-library` entry with `disabled_tools`;
tools found by Codex's own tool search, no tool called):

```text
25 tools visible to Codex for the reference-library server
blocked tools visible: []
control (disabled_tools emptied with -c): the three blocked names appear
  (zotero_delete_collection, zotero_delete_items, zotero_empty_trash)
```

Codex does not load the repository's plugins, so this shows the block for the
user's entry that runs the same pinned copy. An earlier Codex call of
`zotero_status` through the entry (before its base URL moved to the socket)
returned `connected: true` and `writeAccess: true`.

## What was installed and changed on the machine

- `~/.config/systemd/user/reference-library.socket`, `reference-library.service`,
  `reference-library-app.service`, `reference-library-gateway.service`;
  `~/.config/reference-library/reference-library.caddyfile`;
  `~/.local/share/applications/zotero.desktop` (new; the package's entry is
  `/usr/share/applications/zotero.desktop`). `reference-library.socket` is
  enabled and active.
- `~/.claude/settings.json`: `permissions.deny` with six rules (backup
  `~/.claude/settings.json.bak-2026-10-01`).
- `~/.codex/config.toml`: the `zotero` entry renamed `reference-library`, with
  `disabled_tools`, the neutral app name and `ZOTERO_LOCAL_BASE_URL` (backup
  `~/.codex/config.toml.bak-2026-10-01`).
- Caddy 2.11.4 under `~/.local/share/mise/installs/aqua-caddyserver-caddy/`.
- `~/.config/zotero-native-mcp/keys.json` was not read, changed or copied.
- Uninstall: see `docs/architecture.md`, "Reference library".

## E. Idle stop (10 minutes)

One request through the socket, no other traffic:

```text
last request: 20:03:46 [1790852626]    units (proxy, gateway, app): active active active
1100119 /usr/lib/zotero/zotero-bin -app /usr/lib/zotero/app/application.ini --headless
app unit inactive at 20:13:50 [1790853230]      -> 604 s after the request
units (proxy, gateway, app, socket): inactive inactive inactive active
zotero processes: 0
```

`systemd-socket-proxyd` exited after its 10 idle minutes, which left the app
and gateway units unneeded (`StopWhenUnneeded`), so systemd stopped them and
Zotero. The socket stayed active, so the next request starts the chain again
(test D showed the 1.2 s restart).
