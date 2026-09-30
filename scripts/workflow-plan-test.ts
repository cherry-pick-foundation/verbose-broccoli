import {test} from 'node:test';
import {assert, assertEquals, assertRejects} from '@std/assert';
import {dirname, join} from '@std/path';
import {spawnSync} from 'node:child_process';
import {mkdir, mkdtemp, rm, symlink, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {analyzePlan} from './workflow-plan.ts';
import {selectWorkMode, inspectChanges} from './workflow.ts';

const first = 'plugins/demo/src/first.ts';
const second = 'plugins/demo/src/second.ts';
const tasks = [
  {id: 'first', files: [first]},
  {id: 'second', files: [second]},
];
const unchanged = {
  paths: [],
  statuses: [],
  changedLines: 0,
  publicEntryChanged: false,
};

async function fixture(
  files: Record<string, string>,
  run: (root: string) => Promise<void>,
) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-plan-'));
  try {
    for (const [path, content] of Object.entries(files)) {
      await mkdir(dirname(join(root, path)), {recursive: true});
      await writeFile(join(root, path), content);
    }
    await run(root);
  } finally {
    await rm(root, {recursive: true});
  }
}

void test('workflow plan: one bounded task delegates; two independent tasks run in parallel', async () => {
  await fixture(
    {
      [first]: 'export const first = 1;',
      [second]: 'export const second = 2;',
    },
    async root => {
      const single = await analyzePlan(root, {tasks: [tasks[0]]});
      assertEquals(selectWorkMode(unchanged, single).mode, 'DELEGATE');
      const parallel = await analyzePlan(root, {tasks});
      assertEquals(parallel.reasons, []);
      assertEquals(selectWorkMode(unchanged, parallel).mode, 'PARALLEL');
    },
  );
});

void test('workflow plan: shared unchanged dependency permits parallel file edits', async () => {
  await fixture(
    {
      [first]: "export {shared as first} from './shared.ts';",
      [second]: "export {shared as second} from './shared.ts';",
      'plugins/demo/src/shared.ts': 'export const shared = 1;',
    },
    async root => {
      assertEquals(
        selectWorkMode(unchanged, await analyzePlan(root, {tasks})).mode,
        'PARALLEL',
      );
    },
  );
});

void test('workflow plan: direct, transitive, alias and shared consumer dependencies prevent parallel edits', async () => {
  const cases: Record<string, string>[] = [
    {[first]: "export {second as first} from './second.ts';"},
    {
      [first]: "export {middle as first} from './middle.ts';",
      'plugins/demo/src/middle.ts':
        "export {second as middle} from './second.ts';",
    },
    {
      [first]: "export {second as first} from '#second';",
      'package.json': JSON.stringify({
        imports: {'#second': './plugins/demo/src/second.ts'},
      }),
    },
    {
      'plugins/demo/src/consumer.ts':
        "export {first} from './first.ts'; export {second} from './second.ts';",
    },
  ];
  for (const extra of cases) {
    await fixture(
      {
        [first]: 'export const first = 1;',
        [second]: 'export const second = 2;',
        ...extra,
      },
      async root => {
        const result = await analyzePlan(root, {tasks});
        assert(result.reasons.length > 0, JSON.stringify(extra));
        assertEquals(selectWorkMode(unchanged, result).mode, 'REVIEW');
      },
    );
  }
});

void test('workflow plan: root and tests consumers prevent parallel edits across scan roots', async () => {
  const cases: Record<string, string>[] = [
    {
      'consumer.ts':
        "export {first} from './plugins/demo/src/first.ts'; export {second} from './plugins/demo/src/second.ts';",
    },
    {
      'tests/consumer.ts':
        "export {first} from '../plugins/demo/src/first.ts'; export {second} from '../plugins/demo/src/second.ts';",
    },
    {
      'consumer.ts': "export * from './tests/middle.ts';",
      'tests/middle.ts':
        "export {first} from '../plugins/demo/src/first.ts'; export {second} from '../plugins/demo/src/second.ts';",
    },
  ];
  for (const extra of cases) {
    await fixture(
      {
        [first]: 'export const first = 1;',
        [second]: 'export const second = 2;',
        'plugins/demo/package.json': JSON.stringify({
          exports: {
            './first': './src/first.ts',
            './second': './src/second.ts',
          },
        }),
        ...extra,
      },
      async root => {
        const result = await analyzePlan(root, {tasks});
        assert(
          result.reasons.some(
            reason =>
              reason.includes('affect the same files:') &&
              reason.includes('consumer.ts'),
          ),
          JSON.stringify(result),
        );
        assertEquals(selectWorkMode(unchanged, result).mode, 'REVIEW');
      },
    );
  }
});

void test('workflow plan: repository scan keeps tool, vendor and agent cache exclusions', async () => {
  const excluded = [
    'tools/consumer.ts',
    'scripts/vendor/consumer.ts',
    '.agents/cache/consumer.ts',
    '.codex/cache/consumer.ts',
    '.specify/cache/consumer.ts',
    'node_modules/cache/consumer.ts',
    '.deno/cache/consumer.ts',
    '.git/cache/consumer.ts',
  ];
  await fixture(
    {
      [first]: 'export const first = 1;',
      [second]: 'export const second = 2;',
      ...Object.fromEntries(
        excluded.map(path => [path, "import './missing.ts';"]),
      ),
    },
    async root => {
      assertEquals((await analyzePlan(root, {tasks})).reasons, []);
      const result = await analyzePlan(root, {
        tasks: [tasks[0], {id: 'excluded', files: [excluded[0]]}],
      });
      assert(
        result.reasons.some(reason =>
          reason.includes('outside the dependency graph'),
        ),
      );
    },
  );
});

void test('workflow plan: overlap, missing files, unsupported sources and unresolved imports prevent parallel edits', async () => {
  await fixture(
    {
      [first]: 'export const first = 1;',
      [second]: 'export const second = 2;',
      'notes.txt': 'notes',
    },
    async root => {
      for (const file of [first, 'plugins/demo/src/missing.ts', 'notes.txt']) {
        const result = await analyzePlan(root, {
          tasks: [tasks[0], {id: 'other', files: [file]}],
        });
        assertEquals(selectWorkMode(unchanged, result).mode, 'REVIEW', file);
      }
      await writeFile(
        join(root, second),
        "export {missing} from './missing.ts';",
      );
      assertEquals(
        selectWorkMode(unchanged, await analyzePlan(root, {tasks})).mode,
        'REVIEW',
      );
    },
  );
});

void test('workflow plan: symlink aliases cannot give two agents the same writable file', async () => {
  await fixture(
    {
      [first]: 'export const first = 1;',
      [second]: 'export const second = 2;',
    },
    async root => {
      await symlink(join(root, first), join(root, 'plugins/demo/src/alias.ts'));
      const plan = {
        tasks: [tasks[0], {id: 'alias', files: ['plugins/demo/src/alias.ts']}],
      };
      assertEquals(
        selectWorkMode(unchanged, await analyzePlan(root, plan)).mode,
        'REVIEW',
      );
      for (const files of [
        ['plugins/demo/src/alias.ts'],
        ['plugins/demo/src'],
      ]) {
        assertEquals(
          selectWorkMode(
            unchanged,
            await analyzePlan(root, {tasks: [{id: 'single', files}]}),
          ).mode,
          'REVIEW',
        );
      }
      await symlink(join(root, 'plugins/demo/src'), join(root, 'alias'));
      assertEquals(
        selectWorkMode(
          unchanged,
          await analyzePlan(root, {
            tasks: [{id: 'single', files: ['alias/new.ts']}],
          }),
        ).mode,
        'REVIEW',
      );
      assertEquals(
        selectWorkMode(
          unchanged,
          await analyzePlan(root, {
            tasks: [{id: 'new', files: ['plugins/demo/new/file.ts']}],
          }),
        ).mode,
        'DELEGATE',
      );
    },
  );
});

void test('workflow plan: invalid or ambiguous task scopes fail validation', async () => {
  await fixture({}, async root => {
    for (const input of [
      {},
      {tasks: []},
      {tasks: [tasks[0], tasks[0]]},
      ...[
        '../outside.ts',
        '/tmp/outside.ts',
        './plugins/a.ts',
        'plugins//a.ts',
        'plugins/**/*.ts',
        'apps\\a.ts',
      ].map(path => ({tasks: [{id: 'invalid', files: [path]}]})),
    ])
      await assertRejects(() => analyzePlan(root, input));
  });
});

void test('workflow plan: risky planned paths and scope growth still require review', () => {
  const plan = {tasks, reasons: []};
  assertEquals(
    selectWorkMode(
      {...unchanged, paths: ['unplanned.ts'], statuses: ['?']},
      plan,
    ).mode,
    'REVIEW',
  );
  for (const path of [
    'package.json',
    'plugins/demo/src/mod.ts',
    'plugins/demo/migrations/001.sql',
  ]) {
    assertEquals(
      selectWorkMode(unchanged, {
        tasks: [{id: 'risky', files: [path]}],
        reasons: [],
      }).mode,
      'REVIEW',
    );
  }
  assertEquals(
    selectWorkMode({...unchanged, publicEntryChanged: true}, plan).mode,
    'REVIEW',
  );
});

void test('workflow plan: Git integration routes a clean plan then rejects changes outside its scope', async () => {
  await fixture(
    {
      [first]: 'export const first = 1;',
      [second]: 'export const second = 2;',
    },
    async root => {
      for (const args of [
        ['init', '-q'],
        ['add', '.'],
        [
          '-c',
          'user.name=Work mode test',
          '-c',
          'user.email=workflow@example.invalid',
          '-c',
          'commit.gpgsign=false',
          '-c',
          'core.hooksPath=/dev/null',
          'commit',
          '-qm',
          'fixture',
        ],
      ]) {
        const result = spawnSync('git', args, {
          cwd: root,
          stdio: ['ignore', 'pipe', 'pipe'],
        });
        if (result.error) throw result.error;
        assert(result.status === 0, new TextDecoder().decode(result.stderr));
      }
      const result = await inspectChanges(root, 'HEAD', {tasks});
      assertEquals(result.mode, 'PARALLEL');
      assertEquals(result.tasks, tasks);
      await writeFile(join(root, 'outside.txt'), 'outside\n');
      assertEquals(
        (await inspectChanges(root, 'HEAD', {tasks})).mode,
        'REVIEW',
      );
    },
  );
});
