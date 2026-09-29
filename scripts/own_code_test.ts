import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  readlink,
  rm,
  writeFile,
} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {fileURLToPath} from 'node:url';
import {deepStrictEqual, equal, match, notEqual} from 'node:assert/strict';
import {test, type TestContext} from 'node:test';
import {join, relative} from 'node:path';

const script = fileURLToPath(new URL('./own_code.ts', import.meta.url));
const code = (lines: number) =>
  `${Array.from({length: lines}, (_, index) => `const value_${index} = ${index};`).join('\n')}\n`;

function git(repo: string, ...args: string[]) {
  return spawnSync('git', args, {cwd: repo, encoding: 'utf8'});
}

function gitOk(repo: string, ...args: string[]) {
  const result = git(repo, ...args);
  if (result.status !== 0)
    throw new Error(result.stderr || `git ${args.join(' ')} failed`);
  return result.stdout;
}

async function repository(
  t: TestContext,
  options: {
    branch?: string;
    feature?: boolean;
    files?: Record<string, string>;
  } = {},
) {
  const root = await mkdtemp(join(tmpdir(), 'own-code-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const repo = join(root, 'repo');
  const temp = join(root, 'check-temp');
  await Promise.all([mkdir(repo), mkdir(temp)]);
  gitOk(
    repo,
    'init',
    '--quiet',
    '--initial-branch',
    options.branch ?? 'develop',
  );
  gitOk(repo, 'config', 'user.name', 'Own Code Test');
  gitOk(repo, 'config', 'user.email', 'own-code@example.invalid');
  const files = {'base.ts': 'export const base = true;\n', ...options.files};
  for (const [path, contents] of Object.entries(files)) {
    const target = join(repo, path);
    await mkdir(join(target, '..'), {recursive: true});
    await writeFile(target, contents);
  }
  gitOk(repo, 'add', '-A');
  gitOk(repo, 'commit', '--quiet', '-m', 'baseline');
  if (options.feature !== false)
    gitOk(repo, 'switch', '--quiet', '-c', 'feature');
  return {repo, temp};
}

async function put(repo: string, path: string, contents: string) {
  const target = join(repo, path);
  await mkdir(join(target, '..'), {recursive: true});
  await writeFile(target, contents);
}

function runCheck(repo: string, temp: string) {
  const result = spawnSync(
    process.execPath,
    [
      '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',
      '--permission',
      '--allow-fs-read=*',
      '--allow-fs-write=/tmp',
      '--allow-child-process',
      script,
    ],
    {cwd: repo, env: {...process.env, TMPDIR: temp}, encoding: 'utf8'},
  );
  if (result.error) throw result.error;
  return {status: result.status, output: `${result.stdout}${result.stderr}`};
}

async function files(repo: string, directory = repo): Promise<string[]> {
  const entries = await readdir(directory, {withFileTypes: true});
  const paths = await Promise.all(
    entries
      .filter(entry => !(directory === repo && entry.name === '.git'))
      .map(async entry => {
        const path = join(directory, entry.name);
        if (entry.isDirectory()) return files(repo, path);
        if (entry.isSymbolicLink())
          return [`link:${relative(repo, path)}:${await readlink(path)}`];
        if (entry.isFile())
          return [
            `file:${relative(repo, path)}:${(await readFile(path)).toString('base64')}`,
          ];
        return [];
      }),
  );
  return paths.flat().sort();
}

async function snapshot(repo: string) {
  return {
    files: await files(repo),
    status: gitOk(repo, 'status', '--porcelain=v1', '--untracked-files=all'),
    index: (await readFile(join(repo, '.git/index'))).toString('base64'),
  };
}

async function unchanged(
  repo: string,
  before: Awaited<ReturnType<typeof snapshot>>,
) {
  deepStrictEqual(await snapshot(repo), before);
}

async function noTempFiles(temp: string) {
  deepStrictEqual(await readdir(temp), []);
}

void test('300 passes and 301 fails with sizes; both runs leave files, status and index unchanged', async t => {
  const {repo, temp} = await repository(t);
  await put(repo, 'feature.ts', code(300));
  const beforePass = await snapshot(repo);
  const pass = runCheck(repo, temp);
  equal(pass.status, 0, pass.output);
  match(
    pass.output,
    /^Own code: 1 lines at [0-9a-f]{7} \(merge base with develop\), 301 in the worktree; net \+300 of 300 allowed\.$/m,
  );
  match(pass.output, /net \+300 of 300 allowed/);
  await unchanged(repo, beforePass);
  await noTempFiles(temp);

  await put(repo, 'feature.ts', code(301));
  const beforeFail = await snapshot(repo);
  const fail = runCheck(repo, temp);
  equal(fail.status, 1, fail.output);
  match(
    fail.output,
    /Record the user's approval as \*\*Own-code limit\*\*: <number>/,
  );
  match(
    fail.output,
    /^Own code: 1 lines at [0-9a-f]{7} \(merge base with develop\), 302 in the worktree; net \+301 of 300 allowed\.$/m,
  );
  match(fail.output, /net \+301 of 300 allowed/);
  await unchanged(repo, beforeFail);
  await noTempFiles(temp);
});

void test('400 added lines minus 150 deletions pass at net 250', async t => {
  const {repo, temp} = await repository(t, {files: {'old.ts': code(150)}});
  await rm(join(repo, 'old.ts'));
  await put(repo, 'new.ts', code(400));
  const result = runCheck(repo, temp);
  equal(result.status, 0, result.output);
  match(result.output, /net \+250 of 300 allowed/);
  await noTempFiles(temp);
});

void test('clean develop reports net zero', async t => {
  const {repo, temp} = await repository(t, {feature: false});
  const result = runCheck(repo, temp);
  equal(result.status, 0, result.output);
  match(result.output, /net \+0 of 300 allowed/);
  await noTempFiles(temp);
});

void test('untracked code counts and symbolic links do not', async t => {
  const {repo, temp} = await repository(t);
  await put(repo, 'src.ts', code(17));
  const link = spawnSync('ln', ['-s', 'src.ts', 'linked.ts'], {
    cwd: repo,
    encoding: 'utf8',
  });
  equal(link.status, 0, link.stderr);
  const result = runCheck(repo, temp);
  equal(result.status, 0, result.output);
  match(result.output, /net \+17 of 300 allowed/);
  await noTempFiles(temp);
});

void test('missing develop fails and leaves no temporary files', async t => {
  const {repo, temp} = await repository(t, {branch: 'main'});
  const result = runCheck(repo, temp);
  notEqual(result.status, 0, result.output);
  match(result.output, /develop/);
  await noTempFiles(temp);
});

void test('new approvals in each allowed records area raise the limit and name the file', async t => {
  for (const path of [
    'specs/feature/spec.md',
    '.specify/bugs/BUG-1.md',
    '.specify/assessments/review.md',
  ]) {
    const {repo, temp} = await repository(t);
    await put(repo, 'feature.ts', code(400));
    await put(
      repo,
      path,
      '**Own-code limit**: 450, approved by the user on 2026-09-30\n',
    );
    const result = runCheck(repo, temp);
    equal(result.status, 0, result.output);
    match(result.output, /net \+400 of 450 allowed/);
    match(result.output, new RegExp(path.replaceAll('.', '\\.')));
    await noTempFiles(temp);
  }
});

void test('largest new approval sets the limit', async t => {
  const {repo, temp} = await repository(t);
  await put(repo, 'feature.ts', code(400));
  await put(repo, 'specs/feature/spec.md', '**Own-code limit**: 450\n');
  await put(repo, '.specify/bugs/BUG-1.md', '**Own-code limit**: 500\n');
  const result = runCheck(repo, temp);
  equal(result.status, 0, result.output);
  match(result.output, /net \+400 of 500 allowed/);
  match(result.output, /\.specify\/bugs\/BUG-1\.md/);
  await noTempFiles(temp);
});

void test('approval at or below 300 does not raise the limit', async t => {
  const {repo, temp} = await repository(t);
  await put(repo, 'feature.ts', code(301));
  await put(repo, 'specs/feature/spec.md', '**Own-code limit**: 300\n');
  const result = runCheck(repo, temp);
  equal(result.status, 1, result.output);
  match(result.output, /net \+301 of 300 allowed/);
  await noTempFiles(temp);
});

void test('approval already present at the merge base is stale', async t => {
  const {repo, temp} = await repository(t, {
    files: {'specs/old/spec.md': '**Own-code limit**: 450\n'},
  });
  await put(repo, 'feature.ts', code(400));
  const result = runCheck(repo, temp);
  equal(result.status, 1, result.output);
  match(result.output, /net \+400 of 300 allowed/);
  await noTempFiles(temp);
});

void test('quoted approval text and an approval outside the records do not count', async t => {
  const {repo, temp} = await repository(t);
  await put(repo, 'feature.ts', code(301));
  await put(
    repo,
    'specs/feature/spec.md',
    'Example: **Own-code limit**: 450\n',
  );
  await put(repo, 'docs/approval.md', '**Own-code limit**: 450\n');
  const result = runCheck(repo, temp);
  equal(result.status, 1, result.output);
  match(result.output, /net \+301 of 300 allowed/);
  await noTempFiles(temp);
});

void test('test paths and file-name suffixes do not count', async t => {
  const {repo, temp} = await repository(t);
  await put(repo, 'tests/under.ts', code(500));
  await put(repo, 'src/helper_test.ts', code(500));
  await put(repo, 'src/helper.test.js', code(500));
  const result = runCheck(repo, temp);
  equal(result.status, 0, result.output);
  match(result.output, /net \+0 of 300 allowed/);
  await noTempFiles(temp);
});

void test('hashes in all upstream record forms exclude matching files', async t => {
  const {repo, temp} = await repository(t);
  const copy = code(500);
  const hash = createHash('sha256').update(copy).digest('hex');
  await put(repo, 'vendor/markdown.ts', copy);
  await put(repo, 'vendor/json.ts', copy);
  await put(repo, 'vendor/manifest.ts', copy);
  await put(repo, 'vendor/UPSTREAM.md', hash);
  await put(repo, 'vendor/upstream.json', JSON.stringify({sha256: hash}));
  await put(
    repo,
    '.specify/integrations/tool.manifest.json',
    JSON.stringify({sha256: hash}),
  );
  const result = runCheck(repo, temp);
  equal(result.status, 0, result.output);
  match(result.output, /net \+0 of 300 allowed/);
  await noTempFiles(temp);
});

void test('a patched upstream copy counts in full', async t => {
  const {repo, temp} = await repository(t);
  const original = code(500);
  const patched = original.replace('= 0;', '= 1;');
  const hash = createHash('sha256').update(original).digest('hex');
  await put(repo, 'vendor/copy.ts', patched);
  await put(repo, 'vendor/UPSTREAM.md', hash);
  const result = runCheck(repo, temp);
  equal(result.status, 1, result.output);
  match(result.output, /net \+500 of 300 allowed/);
  await noTempFiles(temp);
});

void test('non-programming files do not count', async t => {
  const {repo, temp} = await repository(t);
  await put(
    repo,
    'README.md',
    Array.from({length: 500}, (_, i) => `# row ${i}`).join('\n'),
  );
  await put(
    repo,
    'config.json',
    `[{\n${Array.from({length: 500}, (_, i) => `  "key_${i}": ${i}`).join(',\n')}\n}]\n`,
  );
  await put(
    repo,
    'config.yaml',
    Array.from({length: 500}, (_, i) => `key_${i}: ${i}`).join('\n'),
  );
  const result = runCheck(repo, temp);
  equal(result.status, 0, result.output);
  match(result.output, /net \+0 of 300 allowed/);
  await noTempFiles(temp);
});
