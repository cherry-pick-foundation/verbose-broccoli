import {spawnSync} from 'node:child_process';
import {test} from 'node:test';
import {
  mkdir,
  mkdtemp,
  readFile,
  realpath,
  rm,
  stat,
  symlink,
  writeFile,
} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {
  assert,
  assertEquals,
  assertMatch,
  assertRejects,
  assertThrows,
} from '@std/assert';
import {dirname, fromFileUrl, join} from '@std/path';
import {
  checkNpmEnvironment,
  lockedDependencies,
  probeTurboVersion,
  probeVersion,
  runDoctor,
} from './doctor.ts';
import {sha256} from './hash.ts';

const executable = process.execPath;
const realGit = new TextDecoder()
  .decode(commandOutput('which', {args: ['git']}).stdout)
  .trim();
const repositoryRoot = fromFileUrl(new URL('../', import.meta.url));
const script = fromFileUrl(new URL('./doctor.ts', import.meta.url));
const lock = fromFileUrl(new URL('../package-lock.json', import.meta.url));

function commandOutput(
  command: string,
  options: {args: string[]; cwd?: string; env?: Record<string, string>},
) {
  const result = spawnSync(command, options.args, {
    cwd: options.cwd,
    env: options.env ? {...process.env, ...options.env} : undefined,
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

async function temporary(run: (root: string) => Promise<void>) {
  const root = await mkdtemp(join(tmpdir(), 'doctor-test-'));
  try {
    await run(root);
  } finally {
    await rm(root, {recursive: true});
  }
}

async function fixture(root: string, name: string, code: string) {
  const path = join(root, name);
  await writeFile(path, `#!${executable}\n${code}\n`, {
    mode: 0o755,
  });
  return path;
}

function shellQuote(value: string) {
  return `'${value.replaceAll("'", "'\\''")}'`;
}

async function gitWrapper(root: string) {
  const path = join(root, 'git');
  await writeFile(
    path,
    `#!/bin/sh\nif [ "$1" = config ] && [ "$2" = --get ] && [ "$3" = core.hooksPath ]; then\nprintf '%s\\n' scripts/git-hooks\nexit 0\nfi\nexec ${shellQuote(realGit)} "$@"\n`,
    {mode: 0o755},
  );
  return path;
}

async function cli(
  root: string,
  args: string[] = [],
  permissions = ['--allow-fs-read=*', '--allow-child-process'],
  env: Record<string, string> = {},
) {
  await gitWrapper(root);
  return commandOutput(process.execPath, {
    args: [
      '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',
      '--disable-warning=SecurityWarning',
      '--permission',
      ...permissions,
      script,
      ...args,
    ],
    cwd: root,
    env: {PATH: `${root}:${process.env.PATH}`, ...env},
  });
}

async function assertErrorCode(action: () => Promise<unknown>, code: string) {
  const error = await assertRejects(action, Error);
  assertEquals((error as NodeJS.ErrnoException).code, code);
}

function json(output: ReturnType<typeof commandOutput>) {
  return JSON.parse(
    new TextDecoder().decode(output.success ? output.stdout : output.stderr),
  );
}

void test('doctor: direct Node CLI works from an empty HOME', async () => {
  await temporary(async root => {
    const home = join(root, 'empty-home');
    await mkdir(home);
    const output = await cli(root, [], undefined, {HOME: home});
    assert(output.success, new TextDecoder().decode(output.stderr));
    assertEquals(json(output).status, 'PASS');
    assertEquals(json(output).runtime.version, process.version);
  });
});

void test('doctor: installed root Turborepo matches the lock', async () => {
  const report = await runDoctor();
  assertEquals(report.turbo.version, '2.11.5');
});

void test('doctor: Turborepo probe requires the locked version and npm ci repair', async () => {
  await temporary(async root => {
    const wrong = await fixture(root, 'wrong-turbo', "console.log('2.11.4');");
    await assertRejects(
      () => probeTurboVersion(wrong, '2.11.5'),
      Error,
      'run npm ci',
    );
    const right = await fixture(root, 'right-turbo', "console.log('2.11.5');");
    assertEquals(await probeTurboVersion(right, '2.11.5'), '2.11.5');
  });
});

void test('doctor test commands reject children terminated by a signal', () => {
  assertThrows(
    () => commandOutput('sh', {args: ['-c', 'kill -TERM $$']}),
    Error,
    'SIGTERM',
  );
});

void test('doctor: installed identities, versions and root lock work outside the checkout', async () => {
  await temporary(async root => {
    const output = await cli(root);
    assert(output.success, new TextDecoder().decode(output.stderr));
    const report = json(output);
    assertEquals(report.status, 'PASS');
    assertEquals(
      report.quarto.canonical,
      await realpath('/usr/local/bin/quarto'),
    );
    assertEquals(report.quarto.version, '1.10.18');
    assertEquals(report.uv.version, '0.11.32');
    assertEquals(report.gitFlow.version, '2.1.0');
    assertEquals(report.lychee.version, '0.24.2');
    assertEquals(report.codexbar.version, '0.69.0');
    const [nodeMajor, nodeMinor] = report.node.version.split('.').map(Number);
    assert(
      nodeMajor > 24 || (nodeMajor === 24 && nodeMinor >= 12),
      report.node.version,
    );
    assertEquals(report.gitFlow.config.status, 'PASS');
    assertEquals(report.specKit, {
      project: 'tools/spec-kit',
      python: 'tools/spec-kit/.venv/bin/python',
      sync: 'PASS',
    });
    assertEquals(report.shellCheck, {
      project: 'tools/shellcheck',
      python: 'tools/shellcheck/.venv/bin/python',
      sync: 'PASS',
    });
    assertEquals(report.scc, {
      project: 'tools/scc',
      python: 'tools/scc/.venv/bin/python',
      sync: 'PASS',
    });
    assertEquals(report.ruff, {
      project: 'tools/ruff',
      python: 'tools/ruff/.venv/bin/python',
      sync: 'PASS',
    });
    assertEquals(report.uvWorkspace, {
      project: '.',
      python: '.venv/bin/python',
      sync: 'PASS',
    });
    assertEquals(report.rootNpm, {
      project: '.',
      nodeModules: './node_modules',
      npm: 'PASS',
    });
    assertEquals(report.wikiConsistency, {
      project: 'packages/wiki-consistency',
      nodeModules: 'packages/wiki-consistency/node_modules',
      npm: 'PASS',
    });
    assertEquals(report.runtime, {
      version: process.version,
      platform: process.platform,
      arch: process.arch,
    });
    assertEquals(report.lock.path, lock);
    assertEquals(report.lock.sha256, await sha256(await readFile(lock)));
    const packageLock = JSON.parse(await readFile(lock, 'utf8'));
    const directDependencies = {
      ...packageLock.packages[''].dependencies,
      ...packageLock.packages[''].devDependencies,
    };
    assertEquals(
      report.lock.dependencies,
      Object.fromEntries(
        Object.keys(directDependencies).map(name => [
          name,
          packageLock.packages[`node_modules/${name}`].version,
        ]),
      ),
    );
    assertThrows(
      () =>
        lockedDependencies({
          '': {dependencies: {missing: '^1.0.0'}},
        }),
      Error,
      'Missing locked dependency: missing',
    );
    assertEquals(report.turbo.version, '2.11.5');
    assert(!new TextDecoder().decode(output.stdout).includes('HOME='));
  });
});

void test('doctor: invalid Quarto paths fail before report creation', async () => {
  await temporary(async root => {
    const report = join(root, 'report.json');
    const wrong = await fixture(
      root,
      'wrong-quarto',
      "console.log('1.10.17');",
    );
    const plain = join(root, 'not-executable');
    await writeFile(plain, 'not executable', {mode: 0o644});
    for (const options of [
      {quarto: 'quarto'},
      {quarto: join(root, 'missing')},
      {quarto: wrong},
      {quarto: root},
      {quarto: plain},
    ]) {
      await assertRejects(() => runDoctor({...options, report}));
      await assertErrorCode(() => stat(report), 'ENOENT');
    }
    await assertRejects(
      () => runDoctor({quarto: wrong}),
      Error,
      'quarto must report version 1.10.18',
    );
    await assertRejects(
      () => runDoctor({quarto: executable}),
      Error,
      'quarto must report version 1.10.18',
    );
  });
});

void test('doctor: Quarto aliases pass while .venv and wrong identities are refused', async () => {
  await temporary(async root => {
    const git = await fakeGit(root, 'scripts/git-hooks');
    const quarto = await fixture(
      root,
      'quarto-runtime',
      "console.log('1.10.18');",
    );
    const alias = join(root, 'quarto-alias');
    await symlink(quarto, alias);
    assertEquals(
      (await runDoctor({quarto: alias, git})).quarto.canonical,
      await realpath(quarto),
    );
    for (const directory of ['.venv', 'quarto']) {
      await mkdir(join(root, directory));
      const path = join(root, directory, 'quarto');
      await symlink(directory === '.venv' ? quarto : executable, path);
      await assertRejects(
        () => runDoctor({quarto: path}),
        Error,
        directory === '.venv'
          ? 'outside .venv'
          : 'quarto must report version 1.10.18',
      );
    }
  });
});

async function fakeGit(root: string, value: string | undefined) {
  const result =
    value === undefined
      ? 'process.exit(1);'
      : `console.log(${JSON.stringify(value)});`;
  return await fixture(
    root,
    'fake-git',
    `if (process.argv.slice(2).join(' ') !== 'config --get core.hooksPath') process.exit(2); ${result}`,
  );
}

void test('doctor: git hooks path must match and is recorded', async () => {
  await temporary(async root => {
    const passingGit = await fakeGit(root, 'scripts/git-hooks');
    const report = await runDoctor({git: passingGit});
    assertEquals(report.gitHooksPath, 'scripts/git-hooks');

    for (const value of [undefined, '.git/hooks']) {
      const git = await fakeGit(root, value);
      await assertRejects(
        () => runDoctor({git}),
        Error,
        'Git hooks are not installed; run git config core.hooksPath scripts/git-hooks.',
      );
    }
  });
});

void test('doctor: version probes require exact versions, successful exit and bounded duration', async () => {
  await temporary(async root => {
    const wrongLychee = await fixture(
      root,
      'wrong-lychee',
      "console.log('lychee 0.24.1');",
    );
    await assertRejects(
      () => probeVersion(wrongLychee, 'lychee'),
      Error,
      'lychee must report version 0.24.2',
    );
    const wrongCodexBar = await fixture(
      root,
      'wrong-codexbar',
      "console.log('CodexBar 0.68.0');",
    );
    await assertRejects(
      () => probeVersion(wrongCodexBar, 'codexbar'),
      Error,
      'codexbar must report version 0.69.0',
    );
    const wrongQuarto = await fixture(
      root,
      'wrong-quarto',
      "console.log('1.10.17');",
    );
    await assertRejects(
      () => probeVersion(wrongQuarto, 'quarto'),
      Error,
      'quarto must report version 1.10.18',
    );
    const wrongUv = await fixture(
      root,
      'wrong-uv',
      "console.log('uv 0.11.31');",
    );
    await assertRejects(() => probeVersion(wrongUv, 'uv'), Error, '0.11.32');
    const failure = await fixture(
      root,
      'failure',
      "console.log('1.10.18'); process.exit(1);",
    );
    await assertRejects(
      () => probeVersion(failure, 'quarto'),
      Error,
      'probe failed',
    );
    const noisy = await fixture(
      root,
      'noisy',
      "console.log('x'.repeat(4097));",
    );
    await assertRejects(
      () => probeVersion(noisy, 'quarto'),
      Error,
      'probe failed',
    );
    const slow = await fixture(
      root,
      'slow',
      'await new Promise(resolve => setTimeout(resolve, 30000));',
    );
    const started = performance.now();
    await assertRejects(() => probeVersion(slow, 'quarto'));
    assert(performance.now() - started < 15000);
  });
});

void test('doctor: git-flow version and shared configuration status are required', async () => {
  await temporary(async root => {
    const wrong = await fixture(
      root,
      'wrong-git-flow',
      "if (process.argv[2] === 'version') console.log('2.0.0 (git-flow-next)');",
    );
    await assertRejects(
      () => runDoctor({gitFlow: wrong}),
      Error,
      'git-flow must report version 2.1.0',
    );

    const drifted = await fixture(
      root,
      'drifted-git-flow',
      "if (process.argv[2] === 'version') console.log('2.1.0 (git-flow-next)'); else process.exit(6);",
    );
    await assertRejects(
      () => runDoctor({gitFlow: drifted}),
      Error,
      'git-flow shared configuration has drifted',
    );
  });
});

void test('doctor: a missing or stale Spec Kit environment fails with sync guidance', async () => {
  await temporary(async root => {
    const stale = await fixture(
      root,
      'uv',
      "if (process.argv[2] === '--version') console.log('uv 0.11.32'); else process.exit(1);",
    );
    await assertRejects(
      () => runDoctor({uv: stale}),
      Error,
      'run uv sync --locked --project tools/spec-kit',
    );
  });
});

void test('doctor: a missing or stale ShellCheck environment fails with sync guidance', async () => {
  await temporary(async root => {
    const stale = await fixture(
      root,
      'uv',
      "if (process.argv[2] === '--version') console.log('uv 0.11.32'); else if (process.argv.at(-1) === 'tools/shellcheck') process.exit(1);",
    );
    await assertRejects(
      () => runDoctor({uv: stale}),
      Error,
      'run uv sync --locked --project tools/shellcheck',
    );
  });
});

void test('doctor: a missing or stale scc environment fails with sync guidance', async () => {
  await temporary(async root => {
    const stale = await fixture(
      root,
      'uv',
      "if (process.argv[2] === '--version') console.log('uv 0.11.32'); else if (process.argv.at(-1) === 'tools/scc') process.exit(1);",
    );
    await assertRejects(
      () => runDoctor({uv: stale}),
      Error,
      'run uv sync --locked --project tools/scc',
    );
  });
});

void test('doctor: a missing or stale Ruff environment fails with sync guidance', async () => {
  await temporary(async root => {
    const stale = await fixture(
      root,
      'uv',
      "if (process.argv[2] === '--version') console.log('uv 0.11.32'); else if (process.argv.at(-1) === 'tools/ruff') process.exit(1);",
    );
    await assertRejects(
      () => runDoctor({uv: stale}),
      Error,
      'run uv sync --locked --project tools/ruff',
    );
  });
});

void test('doctor: a missing or stale doc-regions environment fails with sync guidance', async () => {
  await temporary(async root => {
    const stale = await fixture(
      root,
      'uv',
      "if (process.argv[2] === '--version') console.log('uv 0.11.32'); else if (process.argv.includes('--all-packages')) process.exit(1);",
    );
    await assertRejects(
      () => runDoctor({uv: stale}),
      Error,
      'run uv sync --locked --all-packages --extra education',
    );
  });
});

void test('doctor: wiki-consistency Python is checked through the root uv workspace', async () => {
  await temporary(async root => {
    const stale = await fixture(
      root,
      'uv',
      "if (process.argv[2] === '--version') console.log('uv 0.11.32'); else if (process.argv.at(-1) === 'packages/wiki-consistency') process.exit(1);",
    );
    const report = await runDoctor({uv: stale});
    assertEquals(report.uvWorkspace, {
      project: '.',
      python: '.venv/bin/python',
      sync: 'PASS',
    });
  });
});

void test('doctor: a missing or stale wiki-consistency Node environment fails with install guidance', async () => {
  await temporary(async root => {
    const stale = await fixture(
      root,
      'npm',
      "if (process.argv.at(-1) !== '.') process.exit(1);",
    );
    const options = {npm: stale, git: await fakeGit(root, 'scripts/git-hooks')};
    await assertRejects(
      () => runDoctor(options),
      Error,
      'run npm run wiki-consistency:install',
    );
  });
});

void test('doctor: npm ls success does not hide npm package-lock drift', async () => {
  await temporary(async root => {
    const project = join(root, 'wiki-consistency');
    const nodeModules = join(project, 'node_modules');
    await mkdir(nodeModules, {recursive: true});
    await writeFile(
      join(project, 'package-lock.json'),
      JSON.stringify({
        lockfileVersion: 3,
        packages: {'node_modules/qmd': {version: '2.0.0'}},
      }),
    );
    const installedLock = join(nodeModules, '.package-lock.json');
    await writeFile(
      installedLock,
      JSON.stringify({
        lockfileVersion: 3,
        packages: {'node_modules/qmd': {version: '2.5.0'}},
      }),
    );
    const npm = await fixture(root, 'npm', 'process.exit(0);');

    await assertRejects(
      () => checkNpmEnvironment(npm, project),
      Error,
      'node_modules is missing or out of sync',
    );
    await writeFile(installedLock, '{');
    await assertRejects(
      () => checkNpmEnvironment(npm, project),
      Error,
      'node_modules is missing or out of sync',
    );
    await rm(installedLock);
    await assertRejects(
      () => checkNpmEnvironment(npm, project),
      Error,
      'node_modules is missing or out of sync',
    );
  });
});

void test('doctor: Node must be installed and at least version 24.12.0', async () => {
  await temporary(async root => {
    const git = await fakeGit(root, 'scripts/git-hooks');
    const missing = {node: join(root, 'missing-node'), git};
    await assertRejects(() => runDoctor(missing), Error, 'not found');

    for (const [name, version] of [
      ['old-node', 'v24.11.1'],
      ['unsupported-node', 'v22.20.0'],
    ]) {
      const old = await fixture(root, name, `console.log('${version}');`);
      await assertRejects(
        () => runDoctor({node: old, git}),
        Error,
        'Node.js 24.12.0 or later',
      );
    }

    const supported = await fixture(
      root,
      'supported-node',
      "console.log('v24.12.0');",
    );
    assertEquals(
      (await runDoctor({node: supported, git})).node.version,
      '24.12.0',
    );
  });
});

void test('doctor: report is private, create-only and refuses README paths and symlinks', async () => {
  await temporary(async root => {
    const report = join(root, 'report.json');
    const git = await fakeGit(root, 'scripts/git-hooks');
    const result = await runDoctor({report, git});
    assertEquals(JSON.parse(await readFile(report, 'utf8')), result);
    assertEquals((await stat(report)).mode & 0o777, 0o600);
    await assertErrorCode(() => runDoctor({report, git}), 'EEXIST');
    for (const path of [
      join(root, 'README.md'),
      join(root, 'README.md', 'report.json'),
    ])
      await assertRejects(
        () => runDoctor({report: path, git}),
        Error,
        'README',
      );
    const alias = join(root, 'report-link.json');
    await symlink(join(root, 'README.md'), alias);
    await assertErrorCode(() => runDoctor({report: alias, git}), 'EEXIST');
    assertEquals(JSON.parse(await readFile(report, 'utf8')), result);
  });
});

void test('doctor: CLI rejects invalid flags and missing runtime/report permissions', async () => {
  await temporary(async root => {
    for (const args of [['--unknown'], ['--node'], ['unexpected']]) {
      const output = await cli(root, args);
      assertEquals(output.code, 2);
      assertEquals(output.stdout.length, 0);
      assertEquals(json(output).error.code, 'INVALID_ARGUMENT');
    }
    const report = join(root, 'report.json');
    const deniedRun = await cli(root, [], ['--allow-fs-read=*']);
    assertEquals(deniedRun.code, 1);
    assertMatch(
      json(deniedRun).error.message,
      /--allow-child-process to manage permissions/,
    );
    const deniedRead = await cli(
      root,
      [],
      [
        `--allow-fs-read=${join(repositoryRoot, 'scripts')}`,
        `--allow-fs-read=${join(repositoryRoot, 'plugins')}`,
        `--allow-fs-read=${join(repositoryRoot, 'node_modules')}`,
        `--allow-fs-read=${join(repositoryRoot, 'packages')}`,
        `--allow-fs-read=${join(repositoryRoot, 'package.json')}`,
        `--allow-fs-read=${join(repositoryRoot, 'pyproject.toml')}`,
        `--allow-fs-read=${join(repositoryRoot, 'uv.lock')}`,
        `--allow-fs-read=${executable}`,
        '--allow-fs-read=/usr/local/bin/quarto',
        '--allow-child-process',
      ],
    );
    assertEquals(deniedRead.code, 1);
    assertMatch(
      json(deniedRead).error.message,
      /--allow-fs-read to manage permissions/,
    );
    const deniedWrite = await cli(root, ['--report', report]);
    assertEquals(deniedWrite.code, 1);
    assertMatch(
      json(deniedWrite).error.message,
      /--allow-fs-write to manage permissions/,
    );
    await assertErrorCode(() => stat(report), 'ENOENT');
    const written = await cli(
      root,
      ['--report', report],
      [
        '--allow-fs-read=*',
        '--allow-child-process',
        `--allow-fs-write=${report}`,
      ],
    );
    assert(written.success);
    assertEquals(JSON.parse(await readFile(report, 'utf8')), json(written));
    assertEquals(dirname(report), root);
  });
});
