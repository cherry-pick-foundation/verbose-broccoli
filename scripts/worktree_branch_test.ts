import {test} from 'node:test';
import {assert, assertEquals, assertMatch} from '@std/assert';
import {basename, dirname, fromFileUrl, join} from '@std/path';
import {spawnSync} from 'node:child_process';

const script = fromFileUrl(new URL('./worktree-branch.sh', import.meta.url));
const decoder = new TextDecoder();

async function git(cwd: string, ...args: string[]) {
  const result = spawnSync('git', args, {
    cwd,
    env: {...process.env, ...gitEnv(cwd)},
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  if (result.error) throw result.error;
  const stdout = decoder.decode(result.stdout).trim();
  const stderr = decoder.decode(result.stderr).trim();
  assert(result.status === 0, `git ${args.join(' ')} failed: ${stderr}`);
  return stdout;
}

function gitEnv(cwd: string) {
  const home = dirname(cwd);
  return {
    GIT_CONFIG_GLOBAL: join(home, '.gitconfig'),
    GIT_CONFIG_NOSYSTEM: '1',
    HOME: home,
  };
}

async function runScript(cwd: string) {
  const result = spawnSync('sh', [script], {
    cwd,
    env: {...process.env, ...gitEnv(cwd)},
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  if (result.error) throw result.error;
  return {
    code: result.status ?? 1,
    stdout: decoder.decode(result.stdout).trim(),
    stderr: decoder.decode(result.stderr).trim(),
  };
}

type AddWorktree = (
  repo: string,
  name: string,
  base?: string,
  detached?: boolean,
) => Promise<string>;

async function temporary(
  run: (repo: string, addWorktree: AddWorktree) => Promise<void>,
) {
  const root = await Deno.makeTempDir({prefix: 'worktree-branch-test-'});
  const repo = join(root, 'develop');
  const addWorktree: AddWorktree = async (
    repo,
    name,
    base = 'develop',
    detached = false,
  ) => {
    const folder = join(dirname(repo), name);
    if (detached) {
      await git(repo, 'worktree', 'add', '--detach', folder, base);
    } else {
      await git(repo, 'worktree', 'add', '-b', name, folder, base);
    }
    return folder;
  };
  try {
    await Deno.mkdir(repo);
    await git(repo, 'init', '--initial-branch=develop');
    await git(repo, 'config', 'user.name', 'Worktree Branch Test');
    await git(
      repo,
      'config',
      'user.email',
      'worktree-branch-test@example.invalid',
    );
    await Deno.writeTextFile(join(repo, 'seed.txt'), 'seed\n');
    await git(repo, 'add', 'seed.txt');
    await git(repo, 'commit', '-m', 'initial');
    await git(repo, 'branch', 'main');
    await run(repo, addWorktree);
  } finally {
    await Deno.remove(root, {recursive: true});
  }
}

async function snapshot(repo: string) {
  return {
    refs: await git(repo, 'for-each-ref', '--format=%(refname) %(objectname)'),
    worktrees: await git(repo, 'worktree', 'list', '--porcelain'),
  };
}

function normalizeCurrentBranch(worktrees: string, folder: string) {
  return worktrees
    .split('\n\n')
    .map(worktree => {
      if (!worktree.startsWith(`worktree ${folder}\n`)) return worktree;
      return worktree.replace(/^branch .*$/m, 'branch <current>');
    })
    .join('\n\n');
}

async function assertOnlyRefRenamed(
  repo: string,
  beforeRefs: string,
  oldName: string,
  newName: string,
) {
  const refs = beforeRefs
    .split('\n')
    .filter(Boolean)
    .map(ref => {
      const oldRef = `refs/heads/${oldName} `;
      return ref.startsWith(oldRef)
        ? `refs/heads/${newName} ${ref.slice(oldRef.length)}`
        : ref;
    })
    .sort();
  assertEquals(
    (await git(repo, 'for-each-ref', '--format=%(refname) %(objectname)'))
      .split('\n')
      .filter(Boolean)
      .sort(),
    refs,
  );
}

async function assertUnchanged(
  repo: string,
  before: Awaited<ReturnType<typeof snapshot>>,
) {
  assertEquals(await snapshot(repo), before);
}

test('worktree branch: applies the documented name mappings and is idempotent', async () => {
  await temporary(async (repo, addWorktree) => {
    const cases = [
      {name: 'release-1.0', base: 'develop', target: 'release/1.0'},
      {name: 'hotfix-1.0', base: 'main', target: 'hotfix/1.0'},
      {
        name: 'governance-policies',
        base: 'develop',
        target: 'feature/governance-policies',
      },
      {
        name: 'feature-governance-policies',
        base: 'develop',
        target: 'feature/governance-policies',
      },
    ];
    for (const {name, base, target} of cases) {
      const folder = await addWorktree(repo, name, base);
      const before = await snapshot(repo);
      const head = await git(folder, 'rev-parse', 'HEAD');
      const result = await runScript(folder);
      assertEquals(result.code, 0, result.stderr);
      assertEquals(await git(folder, 'branch', '--show-current'), target);
      assertEquals(await git(folder, 'rev-parse', 'HEAD'), head);
      assertEquals(basename(folder), name);
      assertEquals(await git(folder, 'rev-parse', '--show-toplevel'), folder);
      await assertOnlyRefRenamed(repo, before.refs, name, target);
      assertEquals(
        normalizeCurrentBranch(before.worktrees, folder),
        normalizeCurrentBranch((await snapshot(repo)).worktrees, folder),
      );

      const afterFirstRun = await snapshot(repo);
      const second = await runScript(folder);
      assertEquals(second.code, 0, second.stderr);
      assertEquals(await snapshot(repo), afterFirstRun);
      await git(repo, 'worktree', 'remove', folder);
      await git(repo, 'branch', '-D', target);
    }
  });
});

test('worktree branch: skips branches that must not be renamed', async () => {
  await temporary(async (repo, addWorktree) => {
    const cases = ['feature/already', 'release/already', 'hotfix/already'];
    for (const name of cases) {
      const folder = await addWorktree(repo, name);
      const before = await snapshot(repo);
      const result = await runScript(folder);
      assertEquals(result.code, 0, result.stderr);
      await assertUnchanged(repo, before);
    }

    const ownCommit = await addWorktree(repo, 'own-commit');
    await Deno.writeTextFile(join(ownCommit, 'own.txt'), 'own\n');
    await git(ownCommit, 'add', 'own.txt');
    await git(ownCommit, 'commit', '-m', 'own change');
    let before = await snapshot(repo);
    let result = await runScript(ownCommit);
    assertEquals(result.code, 0, result.stderr);
    await assertUnchanged(repo, before);

    const upstream = await addWorktree(repo, 'upstream-branch');
    await git(repo, 'branch', '--set-upstream-to=develop', 'upstream-branch');
    before = await snapshot(repo);
    result = await runScript(upstream);
    assertEquals(result.code, 0, result.stderr);
    await assertUnchanged(repo, before);

    const detached = await addWorktree(repo, 'detached', 'develop', true);
    before = await snapshot(repo);
    result = await runScript(detached);
    assertEquals(result.code, 0, result.stderr);
    await assertUnchanged(repo, before);

    const main = await git(repo, 'rev-parse', 'main');
    const mainFolder = join(dirname(repo), 'main-worktree');
    await git(repo, 'worktree', 'add', mainFolder, 'main');
    before = await snapshot(repo);
    result = await runScript(mainFolder);
    assertEquals(result.code, 0, result.stderr);
    assertEquals(await git(mainFolder, 'rev-parse', 'HEAD'), main);
    await assertUnchanged(repo, before);

    before = await snapshot(repo);
    result = await runScript(repo);
    assertEquals(result.code, 0, result.stderr);
    await assertUnchanged(repo, before);
  });
});

test('worktree branch: refuses invalid or existing targets without changes', async () => {
  await temporary(async (repo, addWorktree) => {
    const cases = ['release-', 'release-.hidden'];
    for (const name of cases) {
      const folder = await addWorktree(repo, name);
      const before = await snapshot(repo);
      const result = await runScript(folder);
      assertEquals(result.code, 1, result.stderr);
      assert(result.stderr.length > 0);
      assertEquals(await git(folder, 'branch', '--show-current'), name);
      await assertUnchanged(repo, before);
    }

    const collision = await addWorktree(repo, 'release-2.0');
    await git(repo, 'branch', 'release/2.0', 'develop');
    const before = await snapshot(repo);
    const result = await runScript(collision);
    assertEquals(result.code, 1, result.stderr);
    assertMatch(result.stderr, /already exists/i);
    assertEquals(
      await git(collision, 'branch', '--show-current'),
      'release-2.0',
    );
    await assertUnchanged(repo, before);
  });
});
