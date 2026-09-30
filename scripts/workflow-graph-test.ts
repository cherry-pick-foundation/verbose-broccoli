import {execFileSync} from 'node:child_process';
import {mkdir, mkdtemp, rm, symlink, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {test} from 'node:test';
import {assert, assertRejects} from '@std/assert';
import {join} from '@std/path';
import {dependencyCruiser, isFullCommitHash} from './workflow-depcruise.ts';
import {getFileAccessError} from './workflow-files.ts';
import {inspectSymbol} from './workflow-symbol.ts';

async function fixture(files: Record<string, string>) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-graph-'));
  for (const [path, source] of Object.entries(files)) {
    const target = join(root, path);
    await mkdir(join(target, '..'), {recursive: true});
    await writeFile(target, source);
  }
  return root;
}

const git = (root: string, ...args: string[]) =>
  execFileSync('git', args, {cwd: root, encoding: 'utf8'}).trim();

void test('workflow graph: dependency-cruiser returns raw JSON for reaches and symbol queries', async () => {
  const root = await fixture({
    'package.json': '{}',
    'plugins/demo/math.ts':
      'export function double(value: number) { return value * 2; }',
    'plugins/demo/use.ts':
      "import {double} from './math.ts'; export const result = double(2);",
  });
  try {
    const graph = await dependencyCruiser(root, {
      reaches: '^plugins/demo/math\\.ts$',
    });
    const sources = new Set(graph.modules.map(module => module.source));
    assert(graph.summary);
    assert(sources.has('plugins/demo/math.ts'));
    assert(sources.has('plugins/demo/use.ts'));

    const symbols = await inspectSymbol(
      root,
      graph,
      'plugins/demo/math.ts',
      1,
      17,
    );
    assert(JSON.stringify(symbols).includes('double'));
  } finally {
    await rm(root, {recursive: true});
  }
});

void test('workflow graph: affected queries require a full SHA and include changed dependents', async () => {
  const root = await fixture({
    'package.json': '{}',
    'plugins/demo/math.ts': 'export const value = 1;',
    'plugins/demo/use.ts':
      "import {value} from './math.ts'; export const result = value;",
  });
  try {
    git(root, 'init', '--quiet');
    git(root, 'config', 'user.email', 'test@example.invalid');
    git(root, 'config', 'user.name', 'Synthetic Test');
    git(root, 'add', '.');
    git(root, 'commit', '--quiet', '-m', 'fixture');
    const base = git(root, 'rev-parse', 'HEAD');
    assert(isFullCommitHash(base));
    await writeFile(
      join(root, 'plugins/demo/math.ts'),
      'export const value = 2;',
    );

    await assertRejects(
      () => dependencyCruiser(root, {affected: 'HEAD'}),
      Error,
      'full commit hash',
    );
    const graph = await dependencyCruiser(root, {affected: base});
    const sources = new Set(graph.modules.map(module => module.source));
    assert(sources.has('plugins/demo/math.ts'));
    assert(sources.has('plugins/demo/use.ts'));
  } finally {
    await rm(root, {recursive: true});
  }
});

void test('workflow graph: selected paths reject missing files and symlinks', async () => {
  const root = await fixture({
    'plugins/demo/value.ts': 'export const value = 1;',
  });
  try {
    await symlink('value.ts', join(root, 'plugins/demo/alias.ts'));
    assert(
      (await getFileAccessError(root, 'plugins/demo/value.ts', true)) ===
        undefined,
    );
    assert(await getFileAccessError(root, 'plugins/demo/missing.ts', true));
    assert(await getFileAccessError(root, 'plugins/demo/alias.ts', true));
  } finally {
    await rm(root, {recursive: true});
  }
});
