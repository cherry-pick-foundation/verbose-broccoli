import {spawnSync} from 'node:child_process';
import {
  copyFile,
  mkdir,
  mkdtemp,
  readdir,
  readFile,
  rm,
  writeFile,
} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';
import {assert, assertEquals} from '@std/assert';
import {join} from '@std/path';

const repositoryRoot = fileURLToPath(new URL('../', import.meta.url));
const commitizenProject = join(repositoryRoot, 'tools/commitizen');
const gitEnv = {
  GIT_CONFIG_GLOBAL: '/dev/null',
  GIT_CONFIG_NOSYSTEM: '1',
};

function command(
  executable: string,
  args: string[],
  cwd: string,
  env: Record<string, string> = {},
) {
  const result = spawnSync(executable, args, {
    cwd,
    env: {...process.env, ...gitEnv, ...env},
    encoding: 'utf8',
    timeout: 30_000,
  });
  if (result.error) throw result.error;
  if (result.signal)
    throw new Error(`${executable} terminated by signal ${result.signal}`);
  return {
    code: result.status ?? 1,
    stdout: result.stdout ?? '',
    output: `${result.stdout ?? ''}${result.stderr ?? ''}`,
  };
}

void test('constitution bump rewrites the version line in a temporary copy', async () => {
  const root = await mkdtemp(join(tmpdir(), 'constitution-bump-test-'));
  try {
    await mkdir(join(root, '.specify/memory'), {recursive: true});
    await copyFile(join(repositoryRoot, '.cz.toml'), join(root, '.cz.toml'));
    await writeFile(
      join(root, '.specify/memory/constitution.md'),
      'Synthetic fixture mentions 2.2.0 here.\n\n**Version**: 2.2.0 | Ratified: test\n',
    );

    for (const args of [
      ['init', '--quiet', '--initial-branch=main'],
      ['config', 'user.name', 'Constitution Test'],
      ['config', 'user.email', 'constitution-test@example.invalid'],
      ['add', '.'],
      ['commit', '--quiet', '-m', 'fix: seed fixture'],
    ]) {
      const result = command('git', args, root);
      assertEquals(result.code, 0, result.output);
    }

    const uv = command('mise', ['which', 'uv'], repositoryRoot);
    assertEquals(uv.code, 0, uv.output);
    const headBefore = command('git', ['rev-parse', 'HEAD'], root);
    const bump = command(
      uv.stdout.trim(),
      [
        'run',
        '--project',
        commitizenProject,
        '--frozen',
        '--no-sync',
        'cz',
        'bump',
        '--files-only',
        '--yes',
        '--increment',
        'PATCH',
      ],
      root,
    );
    assertEquals(bump.code, 0, bump.output);
    assertEquals(
      await readFile(join(root, '.specify/memory/constitution.md'), 'utf8'),
      'Synthetic fixture mentions 2.2.0 here.\n\n**Version**: 2.2.1 | Ratified: test\n',
    );
    assert(
      (await readFile(join(root, '.cz.toml'), 'utf8')).includes(
        'version = "2.2.1"',
      ),
    );
    assertEquals(
      command('git', ['rev-parse', 'HEAD'], root).output,
      headBefore.output,
    );
    assertEquals(command('git', ['tag', '--list'], root).output, '');
    assert(!(await readdir(root)).includes('CHANGELOG.md'));
  } finally {
    await rm(root, {recursive: true, force: true});
  }
});
