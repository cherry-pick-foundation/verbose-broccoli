import {assert, assertEquals, assertMatch, assertRejects} from '@std/assert';
import {dirname, fromFileUrl, join} from '@std/path';
import {checkNpmEnvironment, probeVersion, runDoctor} from './doctor.ts';
import {sha256} from './hash.ts';

const executable = Deno.execPath();
const realGit = new TextDecoder()
  .decode((await new Deno.Command('which', {args: ['git']}).output()).stdout)
  .trim();
const script = fromFileUrl(new URL('./doctor.ts', import.meta.url));
const config = fromFileUrl(new URL('../deno.json', import.meta.url));
const lock = fromFileUrl(new URL('../deno.lock', import.meta.url));

async function temporary(run: (root: string) => Promise<void>) {
  const root = await Deno.makeTempDir({prefix: 'doctor-test-'});
  try {
    await run(root);
  } finally {
    await Deno.remove(root, {recursive: true});
  }
}

async function fixture(root: string, name: string, code: string) {
  const path = join(root, name);
  await Deno.writeTextFile(path, `#!${executable} run\n${code}\n`, {
    mode: 0o755,
  });
  return path;
}

function shellQuote(value: string) {
  return `'${value.replaceAll("'", "'\\''")}'`;
}

async function gitWrapper(root: string) {
  const path = join(root, 'git');
  await Deno.writeTextFile(
    path,
    `#!/bin/sh\nif [ "$1" = config ] && [ "$2" = --get ] && [ "$3" = core.hooksPath ]; then\nprintf '%s\\n' scripts/git-hooks\nexit 0\nfi\nexec ${shellQuote(realGit)} "$@"\n`,
    {mode: 0o755},
  );
  return path;
}

async function cli(
  root: string,
  args: string[] = [],
  permissions = ['--allow-read', '--allow-run'],
) {
  await gitWrapper(root);
  return await new Deno.Command(executable, {
    cwd: root,
    args: [
      'run',
      '--config',
      config,
      '--frozen',
      '--cached-only',
      '--no-prompt',
      ...permissions,
      script,
      ...args,
    ],
    env: {PATH: `${root}:${Deno.env.get('PATH')}`},
    stdout: 'piped',
    stderr: 'piped',
  }).output();
}

function json(output: Deno.CommandOutput) {
  return JSON.parse(
    new TextDecoder().decode(output.success ? output.stdout : output.stderr),
  );
}

Deno.test('doctor: root task permits relocated and symlinked runtimes', async () => {
  await temporary(async root => {
    const installed = join(root, 'standalone runtime');
    const alias = join(root, 'alias runtime');
    await Deno.mkdir(installed);
    await Deno.mkdir(alias);
    await gitWrapper(installed);
    await gitWrapper(alias);
    const binary = join(installed, 'deno');
    await Deno.copyFile(executable, binary);
    await Deno.symlink(binary, join(alias, 'deno'));
    for (const directory of [installed, alias]) {
      const output = await new Deno.Command(join(directory, 'deno'), {
        args: ['task', '--config', config, 'doctor'],
        env: {PATH: `${directory}:${Deno.env.get('PATH')}`},
        stdout: 'piped',
        stderr: 'piped',
      }).output();
      assert(output.success, new TextDecoder().decode(output.stderr));
      assertEquals(json(output).deno.canonical, binary);
    }
  });
});

Deno.test('doctor: installed identities, versions and root lock work outside the checkout', async () => {
  await temporary(async root => {
    const output = await cli(root);
    assert(output.success, new TextDecoder().decode(output.stderr));
    const report = json(output);
    assertEquals(report.status, 'PASS');
    assertEquals(report.deno.canonical, await Deno.realPath(executable));
    assertEquals(
      report.quarto.canonical,
      await Deno.realPath('/usr/local/bin/quarto'),
    );
    assertEquals(report.deno.version, '2.9.6');
    assertEquals(report.quarto.version, '1.10.18');
    assertEquals(report.uv.version, '0.11.32');
    assertEquals(report.gitFlow.version, '2.1.0');
    assertEquals(report.lychee.version, '0.24.2');
    assert(Number.parseInt(report.node.version, 10) >= 22);
    assertEquals(report.gitFlow.config.status, 'PASS');
    assertEquals(report.specKit, {
      project: 'tools/spec-kit',
      python: 'tools/spec-kit/.venv/bin/python',
      sync: 'PASS',
    });
    assertEquals(report.ruff, {
      project: 'tools/ruff',
      python: 'tools/ruff/.venv/bin/python',
      sync: 'PASS',
    });
    assertEquals(report.docRegions, {
      project: 'packages/doc-regions',
      python: 'packages/doc-regions/.venv/bin/python',
      sync: 'PASS',
    });
    assertEquals(report.wikiConsistency, {
      project: 'packages/wiki-consistency',
      python: 'packages/wiki-consistency/.venv/bin/python',
      sync: 'PASS',
      nodeModules: 'packages/wiki-consistency/node_modules',
      npm: 'PASS',
    });
    assertEquals(report.runtime.version, Deno.version);
    assertEquals(report.runtime.build, Deno.build);
    assertEquals(report.lock.path, lock);
    assertEquals(report.lock.sha256, await sha256(await Deno.readFile(lock)));
    assertEquals(report.lock.dependencies['jsr:@std/assert@1'], '1.0.19');
    assert(!new TextDecoder().decode(output.stdout).includes('HOME='));
  });
});

Deno.test('doctor: missing, relative, non-executable and wrong-identity paths fail before report creation', async () => {
  await temporary(async root => {
    const report = join(root, 'report.json');
    const wrong = await fixture(
      root,
      'other-deno',
      "console.log('deno 2.9.6');",
    );
    const plain = join(root, 'not-executable');
    await Deno.writeTextFile(plain, 'not executable', {mode: 0o644});
    for (const options of [
      {deno: 'deno'},
      {deno: join(root, 'missing')},
      {deno: wrong},
      {quarto: root},
      {quarto: plain},
    ]) {
      await assertRejects(() => runDoctor({...options, report}));
      await assertRejects(() => Deno.stat(report), Deno.errors.NotFound);
    }
    await assertRejects(
      () => runDoctor({deno: wrong}),
      Error,
      'differs from the executing',
    );
    await assertRejects(
      () => runDoctor({quarto: executable}),
      Error,
      'quarto must report',
    );
  });
});

Deno.test('doctor: standalone aliases pass but .venv and Quarto runtime paths are refused', async () => {
  await temporary(async root => {
    const git = await fakeGit(root, 'scripts/git-hooks');
    const alias = join(root, 'standalone');
    await Deno.symlink(executable, alias);
    assertEquals(
      (await runDoctor({deno: alias, git})).deno.canonical,
      await Deno.realPath(executable),
    );
    for (const directory of ['.venv', 'quarto']) {
      await Deno.mkdir(join(root, directory));
      const path = join(root, directory, 'deno');
      await Deno.symlink(executable, path);
      await assertRejects(
        () => runDoctor({deno: path}),
        Error,
        directory === '.venv' ? 'outside .venv' : 'outside Quarto',
      );
    }
  });
});

async function fakeGit(root: string, value: string | undefined) {
  const result =
    value === undefined
      ? 'Deno.exit(1);'
      : `console.log(${JSON.stringify(value)});`;
  return await fixture(
    root,
    'fake-git',
    `if (Deno.args.join(' ') !== 'config --get core.hooksPath') Deno.exit(2); ${result}`,
  );
}

Deno.test('doctor: git hooks path must match and is recorded', async () => {
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

Deno.test('doctor: version probes require exact versions, successful exit and bounded duration', async () => {
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
    const wrong = await fixture(root, 'wrong', "console.log('deno 2.9.5');");
    await assertRejects(() => probeVersion(wrong, 'deno'), Error, '2.9.6');
    const wrongUv = await fixture(
      root,
      'wrong-uv',
      "console.log('uv 0.11.31');",
    );
    await assertRejects(() => probeVersion(wrongUv, 'uv'), Error, '0.11.32');
    const failure = await fixture(
      root,
      'failure',
      "console.log('1.10.18'); Deno.exit(1);",
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

Deno.test('doctor: git-flow version and shared configuration status are required', async () => {
  await temporary(async root => {
    const wrong = await fixture(
      root,
      'wrong-git-flow',
      "if (Deno.args[0] === 'version') console.log('2.0.0 (git-flow-next)');",
    );
    await assertRejects(
      () => runDoctor({gitFlow: wrong}),
      Error,
      'git-flow must report version 2.1.0',
    );

    const drifted = await fixture(
      root,
      'drifted-git-flow',
      "if (Deno.args[0] === 'version') console.log('2.1.0 (git-flow-next)'); else Deno.exit(6);",
    );
    await assertRejects(
      () => runDoctor({gitFlow: drifted}),
      Error,
      'git-flow shared configuration has drifted',
    );
  });
});

Deno.test('doctor: a missing or stale Spec Kit environment fails with sync guidance', async () => {
  await temporary(async root => {
    const stale = await fixture(
      root,
      'uv',
      "if (Deno.args[0] === '--version') console.log('uv 0.11.32'); else Deno.exit(1);",
    );
    await assertRejects(
      () => runDoctor({uv: stale}),
      Error,
      'run uv sync --locked --project tools/spec-kit',
    );
  });
});

Deno.test('doctor: a missing or stale Ruff environment fails with sync guidance', async () => {
  await temporary(async root => {
    const stale = await fixture(
      root,
      'uv',
      "if (Deno.args[0] === '--version') console.log('uv 0.11.32'); else if (Deno.args.at(-1) === 'tools/ruff') Deno.exit(1);",
    );
    await assertRejects(
      () => runDoctor({uv: stale}),
      Error,
      'run uv sync --locked --project tools/ruff',
    );
  });
});

Deno.test('doctor: a missing or stale doc-regions environment fails with sync guidance', async () => {
  await temporary(async root => {
    const stale = await fixture(
      root,
      'uv',
      "if (Deno.args[0] === '--version') console.log('uv 0.11.32'); else if (Deno.args.at(-1) === 'packages/doc-regions') Deno.exit(1);",
    );
    await assertRejects(
      () => runDoctor({uv: stale}),
      Error,
      'run uv sync --locked --project packages/doc-regions',
    );
  });
});

Deno.test('doctor: a missing or stale wiki-consistency Python environment fails with install guidance', async () => {
  await temporary(async root => {
    const stale = await fixture(
      root,
      'uv',
      "if (Deno.args[0] === '--version') console.log('uv 0.11.32'); else if (Deno.args.at(-1) === 'packages/wiki-consistency') Deno.exit(1);",
    );
    await assertRejects(
      () => runDoctor({uv: stale}),
      Error,
      'run deno task wiki-consistency:install',
    );
  });
});

Deno.test('doctor: a missing or stale wiki-consistency Node environment fails with install guidance', async () => {
  await temporary(async root => {
    const stale = await fixture(root, 'npm', 'Deno.exit(1);');
    const options = {npm: stale, git: await fakeGit(root, 'scripts/git-hooks')};
    await assertRejects(
      () => runDoctor(options),
      Error,
      'run deno task wiki-consistency:install',
    );
  });
});

Deno.test('doctor: npm ls success does not hide npm package-lock drift', async () => {
  await temporary(async root => {
    const project = join(root, 'wiki-consistency');
    const nodeModules = join(project, 'node_modules');
    await Deno.mkdir(nodeModules, {recursive: true});
    await Deno.writeTextFile(
      join(project, 'package-lock.json'),
      JSON.stringify({
        lockfileVersion: 3,
        packages: {'node_modules/qmd': {version: '2.0.0'}},
      }),
    );
    const installedLock = join(nodeModules, '.package-lock.json');
    await Deno.writeTextFile(
      installedLock,
      JSON.stringify({
        lockfileVersion: 3,
        packages: {'node_modules/qmd': {version: '2.5.0'}},
      }),
    );
    const npm = await fixture(root, 'npm', 'Deno.exit(0);');

    await assertRejects(
      () => checkNpmEnvironment(npm, project),
      Error,
      'node_modules is missing or out of sync',
    );
    await Deno.writeTextFile(installedLock, '{');
    await assertRejects(
      () => checkNpmEnvironment(npm, project),
      Error,
      'node_modules is missing or out of sync',
    );
    await Deno.remove(installedLock);
    await assertRejects(
      () => checkNpmEnvironment(npm, project),
      Error,
      'node_modules is missing or out of sync',
    );
  });
});

Deno.test('doctor: Node must be installed and at least version 22', async () => {
  await temporary(async root => {
    const git = await fakeGit(root, 'scripts/git-hooks');
    const missing = {node: join(root, 'missing-node'), git};
    await assertRejects(() => runDoctor(missing), Error, 'not found');

    const old = await fixture(root, 'old-node', "console.log('v20.19.0');");
    const oldNode = {node: old, git};
    await assertRejects(() => runDoctor(oldNode), Error, '22 or later');
  });
});

Deno.test('doctor: report is private, create-only and refuses README paths and symlinks', async () => {
  await temporary(async root => {
    const report = join(root, 'report.json');
    const git = await fakeGit(root, 'scripts/git-hooks');
    const result = await runDoctor({report, git});
    assertEquals(JSON.parse(await Deno.readTextFile(report)), result);
    assertEquals((await Deno.stat(report)).mode! & 0o777, 0o600);
    await assertRejects(
      () => runDoctor({report, git}),
      Deno.errors.AlreadyExists,
    );
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
    await Deno.symlink(join(root, 'README.md'), alias);
    await assertRejects(
      () => runDoctor({report: alias, git}),
      Deno.errors.AlreadyExists,
    );
    assertEquals(JSON.parse(await Deno.readTextFile(report)), result);
  });
});

Deno.test('doctor: CLI rejects invalid flags and missing runtime/report permissions', async () => {
  await temporary(async root => {
    for (const args of [['--unknown'], ['--deno'], ['unexpected']]) {
      const output = await cli(root, args);
      assertEquals(output.code, 2);
      assertEquals(output.stdout.length, 0);
      assertEquals(json(output).error.code, 'INVALID_ARGUMENT');
    }
    const deniedRun = await cli(root, [], ['--allow-read']);
    assertEquals(deniedRun.code, 1);
    assertMatch(json(deniedRun).error.message, /run access/);
    const deniedRead = await cli(
      root,
      [],
      ['--allow-read', `--deny-read=${lock}`, '--allow-run'],
    );
    assertEquals(deniedRead.code, 1);
    assertMatch(json(deniedRead).error.message, /read access/);
    const report = join(root, 'report.json');
    const deniedWrite = await cli(root, ['--report', report]);
    assertEquals(deniedWrite.code, 1);
    assertMatch(json(deniedWrite).error.message, /write access/);
    await assertRejects(() => Deno.stat(report), Deno.errors.NotFound);
    const written = await cli(
      root,
      ['--report', report],
      ['--allow-read', '--allow-run', `--allow-write=${report}`],
    );
    assert(written.success);
    assertEquals(JSON.parse(await Deno.readTextFile(report)), json(written));
    assertEquals(dirname(report), root);
  });
});
