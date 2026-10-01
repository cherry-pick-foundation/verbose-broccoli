// Turborepo replays a cached result only while a task's hash is unchanged
// (specs/039-cpu-load-relief/research.md). These tests copy the working tree
// into a fresh Git repository and check, with `--dry=json` through the real
// `npm run turborepo` script, that a change to each kind of declared input
// changes the hash of the cached tasks that read it.
import {spawnSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import {
  appendFile,
  chmod,
  cp,
  mkdir,
  mkdtemp,
  rm,
  symlink,
  writeFile,
} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {delimiter, dirname} from 'node:path';
import {test} from 'node:test';
import {assertEquals, assertNotEquals} from '@std/assert';
import {fromFileUrl, join} from '@std/path';

const root = fromFileUrl(new URL('..', import.meta.url));
const isolated = {GIT_CONFIG_GLOBAL: '/dev/null', GIT_CONFIG_NOSYSTEM: '1'};

function run(
  cwd: string,
  command: string,
  args: string[],
  env: Record<string, string> = {},
) {
  const result = spawnSync(command, args, {
    cwd,
    env: {...process.env, ...isolated, ...env},
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  assertEquals(result.status, 0, result.stderr);
  return result.stdout;
}

// The working tree's tracked and unignored files, plus stand-ins for the
// ignored installed environments: a package file in each npm tree and each
// kind of uv environment, and a native program in a tool environment.
const installed = [
  'node_modules/x/index.js',
  'packages/wiki-consistency/node_modules/x/index.js',
  '.venv/lib/python3.14/site-packages/x/__init__.py',
  'tools/ruff/.venv/lib/python3.14/site-packages/x/__init__.py',
  'tools/ruff/.venv/bin/ruff',
];

async function fixture(check: (repo: string) => Promise<void>) {
  const repo = await mkdtemp(join(tmpdir(), 'turbo-cache-'));
  try {
    const files = run(root, 'git', [
      'ls-files',
      '-z',
      '--cached',
      '--others',
      '--exclude-standard',
    ]).split('\0');
    for (const file of files.filter(
      file => file !== '' && existsSync(join(root, file)),
    ))
      await cp(join(root, file), join(repo, file), {verbatimSymlinks: true});
    for (const file of installed) await write(repo, file, 'x = 1\n');
    await mkdir(join(repo, 'node_modules/.bin'));
    await symlink(
      join(root, 'node_modules/turbo/bin/turbo'),
      join(repo, 'node_modules/.bin/turbo'),
    );
    run(repo, 'git', ['init', '--quiet']);
    run(repo, 'git', ['add', '--all']);
    await check(repo);
  } finally {
    await rm(repo, {recursive: true, force: true});
  }
}

async function write(repo: string, file: string, text: string) {
  await mkdir(dirname(join(repo, file)), {recursive: true});
  await writeFile(join(repo, file), text);
}

function hashes(repo: string, env: Record<string, string> = {}) {
  const plan = JSON.parse(
    run(
      repo,
      'npm',
      ['run', '--silent', 'turborepo', '--', 'run', 'check', '--dry=json'],
      env,
    ),
  ) as {tasks: {taskId: string; hash: string}[]};
  return new Map(plan.tasks.map(task => [task.taskId, task.hash]));
}

function assertChanged(
  before: Map<string, string>,
  after: Map<string, string>,
  changed: string[],
  unchanged: string[] = [],
) {
  for (const task of changed)
    assertNotEquals(after.get(task), before.get(task), task);
  for (const task of unchanged)
    assertEquals(after.get(task), before.get(task), task);
}

void test('turbo cache: a changed repository file reruns the tasks that read it', async () => {
  await fixture(async repo => {
    let before = hashes(repo);
    await appendFile(join(repo, 'scripts/doc_sources.py'), '\n');
    let after = hashes(repo);
    assertChanged(
      before,
      after,
      ['doc-regions#test', '//#lint'],
      ['backfire#test'],
    );

    before = after;
    await appendFile(
      join(repo, 'packages/backfire/src/backfire/config.py'),
      '\n',
    );
    after = hashes(repo);
    assertChanged(
      before,
      after,
      [
        'backfire#test',
        'credit-offers#test',
        'wiki-consistency#test',
        '//#typecheck',
      ],
      ['jev-ultrafast#test', 'doc-regions#test'],
    );

    before = after;
    await write(repo, 'docs/untracked-note.md', 'New.\n');
    after = hashes(repo);
    assertChanged(
      before,
      after,
      ['//#lint', '//#test:workflow'],
      ['backfire#test'],
    );
  });
});

void test("turbo cache: Turborepo's own task logs are not inputs", async () => {
  await fixture(async repo => {
    const before = hashes(repo);
    await write(repo, '.turbo/turbo-lint.log', 'Log.\n');
    await write(repo, 'packages/backfire/.turbo/turbo-test.log', 'Log.\n');
    assertChanged(before, hashes(repo), [], ['//#lint', 'backfire#test']);
  });
});

void test('turbo cache: a changed installed environment reruns every cached task', async () => {
  await fixture(async repo => {
    let before = hashes(repo);
    for (const file of installed) {
      await appendFile(join(repo, file), '\n');
      const after = hashes(repo);
      assertChanged(before, after, ['backfire#test', '//#typecheck'], []);
      before = after;
    }
  });
});

void test('turbo cache: a changed program or its outside config reruns every cached task', async () => {
  await fixture(async repo => {
    const before = hashes(repo);
    const bin = join(repo, '.local/bin');
    await write(
      repo,
      '.local/bin/git',
      `#!/bin/sh\n[ "$1" = --version ] && echo "git version 0.0.0" && exit\nexec ${run(root, 'sh', ['-c', 'command -v git']).trim()} "$@"\n`,
    );
    await chmod(join(bin, 'git'), 0o755);
    const path = `${bin}${delimiter}${process.env.PATH ?? ''}`;
    assertChanged(before, hashes(repo, {PATH: path}), [
      'backfire#test',
      '//#lint',
    ]);

    const config = join(repo, '.local/gitconfig');
    await write(repo, '.local/gitconfig', '[core]\n\tautocrlf = true\n');
    assertChanged(before, hashes(repo, {GIT_CONFIG_GLOBAL: config}), [
      'backfire#test',
      '//#lint',
    ]);

    assertChanged(before, hashes(repo, {UV_PYTHON: '3.13'}), [
      'backfire#test',
      '//#lint',
    ]);
  });
});
