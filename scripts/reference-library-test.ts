import {spawnSync} from 'node:child_process';
import {test} from 'node:test';
import {readFile, mkdtemp, mkdir, rm, writeFile, stat} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {assert, assertEquals, assertMatch} from '@std/assert';
import {fromFileUrl, join} from '@std/path';

const ROOT = fromFileUrl(new URL('../', import.meta.url));
const INFRA = join(ROOT, 'infra/reference-library');
const ZOTERO_PORT = '23119';
const BLOCKED_TOOLS = [
  'zotero_delete_items',
  'zotero_delete_collection',
  'zotero_empty_trash',
];

const read = (...path: string[]) => readFile(join(ROOT, ...path), 'utf8');

function match(text: string, pattern: RegExp, what: string) {
  const found = pattern.exec(text);
  assert(found !== null, `${what} not found`);
  return found[1];
}

void test('reference library: the socket, proxy, gateway and app agree on ports', async () => {
  const socket = await read('infra/reference-library/reference-library.socket');
  const proxy = await read('infra/reference-library/reference-library.service');
  const caddyfile = await read(
    'infra/reference-library/reference-library.caddyfile',
  );

  const socketPort = match(
    socket,
    /^ListenStream=127\.0\.0\.1:(\d+)$/m,
    'socket port',
  );
  const gatewayPort = match(
    proxy,
    /--exit-idle-time=10min 127\.0\.0\.1:(\d+)$/m,
    'proxy target',
  );
  assert(socketPort !== ZOTERO_PORT, "the socket must not take Zotero's port");
  assert(gatewayPort !== socketPort && gatewayPort !== ZOTERO_PORT);
  assertEquals(
    match(caddyfile, /^http:\/\/127\.0\.0\.1:(\d+) \{$/m, 'gateway site'),
    gatewayPort,
  );
  assertEquals(
    match(caddyfile, /reverse_proxy 127\.0\.0\.1:(\d+) \{/, 'upstream'),
    ZOTERO_PORT,
  );
  assertMatch(caddyfile, /header_up Host \{upstream_hostport\}/);
  for (const option of ['admin off', 'persist_config off', 'auto_https off']) {
    assert(caddyfile.includes(option), `Caddyfile must set ${option}`);
  }
  assertMatch(caddyfile, /bind 127\.0\.0\.1/);
});

void test('reference library: units start on demand, wait for the API and stop when unneeded', async () => {
  const proxy = await read('infra/reference-library/reference-library.service');
  const app = await read(
    'infra/reference-library/reference-library-app.service',
  );
  const gateway = await read(
    'infra/reference-library/reference-library-gateway.service',
  );

  // The proxy lives and dies with the app unit and needs the gateway.
  assertMatch(proxy, /^BindsTo=reference-library-app\.service$/m);
  assertMatch(proxy, /^Requires=reference-library-gateway\.service$/m);
  assertMatch(
    proxy,
    /^After=reference-library-app\.service reference-library-gateway\.service$/m,
  );
  assertMatch(app, /^StopWhenUnneeded=yes$/m);
  assertMatch(gateway, /^StopWhenUnneeded=yes$/m);
  assertMatch(gateway, /^After=reference-library-app\.service$/m);
  // An open app that answers means no second copy: the unit holds a
  // connection to it instead; otherwise it runs the app without a window.
  assertMatch(
    app,
    /^ExecStart=\/bin\/sh -c 'curl [^']*127\.0\.0\.1:23119\/[^']* && exec socat -u TCP:127\.0\.0\.1:23119 \/dev\/null; exec \/usr\/bin\/zotero --headless'$/m,
  );
  // The proxy waits for the API: the app unit is not active before it answers.
  assertMatch(
    app,
    /^ExecStartPost=.*--retry-connrefused .*127\.0\.0\.1:23119\//m,
  );

  const pin = match(
    await read('.config/mise.toml'),
    /^"aqua:caddyserver\/caddy" = "([^"]+)"$/m,
    'Caddy pin',
  );
  assertMatch(
    gateway,
    new RegExp(
      `^ExecStart=%h/\\.local/share/mise/installs/aqua-caddyserver-caddy/${pin.replaceAll('.', '\\.')}/caddy run `,
      'm',
    ),
  );
  assert(
    (await read('.config/mise.lock')).includes(
      `[[tools."aqua:caddyserver/caddy"]]\nversion = "${pin}"`,
    ),
    '.config/mise.lock must lock the pinned Caddy',
  );
});

void test('reference library: the shortcut stops the background copy, then opens the app', async () => {
  const shortcut = await read(
    'infra/reference-library/reference-library-app.desktop',
  );
  const exec = match(shortcut, /^Exec=(.*)$/m, 'Exec');
  const stop = exec.indexOf(
    'systemctl --user stop reference-library-app.service',
  );
  const open = exec.indexOf('exec /usr/lib/zotero/zotero');
  assert(stop !== -1 && open > stop, 'stop first, then open the app');
  assertMatch(shortcut, /^Name=Zotero$/m);
});

// desktop-file-validate accepts quoting that GLib refuses, so run the
// shortcut through GLib with its two commands swapped for harmless ones.
void test(
  'reference library: GLib runs the shortcut and passes the URL through',
  {
    skip: spawnSync('gio', ['version']).error ? 'gio is not installed' : false,
  },
  async () => {
    const temp = await mkdtemp(join(tmpdir(), 'reference-library-'));
    try {
      const out = join(temp, 'out');
      const app = join(temp, 'app');
      await writeFile(
        app,
        `#!/bin/sh\nfor arg; do echo "[$arg]" >> ${out}; done\n`,
        {
          mode: 0o755,
        },
      );
      const shortcut = (
        await read('infra/reference-library/reference-library-app.desktop')
      )
        .replace(
          'systemctl --user stop reference-library-app.service',
          `echo stopped >> ${out}`,
        )
        .replace('exec /usr/lib/zotero/zotero', `exec ${app}`);
      const file = join(temp, 'shortcut.desktop');
      await writeFile(file, shortcut);
      for (const args of [['zotero://select/library/items/ABCD1234'], []]) {
        const result = spawnSync('gio', ['launch', file, ...args], {
          encoding: 'utf8',
        });
        assertEquals(result.status, 0, result.stderr);
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      assertEquals((await readFile(out, 'utf8')).split('\n'), [
        'stopped',
        '[--url]',
        '[zotero://select/library/items/ABCD1234]',
        'stopped',
        '[--url]',
        '',
      ]);
    } finally {
      await rm(temp, {recursive: true});
    }
  },
);

void test('reference library: install.sh copies the files and starts the socket', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'reference-library-'));
  try {
    const bin = join(temp, 'bin');
    await mkdir(bin);
    const log = join(temp, 'systemctl.log');
    await writeFile(
      join(bin, 'systemctl'),
      `#!/bin/sh\necho "$*" >> "${log}"\n`,
      {mode: 0o755},
    );
    const result = spawnSync('sh', [join(INFRA, 'install.sh')], {
      env: {
        PATH: `${bin}:${process.env.PATH}`,
        HOME: temp,
        XDG_CONFIG_HOME: join(temp, 'config'),
        XDG_DATA_HOME: join(temp, 'data'),
      },
      encoding: 'utf8',
    });
    assertEquals(result.status, 0, result.stderr);
    for (const file of [
      'config/systemd/user/reference-library.socket',
      'config/systemd/user/reference-library.service',
      'config/systemd/user/reference-library-app.service',
      'config/systemd/user/reference-library-gateway.service',
      'config/reference-library/reference-library.caddyfile',
      'data/applications/zotero.desktop',
    ]) {
      assert((await stat(join(temp, file))).isFile(), `${file} not installed`);
    }
    assertEquals(
      await readFile(join(temp, 'data/applications/zotero.desktop'), 'utf8'),
      await readFile(join(INFRA, 'reference-library-app.desktop'), 'utf8'),
    );
    assertEquals((await readFile(log, 'utf8')).trim().split('\n'), [
      '--user daemon-reload',
      '--user enable --now reference-library.socket',
    ]);
  } finally {
    await rm(temp, {recursive: true});
  }
});

void test('reference library: the work area pins the connector and Claude Code blocks its delete tools', async () => {
  const manifest = JSON.parse(await read('plugins/work/package.json'));
  assertEquals(manifest.dependencies, {'zotero-native-mcp': '1.0.1'});
  const lock = JSON.parse(await read('plugins/work/package-lock.json'));
  const locked = lock.packages['node_modules/zotero-native-mcp'];
  assertEquals(locked.version, '1.0.1');
  assertMatch(locked.integrity, /^sha512-/);

  // The blocked names must still be tools of the pinned package.
  const tools = (
    await Promise.all(
      ['items', 'collections'].map(file =>
        read(
          'plugins/work/node_modules/zotero-native-mcp/build/tools',
          `${file}.js`,
        ),
      ),
    )
  ).join('\n');
  for (const tool of BLOCKED_TOOLS) {
    assert(
      tools.includes(`name: '${tool}'`),
      `${tool} is not a connector tool`,
    );
  }

  // Claude Code names a user-added server's tools mcp__<server>__<tool>.
  const deny: string[] = JSON.parse(await read('.claude/settings.json'))
    .permissions.deny;
  for (const tool of BLOCKED_TOOLS) {
    const name = `mcp__reference-library__${tool}`;
    assert(deny.includes(name), `${name} must be denied`);
  }
});
