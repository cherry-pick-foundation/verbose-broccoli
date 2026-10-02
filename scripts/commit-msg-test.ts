import {spawnSync} from 'node:child_process';
import {
  copyFile,
  mkdir,
  mkdtemp,
  rm,
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

    await mkdir(join(repo, '.codex'));
    const config = join(repo, '.codex/config.toml');
    const portable = '[features]\nhooks = true\n';
    await writeFile(config, portable);
    assertEquals(
      command('git', ['add', '.codex/config.toml'], repo, env).code,
      0,
    );
    const generated =
      '# BEGIN generated plugin discovery\n[mcp_servers.synthetic]\nargs = ["/machine-specific/checkout/server"]\n# END generated plugin discovery\n';
    await writeFile(config, portable + generated);
    result = command(
      'git',
      ['commit', '-m', 'test: allow unstaged runtime discovery'],
      repo,
      env,
    );
    assertEquals(result.code, 0, result.output);
    assertEquals(
      command('git', ['show', 'HEAD:.codex/config.toml'], repo, env).output,
      portable,
    );
    const cleanHead = command('git', ['rev-parse', 'HEAD'], repo, env).output;
    for (const block of [generated, '# END generated plugin discovery\n']) {
      await writeFile(config, portable + block);
      assertEquals(
        command('git', ['add', '.codex/config.toml'], repo, env).code,
        0,
      );
      // A clean working file must not hide the staged machine-specific block.
      await writeFile(config, portable);
      result = command(
        'git',
        ['commit', '-m', 'test: refuse staged runtime discovery'],
        repo,
        env,
      );
      assert(result.code !== 0, result.output);
      assertMatch(
        result.output,
        /Generated Codex discovery must stay out of the index/,
      );
      assertEquals(
        command('git', ['rev-parse', 'HEAD'], repo, env).output,
        cleanHead,
      );
    }
  } finally {
    await rm(root, {recursive: true, force: true});
  }
});
