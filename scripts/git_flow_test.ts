import {assert, assertEquals, assertMatch} from '@std/assert';
import {dirname, fromFileUrl, join} from '@std/path';

const root = fromFileUrl(new URL('../', import.meta.url));
const sharedConfig = join(root, '.gitflow');
const sharedHook = join(root, 'scripts/git-flow-hooks/pre-flow-feature-finish');
const featureName = 'flow-test';
const featureBranch = `feature/${featureName}`;
const decoder = new TextDecoder();

async function git(cwd: string, ...args: string[]) {
  const result = await new Deno.Command('git', {
    args,
    cwd,
    env: {
      GIT_CONFIG_GLOBAL: join(dirname(cwd), '.gitconfig'),
      GIT_CONFIG_NOSYSTEM: '1',
      HOME: dirname(cwd),
    },
    stdout: 'piped',
    stderr: 'piped',
  }).output();
  const stdout = decoder.decode(result.stdout).trim();
  const stderr = decoder.decode(result.stderr).trim();
  assert(result.success, `git ${args.join(' ')} failed: ${stderr}`);
  return stdout;
}

async function attemptFinish(cwd: string) {
  const result = await new Deno.Command('git', {
    args: ['flow', 'feature', 'finish', featureName],
    cwd,
    env: {
      GIT_CONFIG_GLOBAL: join(dirname(cwd), '.gitconfig'),
      GIT_CONFIG_NOSYSTEM: '1',
      HOME: dirname(cwd),
    },
    stdout: 'piped',
    stderr: 'piped',
  }).output();
  return {
    code: result.code,
    output: `${decoder.decode(result.stdout)}\n${decoder.decode(
      result.stderr,
    )}`,
  };
}

async function temporary(
  run: (root: string, develop: string, feature: string) => Promise<void>,
  verifyExit = 0,
) {
  const root = await Deno.makeTempDir({prefix: 'git-flow-test-'});
  const repo = join(root, 'develop');
  const feature = join(root, 'feature');
  try {
    await Deno.mkdir(repo);
    await git(repo, 'init', '--initial-branch=develop');
    await git(repo, 'config', 'user.name', 'Git Flow Test');
    await git(repo, 'config', 'user.email', 'git-flow-test@example.invalid');
    await Deno.mkdir(join(repo, 'scripts/git-flow-hooks'), {recursive: true});
    await Deno.copyFile(sharedConfig, join(repo, '.gitflow'));
    const hook = join(repo, 'scripts/git-flow-hooks/pre-flow-feature-finish');
    await Deno.copyFile(sharedHook, hook);
    await Deno.chmod(hook, 0o755);
    await Deno.writeTextFile(
      join(repo, 'deno.json'),
      JSON.stringify({
        tasks: {verify: `deno eval 'Deno.exit(${verifyExit})'`},
      }),
    );
    await Deno.writeTextFile(join(repo, 'seed.txt'), 'seed\n');
    await git(repo, 'add', '.gitflow', 'deno.json', 'scripts', 'seed.txt');
    await git(repo, 'commit', '-m', 'initial');
    await git(repo, 'branch', 'main');
    await git(repo, 'worktree', 'add', '-b', featureBranch, feature, 'develop');
    await Deno.writeTextFile(join(feature, 'feature.txt'), 'feature\n');
    await git(feature, 'add', 'feature.txt');
    await git(feature, 'commit', '-m', 'feature change');
    await git(repo, 'config', 'gitflow.shared.trustHooks', 'true');
    await git(repo, 'flow', 'config', 'sync');
    await git(repo, 'flow', 'config', 'status');
    await run(root, repo, feature);
  } finally {
    await Deno.remove(root, {recursive: true});
  }
}

async function snapshot(repo: string, feature: string) {
  return {
    branches: await git(
      repo,
      'for-each-ref',
      '--format=%(refname) %(objectname)',
      'refs/heads',
    ),
    worktrees: await git(repo, 'worktree', 'list', '--porcelain'),
    developStatus: await git(
      repo,
      'status',
      '--porcelain',
      '--untracked-files=all',
    ),
    featureStatus: await git(
      feature,
      'status',
      '--porcelain',
      '--untracked-files=all',
    ),
  };
}

Deno.test('git-flow: feature worktree invocation is refused without changing branches or worktrees', async () => {
  await temporary(async (_root, develop, feature) => {
    const before = await snapshot(develop, feature);
    const result = await attemptFinish(feature);
    assert(result.code !== 0, result.output);
    assertMatch(
      result.output,
      /run the feature finish from the 'develop' worktree/,
    );
    assertEquals(await snapshot(develop, feature), before);
    assertEquals(await git(feature, 'status', '--porcelain'), '');
  });
});

Deno.test('git-flow: finish is refused when develop has a commit the feature lacks', async () => {
  await temporary(async (_root, develop, feature) => {
    await Deno.writeTextFile(join(develop, 'develop-only.txt'), 'develop\n');
    await git(develop, 'add', 'develop-only.txt');
    await git(develop, 'commit', '-m', 'develop advances');
    const before = await snapshot(develop, feature);
    const result = await attemptFinish(develop);
    assert(result.code !== 0, result.output);
    assertMatch(
      result.output,
      /merge 'develop' into 'feature\/flow-test', verify it/,
    );
    assertEquals(await snapshot(develop, feature), before);
  });
});

Deno.test('git-flow: finish is refused when feature verification fails', async () => {
  await temporary(async (_root, develop, feature) => {
    const before = await snapshot(develop, feature);
    const result = await attemptFinish(develop);
    assert(result.code !== 0, result.output);
    assertMatch(
      result.output,
      /verification failed in the 'feature\/flow-test' worktree/,
    );
    assertEquals(await snapshot(develop, feature), before);
  }, 1);
});

Deno.test('git-flow: finish from develop creates the default no-ff merge and keeps the feature worktree', async () => {
  await temporary(async (_root, develop, feature) => {
    const developBefore = await git(develop, 'rev-parse', 'HEAD');
    const featureHead = await git(feature, 'rev-parse', 'HEAD');
    const featureTree = await git(feature, 'rev-parse', 'HEAD^{tree}');
    const result = await attemptFinish(develop);
    assertEquals(result.code, 0, result.output);

    const commit = (
      await git(develop, 'rev-list', '--parents', '-n', '1', 'HEAD')
    ).split(' ');
    assertEquals(commit.slice(1), [developBefore, featureHead]);
    assertEquals(await git(develop, 'rev-parse', 'HEAD^{tree}'), featureTree);
    assertEquals(
      await git(develop, 'log', '-1', '--format=%s'),
      `Merge branch '${featureBranch}' into develop`,
    );
    assertEquals(
      await git(develop, 'rev-parse', `refs/heads/${featureBranch}`),
      featureHead,
    );
    assert(
      (await git(develop, 'worktree', 'list', '--porcelain')).includes(
        `worktree ${feature}\nHEAD ${featureHead}\nbranch refs/heads/${featureBranch}`,
      ),
    );
    assertEquals(await git(develop, 'status', '--porcelain'), '');
    assertEquals(await git(feature, 'status', '--porcelain'), '');
  });
});
