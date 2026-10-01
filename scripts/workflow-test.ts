import {test} from 'node:test';
import {assert, assertEquals, assertRejects, assertThrows} from '@std/assert';
import {dirname, join} from '@std/path';
import {spawnSync} from 'node:child_process';
import {mkdir, mkdtemp, rm, symlink, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {
  assessDifficulty,
  buildWorkModeInstructions,
  sumNumstatLines,
  selectWorkMode,
  inspectChanges,
  parseNameStatus,
} from './workflow.ts';

async function git(root: string, ...args: string[]) {
  const result = spawnSync(
    'git',
    [
      '-c',
      'core.hooksPath=/dev/null',
      '-c',
      'user.name=Workflow Fixture',
      '-c',
      'user.email=fixture@example.invalid',
      '-c',
      'commit.gpgsign=false',
      ...args,
    ],
    {
      cwd: root,
      env: {
        ...process.env,
        GIT_CONFIG_NOSYSTEM: '1',
        GIT_CONFIG_GLOBAL: '/dev/null',
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );
  if (result.error) throw result.error;
  assert(result.status === 0, new TextDecoder().decode(result.stderr));
  return new TextDecoder().decode(result.stdout).trim();
}

async function repository(
  files: Record<string, string>,
  run: (root: string) => Promise<void>,
) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-test-'));
  try {
    await git(root, 'init', '--quiet', '--template=', '--initial-branch=main');
    for (const [path, source] of Object.entries(files)) {
      await mkdir(dirname(join(root, path)), {recursive: true});
      await writeFile(join(root, path), source);
    }
    await git(root, 'add', '--all');
    await git(root, 'commit', '--quiet', '--allow-empty', '-m', 'Fixture');
    await run(root);
  } finally {
    await rm(root, {recursive: true});
  }
}

void test('workflow: size boundaries and mandatory review signals', () => {
  const small = {
    paths: ['src/a.ts', 'src/b.ts'],
    statuses: ['M', 'A'],
    changedLines: 100,
    publicEntryChanged: false,
  };
  assertEquals(selectWorkMode(small).mode, 'DIRECT');
  assertEquals(
    selectWorkMode({...small, paths: [], changedLines: 0}).mode,
    'DIRECT',
  );
  assertEquals(selectWorkMode({...small, changedLines: 101}).mode, 'REVIEW');
  assertEquals(
    selectWorkMode({...small, paths: [...small.paths, 'src/c.ts']}).mode,
    'REVIEW',
  );
  for (const path of [
    'AGENTS.md',
    'package.json',
    'package-lock.json',
    'turbo.json',
    'uv.lock',
    'pyproject.toml',
    '.npmrc',
    'plugins/demo/plugin.json',
    'plugins/demo/mcp.json',
    'src/migrations/001.sql',
    'src/schema.ts',
    'src/domain/value.ts',
    'src/infrastructure/db.ts',
    'packages/shared/value.ts',
    'src/mod.ts',
    'src/index.mts',
  ])
    assertEquals(
      selectWorkMode({...small, paths: [path]}).mode,
      'REVIEW',
      path,
    );
  for (const status of ['D', 'R100', 'U', 'T']) {
    assertEquals(
      selectWorkMode({...small, statuses: [status]}).mode,
      'REVIEW',
      status,
    );
  }
  assertEquals(selectWorkMode({...small, changedLines: null}).mode, 'REVIEW');
  assertEquals(
    selectWorkMode({...small, publicEntryChanged: true}).mode,
    'REVIEW',
  );
});

void test('workflow: NUL records preserve filenames and rename statistics', () => {
  assertEquals(
    parseNameStatus('M\0src/a\tb.ts\0R100\0old\nname.ts\0new\tname.ts\0'),
    {
      paths: ['src/a\tb.ts', 'old\nname.ts', 'new\tname.ts'],
      statuses: ['M', 'R100'],
    },
  );
  assertEquals(sumNumstatLines('2\t3\tsrc/a\tb.ts\0'), 5);
  assertEquals(
    sumNumstatLines('2\t3\t\0old\nname.ts\0new\tname.ts\0' + '1\t0\tnext.ts\0'),
    6,
  );
  assertEquals(sumNumstatLines('-\t-\tbinary.dat\0'), null);
  assertEquals(sumNumstatLines(''), 0);
  assertThrows(() => sumNumstatLines('invalid\0'), Error, 'numstat');
});

void test('workflow: staged, unstaged and untracked changes include odd filenames', async () => {
  await repository(
    {
      '.gitignore': 'ignored.txt\n',
      'src/staged.ts': 'before\n',
      'src/unstaged.ts': 'before\n',
    },
    async root => {
      await writeFile(join(root, 'src/staged.ts'), 'after\n');
      await git(root, 'add', '--', 'src/staged.ts');
      await writeFile(join(root, 'src/unstaged.ts'), 'after\n');
      await writeFile(join(root, 'src/new\tline\n.ts'), 'new\n');
      await writeFile(join(root, 'ignored.txt'), 'ignored\n');
      const result = await inspectChanges(join(root, 'src'));
      assertEquals(result.paths, [
        'src/new\tline\n.ts',
        'src/staged.ts',
        'src/unstaged.ts',
      ]);
      assertEquals(result.statuses, ['M', 'M', '?']);
      assertEquals(result.changed_lines, 5);
      assertEquals(result.changed_files, 3);
      assertEquals(result.mode, 'REVIEW');
    },
  );
});

void test('workflow: worktree reversal cannot conceal staged changes', async () => {
  await repository({'src/value.ts': 'before\n'}, async root => {
    await writeFile(join(root, 'src/value.ts'), 'after\n');
    await git(root, 'add', '--', 'src/value.ts');
    await writeFile(join(root, 'src/value.ts'), 'before\n');
    const result = await inspectChanges(root);
    assertEquals(result.paths, ['src/value.ts']);
    assertEquals(result.statuses, ['M', 'M']);
    assertEquals(result.changed_lines, 4);
    assertEquals(result.mode, 'DIRECT');
  });
});

void test('workflow: Git rename and deletion require review', async () => {
  await repository({'src/old\tname.ts': 'one\ntwo\nthree\n'}, async root => {
    await git(root, 'mv', '--', 'src/old\tname.ts', 'src/new\nname.ts');
    const renamed = await inspectChanges(root);
    assertEquals(renamed.paths, ['src/new\nname.ts', 'src/old\tname.ts']);
    assertEquals(renamed.statuses, ['R100']);
    assertEquals(renamed.changed_lines, 0);
    assertEquals(renamed.mode, 'REVIEW');
  });
  await repository({'src/removed.ts': 'value\n'}, async root => {
    await rm(join(root, 'src/removed.ts'));
    const deleted = await inspectChanges(root);
    assertEquals(deleted.statuses, ['D']);
    assertEquals(deleted.changed_lines, 1);
    assertEquals(deleted.mode, 'REVIEW');
  });
});

void test('workflow: binary and symlink additions cannot become direct work', async () => {
  await repository({'src/value.ts': 'value\n'}, async root => {
    await writeFile(join(root, 'binary.dat'), new Uint8Array([0, 1, 2]));
    const binary = await inspectChanges(root);
    assertEquals(binary.changed_lines, null);
    assertEquals(binary.mode, 'REVIEW');
    await rm(join(root, 'binary.dat'));
    await symlink('src/value.ts', join(root, 'alias.ts'));
    const link = await inspectChanges(root);
    assertEquals(link.paths, ['alias.ts']);
    assertEquals(link.changed_lines, null);
    assertEquals(link.mode, 'REVIEW');
  });
});

void test('workflow: static public entry rules identify configured exports', async () => {
  await repository(
    {
      'plugins/code/skills/clean-code/scripts/cli.ts':
        'export const value = 1;\n',
    },
    async root => {
      await writeFile(
        join(root, 'plugins/code/skills/clean-code/scripts/cli.ts'),
        'export const value = 2;\n',
      );
      const result = await inspectChanges(root);
      assertEquals(result.public_entry_changed, true);
      assertEquals(result.mode, 'REVIEW');
    },
  );
});

void test('workflow: explicit baseline includes commits and invalid refs fail', async () => {
  await repository({'src/value.ts': 'before\n'}, async root => {
    const initial = await git(root, 'rev-parse', 'HEAD');
    await writeFile(join(root, 'src/value.ts'), 'after\n');
    await git(root, 'add', '--', 'src/value.ts');
    await git(root, 'commit', '--quiet', '-m', 'Fixture update');
    assertEquals((await inspectChanges(root)).paths, []);
    const result = await inspectChanges(root, initial);
    assertEquals(result.base, initial);
    assertEquals(result.paths, ['src/value.ts']);
    assertEquals(result.changed_lines, 2);
    await assertRejects(() => inspectChanges(root, 'missing-ref'), Error);
  });
});

void test('workflow: difficulty thresholds are independent of review mode', () => {
  const sample = {
    paths: ['src/a.ts'],
    statuses: ['M'],
    changedLines: 20,
    publicEntryChanged: false,
  };
  for (const [lines, level] of [
    [20, 'very_easy'],
    [21, 'easy'],
    [100, 'easy'],
    [101, 'medium'],
    [500, 'medium'],
    [501, 'difficult'],
    [2000, 'difficult'],
    [2001, 'very_difficult'],
  ] as const)
    assertEquals(
      assessDifficulty({...sample, changedLines: lines}).level,
      level,
    );
  for (const [count, level] of [
    [1, 'very_easy'],
    [2, 'easy'],
    [3, 'medium'],
    [5, 'medium'],
    [6, 'difficult'],
    [20, 'difficult'],
    [21, 'very_difficult'],
  ] as const)
    assertEquals(
      assessDifficulty({
        ...sample,
        paths: Array.from({length: count}, (_, i) => `src/${i}.ts`),
      }).level,
      level,
    );
  assertEquals(assessDifficulty({...sample, paths: []}).level, null);
  assertEquals(assessDifficulty({...sample, changedLines: null}).level, null);
  assertEquals(
    assessDifficulty({...sample, publicEntryChanged: true}).level,
    'difficult',
  );
  assertEquals(
    assessDifficulty({...sample, statuses: ['R100']}).level,
    'difficult',
  );
  const config = {...sample, paths: ['package.json']};
  assertEquals(selectWorkMode(config).mode, 'REVIEW');
  assertEquals(assessDifficulty(config).level, 'very_easy');
});

void test('workflow: task difficulty excludes unrelated binary changes without weakening review', async () => {
  await repository({'src/a.ts': 'before\n'}, async root => {
    await writeFile(join(root, 'src/a.ts'), 'after\n');
    await writeFile(join(root, 'unrelated.dat'), new Uint8Array([0, 1, 2]));
    const result = await inspectChanges(root, 'HEAD', {
      tasks: [{id: 'small', files: ['src/a.ts']}],
    });
    assertEquals(result.mode, 'REVIEW');
    assertEquals(result.changed_lines, null);
    assertEquals(result.difficulty[0].level, 'very_easy');
    assertEquals(result.difficulty[0].facts?.changed_lines, 2);
    assertEquals(result.difficulty[0].task, 'small');
    assertEquals(result.difficulty[0].scope, ['src/a.ts']);
    const workspace = await inspectChanges(root);
    assertEquals(workspace.difficulty[0].level, null);
    assertEquals(workspace.difficulty[0].scope, 'workspace');
  });
});

void test('workflow: planned work with no observed diff remains unassessed', async () => {
  await repository({'src/a.ts': 'before\n'}, async root => {
    const result = await inspectChanges(root, 'HEAD', {
      tasks: [{id: 'future', files: ['src/a.ts']}],
    });
    assertEquals(result.difficulty[0].level, null);
  });
});

void test('workflow: invalid directory scopes are not collected for difficulty', async () => {
  await repository({'src/a.ts': 'before\n'}, async root => {
    await writeFile(join(root, 'src/a.ts'), 'after\n');
    const result = await inspectChanges(root, 'HEAD', {
      tasks: [{id: 'invalid', files: ['src']}],
    });
    assertEquals(result.mode, 'REVIEW');
    assertEquals(result.difficulty[0].level, null);
    assertEquals(result.difficulty[0].facts, null);
  });
});

void test('workflow: per-task observations keep literal paths and independent levels', async () => {
  const first = 'plugins/demo/small\tname.ts';
  const second = 'plugins/demo/large.ts';
  await repository(
    {
      [first]: 'export const small = 1;\n',
      [second]: 'export const large = 1;\n',
    },
    async root => {
      await writeFile(join(root, first), 'export const small = 2;\n');
      await writeFile(
        join(root, second),
        `export const large = 2;\n${'// comment\n'.repeat(101)}`,
      );
      const result = await inspectChanges(root, 'HEAD', {
        tasks: [
          {id: 'small', files: [first]},
          {id: 'large', files: [second]},
        ],
      });
      assertEquals(result.mode, 'PARALLEL');
      assertEquals(
        result.difficulty.map(item => item.level),
        ['very_easy', 'medium'],
      );
      assertEquals(
        result.difficulty.map(item => item.facts?.changed_files),
        [1, 1],
      );
      assertEquals(result.difficulty[1].reasons, [
        '변경 줄 수가 100줄을 초과합니다.',
      ]);
      assert(
        result.instructions.some(line =>
          line.includes('no level picks a model by itself'),
        ),
      );
    },
  );
});

void test('workflow: scoped observations include staged, unstaged and untracked changes', async () => {
  await repository({'src/a.ts': 'original\n'}, async root => {
    await writeFile(join(root, 'src/a.ts'), 'staged\n');
    await git(root, 'add', 'src/a.ts');
    await writeFile(join(root, 'src/a.ts'), 'unstaged\n');
    await writeFile(join(root, 'src/new.ts'), 'new\n');
    const result = await inspectChanges(root, 'HEAD', {
      tasks: [{id: 'mixed', files: ['src/a.ts', 'src/new.ts']}],
    });
    assertEquals(result.difficulty[0].facts?.changed_lines, 5);
    assertEquals(result.difficulty[0].facts?.changed_files, 2);
    assertEquals(result.difficulty[0].level, 'easy');
  });
});

void test('workflow: review eligibility does not suppress measurable task difficulty', async () => {
  const first = 'plugins/demo/first.ts';
  const second = 'plugins/demo/second.ts';
  await repository(
    {
      [first]: "export {value} from './second.ts';\n",
      [second]: 'export const value = 1;\n',
    },
    async root => {
      await writeFile(
        join(root, first),
        "export {value} from './second.ts';\n// changed\n",
      );
      await writeFile(join(root, second), 'export const value = 2;\n');
      const result = await inspectChanges(root, 'HEAD', {
        tasks: [
          {id: 'first', files: [first]},
          {id: 'second', files: [second]},
        ],
      });
      assertEquals(result.mode, 'REVIEW');
      assertEquals(
        result.difficulty.map(item => item.level),
        ['very_easy', 'very_easy'],
      );
      const invalid = await inspectChanges(root, 'HEAD', {
        tasks: [{id: 'directory', files: ['plugins/demo']}],
      });
      assertEquals(invalid.difficulty[0].level, null);
      assertEquals(invalid.difficulty[0].facts, null);
    },
  );
});

void test('workflow: destination-only task retains observed rename metadata', async () => {
  await repository({'src/old.ts': 'export const value = 1;\n'}, async root => {
    await git(root, 'mv', 'src/old.ts', 'src/new.ts');
    const result = await inspectChanges(root, 'HEAD', {
      tasks: [{id: 'move', files: ['src/new.ts']}],
    });
    assertEquals(result.mode, 'REVIEW');
    assertEquals(result.difficulty[0].level, 'difficult');
    assertEquals(result.difficulty[0].facts?.structural_change, true);
    assert(result.difficulty[0].reasons[0].includes('이동'));
  });
});

void test('workflow: staged and tracked symlinks remain unassessed', async () => {
  await repository({'src/a.ts': 'before\n'}, async root => {
    await symlink('src/a.ts', join(root, 'alias.ts'));
    await git(root, 'add', 'alias.ts');
    assertEquals((await inspectChanges(root)).difficulty[0].level, null);
    await git(root, 'commit', '--quiet', '-m', 'Link fixture');
    await rm(join(root, 'alias.ts'));
    await symlink('src/missing.ts', join(root, 'alias.ts'));
    assertEquals((await inspectChanges(root)).difficulty[0].level, null);
  });
});

void test('workflow: delegation instructions use Orca workers', () => {
  for (const mode of ['DELEGATE', 'PARALLEL'] as const) {
    const lines = buildWorkModeInstructions(mode, true);
    assert(lines.some(line => line.includes('Orca orchestration')));
    assert(!lines.some(line => line.includes('Goose')));
  }
});

void test('workflow: review instructions time independent review at merge', () => {
  const lines = buildWorkModeInstructions('REVIEW', true);
  assert(
    lines.some(
      line =>
        line.includes(
          'Before the develop merge review, run `npm run doc-regions:prepare -- --base develop --max-evidence-chars <n>` and `npm run doc-regions:audit`',
        ) &&
        line.includes(
          'Send each printed request to the `jev_` tool it names',
        ) &&
        line.includes(
          'Fix target document units marked contradicted or flagged for review',
        ) &&
        line.includes(
          'Report AGENTS.md and constitution findings to the user without changing those files',
        ),
    ),
  );
  assert(
    lines.some(
      line =>
        line.includes('Before each commit') &&
        line.includes('the implementer or the orchestrator reviews the diff'),
    ),
  );
  assert(
    lines.some(
      line =>
        line.includes(
          "fresh reviewer from a provider other than the implementer's (Claude Code, Codex or Copilot; for develop also Antigravity, Grok or Cursor)",
        ) &&
        line.includes('develop (favoring speed)') &&
        line.includes('main (favoring accuracy)') &&
        line.includes('not for each change'),
    ),
  );
  assert(lines.some(line => line.includes('no extra user approval')));
  assert(!lines.some(line => line.includes('separate read-only diff review')));
});

void test('workflow: every mode prints the Linear completion order', () => {
  for (const mode of ['DIRECT', 'DELEGATE', 'PARALLEL', 'REVIEW'] as const) {
    const lines = buildWorkModeInstructions(mode, false);
    assert(
      lines.some(
        line =>
          line.includes('main agent only') &&
          line.includes('In Review') &&
          line.indexOf('In Review') < line.indexOf('Done') &&
          line.includes('merge commit') &&
          line.includes('record location') &&
          line.includes("Linear's UI") &&
          line.includes('add no other Linear integration'),
      ),
    );
  }
});
