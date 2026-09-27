import {assert, assertEquals, assertMatch} from '@std/assert';
import {join} from '@std/path';
import {constitutionVersion, isBreakingCommit} from './constitution_version.ts';

const repository = new URL('../', import.meta.url);
const repositoryRoot = decodeURIComponent(repository.pathname);
const git = (await new Deno.Command('which', {args: ['git']}).output()).stdout;
const gitPath = new TextDecoder().decode(git).trim();
const home = Deno.env.get('HOME') ?? '/tmp';
const denoDir = Deno.env.get('DENO_DIR') ?? join(home, '.cache', 'deno');
const path = Deno.env.get('PATH') ?? '/usr/bin:/bin';
const constitution = (version: string, text = 'Policy text.') =>
  `${text}\n\n**Version**: ${version} | **Ratified**: 2026-09-12 | **Last Amended**: 2026-09-27\n`;
const baseEnv = {
  DENO_DIR: denoDir,
  GIT_CONFIG_GLOBAL: '/dev/null',
  GIT_CONFIG_NOSYSTEM: '1',
  PATH: path,
};
const oldText = constitution('0.22.0');

function check(
  type: string | null | undefined,
  breaking: boolean,
  before: string | null,
  after: string | null,
) {
  return constitutionVersion(type, breaking, before, after);
}

Deno.test('constitution version rule: table and edge cases', () => {
  const minor = constitution('0.23.0', 'Policy text updated.');
  const patch = constitution('0.22.1', 'Policy text updated.');
  const major = constitution('1.0.0', 'Policy text updated.');

  assert(check('feat', false, null, minor)[0]);
  assert(check('feat', false, oldText, null)[0]);
  assert(check('chore', false, oldText, oldText)[0]);
  assert(check('feat', false, oldText, minor)[0]);
  assert(
    check('docs', false, oldText, 'Policy text.\n\n**Version**: 0.22.1\n')[0],
  );
  assert(check('feat', false, oldText, 'Policy text.\n')[0] === false);
  assert(check('feat', false, '**Version**: 0.22\n', minor)[0] === false);
  assert(
    check(
      'feat',
      false,
      oldText,
      '**Version**: 0.23 | **Ratified**: 2026-09-12\n',
    )[0] === false,
  );
  assert(
    check('feat', false, `${oldText}${constitution('0.22.0')}`, minor)[0] ===
      false,
  );

  assert(check('feat', true, oldText, major)[0]);
  assert(check('feat', false, oldText, minor)[0]);
  assert(check('docs', false, oldText, patch)[0]);
  assert(check('fix', false, oldText, patch)[0]);
  assert(check('refactor', false, oldText, patch)[0] === false);
  assert(check('refactor', true, oldText, major)[0]);
  assert(
    check(
      'feat',
      false,
      oldText,
      constitution('0.22.0', 'Changed text.'),
    )[0] === false,
  );
  assert(check('feat', false, oldText, constitution('0.24.0'))[0] === false);
  assert(check('feat', false, oldText, constitution('0.21.9'))[0] === false);
  assert(check('chore', false, oldText, patch)[0] === false);
  assert(
    check(
      'feat',
      false,
      oldText,
      constitution('0.22.0', 'Revised policy.'),
    )[0] === false,
  );

  assert(isBreakingCommit([{title: 'BREAKING CHANGE'}]));
  assert(isBreakingCommit([{title: 'BREAKING-CHANGE'}]));
  assert(!isBreakingCommit([{title: 'OTHER'}]));

  assertMatch(
    check('chore', false, oldText, patch)[1],
    /cannot change the constitution/,
  );
  assertMatch(
    check('feat', false, oldText, constitution('0.22.0', 'Changed text.'))[1],
    /0\.23\.0/,
  );
});

Deno.test('constitution version rule: Git errors refuse changed commits', async () => {
  const root = await Deno.makeTempDir({prefix: 'commit-msg-git-error-'});
  try {
    const moduleUrl = new URL('./constitution_version.ts', import.meta.url)
      .href;
    const probe = `import {constitutionVersionRule} from ${JSON.stringify(moduleUrl)}; console.log(JSON.stringify(await constitutionVersionRule({type: 'feat'})));`;
    const result = await new Deno.Command(Deno.execPath(), {
      args: [
        'eval',
        '--allow-read',
        '--allow-env=PATH',
        '--allow-run=git',
        probe,
      ],
      cwd: root,
      env: {DENO_DIR: denoDir, PATH: path},
      stdout: 'piped',
      stderr: 'piped',
    }).output();
    assert(result.success, output(result));
    assertMatch(output(result), /Could not check HEAD/);
  } finally {
    await Deno.remove(root, {recursive: true});
  }
});

interface Repo {
  root: string;
  env: Record<string, string>;
}

async function runGit(
  repo: Repo,
  args: string[],
  extraEnv: Record<string, string> = {},
) {
  return await new Deno.Command(gitPath, {
    args: ['-C', repo.root, ...args],
    env: {
      ...repo.env,
      ...extraEnv,
    },
    stdout: 'piped',
    stderr: 'piped',
  }).output();
}

function output(result: Deno.CommandOutput) {
  return (
    new TextDecoder().decode(result.stdout) +
    new TextDecoder().decode(result.stderr)
  );
}

async function createRepo(): Promise<Repo> {
  const root = await Deno.makeTempDir({prefix: 'commit-msg-test-'});
  const tempHome = join(root, 'home');
  await Deno.mkdir(tempHome);
  const repo = {
    root,
    env: {...baseEnv, HOME: tempHome},
  };
  await Deno.mkdir(join(root, 'scripts', 'git-hooks'), {recursive: true});
  await Deno.mkdir(join(root, '.specify', 'memory'), {recursive: true});
  await Deno.copyFile(
    join(repositoryRoot, 'deno.json'),
    join(root, 'deno.json'),
  );
  await Deno.copyFile(
    join(repositoryRoot, 'deno.lock'),
    join(root, 'deno.lock'),
  );
  for (const file of ['commitlint.config.mjs', 'constitution_version.ts']) {
    await Deno.copyFile(
      join(repositoryRoot, 'scripts', file),
      join(root, 'scripts', file),
    );
  }
  const hook = join(root, 'scripts', 'git-hooks', 'commit-msg');
  await Deno.copyFile(
    join(repositoryRoot, 'scripts', 'git-hooks', 'commit-msg'),
    hook,
  );
  await Deno.chmod(hook, 0o755);
  await Deno.writeTextFile(
    join(root, '.specify', 'memory', 'constitution.md'),
    oldText,
  );
  await Deno.writeTextFile(join(root, 'tracked.txt'), 'seed\n');

  const init = await runGit(repo, ['init', '--quiet', '--initial-branch=main']);
  assert(init.success, output(init));
  for (const [key, value] of [
    ['user.name', 'Commit Test'],
    ['user.email', 'commit-test@example.invalid'],
  ]) {
    const config = await runGit(repo, ['config', key, value]);
    assert(config.success, output(config));
  }
  const add = await runGit(repo, ['add', '.']);
  assert(add.success, output(add));
  const seed = await runGit(repo, ['commit', '--quiet', '-m', 'chore: seed']);
  assert(seed.success, output(seed));
  const hooks = await runGit(repo, [
    'config',
    'core.hooksPath',
    'scripts/git-hooks',
  ]);
  assert(hooks.success, output(hooks));
  return repo;
}

async function withRepo(run: (repo: Repo) => Promise<void>) {
  const repo = await createRepo();
  try {
    await run(repo);
  } finally {
    await Deno.remove(repo.root, {recursive: true});
  }
}

async function writeConstitution(repo: Repo, text: string) {
  await Deno.writeTextFile(
    join(repo.root, '.specify', 'memory', 'constitution.md'),
    text,
  );
  const result = await runGit(repo, ['add', '.specify/memory/constitution.md']);
  assert(result.success, output(result));
}

async function commit(
  repo: Repo,
  message: string,
  args: string[] = [],
  extraEnv: Record<string, string> = {},
) {
  return await runGit(repo, ['commit', ...args, '-m', message], extraEnv);
}

Deno.test('commit-msg hook: amendments use the parent constitution version', async () => {
  await withRepo(async repo => {
    await writeConstitution(repo, constitution('1.0.0', 'Breaking change.'));
    const first = await commit(repo, 'docs!: break');
    assert(first.success, output(first));
    const replaced = output(await runGit(repo, ['rev-parse', 'HEAD'])).trim();

    await writeConstitution(repo, constitution('1.0.0', 'Follow-up text.'));
    const amend = await runGit(repo, ['commit', '--amend', '--no-edit']);
    assert(amend.success, output(amend));
    assert(
      output(await runGit(repo, ['rev-parse', 'HEAD'])).trim() !== replaced,
    );
    const committed = output(
      await runGit(repo, ['show', 'HEAD:.specify/memory/constitution.md']),
    );
    assertMatch(committed, /Follow-up text/);
    assertMatch(committed, /\*\*Version\*\*: 1\.0\.0/);
  });

  await withRepo(async repo => {
    await writeConstitution(repo, constitution('1.0.0', 'Breaking change.'));
    const first = await commit(repo, 'docs!: break');
    assert(first.success, output(first));
    await writeConstitution(repo, constitution('1.0.0', 'Reworded change.'));
    const amend = await runGit(repo, [
      'commit',
      '--amend',
      '-m',
      'docs!: break',
    ]);
    assert(amend.success, output(amend));
    assertMatch(
      output(
        await runGit(repo, ['show', 'HEAD:.specify/memory/constitution.md']),
      ),
      /\*\*Version\*\*: 1\.0\.0/,
    );
  });

  await withRepo(async repo => {
    await writeConstitution(repo, constitution('1.0.0', 'Breaking change.'));
    const first = await commit(repo, 'docs!: break');
    assert(first.success, output(first));
    const before = output(await runGit(repo, ['rev-parse', 'HEAD']));
    await writeConstitution(repo, constitution('2.0.0', 'Bumped again.'));
    const amend = await runGit(repo, [
      'commit',
      '--amend',
      '-m',
      'docs!: break again',
    ]);
    assert(!amend.success);
    assertMatch(output(amend), /requires 1\.0\.0; found 2\.0\.0/);
    assertEquals(output(await runGit(repo, ['rev-parse', 'HEAD'])), before);
  });

  await withRepo(async repo => {
    await Deno.writeTextFile(join(repo.root, 'docs.txt'), 'first\n');
    const add = await runGit(repo, ['add', 'docs.txt']);
    assert(add.success, output(add));
    const first = await commit(repo, 'docs: update docs');
    assert(first.success, output(first));
    const before = output(await runGit(repo, ['rev-parse', 'HEAD']));

    await writeConstitution(repo, constitution('0.22.0', 'New text.'));
    const refused = await runGit(repo, [
      'commit',
      '--amend',
      '-m',
      'docs: update docs',
    ]);
    assert(!refused.success);
    assertMatch(output(refused), /requires 0\.22\.1; found 0\.22\.0/);
    assertEquals(output(await runGit(repo, ['rev-parse', 'HEAD'])), before);

    await writeConstitution(repo, constitution('0.22.1', 'New text.'));
    const accepted = await runGit(repo, [
      'commit',
      '--amend',
      '-m',
      'docs: update docs',
    ]);
    assert(accepted.success, output(accepted));
    assertMatch(
      output(
        await runGit(repo, ['show', 'HEAD:.specify/memory/constitution.md']),
      ),
      /\*\*Version\*\*: 0\.22\.1/,
    );
  });

  await withRepo(async repo => {
    await writeConstitution(repo, constitution('1.0.0', 'Breaking change.'));
    const first = await commit(repo, 'docs!: break');
    assert(first.success, output(first));
    const before = output(await runGit(repo, ['rev-parse', 'HEAD']));

    await writeConstitution(repo, constitution('1.0.0', 'Follow-up change.'));
    const refused = await commit(repo, 'docs!: follow up', [], {
      CONSTITUTION_VERSION_AMEND: '1',
    });
    assert(!refused.success);
    assertMatch(output(refused), /requires 2\.0\.0; found 1\.0\.0/);
    assertEquals(output(await runGit(repo, ['rev-parse', 'HEAD'])), before);

    await writeConstitution(repo, constitution('2.0.0', 'Follow-up change.'));
    const accepted = await commit(repo, 'docs!: follow up', [], {
      CONSTITUTION_VERSION_AMEND: '1',
    });
    assert(accepted.success, output(accepted));
  });
});

Deno.test('commit-msg hook: real commits, index handling, and Deno lookup', async () => {
  await withRepo(async repo => {
    await Deno.writeTextFile(join(repo.root, 'invalid.txt'), 'change\n');
    await runGit(repo, ['add', 'invalid.txt']);
    const before = output(await runGit(repo, ['rev-parse', 'HEAD']));
    const invalid = await commit(repo, 'Update files');
    assert(!invalid.success);
    assertMatch(output(invalid), /type-empty|subject-empty/);
    assertEquals(output(await runGit(repo, ['rev-parse', 'HEAD'])), before);
  });

  await withRepo(async repo => {
    await Deno.writeTextFile(join(repo.root, 'trailers.txt'), 'accepted\n');
    await runGit(repo, ['add', 'trailers.txt']);
    const result = await commit(
      repo,
      'feat: accept review trailers\n\nSpec-Kit-Task: T006\nReviewed-by: Reviewer\nReviewed-commit: abcdef123\nCo-Authored-By: Author <author@example.invalid>\nSigned-off-by: Commit Test <commit-test@example.invalid>',
    );
    assert(result.success, output(result));
  });

  await withRepo(async repo => {
    await runGit(repo, ['checkout', '-b', 'feature']);
    await Deno.writeTextFile(join(repo.root, 'feature.txt'), 'feature\n');
    await runGit(repo, ['add', 'feature.txt']);
    const feature = await commit(repo, 'feat: add feature change');
    assert(feature.success, output(feature));
    await runGit(repo, ['checkout', 'main']);
    await Deno.writeTextFile(join(repo.root, 'main.txt'), 'main\n');
    await runGit(repo, ['add', 'main.txt']);
    const main = await commit(repo, 'docs: add main change');
    assert(main.success, output(main));
    const merge = await runGit(repo, ['merge', '--no-ff', 'feature']);
    assert(merge.success, output(merge));
    assertMatch(
      output(await runGit(repo, ['log', '-1', '--format=%B'])),
      /^Merge branch 'feature'\n/,
    );
  });

  await withRepo(async repo => {
    const bumps = [
      ['feat: add principle', constitution('0.23.0', 'Policy text updated.')],
      [
        'docs: clarify wording',
        constitution('0.23.1', 'Policy text updated again.'),
      ],
      ['fix: correct wording', constitution('0.23.2', 'Policy corrected.')],
      ['feat!: change governance', constitution('1.0.0', 'New governance.')],
      [
        'docs: describe breaking change\n\nBREAKING-CHANGE: governance changed',
        constitution('2.0.0', 'Updated governance.'),
      ],
    ];
    for (const [message, text] of bumps) {
      await writeConstitution(repo, text);
      const result = await commit(repo, message);
      assert(result.success, output(result));
    }
  });

  for (const [message, text, expected] of [
    [
      'feat: wrong version step',
      constitution('0.22.1', 'Policy text updated.'),
      /requires 0\.23\.0/,
    ],
    [
      'chore: change constitution',
      constitution('0.22.1', 'Policy text updated.'),
      /cannot change the constitution.*0\.22\.0/,
    ],
    [
      'feat: change text only',
      constitution('0.22.0', 'Changed text.'),
      /requires 0\.23\.0/,
    ],
  ] as const) {
    await withRepo(async repo => {
      await writeConstitution(repo, text);
      const before = output(await runGit(repo, ['rev-parse', 'HEAD']));
      const result = await commit(repo, message);
      assert(!result.success);
      assertMatch(output(result), expected);
      assertEquals(output(await runGit(repo, ['rev-parse', 'HEAD'])), before);
    });
  }

  await withRepo(async repo => {
    await Deno.writeTextFile(join(repo.root, 'tracked.txt'), 'updated\n');
    await writeConstitution(
      repo,
      constitution('0.22.1', 'Staged wrong version.'),
    );
    await Deno.writeTextFile(
      join(repo.root, '.specify', 'memory', 'constitution.md'),
      constitution('0.23.0', 'Policy text updated.'),
    );
    const result = await runGit(repo, [
      'commit',
      '-a',
      '-m',
      'feat: update tracked files',
    ]);
    assert(result.success, output(result));
    const committed = await runGit(repo, [
      'show',
      'HEAD:.specify/memory/constitution.md',
    ]);
    assertMatch(output(committed), /\*\*Version\*\*: 0\.23\.0/);
  });

  await withRepo(async repo => {
    await Deno.writeTextFile(join(repo.root, 'missing-deno.txt'), 'change\n');
    await runGit(repo, ['add', 'missing-deno.txt']);
    const before = output(await runGit(repo, ['rev-parse', 'HEAD']));
    const missing = await commit(repo, 'feat: commit without deno', [], {
      PATH: join(repo.root, 'empty-path'),
    });
    assert(!missing.success);
    assertMatch(
      output(missing),
      /Commit refused: Deno 2\.9\.6 was not found\./,
    );
    assertEquals(output(await runGit(repo, ['rev-parse', 'HEAD'])), before);
  });

  await withRepo(async repo => {
    await Deno.writeTextFile(join(repo.root, 'timed.txt'), 'timing\n');
    await runGit(repo, ['add', 'timed.txt']);
    const started = performance.now();
    const result = await commit(repo, 'test: measure hook runtime');
    const duration = performance.now() - started;
    assert(result.success, output(result));
    assert(duration < 2000, `Commit-msg hook took ${duration.toFixed(0)} ms.`);
    console.log(`Measured commit-msg hook: ${duration.toFixed(0)} ms`);
  });
});
