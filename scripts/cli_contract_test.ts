import {assert, assertEquals, assertMatch} from '@std/assert';
import {assertSnapshot} from '@std/testing/snapshot';
import {fromFileUrl, join} from '@std/path';

const root = fromFileUrl(new URL('../', import.meta.url));
const skill = join(root, 'plugins/code/skills/clean-code');
const commands = [
  {name: 'doctor', script: 'scripts/doctor.ts'},
  {name: 'workflow', script: 'scripts/workflow.ts'},
  {name: 'clean-architecture', script: 'scripts/clean_architecture.ts'},
  {name: 'plugins:validate', script: 'scripts/validate_plugins.ts'},
  {
    name: 'clean-code',
    script: 'plugins/code/skills/clean-code/scripts/clean_code.ts',
  },
];
const decoder = new TextDecoder();

function execute(args: string[], cwd = root) {
  return new Deno.Command(Deno.execPath(), {
    args,
    cwd,
    stdout: 'piped',
    stderr: 'piped',
    env: {
      NO_COLOR: '1',
      DENO_NO_UPDATE_CHECK: '1',
      PATH: `${Deno.execPath().slice(0, Deno.execPath().lastIndexOf('/'))}:${Deno.env.get('PATH') ?? ''}`,
      // Keep host Git config, such as a runner's global LFS filters, out of
      // the commands' fixture repositories, as the git() helper below does.
      GIT_CONFIG_NOSYSTEM: '1',
      GIT_CONFIG_GLOBAL: '/dev/null',
    },
  }).output();
}

function invoke(item: (typeof commands)[number], args: string[], cwd = root) {
  return execute(
    [
      'run',
      '--quiet',
      '--config',
      item.name === 'clean-code'
        ? join(skill, 'deno.json')
        : join(root, 'deno.json'),
      '--frozen',
      '--cached-only',
      '--no-prompt',
      '--allow-read',
      '--allow-write',
      '--allow-env',
      '--allow-sys',
      '--allow-run',
      join(root, item.script),
      ...args,
    ],
    cwd,
  );
}

function errorResult(
  result: Deno.CommandOutput,
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

async function git(cwd: string, args: string[]) {
  const result = await new Deno.Command('git', {
    cwd,
    args: [
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
    env: {GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null'},
    stdout: 'piped',
    stderr: 'piped',
  }).output();
  assert(result.success, decoder.decode(result.stderr));
}

async function fixture(
  run: (repo: string, directory: string) => Promise<void>,
) {
  const directory = await Deno.makeTempDir({prefix: 'cli-contract-'});
  const repo = join(directory, 'repo');
  try {
    await Deno.mkdir(join(repo, 'scripts'), {recursive: true});
    await Deno.writeTextFile(join(repo, 'deno.json'), '{}\n');
    await Deno.writeTextFile(
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
    await Deno.remove(directory, {recursive: true});
  }
}

for (const item of commands) {
  Deno.test(`CLI ${item.name}: help and invalid arguments`, async t => {
    const help = await execute(['task', '--quiet', item.name, '--help']);
    assertEquals(help.code, 0, decoder.decode(help.stderr));
    assertEquals(help.stderr.length, 0);
    const text = decoder.decode(help.stdout);
    assertMatch(text, /Usage:/);
    assertMatch(text, /--help/);
    assertEquals(text.includes('\u001b'), false);
    await assertSnapshot(t, text);
    const bad = await execute([
      'task',
      '--quiet',
      item.name,
      '--unknown-cli-option',
    ]);
    errorResult(bad, 2, 'INVALID_ARGUMENT');
  });

  Deno.test(`CLI ${item.name}: actual success and failure streams`, async () => {
    await fixture(async (repo, directory) => {
      let args: string[] = [];
      if (item.name === 'plugins:validate') args = [join(root, 'plugins/chat')];
      const success = await invoke(item, args, repo);
      assertEquals(success.code, 0, decoder.decode(success.stderr));
      assertEquals(success.stderr.length, 0);
      const output = JSON.parse(decoder.decode(success.stdout));
      assert(output && typeof output === 'object' && !Array.isArray(output));
      const missing = join(directory, 'missing');
      let failureArgs: string[] = [];
      if (item.name === 'doctor') failureArgs = ['--deno', missing];
      if (item.name === 'plugins:validate') failureArgs = [missing];
      if (item.name === 'clean-architecture')
        await Deno.writeTextFile(join(repo, 'deno.json'), '{ invalid');
      if (item.name === 'clean-code')
        await Deno.writeTextFile(
          join(repo, 'scripts/value.ts'),
          'export function broken( {',
        );
      const failure = await invoke(
        item,
        failureArgs,
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

Deno.test('CLI: semantic input mistakes fail before execution', async () => {
  const cases: [string, string[]][] = [
    ['doctor', ['--deno', 'relative']],
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

Deno.test('CLI clean-code: copied skill stays independently runnable', async () => {
  await fixture(async (repo, directory) => {
    const installed = join(directory, 'installed-skill');
    await Deno.mkdir(join(installed, 'scripts'), {recursive: true});
    for (const file of [
      'deno.json',
      'deno.lock',
      'scripts/cli.ts',
      'scripts/clean_code.ts',
    ])
      await Deno.copyFile(join(skill, file), join(installed, file));
    const result = await execute(
      [
        'run',
        '--quiet',
        '--config',
        join(installed, 'deno.json'),
        '--frozen',
        '--cached-only',
        '--no-prompt',
        '--allow-read',
        '--allow-env',
        join(installed, 'scripts/clean_code.ts'),
        '--scope',
      ],
      repo,
    );
    assertEquals(result.code, 0, decoder.decode(result.stderr));
    assertEquals(result.stderr.length, 0);
    assertEquals(JSON.parse(decoder.decode(result.stdout)).selected, [
      'scripts/value.ts',
    ]);
  });
});

Deno.test('CLI validators: failed checks preserve diagnostics without partial stdout', async () => {
  await fixture(async (repo, directory) => {
    const plugin = join(directory, 'bad-plugin');
    await Deno.mkdir(plugin);
    await Deno.writeTextFile(join(plugin, 'plugin.json'), '{}');
    const validator = commands.find(item => item.name === 'plugins:validate')!;
    const schemaFailure = errorResult(
      await invoke(validator, [join(root, 'plugins/chat'), plugin]),
      1,
      'CHECK_FAILED',
    );
    assert(schemaFailure.details.errors.length > 0);
    await Deno.mkdir(join(repo, 'plugins/demo/domain'), {recursive: true});
    await Deno.mkdir(join(repo, 'plugins/demo/infrastructure'), {
      recursive: true,
    });
    await Deno.writeTextFile(
      join(repo, 'plugins/demo/domain/value.ts'),
      "import {db} from '../infrastructure/db.ts'; export const value = db;",
    );
    await Deno.writeTextFile(
      join(repo, 'plugins/demo/infrastructure/db.ts'),
      'export const db = 1;',
    );
    const architecture = commands.find(
      item => item.name === 'clean-architecture',
    )!;
    const graphFailure = errorResult(
      await invoke(architecture, [], repo),
      1,
      'CHECK_FAILED',
    );
    assert(graphFailure.details.violations.length > 0);
  });
});

Deno.test('CLI workflow: invalid plan schema takes precedence over Git execution', async () => {
  await fixture(async (_repo, directory) => {
    const plan = join(directory, 'invalid-plan.json');
    await Deno.writeTextFile(plan, '{"tasks":[]}');
    const workflow = commands.find(item => item.name === 'workflow')!;
    errorResult(
      await invoke(workflow, ['--plan', plan], directory),
      2,
      'INVALID_ARGUMENT',
    );
  });
});
