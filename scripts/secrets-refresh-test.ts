import {test} from 'node:test';
import {assert, assertEquals, assertFalse} from '@std/assert';
import {fromFileUrl, join} from '@std/path';
import {spawnSync} from 'node:child_process';
import {
  chmod,
  link,
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  rm,
  stat,
  writeFile,
} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {delimiter} from 'node:path';

const script = fromFileUrl(new URL('./secrets-refresh.ts', import.meta.url));
const TOKEN_A = 'synthetic-token-a';
const TOKEN_B = 'synthetic-token-b';
const PROJECT_A = 'synthetic-project-a';
const PROJECT_B = 'synthetic-project-b';
const KEY_A = 'synthetic-hive-key';
const KEY_B = 'synthetic-cloudflare-key';
const KEY_C = 'synthetic-shared-secret';
const CLIENT_JSON =
  '{\n  "installed": {"client_secret": "synthetic-json-secret"}\n}';
const SERVER = 'https://synthetic-vault.example.test';
const secretsA = [
  {key: 'HIVE_API_KEY', value: KEY_A},
  {key: 'CLOUDFLARE_API_TOKEN', value: KEY_B},
  {key: 'CLOUDFLARE_ACCOUNT_ID', value: 'synthetic-account-id'},
  {key: 'AGENTROUTER_API_KEY', value: 'synthetic-router-key'},
  {key: 'GWS_CLIENT_SECRET_JSON', value: CLIENT_JSON},
  {key: 'UNMAPPED_KEY', value: 'synthetic-unmapped'},
];
const secretsB = [
  {key: 'OCIS_MCP_HTTP_SECRET', value: KEY_C},
  {key: 'OCIS_CF_ACCESS_CLIENT_SECRET', value: 'synthetic-access-secret'},
];

// The fake is a Node executable, so it records the exact child environment
// without a shell adding its own variables. Only synthetic data is used.
const fakeBws = `#!${process.execPath}
const fs = require('node:fs');
const path = require('node:path');
const dir = path.dirname(process.argv[1]);
const project = process.argv[4];
fs.appendFileSync(path.join(dir, 'calls.jsonl'), JSON.stringify({argv: process.argv.slice(2), env: process.env, umask: process.umask()}) + '\\n');
process.stderr.write(process.env.BWS_ACCESS_TOKEN + ' ' + project);
process.stdout.write(fs.readFileSync(path.join(dir, project + '.json')));
if (fs.existsSync(path.join(dir, 'temporary-blocker'))) {
  const target = fs.readFileSync(path.join(dir, 'temporary-blocker'), 'utf8');
  fs.writeFileSync(target + '.' + process.ppid + '.tmp', 'synthetic-blocker', {mode: 0o600});
}
process.exit(Number(fs.readFileSync(path.join(dir, project + '.status'), 'utf8')));
`;

// Node's permission model refuses fs.symlink with /tmp-only write access.
// The existing child-process grant lets ln create synthetic links in /tmp.
function makeSymlink(source: string, target: string) {
  assert(source.startsWith('/tmp/') && target.startsWith('/tmp/'));
  const result = spawnSync('ln', ['-s', '--', source, target], {
    encoding: 'utf8',
  });
  assertEquals(result.status, 0, result.stderr);
}

async function setup(configName = 'config') {
  const root = await mkdtemp(join(tmpdir(), 'secrets-refresh-'));
  const bin = join(root, 'bin');
  const config = join(root, configName);
  const operator = join(config, 'verbose-broccoli', 'secrets.json');
  const providers = join(config, 'verbose-broccoli', 'providers');
  const tokenA = join(root, 'token-a.env');
  const tokenB = join(root, 'token-b.env');
  const omp = join(root, '.omp', 'agent', '.env');
  const client = join(config, 'ocis-mcp', 'client.env');
  const cloudflare = join(config, 'ocis-mcp', 'cloudflare-client.env');
  const gws = join(config, 'gws', 'client_secret.json');
  for (const parent of [
    bin,
    providers,
    join(root, '.omp', 'agent'),
    join(config, 'ocis-mcp'),
    join(config, 'gws'),
  ])
    await mkdir(parent, {recursive: true, mode: 0o700});
  await writeFile(join(bin, 'bws'), fakeBws, {mode: 0o755});
  for (const [project, secrets] of [
    [PROJECT_A, secretsA],
    [PROJECT_B, secretsB],
  ] as const) {
    await writeFile(join(bin, `${project}.json`), JSON.stringify(secrets));
    await writeFile(join(bin, `${project}.status`), '0');
  }
  await writeFile(tokenA, `BWS_ACCESS_TOKEN=${TOKEN_A}\n`, {mode: 0o600});
  await writeFile(tokenB, `BWS_ACCESS_TOKEN=${TOKEN_B}\n`, {mode: 0o600});
  const settings = {
    sources: {
      'org-a': {token_file: tokenA, project: PROJECT_A},
      'org-b': {token_file: tokenB, project: PROJECT_B, server: SERVER},
    },
    files: {
      'hive.env': {source: 'org-a', variables: {HIVE_API_KEY: 'HIVE_API_KEY'}},
      'cloudflare.env': {
        source: 'org-a',
        variables: {
          CLOUDFLARE_API_TOKEN: 'CLOUDFLARE_API_TOKEN',
          CLOUDFLARE_ACCOUNT_ID: 'CLOUDFLARE_ACCOUNT_ID',
        },
      },
      [omp]: {
        source: 'org-a',
        variables: {
          AGENTROUTER_API_KEY: 'AGENTROUTER_API_KEY',
          THEHIVE_API_KEY: 'HIVE_API_KEY',
        },
      },
      [client]: {
        source: 'org-b',
        variables: {OCIS_MCP_HTTP_SECRET: 'OCIS_MCP_HTTP_SECRET'},
      },
      [cloudflare]: {
        source: 'org-b',
        variables: {
          OCIS_MCP_HTTP_SECRET: 'OCIS_MCP_HTTP_SECRET',
          OCIS_CF_ACCESS_CLIENT_SECRET: 'OCIS_CF_ACCESS_CLIENT_SECRET',
        },
      },
      [gws]: {source: 'org-a', content: 'GWS_CLIENT_SECRET_JSON'},
    },
  };
  await writeFile(operator, JSON.stringify(settings));
  const targets = [
    join(providers, 'hive.env'),
    join(providers, 'cloudflare.env'),
    omp,
    client,
    cloudflare,
    gws,
  ];
  for (const path of targets) {
    await writeFile(path, 'OLD=unchanged\n', {mode: 0o644});
    await chmod(path, 0o644);
  }
  await writeFile(targets[0], 'HIVE_API_KEY=old\n');
  await writeFile(
    omp,
    '# OMP comment\r\n\r\nTHEHIVE_API_KEY\r\nTHEHIVE_API_KEY=old\r\nLOCAL_ID=preserve',
  );
  await writeFile(
    cloudflare,
    '# access settings\nOCIS_CF_ACCESS_CLIENT_ID=preserve-id\nOCIS_MCP_HTTP_SECRET=old\n',
  );
  return {
    root,
    bin,
    config,
    operator,
    providers,
    tokenA,
    tokenB,
    omp,
    client,
    cloudflare,
    gws,
    settings,
    targets,
  };
}

type Fixture = Awaited<ReturnType<typeof setup>>;
async function save(fixture: Fixture, settings: unknown = fixture.settings) {
  await writeFile(fixture.operator, JSON.stringify(settings));
}
function run(fixture: Fixture, xdg = fixture.config, npmCommand = false) {
  const result = spawnSync(
    npmCommand ? 'npm' : process.execPath,
    npmCommand
      ? ['run', 'secrets:refresh']
      : ['--disable-warning=MODULE_TYPELESS_PACKAGE_JSON', script],
    {
      env: {
        PATH: [fixture.bin, process.env.PATH].join(delimiter),
        HOME: fixture.root,
        XDG_CONFIG_HOME: xdg,
        BWS_PROFILE: 'must-not-inherit',
        RUST_LOG: 'must-not-inherit',
      },
      encoding: 'utf8',
    },
  );
  const output = result.stdout + result.stderr;
  for (const value of [
    TOKEN_A,
    TOKEN_B,
    PROJECT_A,
    PROJECT_B,
    KEY_A,
    KEY_B,
    KEY_C,
    CLIENT_JSON,
    SERVER,
    'https://vault.bitwarden.com',
    'synthetic-json-secret',
    'synthetic-account-id',
    'synthetic-router-key',
    'synthetic-access-secret',
    'synthetic-unmapped',
  ])
    assertFalse(output.includes(value), output);
  return {code: result.status, output};
}
async function calls(fixture: Fixture) {
  try {
    return (await readFile(join(fixture.bin, 'calls.jsonl'), 'utf8'))
      .trim()
      .split('\n')
      .map(
        line =>
          JSON.parse(line) as {
            argv: string[];
            env: Record<string, string>;
            umask: number;
          },
      );
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
    return [];
  }
}
async function snapshot(fixture: Fixture) {
  return Promise.all(
    fixture.targets.map(async path => {
      const info = await lstat(path);
      return {bytes: await readFile(path), mode: info.mode, uid: info.uid};
    }),
  );
}
async function refusal(fixture: Fixture, beforeFetch = false) {
  const before = await snapshot(fixture);
  const result = run(fixture);
  assertEquals(result.code, 1, result.output);
  assertEquals(await snapshot(fixture), before);
  if (beforeFetch) assertEquals(await calls(fixture), []);
  assertFalse(
    (await readdir(fixture.providers)).some(file => file.endsWith('.tmp')),
  );
}
async function withFixture(action: (fixture: Fixture) => Promise<void>) {
  const fixture = await setup();
  try {
    await action(fixture);
  } finally {
    await rm(fixture.root, {recursive: true});
  }
}

void test('two sources refresh aliases, preserve unmapped bytes, and write exact content privately', async () => {
  await withFixture(async fixture => {
    await rm(join(fixture.providers, 'cloudflare.env'));
    // Non-UTF-8 bytes in an unmapped line also survive.
    await writeFile(fixture.client, Buffer.from([0xff, 0x0a]));
    const result = run(fixture, fixture.config, true);
    assertEquals(result.code, 0, result.output);
    assertEquals(
      await readFile(join(fixture.providers, 'hive.env'), 'utf8'),
      `HIVE_API_KEY=${KEY_A}\n`,
    );
    assertEquals(
      await readFile(join(fixture.providers, 'cloudflare.env'), 'utf8'),
      `CLOUDFLARE_API_TOKEN=${KEY_B}\nCLOUDFLARE_ACCOUNT_ID=synthetic-account-id\n`,
    );
    assertEquals(
      await readFile(fixture.omp, 'utf8'),
      `# OMP comment\r\n\r\nTHEHIVE_API_KEY\r\nTHEHIVE_API_KEY=${KEY_A}\r\nLOCAL_ID=preserve\nAGENTROUTER_API_KEY=synthetic-router-key\n`,
    );
    assertEquals(
      await readFile(fixture.client),
      Buffer.concat([
        Buffer.from([0xff, 0x0a]),
        Buffer.from(`OCIS_MCP_HTTP_SECRET=${KEY_C}\n`),
      ]),
    );
    assertEquals(
      await readFile(fixture.cloudflare, 'utf8'),
      `# access settings\nOCIS_CF_ACCESS_CLIENT_ID=preserve-id\nOCIS_MCP_HTTP_SECRET=${KEY_C}\nOCIS_CF_ACCESS_CLIENT_SECRET=synthetic-access-secret\n`,
    );
    assertEquals(await readFile(fixture.gws, 'utf8'), CLIENT_JSON);
    for (const path of fixture.targets) {
      const info = await stat(path);
      assertEquals(info.mode & 0o777, 0o600);
      assertEquals(info.uid, process.getuid!());
    }
    const fetched = await calls(fixture);
    assertEquals(fetched.length, 2);
    for (const [index, project, token, server] of [
      [0, PROJECT_A, TOKEN_A, 'https://vault.bitwarden.com'],
      [1, PROJECT_B, TOKEN_B, SERVER],
    ] as const) {
      assertEquals(fetched[index].argv, [
        'secret',
        'list',
        project,
        '--output',
        'json',
        '--color',
        'no',
      ]);
      assertFalse(fetched[index].argv.join(' ').includes(token));
      assertEquals(fetched[index].env, {
        PATH: fetched[index].env.PATH,
        HOME: fixture.root,
        BWS_ACCESS_TOKEN: token,
        BWS_SERVER_URL: server,
      });
      assert(fetched[index].env.PATH.split(delimiter).includes(fixture.bin));
      assertEquals(fetched[index].umask, 0o077);
    }
    assertEquals((await readdir(fixture.providers)).sort(), [
      'cloudflare.env',
      'hive.env',
    ]);
    assert(result.output.includes('6 files'));
  });
});

void test('existing mapped final lines and CR-only endings stay in place', async () => {
  await withFixture(async fixture => {
    await writeFile(
      join(fixture.providers, 'hive.env'),
      '# comment\rHIVE_API_KEY=old',
    );
    assertEquals(run(fixture).code, 0);
    assertEquals(
      await readFile(join(fixture.providers, 'hive.env'), 'utf8'),
      `# comment\rHIVE_API_KEY=${KEY_A}`,
    );
  });
});

for (const failure of [
  'wrong-mode-a',
  'wrong-mode-b',
  'symlink',
  'symlink-parent',
  'missing',
  'missing-token',
  'duplicate-token',
  'empty-token',
  'unused-bad-token',
]) {
  void test(`token preflight refuses ${failure} before every bws call`, async () => {
    await withFixture(async fixture => {
      if (failure === 'wrong-mode-a') await chmod(fixture.tokenA, 0o640);
      if (failure === 'wrong-mode-b' || failure === 'unused-bad-token')
        await chmod(fixture.tokenB, 0o644);
      if (failure === 'unused-bad-token') {
        for (const [key, target] of Object.entries(fixture.settings.files))
          if (target.source === 'org-b') delete fixture.settings.files[key];
        await save(fixture);
      }
      if (failure === 'symlink') {
        await rm(fixture.tokenB);
        makeSymlink(fixture.tokenA, fixture.tokenB);
      }
      if (failure === 'symlink-parent') {
        makeSymlink(fixture.root, join(fixture.root, 'alias'));
        fixture.settings.sources['org-b'].token_file = join(
          fixture.root,
          'alias',
          'token-b.env',
        );
        await save(fixture);
      }
      if (failure === 'missing') await rm(fixture.tokenB);
      if (failure === 'missing-token')
        await writeFile(fixture.tokenB, 'OTHER=ignored\n');
      if (failure === 'duplicate-token')
        await writeFile(
          fixture.tokenB,
          `BWS_ACCESS_TOKEN=${TOKEN_B}\nBWS_ACCESS_TOKEN=${TOKEN_B}\n`,
        );
      if (failure === 'empty-token')
        await writeFile(fixture.tokenB, 'BWS_ACCESS_TOKEN=\n');
      await refusal(fixture, true);
    });
  });
}

for (const failure of [
  'source-a',
  'source-b',
  'missing',
  'duplicate',
  'empty',
  'newline',
  'carriage-return',
  'empty-content',
  'malformed-json',
  'non-array',
  'null-secret',
  'bad-key',
  'bad-value',
]) {
  void test(`collection/value failure ${failure} preserves every target byte and mode`, async () => {
    await withFixture(async fixture => {
      let output: unknown = secretsB;
      if (failure.startsWith('source-'))
        await writeFile(
          join(
            fixture.bin,
            `${failure === 'source-a' ? PROJECT_A : PROJECT_B}.status`,
          ),
          '1',
        );
      if (failure === 'missing') output = [];
      if (failure === 'duplicate') output = [...secretsB, secretsB[0]];
      if (failure === 'empty')
        output = [{...secretsB[0], value: ''}, secretsB[1]];
      if (failure === 'newline' || failure === 'carriage-return')
        output = [
          {...secretsB[0], value: failure === 'newline' ? 'a\nb' : 'a\rb'},
          secretsB[1],
        ];
      if (failure === 'empty-content')
        await writeFile(
          join(fixture.bin, `${PROJECT_A}.json`),
          JSON.stringify(
            secretsA.map(secret =>
              secret.key === 'GWS_CLIENT_SECRET_JSON'
                ? {...secret, value: ''}
                : secret,
            ),
          ),
        );
      if (failure === 'non-array') output = {key: 'bad'};
      if (failure === 'null-secret') output = [null];
      if (failure === 'bad-key') output = [{key: 1, value: KEY_C}];
      if (failure === 'bad-value')
        output = [{key: 'OCIS_MCP_HTTP_SECRET', value: 1}];
      await writeFile(
        join(fixture.bin, `${PROJECT_B}.json`),
        failure === 'malformed-json' ? TOKEN_B : JSON.stringify(output),
      );
      await refusal(fixture);
    });
  });
}

for (const failure of [
  'both-kinds',
  'unknown-source',
  'empty-map',
  'bad-variable',
  'bad-secret-name',
  'unknown-field',
  'old-shape',
  'null-config',
  'null-source',
  'null-target',
  'no-files',
  'no-sources',
  'http-server',
  'relative-token',
]) {
  void test(`invalid configuration ${failure} is refused before collection`, async () => {
    await withFixture(async fixture => {
      const settings = fixture.settings;
      const target = settings.files['hive.env'];
      let replacement: unknown = settings;
      if (failure === 'both-kinds')
        Object.assign(target, {content: 'HIVE_API_KEY'});
      if (failure === 'unknown-source') target.source = 'unknown';
      if (failure === 'empty-map')
        target.variables = {} as typeof target.variables;
      if (failure === 'bad-variable')
        target.variables = {
          'BAD-NAME': 'HIVE_API_KEY',
        } as unknown as typeof target.variables;
      if (failure === 'bad-secret-name') target.variables.HIVE_API_KEY = '';
      if (failure === 'unknown-field') Object.assign(target, {typo: true});
      if (failure === 'old-shape')
        replacement = {
          project: PROJECT_A,
          files: {'hive.env': ['HIVE_API_KEY']},
        };
      if (failure === 'null-config') replacement = null;
      if (failure === 'null-source')
        Object.assign(settings.sources, {'org-b': null});
      if (failure === 'null-target')
        Object.assign(settings.files, {'hive.env': null});
      if (failure === 'no-files') replacement = {...settings, files: {}};
      if (failure === 'no-sources') replacement = {...settings, sources: {}};
      if (failure === 'http-server')
        settings.sources['org-b'].server =
          'http://synthetic-vault.example.test';
      if (failure === 'relative-token')
        settings.sources['org-b'].token_file = 'relative.env';
      await save(fixture, replacement);
      await refusal(fixture, true);
    });
  });
}

for (const failure of [
  'token-file',
  'operator-file',
  'outside-home',
  'inside-home',
  'traversal',
  'hidden-name',
  'reserved-name',
  'duplicate-target',
  'duplicate-variable',
  'symlink-file',
  'dangling-symlink',
  'symlink-parent',
  'token-parent-alias',
  'operator-parent-alias',
  'hardlink-token',
  'hardlink-operator',
  'missing-parent',
  'writable-parent',
  'directory-target',
  'kind-provider',
  'kind-gws',
]) {
  void test(`unsafe or ambiguous target ${failure} preserves all targets`, async () => {
    await withFixture(async fixture => {
      const target = fixture.settings.files['hive.env'];
      let extra: string | undefined;
      if (failure === 'token-file') extra = fixture.tokenA;
      if (failure === 'operator-file') extra = fixture.operator;
      if (failure === 'outside-home') extra = '/tmp/unapproved.env';
      if (failure === 'inside-home')
        extra = join(fixture.root, 'unapproved.env');
      if (failure === 'traversal')
        extra = join(fixture.config, 'ocis-mcp') + '/../ocis-mcp/client.env';
      if (failure === 'hidden-name') extra = '.hidden';
      if (failure === 'reserved-name') extra = 'bitwarden.env';
      if (failure === 'duplicate-target')
        extra = join(fixture.config, 'ocis-mcp') + '/./client.env';
      if (failure === 'duplicate-variable')
        await writeFile(
          join(fixture.providers, 'hive.env'),
          'HIVE_API_KEY=one\nHIVE_API_KEY=two\n',
        );
      if (failure === 'symlink-file' || failure === 'dangling-symlink') {
        const alias = join(fixture.providers, 'alias.env');
        makeSymlink(
          failure === 'symlink-file'
            ? fixture.tokenA
            : join(fixture.root, 'missing'),
          alias,
        );
        extra = 'alias.env';
      }
      if (failure === 'symlink-parent') {
        const parent = join(fixture.config, 'ocis-mcp');
        await rm(parent, {recursive: true});
        await mkdir(join(fixture.root, 'redirected'));
        await writeFile(
          join(fixture.root, 'redirected', 'client.env'),
          'OLD=unchanged\n',
        );
        await writeFile(
          join(fixture.root, 'redirected', 'cloudflare-client.env'),
          'OLD=unchanged\n',
        );
        makeSymlink(join(fixture.root, 'redirected'), parent);
      }
      if (
        failure === 'token-parent-alias' ||
        failure === 'operator-parent-alias'
      ) {
        const alias = join(fixture.root, 'alias');
        makeSymlink(
          failure === 'token-parent-alias'
            ? fixture.providers
            : join(fixture.config, 'verbose-broccoli'),
          alias,
        );
        fixture.settings.sources['org-b'].token_file = join(
          alias,
          failure === 'token-parent-alias' ? 'hive.env' : 'secrets.json',
        );
        if (failure === 'operator-parent-alias')
          Object.assign(target, {source: 'org-b'});
        await save(fixture);
      }
      if (failure === 'hardlink-token' || failure === 'hardlink-operator') {
        extra = 'alias.env';
        await link(
          failure === 'hardlink-token' ? fixture.tokenA : fixture.operator,
          join(fixture.providers, extra),
        );
      }
      if (failure === 'missing-parent') {
        await rm(join(fixture.config, 'gws'), {recursive: true});
        fixture.targets = fixture.targets.filter(path => path !== fixture.gws);
      }
      if (failure === 'writable-parent')
        await chmod(join(fixture.config, 'gws'), 0o770);
      if (failure === 'directory-target') {
        extra = 'directory.env';
        await mkdir(join(fixture.providers, extra));
      }
      if (failure === 'kind-provider')
        Object.assign(target, {content: 'HIVE_API_KEY', variables: undefined});
      if (failure === 'kind-gws')
        fixture.settings.files[fixture.gws] = {
          source: 'org-a',
          variables: {HIVE_API_KEY: 'HIVE_API_KEY'},
        };
      if (extra) fixture.settings.files[extra] = target;
      await save(fixture);
      await refusal(fixture, failure !== 'duplicate-variable');
      assertEquals(
        await readFile(fixture.tokenA, 'utf8'),
        `BWS_ACCESS_TOKEN=${TOKEN_A}\n`,
      );
    });
  });
}

void test('malformed operator JSON is sanitized before any bws call', async () => {
  await withFixture(async fixture => {
    await writeFile(fixture.operator, TOKEN_A);
    await refusal(fixture, true);
  });
});

void test('empty and relative XDG roots use HOME/.config', async () => {
  for (const xdg of ['', 'relative-config']) {
    const fixture = await setup('.config');
    try {
      assertEquals(run(fixture, xdg).code, 0);
      assertEquals(await readFile(fixture.gws, 'utf8'), CLIENT_JSON);
    } finally {
      await rm(fixture.root, {recursive: true});
    }
  }
});

void test('an unused source is still fetched and its failure preserves every target', async () => {
  await withFixture(async fixture => {
    for (const [key, target] of Object.entries(fixture.settings.files))
      if (target.source === 'org-b') delete fixture.settings.files[key];
    await save(fixture);
    await writeFile(join(fixture.bin, `${PROJECT_B}.status`), '1');
    await refusal(fixture);
    assertEquals((await calls(fixture)).length, 2);
  });
});

void test('temporary preparation failure leaves every target unchanged and removes prepared files', async () => {
  await withFixture(async fixture => {
    await writeFile(join(fixture.bin, 'temporary-blocker'), fixture.gws);
    await refusal(fixture);
    for (const parent of [
      join(fixture.root, '.omp', 'agent'),
      join(fixture.config, 'ocis-mcp'),
    ])
      assertFalse((await readdir(parent)).some(file => file.endsWith('.tmp')));
    // The pre-existing blocker is not ours to remove.
    assertEquals(
      (await readdir(join(fixture.config, 'gws'))).filter(file =>
        file.endsWith('.tmp'),
      ).length,
      1,
    );
  });
});
