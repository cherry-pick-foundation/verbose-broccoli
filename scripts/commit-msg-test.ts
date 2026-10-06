import {spawnSync} from 'node:child_process';
import {
  copyFile,
  mkdir,
  mkdtemp,
  rm,
  readFile,
  symlink,
  writeFile,
} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';
import {assert, assertEquals, assertMatch} from '@std/assert';
import {join} from '@std/path';

const repositoryRoot = fileURLToPath(new URL('../', import.meta.url));

function command(
  executable: string,
  args: string[],
  cwd: string,
  env: NodeJS.ProcessEnv,
) {
  const result = spawnSync(executable, args, {
    cwd,
    env,
    encoding: 'utf8',
    timeout: 30_000,
  });
  if (result.error) throw result.error;
  if (result.signal)
    throw new Error(`${executable} terminated by signal ${result.signal}`);
  return {
    code: result.status ?? 1,
    output: `${result.stdout ?? ''}${result.stderr ?? ''}`,
  };
}

void test('lefthook commit-msg accepts conventional commits and rejects invalid ones', async () => {
  const root = await mkdtemp(join(tmpdir(), 'lefthook-commit-msg-test-'));
  const repo = join(root, 'repo');
  const env: NodeJS.ProcessEnv = {
    ...process.env,
    GIT_CONFIG_GLOBAL: '/dev/null',
    GIT_CONFIG_NOSYSTEM: '1',
  };
  delete env.LEFTHOOK;

  try {
    await mkdir(repo);
    await mkdir(join(repo, 'scripts'));
    await mkdir(join(repo, '.config'));
    await copyFile(
      join(repositoryRoot, '.config/lefthook.yml'),
      join(repo, '.config/lefthook.yml'),
    );
    await copyFile(
      join(repositoryRoot, 'scripts/commitlint.config.mjs'),
      join(repo, 'scripts/commitlint.config.mjs'),
    );
    await copyFile(
      join(repositoryRoot, 'scripts/guarded-mise-trust.sh'),
      join(repo, 'scripts/guarded-mise-trust.sh'),
    );
    await symlink(
      join(repositoryRoot, 'node_modules'),
      join(repo, 'node_modules'),
      'dir',
    );

    for (const args of [
      ['init', '--quiet', '--template=', '--initial-branch=main'],
      ['config', 'user.name', 'Commit Test'],
      ['config', 'user.email', 'commit-test@example.invalid'],
    ]) {
      const result = command('git', args, repo, env);
      assertEquals(result.code, 0, result.output);
    }

    const install = command(
      join(repo, 'node_modules/.bin/lefthook'),
      ['install'],
      repo,
      env,
    );
    assertEquals(install.code, 0, install.output);

    await writeFile(join(repo, 'seed.txt'), 'synthetic fixture\n');
    let result = command('git', ['add', 'seed.txt'], repo, env);
    assertEquals(result.code, 0, result.output);
    result = command(
      'git',
      [
        'commit',
        '-m',
        'feat: accept review trailers',
        '-m',
        'Spec-Kit-Task: T006\nReviewed-by: Reviewer\nReviewed-commit: abcdef123\nCo-Authored-By: Author <author@example.invalid>\nSigned-off-by: Commit Test <commit-test@example.invalid>',
      ],
      repo,
      env,
    );
    assertEquals(result.code, 0, result.output);

    for (const args of [
      ['checkout', '-b', 'feature'],
      ['commit', '--allow-empty', '-m', 'feat: add a feature change'],
      ['checkout', 'main'],
      ['commit', '--allow-empty', '-m', 'docs: add a main change'],
      ['merge', '--no-ff', 'feature'],
    ]) {
      result = command('git', args, repo, env);
      assertEquals(result.code, 0, result.output);
    }

    const head = command('git', ['rev-parse', 'HEAD'], repo, env);
    result = command(
      'git',
      ['commit', '--allow-empty', '-m', 'Update files'],
      repo,
      env,
    );
    assert(result.code !== 0, result.output);
    assertMatch(result.output, /type-empty|subject-empty/);
    assertEquals(
      command('git', ['rev-parse', 'HEAD'], repo, env).output,
      head.output,
    );
  } finally {
    await rm(root, {recursive: true, force: true});
  }
});

void test('checkout and merge trust only reviewed mise bytes without runtimes', async () => {
  const root = await mkdtemp(join(tmpdir(), 'guarded-mise-trust-test-'));
  const repo = join(root, 'linked worktree');
  const receipt = join(root, 'trust-receipt');
  const env: NodeJS.ProcessEnv = {
    ...process.env,
    GIT_CONFIG_GLOBAL: '/dev/null',
    GIT_CONFIG_NOSYSTEM: '1',
    TRUST_RECEIPT: receipt,
  };
  delete env.LEFTHOOK;
  delete env.LEFTHOOK_BIN;
  const git = (...args: string[]) => {
    const result = command('git', args, repo, env);
    assertEquals(result.code, 0, result.output);
    return result.output.trim();
  };
  try {
    await mkdir(repo);
    await mkdir(join(repo, '.config'));
    await mkdir(join(root, 'bin'));
    await writeFile(receipt, '');
    await copyFile(
      join(repositoryRoot, '.config/lefthook.yml'),
      join(repo, '.config/lefthook.yml'),
    );
    await symlink(
      join(repositoryRoot, 'scripts'),
      join(repo, 'scripts'),
      'dir',
    );
    await symlink(
      join(repositoryRoot, 'node_modules'),
      join(repo, 'node_modules'),
      'dir',
    );
    await writeFile(
      join(root, 'bin/mise'),
      '#!/bin/sh\nprintf "%s\\n" "$*" >> "$TRUST_RECEIPT"\n',
      {mode: 0o755},
    );
    for (const runtime of ['node', 'python', 'python3']) {
      await writeFile(join(root, 'bin', runtime), '#!/bin/sh\nexit 99\n', {
        mode: 0o755,
      });
    }
    git('init', '--quiet', '--template=', '--initial-branch=develop');
    git('config', 'user.name', 'Hook Test');
    git('config', 'user.email', 'hook-test@example.invalid');
    await writeFile(
      join(repo, '.config/mise.toml'),
      '[env]\nSYNTHETIC = "reviewed"\n',
    );
    git('add', '.config');
    git('commit', '-m', 'test: seed reviewed config');
    const reviewed = git('rev-parse', 'HEAD');
    git('checkout', '-b', 'feature');
    await writeFile(
      join(repo, '.config/mise.toml'),
      '[env]\nSYNTHETIC = "unreviewed"\n',
    );
    git('add', '.config/mise.toml');
    git('commit', '-m', 'test: change config');
    const differing = git('rev-parse', 'HEAD');
    const linked = join(root, 'other worktree');
    git('worktree', 'add', '--detach', linked, differing);
    for (const path of ['scripts', 'node_modules']) {
      await symlink(join(repositoryRoot, path), join(linked, path), 'dir');
    }
    const install = command(
      join(repo, 'node_modules/lefthook-linux-x64/bin/lefthook'),
      ['install'],
      repo,
      env,
    );
    assertEquals(install.code, 0, install.output);
    env.PATH = `${join(root, 'bin')}:/usr/bin:/bin`;
    const unprepared = join(root, 'unprepared worktree');
    git('worktree', 'add', '--detach', unprepared, differing);
    assertEquals(
      command('git', ['checkout', reviewed], unprepared, env).code,
      0,
    );
    assertEquals(await readFile(receipt, 'utf8'), '');
    assert(
      command(
        'git',
        ['commit', '--allow-empty', '-m', 'test: require commit dependencies'],
        unprepared,
        env,
      ).code !== 0,
    );
    assertEquals(command('git', ['checkout', reviewed], linked, env).code, 0);
    assertEquals(await readFile(receipt, 'utf8'), 'trust .config/mise.toml\n');
    await writeFile(receipt, '');
    git('checkout', 'develop');
    assertEquals(await readFile(receipt, 'utf8'), 'trust .config/mise.toml\n');
    await writeFile(receipt, '');
    git('checkout', 'feature');
    assertEquals(await readFile(receipt, 'utf8'), '');
    git('checkout', '--', '.config/mise.toml');
    assertEquals(await readFile(receipt, 'utf8'), '');
    // A dirty file must not be trusted even when the event's new tree matches.
    const checkout = join(repo, '.git/hooks/post-checkout');
    assertEquals(
      command('sh', [checkout, differing, reviewed, '1'], repo, env).code,
      0,
    );
    assertEquals(await readFile(receipt, 'utf8'), '');
    git('checkout', 'develop');
    await writeFile(receipt, '');
    // File restoration safely renews matching trust; unchanged branches skip it.
    git('checkout', '--', '.config/mise.toml');
    assertEquals(await readFile(receipt, 'utf8'), 'trust .config/mise.toml\n');
    await writeFile(receipt, '');
    git('checkout', '-b', 'unchanged');
    assertEquals(await readFile(receipt, 'utf8'), '');
    // Git attributes must not normalize different bytes into an approved match.
    await writeFile(join(repo, '.gitattributes'), '*.toml text\n');
    await writeFile(
      join(repo, '.config/mise.toml'),
      '[env]\r\nSYNTHETIC = "reviewed"\r\n',
    );
    assertEquals(
      command('sh', [checkout, differing, reviewed, '1'], repo, env).code,
      0,
    );
    assertEquals(await readFile(receipt, 'utf8'), '');
    await writeFile(
      join(repo, '.config/mise.toml'),
      '[env]\nSYNTHETIC = "reviewed"\n',
    );
    await rm(join(repo, '.gitattributes'));
    // Differing merge content stays untrusted while develop still holds old bytes.
    git('merge', '--ff-only', 'feature');
    assertEquals(await readFile(receipt, 'utf8'), '');
    git('checkout', '-b', 'reviewed-merge', reviewed);
    await writeFile(receipt, '');
    git('branch', '-D', 'develop');
    assertEquals(
      command('sh', [checkout, differing, reviewed, '1'], repo, env).code,
      0,
    );
    assertEquals(await readFile(receipt, 'utf8'), '');
    git('branch', 'develop', differing);
    git('merge', '--ff-only', 'feature');
    assertEquals(await readFile(receipt, 'utf8'), 'trust .config/mise.toml\n');
    git('checkout', '-b', 'squash-merge', reviewed);
    await writeFile(receipt, '');
    git('merge', '--squash', 'feature');
    assertEquals(await readFile(receipt, 'utf8'), 'trust .config/mise.toml\n');
  } finally {
    await rm(root, {recursive: true, force: true});
  }
});
