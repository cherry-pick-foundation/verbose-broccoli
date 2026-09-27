import {assert, assertEquals, assertRejects, assertThrows} from '@std/assert';
import {dirname, join} from '@std/path';
import {
  assessDifficulty,
  buildWorkModeInstructions,
  sumNumstatLines,
  selectWorkMode,
  inspectChanges,
  parseNameStatus,
} from './workflow.ts';

async function git(root: string, ...args: string[]) {
  const result = await new Deno.Command('git', {
    cwd: root,
    args: [
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
    env: {GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null'},
    stdout: 'piped',
    stderr: 'piped',
  }).output();
  assert(result.success, new TextDecoder().decode(result.stderr));
  return new TextDecoder().decode(result.stdout).trim();
}

async function repository(
  files: Record<string, string>,
  run: (root: string) => Promise<void>,
) {
  const root = await Deno.makeTempDir({prefix: 'workflow-test-'});
  try {
    await git(root, 'init', '--quiet', '--template=', '--initial-branch=main');
    for (const [path, source] of Object.entries(files)) {
      await Deno.mkdir(dirname(join(root, path)), {recursive: true});
      await Deno.writeTextFile(join(root, path), source);
    }
    await git(root, 'add', '--all');
    await git(root, 'commit', '--quiet', '--allow-empty', '-m', 'Fixture');
    await run(root);
  } finally {
    await Deno.remove(root, {recursive: true});
  }
}

Deno.test('workflow: size boundaries and mandatory review signals', () => {
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
    'deno.jsonc',
    'deno.lock',
    'package.json',
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

Deno.test('workflow: NUL records preserve filenames and rename statistics', () => {
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

Deno.test('workflow: staged, unstaged and untracked changes include odd filenames', async () => {
  await repository(
    {
      '.gitignore': 'ignored.txt\n',
      'src/staged.ts': 'before\n',
      'src/unstaged.ts': 'before\n',
    },
    async root => {
      await Deno.writeTextFile(join(root, 'src/staged.ts'), 'after\n');
      await git(root, 'add', '--', 'src/staged.ts');
      await Deno.writeTextFile(join(root, 'src/unstaged.ts'), 'after\n');
      await Deno.writeTextFile(join(root, 'src/new\tline\n.ts'), 'new\n');
      await Deno.writeTextFile(join(root, 'ignored.txt'), 'ignored\n');
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

Deno.test('workflow: worktree reversal cannot conceal staged changes', async () => {
  await repository({'src/value.ts': 'before\n'}, async root => {
    await Deno.writeTextFile(join(root, 'src/value.ts'), 'after\n');
    await git(root, 'add', '--', 'src/value.ts');
    await Deno.writeTextFile(join(root, 'src/value.ts'), 'before\n');
    const result = await inspectChanges(root);
    assertEquals(result.paths, ['src/value.ts']);
    assertEquals(result.statuses, ['M', 'M']);
    assertEquals(result.changed_lines, 4);
    assertEquals(result.mode, 'DIRECT');
  });
});

Deno.test('workflow: Git rename and deletion require review', async () => {
  await repository({'src/old\tname.ts': 'one\ntwo\nthree\n'}, async root => {
    await git(root, 'mv', '--', 'src/old\tname.ts', 'src/new\nname.ts');
    const renamed = await inspectChanges(root);
    assertEquals(renamed.paths, ['src/new\nname.ts', 'src/old\tname.ts']);
    assertEquals(renamed.statuses, ['R100']);
    assertEquals(renamed.changed_lines, 0);
    assertEquals(renamed.mode, 'REVIEW');
  });
  await repository({'src/removed.ts': 'value\n'}, async root => {
    await Deno.remove(join(root, 'src/removed.ts'));
    const deleted = await inspectChanges(root);
    assertEquals(deleted.statuses, ['D']);
    assertEquals(deleted.changed_lines, 1);
    assertEquals(deleted.mode, 'REVIEW');
  });
});

Deno.test('workflow: binary and symlink additions cannot become direct work', async () => {
  await repository({'src/value.ts': 'value\n'}, async root => {
    await Deno.writeFile(join(root, 'binary.dat'), new Uint8Array([0, 1, 2]));
    const binary = await inspectChanges(root);
    assertEquals(binary.changed_lines, null);
    assertEquals(binary.mode, 'REVIEW');
    await Deno.remove(join(root, 'binary.dat'));
    await Deno.symlink('src/value.ts', join(root, 'alias.ts'));
    const symlink = await inspectChanges(root);
    assertEquals(symlink.paths, ['alias.ts']);
    assertEquals(symlink.changed_lines, null);
    assertEquals(symlink.mode, 'REVIEW');
  });
});

Deno.test('workflow: Deno exports identify nonstandard public entry filenames', async () => {
  await repository(
    {
      'plugins/demo/deno.json': JSON.stringify({exports: './src/api.ts'}),
      'plugins/demo/src/api.ts': 'export const value = 1;\n',
    },
    async root => {
      await Deno.writeTextFile(
        join(root, 'plugins/demo/src/api.ts'),
        'export const value = 2;\n',
      );
      const result = await inspectChanges(root);
      assertEquals(result.public_entry_changed, true);
      assertEquals(result.mode, 'REVIEW');
    },
  );
});

Deno.test('workflow: explicit baseline includes commits and invalid refs fail', async () => {
  await repository({'src/value.ts': 'before\n'}, async root => {
    const initial = await git(root, 'rev-parse', 'HEAD');
    await Deno.writeTextFile(join(root, 'src/value.ts'), 'after\n');
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

Deno.test('workflow: difficulty thresholds are independent of review mode', () => {
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
  const config = {...sample, paths: ['deno.jsonc']};
  assertEquals(selectWorkMode(config).mode, 'REVIEW');
  assertEquals(assessDifficulty(config).level, 'very_easy');
});

Deno.test('workflow: task difficulty excludes unrelated binary changes without weakening review', async () => {
  await repository({'src/a.ts': 'before\n'}, async root => {
    await Deno.writeTextFile(join(root, 'src/a.ts'), 'after\n');
    await Deno.writeFile(
      join(root, 'unrelated.dat'),
      new Uint8Array([0, 1, 2]),
    );
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

Deno.test('workflow: planned work with no observed diff remains unassessed', async () => {
  await repository({'src/a.ts': 'before\n'}, async root => {
    const result = await inspectChanges(root, 'HEAD', {
      tasks: [{id: 'future', files: ['src/a.ts']}],
    });
    assertEquals(result.difficulty[0].level, null);
  });
});

Deno.test('workflow: invalid directory scopes are not collected for difficulty', async () => {
  await repository({'src/a.ts': 'before\n'}, async root => {
    await Deno.writeTextFile(join(root, 'src/a.ts'), 'after\n');
    const result = await inspectChanges(root, 'HEAD', {
      tasks: [{id: 'invalid', files: ['src']}],
    });
    assertEquals(result.mode, 'REVIEW');
    assertEquals(result.difficulty[0].level, null);
    assertEquals(result.difficulty[0].facts, null);
  });
});

Deno.test('workflow: per-task observations keep literal paths and independent levels', async () => {
  const first = 'plugins/demo/small\tname.ts';
  const second = 'plugins/demo/large.ts';
  await repository(
    {
      [first]: 'export const small = 1;\n',
      [second]: 'export const large = 1;\n',
    },
    async root => {
      await Deno.writeTextFile(join(root, first), 'export const small = 2;\n');
      await Deno.writeTextFile(
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
          line.includes('Select models separately'),
        ),
      );
    },
  );
});

Deno.test('workflow: scoped observations include staged, unstaged and untracked changes', async () => {
  await repository({'src/a.ts': 'original\n'}, async root => {
    await Deno.writeTextFile(join(root, 'src/a.ts'), 'staged\n');
    await git(root, 'add', 'src/a.ts');
    await Deno.writeTextFile(join(root, 'src/a.ts'), 'unstaged\n');
    await Deno.writeTextFile(join(root, 'src/new.ts'), 'new\n');
    const result = await inspectChanges(root, 'HEAD', {
      tasks: [{id: 'mixed', files: ['src/a.ts', 'src/new.ts']}],
    });
    assertEquals(result.difficulty[0].facts?.changed_lines, 5);
    assertEquals(result.difficulty[0].facts?.changed_files, 2);
    assertEquals(result.difficulty[0].level, 'easy');
  });
});

Deno.test('workflow: review eligibility does not suppress measurable task difficulty', async () => {
  const first = 'plugins/demo/first.ts';
  const second = 'plugins/demo/second.ts';
  await repository(
    {
      [first]: "export {value} from './second.ts';\n",
      [second]: 'export const value = 1;\n',
    },
    async root => {
      await Deno.writeTextFile(
        join(root, first),
        "export {value} from './second.ts';\n// changed\n",
      );
      await Deno.writeTextFile(join(root, second), 'export const value = 2;\n');
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

Deno.test('workflow: destination-only task retains observed rename metadata', async () => {
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

Deno.test('workflow: staged and tracked symlinks remain unassessed', async () => {
  await repository({'src/a.ts': 'before\n'}, async root => {
    await Deno.symlink('src/a.ts', join(root, 'alias.ts'));
    await git(root, 'add', 'alias.ts');
    assertEquals((await inspectChanges(root)).difficulty[0].level, null);
    await git(root, 'commit', '--quiet', '-m', 'Link fixture');
    await Deno.remove(join(root, 'alias.ts'));
    await Deno.symlink('src/missing.ts', join(root, 'alias.ts'));
    assertEquals((await inspectChanges(root)).difficulty[0].level, null);
  });
});

Deno.test('workflow: delegation instructions use Orca workers', () => {
  for (const mode of ['DELEGATE', 'PARALLEL'] as const) {
    const lines = buildWorkModeInstructions(mode, true);
    assert(lines.some(line => line.includes('Orca orchestration')));
    assert(!lines.some(line => line.includes('Goose')));
  }
});

Deno.test('workflow: review instructions time independent review at merge', () => {
  const lines = buildWorkModeInstructions('REVIEW', true);
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
        line.includes('fresh reviewer from the other provider') &&
        line.includes('develop (favoring speed)') &&
        line.includes('main (favoring accuracy)') &&
        line.includes('not for each change'),
    ),
  );
  assert(lines.some(line => line.includes('no extra user approval')));
  assert(!lines.some(line => line.includes('separate read-only diff review')));
});

Deno.test('workflow: every mode prints the Linear completion order', () => {
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
