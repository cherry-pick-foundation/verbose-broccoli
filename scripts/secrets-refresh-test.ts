import {test} from 'node:test';
import {assert, assertEquals, assertFalse} from '@std/assert';
import {fromFileUrl, join} from '@std/path';
import {spawnSync} from 'node:child_process';
import {
  chmod,
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
const TOKEN = 'fake-access-token';
const KEY_A = 'fake-key-a';
const KEY_B = 'fake-key-b';
const KEY_C = 'fake-key-c';

// A fake bws that records its arguments and environment and prints the JSON
// the test put beside it, like `bws secret list <project> --output json`.
const fakeBws = `#!/bin/sh
dir="$(dirname "$0")"
echo "$*" > "$dir/argv"
env > "$dir/env"
cat "$dir/output.json"
exit "$(cat "$dir/status")"
`;

// A temporary home with the operator configuration, a private token file and
// the fake bws first on PATH. `existing` is written to hive.env beforehand.
async function setup(output: unknown, existing?: string) {
  const root = await mkdtemp(join(tmpdir(), 'secrets-refresh-'));
  const bin = join(root, 'bin');
  const config = join(root, 'config', 'verbose-broccoli');
  const providers = join(config, 'providers');
  await mkdir(bin);
  await mkdir(providers, {recursive: true, mode: 0o700});
  await writeFile(join(bin, 'bws'), fakeBws, {mode: 0o755});
  await writeFile(join(bin, 'output.json'), JSON.stringify(output));
  await writeFile(join(bin, 'status'), '0');
  await writeFile(
    join(config, 'secrets.json'),
    JSON.stringify({
      project: 'fake-project',
      files: {
        'hive.env': ['HIVE_API_KEY'],
        'cloudflare.env': ['CLOUDFLARE_API_TOKEN', 'CLOUDFLARE_ACCOUNT_ID'],
      },
    }),
  );
  await writeFile(
    join(providers, 'bitwarden.env'),
    `BWS_ACCESS_TOKEN=${TOKEN}\n`,
    {
      mode: 0o600,
    },
  );
  if (existing !== undefined) {
    await writeFile(join(providers, 'hive.env'), existing, {mode: 0o644});
    await chmod(join(providers, 'hive.env'), 0o644);
  }
  return {root, bin, providers};
}

function run(root: string, bin: string) {
  const result = spawnSync(
    process.execPath,
    ['--disable-warning=MODULE_TYPELESS_PACKAGE_JSON', script],
    {
      env: {
        PATH: [bin, process.env.PATH].join(delimiter),
        HOME: root,
        XDG_CONFIG_HOME: join(root, 'config'),
      },
      encoding: 'utf8',
    },
  );
  return {code: result.status, output: result.stdout + result.stderr};
}

const secrets = [
  {key: 'CLOUDFLARE_ACCOUNT_ID', value: KEY_C},
  {key: 'HIVE_API_KEY', value: KEY_A},
  {key: 'CLOUDFLARE_API_TOKEN', value: KEY_B},
  {key: 'UNMAPPED_KEY', value: 'fake-unmapped'},
];

void test('refresh writes each key file as private variable lines in the configured order', async () => {
  const {root, bin, providers} = await setup(secrets, 'HIVE_API_KEY=old\n');
  try {
    const result = run(root, bin);
    assertEquals(result.code, 0, result.output);
    assertEquals(
      await readFile(join(providers, 'hive.env'), 'utf8'),
      `HIVE_API_KEY=${KEY_A}\n`,
    );
    assertEquals(
      await readFile(join(providers, 'cloudflare.env'), 'utf8'),
      `CLOUDFLARE_API_TOKEN=${KEY_B}\nCLOUDFLARE_ACCOUNT_ID=${KEY_C}\n`,
    );
    for (const file of ['hive.env', 'cloudflare.env']) {
      const info = await stat(join(providers, file));
      assertEquals(info.mode & 0o777, 0o600);
      assertEquals(info.uid, process.getuid!());
    }
    // No temporary file stays, and an unmapped secret gets no file.
    assertEquals((await readdir(providers)).sort(), [
      'bitwarden.env',
      'cloudflare.env',
      'hive.env',
    ]);
  } finally {
    await rm(root, {recursive: true});
  }
});

void test('refresh passes the token in the environment, never in the arguments, and prints no value', async () => {
  const {root, bin} = await setup(secrets);
  try {
    const result = run(root, bin);
    assertEquals(result.code, 0, result.output);
    const argv = await readFile(join(bin, 'argv'), 'utf8');
    assertEquals(
      argv.trim(),
      'secret list fake-project --output json --color no',
    );
    assertFalse(argv.includes(TOKEN));
    assert(
      (await readFile(join(bin, 'env'), 'utf8')).includes(
        `BWS_ACCESS_TOKEN=${TOKEN}`,
      ),
    );
    for (const value of [TOKEN, KEY_A, KEY_B, KEY_C])
      assertFalse(result.output.includes(value));
  } finally {
    await rm(root, {recursive: true});
  }
});

void test('refresh changes no file when a mapped secret is missing', async () => {
  const {root, bin, providers} = await setup(
    secrets.filter(secret => secret.key !== 'CLOUDFLARE_ACCOUNT_ID'),
    'HIVE_API_KEY=old\n',
  );
  try {
    const result = run(root, bin);
    assertEquals(result.code, 1);
    assert(result.output.includes('CLOUDFLARE_ACCOUNT_ID'), result.output);
    assertEquals(
      await readFile(join(providers, 'hive.env'), 'utf8'),
      'HIVE_API_KEY=old\n',
    );
  } finally {
    await rm(root, {recursive: true});
  }
});

void test('refresh changes no file when bws fails', async () => {
  const {root, bin, providers} = await setup([], 'HIVE_API_KEY=old\n');
  try {
    await writeFile(join(bin, 'status'), '1');
    const result = run(root, bin);
    assertEquals(result.code, 1);
    assert(result.output.includes('status 1'), result.output);
    assertEquals(
      await readFile(join(providers, 'hive.env'), 'utf8'),
      'HIVE_API_KEY=old\n',
    );
  } finally {
    await rm(root, {recursive: true});
  }
});

void test('refresh refuses a value with a line break', async () => {
  const {root, bin, providers} = await setup(
    secrets.map(secret =>
      secret.key === 'HIVE_API_KEY' ? {...secret, value: 'a\nb'} : secret,
    ),
    'HIVE_API_KEY=old\n',
  );
  try {
    const result = run(root, bin);
    assertEquals(result.code, 1);
    assert(result.output.includes('HIVE_API_KEY'), result.output);
    assertEquals(
      await readFile(join(providers, 'hive.env'), 'utf8'),
      'HIVE_API_KEY=old\n',
    );
  } finally {
    await rm(root, {recursive: true});
  }
});

void test('refresh refuses a token file that is not private', async () => {
  const {root, bin, providers} = await setup(secrets);
  try {
    await chmod(join(providers, 'bitwarden.env'), 0o640);
    const result = run(root, bin);
    assertEquals(result.code, 1);
    assert(result.output.includes('mode 600'), result.output);
    await assertRejectsMissing(join(bin, 'argv'));
  } finally {
    await rm(root, {recursive: true});
  }
});

// bws was never run: its argument record does not exist.
async function assertRejectsMissing(path: string) {
  let missing = false;
  try {
    await stat(path);
  } catch {
    missing = true;
  }
  assert(missing, `${path} exists`);
}
