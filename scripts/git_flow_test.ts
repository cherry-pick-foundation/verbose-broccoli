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

test('git-flow test commands reject children terminated by a signal', () => {
  assertThrows(
    () => commandOutput('sh', {args: ['-c', 'kill -TERM $$']}),
    Error,
    'SIGTERM',
  );
});

function output(result: ReturnType<typeof commandOutput>) {
  return decoder.decode(result.stdout) + decoder.decode(result.stderr);
}

async function git(cwd: string, ...args: string[]) {
  const result = await runGit(cwd, args);
  const stdout = decoder.decode(result.stdout).trim();
  const stderr = decoder.decode(result.stderr).trim();
  assert(result.success, `git ${args.join(' ')} failed: ${stderr}`);
  return stdout;
}

async function attemptFinish(cwd: string) {
  const result = await runGit(cwd, ['flow', 'feature', 'finish', featureName]);
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

async function addConstitutionCommit(
  feature: string,
  version: string,
  message: string,
) {
  await writeFile(
    join(feature, '.specify/memory/constitution.md'),
    `Policy text updated.\n\n**Version**: ${version}\n`,
  );
  await git(feature, 'add', '.specify/memory/constitution.md');
  await git(feature, 'commit', '-m', message);
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
    for (const file of ['commitlint.config.mjs', 'constitution_version.ts']) {
      await copyFile(join(root, 'scripts', file), join(repo, 'scripts', file));
    }
    await mkdir(join(repo, '.specify/memory'), {recursive: true});
    await writeFile(
      join(repo, '.specify/memory/constitution.md'),
      'Policy text.\n\n**Version**: 1.0.0\n',
    );
    await writeFile(join(repo, 'seed.txt'), 'seed\n');
    await git(
      repo,
      'add',
      '.gitflow',
      '.gitignore',
      'package.json',
      'package-lock.json',
      'scripts',
      '.specify/memory/constitution.md',
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

test('git-flow: feature worktree invocation is refused without changing branches or worktrees', async () => {
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

test('git-flow: finish is refused when develop has a commit the feature lacks', async () => {
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

test('git-flow: finish is refused when feature verification fails', async () => {
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

test('git-flow: finish is refused when the feature tip has no review record', async () => {
  await temporary(async (_root, develop, feature) => {
    await assertRefusedUnchanged(
      develop,
      feature,
      /feature\/flow-test.*(tree|review-record)/i,
    );
  });
});

test('git-flow: finish is refused when Reviewed-commit is not the record parent', async () => {
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

test('git-flow: finish is refused when the review record changes the tree', async () => {
  await temporary(async (_root, develop, feature) => {
    await addReviewRecord(feature, {changedFile: true});
    await assertRefusedUnchanged(
      develop,
      feature,
      /tip tree differs.*review-record/i,
    );
  });
});

test('git-flow: finish is refused when Reviewed-by is missing', async () => {
  await temporary(async (_root, develop, feature) => {
    const parent = await git(feature, 'rev-parse', 'HEAD');
    await addReviewRecord(feature, {
      trailers: [`Reviewed-commit: ${parent}`],
    });
    await assertRefusedUnchanged(develop, feature, /Reviewed-by/i);
  });
});

test('git-flow: finish is refused when Reviewed-commit is missing', async () => {
  await temporary(async (_root, develop, feature) => {
    await addReviewRecord(feature, {
      trailers: ['Reviewed-by: Claude Code'],
    });
    await assertRefusedUnchanged(develop, feature, /Reviewed-commit/i);
  });
});

test('git-flow: finish is refused when Reviewed-by is duplicated', async () => {
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

test('git-flow: finish is refused when Reviewed-by is empty', async () => {
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

test('git-flow: finish is refused when Reviewed-by has an empty duplicate', async () => {
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

test('git-flow: finish is refused when Reviewed-commit has an empty duplicate', async () => {
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

test('git-flow: finish is refused after develop is merged after the review record', async () => {
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

test('git-flow: abbreviated Reviewed-commit values are accepted', async () => {
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

test('git-flow: lower-case review trailer keys are accepted', async () => {
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

test('git-flow: finish from develop creates the default no-ff merge and keeps the feature worktree', async () => {
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

async function assertRebasedBumpsRefused(action: 'fixup' | 'squash') {
  await temporary(async (_root, develop, feature) => {
    await addConstitutionCommit(feature, '1.0.1', 'docs: first wording');
    await addConstitutionCommit(feature, '1.0.2', 'docs: second wording');
    const rebase = await runGit(feature, ['rebase', '-i', 'develop'], {
      GIT_EDITOR: 'true',
      GIT_SEQUENCE_EDITOR: `sed -i '/docs: second wording/s/^pick /${action} /'`,
    });
    assert(rebase.success, output(rebase));
    const combined = await git(feature, 'rev-parse', 'HEAD');
    assertEquals(
      await git(
        feature,
        'rev-list',
        '--count',
        'develop..HEAD',
        '--',
        '.specify/memory/constitution.md',
      ),
      '1',
    );
    assertMatch(
      await git(
        feature,
        'show',
        `${combined}^:.specify/memory/constitution.md`,
      ),
      /\*\*Version\*\*: 1\.0\.0/,
    );
    assertMatch(
      await git(feature, 'show', `${combined}:.specify/memory/constitution.md`),
      /\*\*Version\*\*: 1\.0\.2/,
    );
    await addReviewRecord(feature);
    await assertRefusedUnchanged(
      develop,
      feature,
      new RegExp(
        `${combined}.*${featureBranch}.*rewrite that commit so it raises the version once for its type`,
        'i',
      ),
    );
  });
}

test('git-flow: fixup rebase that raises the constitution twice is refused', async () => {
  await assertRebasedBumpsRefused('fixup');
});

test('git-flow: squash rebase that raises the constitution twice is refused', async () => {
  await assertRebasedBumpsRefused('squash');
});

test('git-flow: unsquashed fixup commit that changes the constitution is refused', async () => {
  await temporary(async (_root, develop, feature) => {
    const first = await addConstitutionCommit(
      feature,
      '1.0.1',
      'docs: first wording',
    );
    await writeFile(
      join(feature, '.specify/memory/constitution.md'),
      'Policy text updated again.\n\n**Version**: 1.0.2\n',
    );
    await git(feature, 'add', '.specify/memory/constitution.md');
    const fixup = await runGit(feature, ['commit', '--fixup', first], {
      GIT_EDITOR: 'true',
    });
    assert(fixup.success, output(fixup));
    const fixupCommit = await git(feature, 'rev-parse', 'HEAD');
    await addReviewRecord(feature);
    await assertRefusedUnchanged(
      develop,
      feature,
      new RegExp(
        `${fixupCommit}.*${featureBranch}.*rewrite that commit so it raises the version once for its type`,
        'i',
      ),
    );
  });
});

test('git-flow: one correct constitution bump still finishes', async () => {
  await temporary(async (_root, develop, feature) => {
    await addConstitutionCommit(feature, '1.0.1', 'docs: first wording');
    await addReviewRecord(feature);
    const result = await attemptFinish(develop);
    assertEquals(result.code, 0, result.output);
  });
});
