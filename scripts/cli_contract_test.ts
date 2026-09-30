import {spawnSync} from 'node:child_process';
import {
  copyFile,
  cp,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  writeFile,
} from 'node:fs/promises';
import {test} from 'node:test';
import {assert, assertEquals, assertMatch, assertThrows} from '@std/assert';
import {fromFileUrl, join} from '@std/path';
import {delimiter, dirname} from 'node:path';
import {tmpdir} from 'node:os';

const root = fromFileUrl(new URL('../', import.meta.url));
const skill = join(root, 'plugins/code/skills/clean-code');
const commands = [
  {name: 'workflow', script: 'scripts/workflow.ts'},
  {
    name: 'clean-code',
    script: 'plugins/code/skills/clean-code/scripts/clean_code.ts',
  },
];
const decoder = new TextDecoder();

function commandOutput(
  command: string,
  args: string[],
  cwd = root,
  env?: Record<string, string>,
) {
  const result = spawnSync(command, args, {
    cwd,
    env: env ? {...process.env, ...env} : undefined,
    encoding: null,
  });
  if (result.error) throw result.error;
  if (result.signal)
    throw new Error(`${command} terminated by signal ${result.signal}`);
  return {
    code: result.status ?? 1,
    success: result.status === 0,
    stdout: result.stdout ?? Buffer.alloc(0),
    stderr: result.stderr ?? Buffer.alloc(0),
  };
}

void test('CLI test commands reject children terminated by a signal', () => {
  assertThrows(
    () => commandOutput('sh', ['-c', 'kill -TERM $$']),
    Error,
    'SIGTERM',
  );
});

function execute(command: string, args: string[], cwd = root) {
  return commandOutput(command, args, cwd, {
    NO_COLOR: '1',
    PATH: `${dirname(process.execPath)}${delimiter}${process.env.PATH ?? ''}`,
    // Keep host Git config, such as a runner's global LFS filters, out of
    // the commands' fixture repositories, as the git() helper below does.
    GIT_CONFIG_NOSYSTEM: '1',
    GIT_CONFIG_GLOBAL: '/dev/null',
  });
}

function invoke(item: (typeof commands)[number], args: string[], cwd = root) {
  return execute(
    process.execPath,
    [
      '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',
      '--permission',
      '--allow-fs-read=*',
      '--allow-fs-write=*',
      '--allow-child-process',
      join(root, item.script),
      ...args,
    ],
    cwd,
  );
}

function errorResult(
  result: ReturnType<typeof commandOutput>,
  code: number,
  errorCode: string,
) {
  assertEquals(result.code, code, decoder.decode(result.stderr));
  assertEquals(result.stdout.length, 0);
  const parsed = JSON.parse(decoder.decode(result.stderr));
  assertEquals(parsed.error.code, errorCode);
  assertEquals(typeof parsed.error.message, 'string');
  assert(parsed.error.message.length > 0);
  assertEquals(Object.keys(parsed.error).sort(), ['code', 'message']);
  return parsed;
}

void test('CLI contract: backfire install syncs the complete Python workspace', async () => {
  const packageJson = JSON.parse(
    await readFile(join(root, 'package.json'), 'utf8'),
  );
  assertEquals(
    packageJson.scripts['backfire:install'],
    'uv sync --locked --all-packages --extra education --no-build-package grimp',
  );
});

async function git(cwd: string, args: string[]) {
  const result = commandOutput(
    'git',
    [
      '-c',
      'core.hooksPath=/dev/null',
      '-c',
      'user.name=CLI Fixture',
      '-c',
      'user.email=fixture@example.invalid',
      '-c',
      'commit.gpgsign=false',
      ...args,
    ],
    cwd,
    {GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null'},
  );
  assert(result.success, decoder.decode(result.stderr));
}

async function fixture(
  run: (repo: string, directory: string) => Promise<void>,
) {
  const directory = await mkdtemp(join(tmpdir(), 'cli-contract-'));
  const repo = join(directory, 'repo');
  try {
    await mkdir(join(repo, 'scripts'), {recursive: true});
    await copyFile(join(root, 'package.json'), join(repo, 'package.json'));
    await writeFile(
      join(repo, 'scripts/value.ts'),
      'export function value(input: number) { return input + 1; }\n',
    );
    await git(repo, [
      'init',
      '--quiet',
      '--template=',
      '--initial-branch=main',
    ]);
    await git(repo, ['add', '.']);
    await git(repo, ['commit', '--quiet', '-m', 'Fixture']);
    await run(repo, directory);
  } finally {
    await rm(directory, {recursive: true});
  }
}

for (const item of commands) {
  void test(`CLI ${item.name}: help and invalid arguments`, async t => {
    const help = execute('npm', ['run', '--silent', item.name, '--', '--help']);
    assertEquals(help.code, 0, decoder.decode(help.stderr));
    assertEquals(help.stderr.length, 0);
    const text = decoder.decode(help.stdout);
    assertMatch(text, /Usage:/);
    assertMatch(text, /--help/);
    assertEquals(text.includes('\u001b'), false);
    t.assert.snapshot(text);
    const bad = execute('npm', [
      'run',
      '--silent',
      item.name,
      '--',
      '--unknown-cli-option',
    ]);
    errorResult(bad, 2, 'INVALID_ARGUMENT');
  });

  void test(`CLI ${item.name}: actual success and failure streams`, async () => {
    await fixture(async (repo, directory) => {
      const success = await invoke(item, [], repo);
      assertEquals(success.code, 0, decoder.decode(success.stderr));
      assertEquals(success.stderr.length, 0);
      const output = JSON.parse(decoder.decode(success.stdout));
      assert(output && typeof output === 'object' && !Array.isArray(output));
      if (item.name === 'clean-code')
        await writeFile(
          join(repo, 'scripts/value.ts'),
          'export function broken( {',
        );
      const failure = await invoke(
        item,
        [],
        item.name === 'workflow' ? directory : repo,
      );
      errorResult(
        failure,
        1,
        item.name === 'clean-code' ? 'CHECK_FAILED' : 'EXECUTION_FAILED',
      );
    });
  });
}

void test('CLI: semantic input mistakes fail before execution', async () => {
  const cases: [string, string[]][] = [
    ['workflow', ['--plan', '']],
    ['workflow', ['--graph', 'unknown']],
    [
      'workflow',
      [
        '--graph',
        'symbol',
        '--file',
        'missing.ts',
        '--line',
        '0',
        '--column',
        '1',
      ],
    ],
  ];
  for (const [name, args] of cases) {
    const item = commands.find(item => item.name === name)!;
    errorResult(await invoke(item, args), 2, 'INVALID_ARGUMENT');
  }
});

void test('CLI clean-code: copied skill stays independently runnable', async () => {
  await fixture(async (repo, directory) => {
    const installed = join(directory, 'installed-skill');
    await cp(skill, installed, {recursive: true});
    const install = execute('npm', [
      'ci',
      '--prefix',
      installed,
      '--prefer-offline',
      '--ignore-scripts',
      '--no-audit',
      '--no-fund',
    ]);
    assertEquals(install.code, 0, decoder.decode(install.stderr));
    const result = execute(
      process.execPath,
      [join(installed, 'scripts/clean_code.ts'), '--scope'],
      repo,
    );
    assertEquals(result.code, 0, decoder.decode(result.stderr));
    assertEquals(result.stderr.length, 0);
    assertEquals(JSON.parse(decoder.decode(result.stdout)).selected, [
      'scripts/value.ts',
    ]);
  });
});

void test('CLI workflow: invalid plan schema takes precedence over Git execution', async () => {
  await fixture(async (_repo, directory) => {
    const plan = join(directory, 'invalid-plan.json');
    await writeFile(plan, '{"tasks":[]}');
    const workflow = commands.find(item => item.name === 'workflow')!;
    errorResult(
      await invoke(workflow, ['--plan', plan], directory),
      2,
      'INVALID_ARGUMENT',
    );
  });
});
