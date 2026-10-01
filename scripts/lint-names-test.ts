import {test} from 'node:test';
import {assert, assertMatch} from '@std/assert';
import {dirname, fromFileUrl, join} from '@std/path';
import {spawnSync} from 'node:child_process';
import {mkdir, mkdtemp, rm, writeFile} from 'node:fs/promises';
import {homedir, tmpdir} from 'node:os';
import {delimiter} from 'node:path';

const script = fromFileUrl(new URL('./lint-names.sh', import.meta.url));
const decoder = new TextDecoder();

// Mise's shim for ls-lint fails outside a folder with a mise config, such as
// the temporary repositories below. So the tests put the shims folder first on
// PATH, as a shell without mise's activation has it, and the pinned binary that
// `mise which` finds from the repository root ahead of it.
const shims = join(
  process.env.MISE_DATA_DIR ?? join(homedir(), '.local', 'share', 'mise'),
  'shims',
);
const lsLint = spawnSync('mise', ['which', 'ls-lint'], {
  cwd: fromFileUrl(new URL('..', import.meta.url)),
  encoding: 'utf8',
}).stdout.trim();
assert(lsLint !== '', 'mise which ls-lint found no ls-lint');
const path = [dirname(lsLint), shims, process.env.PATH].join(delimiter);

function run(cwd: string, command: string, ...args: string[]) {
  const result = spawnSync(command, args, {
    cwd,
    env: {
      ...process.env,
      PATH: path,
      GIT_CONFIG_GLOBAL: '/dev/null',
      GIT_CONFIG_NOSYSTEM: '1',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  if (result.error) throw result.error;
  return {
    code: result.status ?? 1,
    output: decoder.decode(result.stdout) + decoder.decode(result.stderr),
  };
}

// A fresh Git repository with a kebab-case rule for files and folders, and
// `cache/` and a Korean-named folder ignored, the way `.venv` is in the real
// repository.
async function repository() {
  const root = await mkdtemp(join(tmpdir(), 'lint-names-'));
  run(root, 'git', 'init', '--quiet');
  await writeFile(join(root, '.gitignore'), 'cache/\n한글/\n');
  await mkdir(join(root, '.config'));
  await writeFile(
    join(root, '.config/ls-lint.yml'),
    'ls:\n  .dir: kebab-case | regex:\\.[a-z0-9-]+\n  ".": kebab-case\n  .*: kebab-case\nignore:\n  - .git\n',
  );
  await mkdir(join(root, 'cache', 'Bad_Folder'), {recursive: true});
  await writeFile(join(root, 'cache', 'Bad_File.txt'), '');
  await writeFile(join(root, 'cache', 'Bad_Folder', 'x.txt'), '');
  await mkdir(join(root, '한글'));
  await writeFile(join(root, '한글', 'Bad_Name.txt'), '');
  return root;
}

void test('lint-names skips folders that Git ignores', async () => {
  const root = await repository();
  try {
    const result = run(root, 'sh', script);
    assert(result.code === 0, result.output);
  } finally {
    await rm(root, {recursive: true});
  }
});

void test('lint-names checks untracked files and folders that Git does not ignore', async () => {
  const root = await repository();
  try {
    await mkdir(join(root, 'Bad_Folder'));
    await writeFile(join(root, 'Bad_File.txt'), '');
    const result = run(root, 'sh', script);
    assert(result.code === 1, result.output);
    assertMatch(result.output, /^Bad_File\.txt failed/m);
    assertMatch(result.output, /^Bad_Folder failed/m);
    assert(!result.output.includes('cache'), result.output);
  } finally {
    await rm(root, {recursive: true});
  }
});
