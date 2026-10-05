import {spawnSync} from 'node:child_process';
import {test} from 'node:test';
import {
  chmod,
  copyFile,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  symlink,
  writeFile,
} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {assert, assertEquals, assertMatch, assertThrows} from '@std/assert';
import {dirname, fromFileUrl, join} from '@std/path';

const root = fromFileUrl(new URL('../', import.meta.url));
const sharedConfig = join(root, '.gitflow');
const sharedHook = join(root, 'scripts/git-flow-hooks/pre-flow-feature-finish');
const postHook = join(root, 'scripts/git-flow-hooks/post-flow-feature-finish');
const featureName = 'flow-test';
const featureBranch = `feature/${featureName}`;
const decoder = new TextDecoder();
async function runGit(
  cwd: string,
  args: string[],
  extraEnv: Record<string, string> = {},
) {
  return commandOutput('git', {
    args,
    cwd,
    env: {
      GIT_CONFIG_GLOBAL: join(dirname(cwd), '.gitconfig'),
      GIT_CONFIG_NOSYSTEM: '1',
      HOME: dirname(cwd),
      ...extraEnv,
    },
  });
}

function runPostHook(
  cwd: string,
  args: string[],
  extraEnv: Record<string, string> = {},
) {
  return commandOutput(postHook, {
    args,
    cwd,
    env: {
      GIT_CONFIG_GLOBAL: join(dirname(cwd), '.gitconfig'),
      GIT_CONFIG_NOSYSTEM: '1',
      HOME: dirname(cwd),
      ...extraEnv,
    },
  });
}

function commandOutput(
  command: string,
  options: {args: string[]; cwd?: string; env?: Record<string, string>},
) {
  const result = spawnSync(command, options.args, {
    cwd: options.cwd,
    env: options.env ? {...process.env, ...options.env} : undefined,
    encoding: null,
  });
  if (result.error) throw result.error;
  if (result.signal)
    throw new Error(`${command} terminated by signal ${result.signal}`);
  return {
    code: result.status ?? 1,
    success: result.status === 0,
    stdout: result.stdout ?? Buffer.alloc(0),
    stderr: result.stderr ?? Buffer.alloc(0),
  };
}

void test('git-flow test commands reject children terminated by a signal', () => {
  assertThrows(
    () => commandOutput('sh', {args: ['-c', 'kill -TERM $$']}),
    Error,
    'SIGTERM',
  );
});

async function git(cwd: string, ...args: string[]) {
  const result = await runGit(cwd, args);
  const stdout = decoder.decode(result.stdout).trim();
  const stderr = decoder.decode(result.stderr).trim();
  assert(result.success, `git ${args.join(' ')} failed: ${stderr}`);
  return stdout;
}

async function attemptFinish(cwd: string, name = featureName) {
  const result = await runGit(cwd, ['flow', 'feature', 'finish', name]);
  return {
    code: result.code,
    output: `${decoder.decode(result.stdout)}\n${decoder.decode(
      result.stderr,
    )}`,
  };
}

async function addReviewRecord(
  feature: string,
  options: {
    reviewedCommit?: string;
    trailers?: string[];
    changedFile?: boolean;
  } = {},
) {
  const parent = await git(feature, 'rev-parse', 'HEAD');
  const trailers = options.trailers ?? [
    'Reviewed-by: Claude Code (claude-opus-5-5)',
    `Reviewed-commit: ${options.reviewedCommit ?? parent}`,
  ];
  if (options.changedFile) {
    await writeFile(join(feature, 'reviewed.txt'), 'changed\n');
    await git(feature, 'add', 'reviewed.txt');
  }
  await git(
    feature,
    'commit',
    '--allow-empty',
    '-m',
    'chore(review): record merge review',
    ...(trailers.length ? ['-m', trailers.join('\n')] : []),
  );
  return await git(feature, 'rev-parse', 'HEAD');
}

async function temporary(
  run: (root: string, develop: string, feature: string) => Promise<void>,
  verifyExit = 0,
) {
  const tempRoot = await mkdtemp(join(tmpdir(), 'git-flow-test-'));
  const repo = join(tempRoot, 'develop');
  const feature = join(tempRoot, 'feature');
  try {
    await mkdir(repo);
    await git(repo, 'init', '--initial-branch=develop');
    await git(repo, 'config', 'user.name', 'Git Flow Test');
    await git(repo, 'config', 'user.email', 'git-flow-test@example.invalid');
    await mkdir(join(repo, 'scripts/git-flow-hooks'), {recursive: true});
    await copyFile(sharedConfig, join(repo, '.gitflow'));
    const hook = join(repo, 'scripts/git-flow-hooks/pre-flow-feature-finish');
    await copyFile(sharedHook, hook);
    await chmod(hook, 0o755);
    const postHookCopy = join(
      repo,
      'scripts/git-flow-hooks/post-flow-feature-finish',
    );
    await copyFile(postHook, postHookCopy);
    await chmod(postHookCopy, 0o755);
    const packageConfig = JSON.parse(
      await readFile(join(root, 'package.json'), 'utf8'),
    ) as {scripts: Record<string, string>};
    packageConfig.scripts.verify = `node -e "process.exit(${verifyExit})"`;
    await writeFile(join(repo, 'package.json'), JSON.stringify(packageConfig));
    for (const file of ['.gitignore', 'package-lock.json'])
      await copyFile(join(root, file), join(repo, file));
    await symlink(
      join(root, 'node_modules'),
      join(repo, 'node_modules'),
      'dir',
    );
    await writeFile(join(repo, '.gitignore'), '\nnode_modules\n', {
      flag: 'a',
    });
    await writeFile(join(repo, 'seed.txt'), 'seed\n');
    await git(
      repo,
      'add',
      '.gitflow',
      '.gitignore',
      'package.json',
      'package-lock.json',
      'scripts',
      'seed.txt',
    );
    await git(repo, 'commit', '-m', 'initial');
    await git(repo, 'branch', 'main');
    await git(repo, 'worktree', 'add', '-b', featureBranch, feature, 'develop');
    await writeFile(join(feature, 'feature.txt'), 'feature\n');
    await git(feature, 'add', 'feature.txt');
    await git(feature, 'commit', '-m', 'feature change');
    await git(repo, 'config', 'gitflow.shared.trustHooks', 'true');
    await git(repo, 'flow', 'config', 'sync');
    await git(repo, 'flow', 'config', 'status');
    await run(tempRoot, repo, feature);
  } finally {
    await rm(tempRoot, {recursive: true});
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

void test('git-flow: feature worktree invocation is refused without changing branches or worktrees', async () => {
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

void test('git-flow: finish is refused when develop has a commit the feature lacks', async () => {
  await temporary(async (_root, develop, feature) => {
    await writeFile(join(develop, 'develop-only.txt'), 'develop\n');
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

void test('git-flow: finish is refused when feature verification fails', async () => {
  await temporary(async (_root, develop, feature) => {
    await addReviewRecord(feature);
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

async function assertRefusedUnchanged(
  develop: string,
  feature: string,
  message: RegExp,
) {
  const before = await snapshot(develop, feature);
  const result = await attemptFinish(develop);
  assert(result.code !== 0, result.output);
  assertMatch(result.output, message);
  assertEquals(await snapshot(develop, feature), before);
}

void test('git-flow: finish is refused when the feature tip has no review record', async () => {
  await temporary(async (_root, develop, feature) => {
    await assertRefusedUnchanged(
      develop,
      feature,
      /feature\/flow-test.*(tree|review-record)/i,
    );
  });
});

void test('git-flow: finish is refused when Reviewed-commit is not the record parent', async () => {
  await temporary(async (_root, develop, feature) => {
    await addReviewRecord(feature, {
      reviewedCommit: await git(develop, 'rev-parse', 'HEAD'),
    });
    await assertRefusedUnchanged(
      develop,
      feature,
      /Reviewed-commit.*(parent|reviewed commit)/i,
    );
  });
});

void test('git-flow: finish is refused when the review record changes the tree', async () => {
  await temporary(async (_root, develop, feature) => {
    await addReviewRecord(feature, {changedFile: true});
    await assertRefusedUnchanged(
      develop,
      feature,
      /tip tree differs.*review-record/i,
    );
  });
});

void test('git-flow: finish is refused when Reviewed-by is missing', async () => {
  await temporary(async (_root, develop, feature) => {
    const parent = await git(feature, 'rev-parse', 'HEAD');
    await addReviewRecord(feature, {
      trailers: [`Reviewed-commit: ${parent}`],
    });
    await assertRefusedUnchanged(develop, feature, /Reviewed-by/i);
  });
});

void test('git-flow: finish is refused when Reviewed-commit is missing', async () => {
  await temporary(async (_root, develop, feature) => {
    await addReviewRecord(feature, {
      trailers: ['Reviewed-by: Claude Code'],
    });
    await assertRefusedUnchanged(develop, feature, /Reviewed-commit/i);
  });
});

void test('git-flow: finish is refused when Reviewed-by is duplicated', async () => {
  await temporary(async (_root, develop, feature) => {
    const parent = await git(feature, 'rev-parse', 'HEAD');
    await addReviewRecord(feature, {
      trailers: [
        'Reviewed-by: Claude Code',
        'Reviewed-by: Codex',
        `Reviewed-commit: ${parent}`,
      ],
    });
    await assertRefusedUnchanged(
      develop,
      feature,
      /exactly one non-empty Reviewed-by/i,
    );
  });
});

void test('git-flow: finish is refused when Reviewed-by is empty', async () => {
  await temporary(async (_root, develop, feature) => {
    const parent = await git(feature, 'rev-parse', 'HEAD');
    await addReviewRecord(feature, {
      trailers: ['Reviewed-by:', `Reviewed-commit: ${parent}`],
    });
    await assertRefusedUnchanged(
      develop,
      feature,
      /exactly one non-empty Reviewed-by/i,
    );
  });
});

void test('git-flow: finish is refused when Reviewed-by has an empty duplicate', async () => {
  await temporary(async (_root, develop, feature) => {
    const parent = await git(feature, 'rev-parse', 'HEAD');
    await addReviewRecord(feature, {
      trailers: [
        'Reviewed-by: X',
        'Reviewed-by:',
        `Reviewed-commit: ${parent}`,
      ],
    });
    await assertRefusedUnchanged(
      develop,
      feature,
      /exactly one non-empty Reviewed-by/i,
    );
  });
});

void test('git-flow: finish is refused when Reviewed-commit has an empty duplicate', async () => {
  await temporary(async (_root, develop, feature) => {
    const parent = await git(feature, 'rev-parse', 'HEAD');
    await addReviewRecord(feature, {
      trailers: [
        'Reviewed-by: X',
        `Reviewed-commit: ${parent}`,
        'Reviewed-commit:',
      ],
    });
    await assertRefusedUnchanged(
      develop,
      feature,
      /exactly one non-empty Reviewed-commit/i,
    );
  });
});

void test('git-flow: finish is refused after develop is merged after the review record', async () => {
  await temporary(async (_root, develop, feature) => {
    await addReviewRecord(feature);
    await writeFile(join(develop, 'develop-only.txt'), 'develop\n');
    await git(develop, 'add', 'develop-only.txt');
    await git(develop, 'commit', '-m', 'develop advances');
    await git(feature, 'merge', 'develop', '--no-edit');
    await assertRefusedUnchanged(
      develop,
      feature,
      /single-parent|review-record/i,
    );
  });
});

void test('git-flow: abbreviated Reviewed-commit values are accepted', async () => {
  await temporary(async (_root, develop, feature) => {
    const parent = await git(feature, 'rev-parse', 'HEAD');
    const record = await addReviewRecord(feature, {
      reviewedCommit: parent.slice(0, 8),
    });
    const result = await attemptFinish(develop);
    assertEquals(result.code, 0, result.output);
    const commit = (
      await git(develop, 'rev-list', '--parents', '-n', '1', 'HEAD')
    ).split(' ');
    assertEquals(commit.slice(2), [record]);
    assertEquals(
      await git(develop, 'rev-parse', 'HEAD^{tree}'),
      await git(feature, 'rev-parse', `${parent}^{tree}`),
    );
  });
});

void test('git-flow: lower-case review trailer keys are accepted', async () => {
  await temporary(async (_root, develop, feature) => {
    const parent = await git(feature, 'rev-parse', 'HEAD');
    const record = await addReviewRecord(feature, {
      trailers: ['reviewed-by: Codex', `reviewed-commit: ${parent}`],
    });
    const result = await attemptFinish(develop);
    assertEquals(result.code, 0, result.output);
    const commit = (
      await git(develop, 'rev-list', '--parents', '-n', '1', 'HEAD')
    ).split(' ');
    assertEquals(commit.slice(2), [record]);
  });
});

void test('git-flow: finish from develop creates the default no-ff merge and keeps the feature worktree', async () => {
  await temporary(async (_root, develop, feature) => {
    const reviewedCommit = await git(feature, 'rev-parse', 'HEAD');
    const reviewRecord = await addReviewRecord(feature);
    const developBefore = await git(develop, 'rev-parse', 'HEAD');
    const featureHead = await git(feature, 'rev-parse', 'HEAD');
    const reviewedTree = await git(
      feature,
      'rev-parse',
      `${reviewedCommit}^{tree}`,
    );
    const result = await attemptFinish(develop);
    assertEquals(result.code, 0, result.output);

    const commit = (
      await git(develop, 'rev-list', '--parents', '-n', '1', 'HEAD')
    ).split(' ');
    assertEquals(commit.slice(1), [developBefore, reviewRecord]);
    assertEquals(await git(develop, 'rev-parse', 'HEAD^{tree}'), reviewedTree);
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

void test('git-flow: each successful feature finish prints its retained tip and worktree cleanup steps', async () => {
  await temporary(async (tempRoot, develop, feature) => {
    const firstTip = await addReviewRecord(feature);
    const quotedFeature = join(
      tempRoot,
      ['feature ', "'", '"', '$', '`'].join(''),
    );
    await git(develop, 'worktree', 'move', feature, quotedFeature);
    const first = await attemptFinish(develop);
    assertEquals(first.code, 0, first.output);
    assertMatch(
      first.output,
      new RegExp(`^Source branch tip: ${firstTip}$`, 'm'),
    );
    assertMatch(
      first.output,
      new RegExp(`^Post-merge cleanup for ${featureBranch}$`, 'm'),
    );
    const quotedPath = await git(
      develop,
      'rev-parse',
      '--sq-quote',
      quotedFeature,
    );
    assert(
      first.output.includes(`Source worktree: ${quotedPath}`),
      first.output,
    );
    assertMatch(
      first.output,
      /settle workers first and\s+close only idle feature sessions/i,
    );
    const quotedSelector = await git(
      develop,
      'rev-parse',
      '--sq-quote',
      `path:${quotedFeature}`,
    );
    assert(
      first.output.includes(
        `Orca removal command: orca-ide worktree rm --worktree ${quotedSelector}`,
      ),
      first.output,
    );
    assert(
      first.output.indexOf('Orca removal command:') >
        first.output.indexOf('settle workers first'),
      first.output,
    );
    const quotedBranch = await git(
      develop,
      'rev-parse',
      '--sq-quote',
      featureBranch,
    );
    const quotedTip = await git(develop, 'rev-parse', '--sq-quote', firstTip);
    assert(
      first.output.includes(
        `If Orca deleted the source branch, recreate it at the recorded tip with: git branch ${quotedBranch} ${quotedTip}`,
      ),
      first.output,
    );

    const secondFeature = join(tempRoot, 'feature-two');
    const secondBranch = 'feature/flow-test-two';
    await git(
      develop,
      'worktree',
      'add',
      '-b',
      secondBranch,
      secondFeature,
      'develop',
    );
    await writeFile(join(secondFeature, 'second.txt'), 'second feature\n');
    await git(secondFeature, 'add', 'second.txt');
    await git(secondFeature, 'commit', '-m', 'second feature change');
    const secondTip = await addReviewRecord(secondFeature);
    const second = await attemptFinish(develop, 'flow-test-two');
    assertEquals(second.code, 0, second.output);
    assertMatch(
      second.output,
      new RegExp(`^Source branch tip: ${secondTip}$`, 'm'),
    );
    assertMatch(
      second.output,
      new RegExp(`^Post-merge cleanup for ${secondBranch}$`, 'm'),
    );
    const quotedSecondPath = await git(
      develop,
      'rev-parse',
      '--sq-quote',
      secondFeature,
    );
    assert(
      second.output.includes(`Source worktree: ${quotedSecondPath}`),
      second.output,
    );
    assertMatch(
      second.output,
      /Orca removal command: orca-ide worktree rm --worktree /,
    );
    assertMatch(
      second.output,
      /settle workers first and\s+close only idle feature sessions/i,
    );
    assertEquals(
      await git(develop, 'rev-parse', `refs/heads/${secondBranch}`),
      secondTip,
    );
    assert(
      (await git(develop, 'worktree', 'list', '--porcelain')).includes(
        `worktree ${secondFeature}\nHEAD ${secondTip}\nbranch refs/heads/${secondBranch}`,
      ),
    );
  });
});

void test('git-flow: post hook uses its positional source branch and asks to inspect if none is available', async () => {
  await temporary(async (_root, develop, feature) => {
    const featureTip = await git(
      develop,
      'rev-parse',
      `refs/heads/${featureBranch}`,
    );
    const before = await snapshot(develop, feature);
    const positional = runPostHook(
      develop,
      [featureName, 'develop', featureBranch],
      {BRANCH: '', EXIT_CODE: '0'},
    );
    const positionalOutput = `${decoder.decode(positional.stdout)}\n${decoder.decode(positional.stderr)}`;
    assert(positional.success, positionalOutput);
    assertMatch(
      positionalOutput,
      new RegExp(`^Source branch tip: ${featureTip}$`, 'm'),
    );
    assertMatch(
      positionalOutput,
      new RegExp(`^Post-merge cleanup for ${featureBranch}$`, 'm'),
    );

    const missing = runPostHook(develop, [], {BRANCH: '', EXIT_CODE: '0'});
    const missingOutput = `${decoder.decode(missing.stdout)}\n${decoder.decode(missing.stderr)}`;
    assert(missing.success, missingOutput);
    assertMatch(
      missingOutput,
      /did not provide the source branch; inspect the finish manually/i,
    );
    assert(!missingOutput.includes('orca-ide worktree rm'), missingOutput);
    assertEquals(await snapshot(develop, feature), before);
  });
});

void test('git-flow: failed feature finish never prints cleanup instructions or removes its source', async () => {
  await temporary(async (_root, develop, feature) => {
    const featureTip = await addReviewRecord(feature);
    const commitMsgHook = join(develop, '.git/hooks/commit-msg');
    await writeFile(commitMsgHook, '#!/bin/sh\nexit 1\n');
    await chmod(commitMsgHook, 0o755);

    const result = await attemptFinish(develop);
    assert(result.code !== 0, result.output);
    assert(!result.output.includes('Post-merge cleanup'), result.output);
    const hookResult = runPostHook(develop, [], {
      BRANCH: featureBranch,
      EXIT_CODE: '1',
    });
    assert(hookResult.success);
    assertEquals(decoder.decode(hookResult.stdout), '');
    assertEquals(
      await git(develop, 'rev-parse', `refs/heads/${featureBranch}`),
      featureTip,
    );
    assert(
      (await git(develop, 'worktree', 'list', '--porcelain')).includes(
        `worktree ${feature}`,
      ),
    );
  });
});

void test('git-flow: missing retained source tip warns and leaves the repository unchanged', async () => {
  await temporary(async (_root, develop, feature) => {
    const before = await snapshot(develop, feature);
    const result = runPostHook(develop, [], {
      BRANCH: 'feature/missing',
      EXIT_CODE: '0',
    });
    const output = `${decoder.decode(result.stdout)}\n${decoder.decode(result.stderr)}`;
    assert(result.success, output);
    assertMatch(output, /cannot resolve the retained tip/i);
    assert(!output.includes('orca-ide worktree rm'), output);
    assertEquals(await snapshot(develop, feature), before);
  });
});

void test('git-flow: cleanup command is withheld unless the source worktree is clean and present', async () => {
  await temporary(async (_root, develop, feature) => {
    const branch = featureBranch;
    const runHook = () => {
      const result = runPostHook(develop, [], {BRANCH: branch, EXIT_CODE: '0'});
      return `${decoder.decode(result.stdout)}\n${decoder.decode(result.stderr)}`;
    };

    await writeFile(join(feature, 'dirty.txt'), 'keep me\n');
    const dirty = runHook();
    assertMatch(dirty, /worktree is dirty; preserve it/i);
    assert(!dirty.includes('orca-ide worktree rm'), dirty);
    await rm(join(feature, 'dirty.txt'));

    const gitFile = await readFile(join(feature, '.git'), 'utf8');
    await writeFile(
      join(feature, '.git'),
      'gitdir: /missing-worktree-metadata\n',
    );
    const unreadable = runHook();
    assertMatch(unreadable, /status could not be checked; do not remove it/i);
    assert(!unreadable.includes('orca-ide worktree rm'), unreadable);
    await writeFile(join(feature, '.git'), gitFile);

    await rm(feature, {recursive: true});
    const missing = runHook();
    assertMatch(missing, /source directory is missing/i);
    assert(!missing.includes('orca-ide worktree rm'), missing);

    const noWorktree = runPostHook(develop, [], {
      BRANCH: 'main',
      EXIT_CODE: '0',
    });
    const noWorktreeOutput = `${decoder.decode(noWorktree.stdout)}\n${decoder.decode(noWorktree.stderr)}`;
    assert(noWorktree.success, noWorktreeOutput);
    assertMatch(noWorktreeOutput, /source worktree: not found/i);
    assert(
      !noWorktreeOutput.includes('orca-ide worktree rm'),
      noWorktreeOutput,
    );
  });
});

void test('git-flow: missing finish result asks for inspection without suggesting cleanup', async () => {
  await temporary(async (_root, develop) => {
    const result = runPostHook(develop, [], {BRANCH: featureBranch});
    const output = `${decoder.decode(result.stdout)}\n${decoder.decode(result.stderr)}`;
    assert(result.success, output);
    assertMatch(
      output,
      /did not report the finish result; inspect the finish manually/i,
    );
    assert(!output.includes('orca-ide worktree rm'), output);
  });
});
