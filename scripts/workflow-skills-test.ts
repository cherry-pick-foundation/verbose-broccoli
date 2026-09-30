import {test} from 'node:test';
import {rejects} from 'node:assert/strict';
import {
  assert,
  assertEquals,
  assertNotEquals,
  assertRejects,
  assertThrows,
} from '@std/assert';
import {dirname, fromFileUrl, join} from '@std/path';
import {spawnSync} from 'node:child_process';
import {mkdir, mkdtemp, rm, stat, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {snapshotWorkingTree} from './workflow-git.ts';
import {
  parseCleanCodeScope,
  selectSkills,
  announceSkillTriggers,
} from './workflow-skills.ts';

type Input = Parameters<typeof selectSkills>[0];
const input: Input = {
  taskId: 'fixture-task',
  base: 'a'.repeat(40),
  paths: [],
  mode: 'DIRECT',
  verify: false,
};
const first = 'plugins/demo/first.ts';
const other = 'plugins/demo/other.ts';
const database = 'plugins/demo/database.ts';
const pure = 'export function value(n: number) { return n + 1; }';

async function git(root: string, ...args: string[]) {
  const result = spawnSync(
    'git',
    [
      '-c',
      'core.hooksPath=/dev/null',
      '-c',
      'user.name=Workflow Skills Fixture',
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
  run: (root: string, context: Input) => Promise<void>,
) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-skills-test-'));
  try {
    await git(root, 'init', '--quiet', '--template=', '--initial-branch=main');
    for (const [file, source] of Object.entries(files)) {
      await mkdir(dirname(join(root, file)), {recursive: true});
      await writeFile(join(root, file), source);
    }
    await git(root, 'add', '--all');
    await git(root, 'commit', '--quiet', '-m', 'Skills fixture');
    await run(root, {...input, base: await git(root, 'rev-parse', 'HEAD')});
  } finally {
    await rm(root, {recursive: true});
  }
}

void test('workflow skills: clean-code uses the exact intersection of selected and changed or planned files', () => {
  const selected = [first, other, 'plugins/demo/unrelated.ts'];
  const triggers = selectSkills(
    {
      ...input,
      paths: [first, database, first],
      tasks: [{id: 'planned', files: [other, first]}],
    },
    selected,
  );
  assertEquals(
    triggers.map(trigger => trigger.name),
    ['clean-code'],
  );
  assertEquals(triggers[0].files, [first, other]);
  assertEquals(selectSkills({...input, paths: [database]}, selected), []);
});

void test('workflow skills: actual review code diffs trigger ponytail and every verification mode triggers summary guidance', () => {
  const code = [
    'plugins/demo/removed.ts',
    'plugins/demo/old.mts',
    'plugins/demo/new.jsx',
  ];
  for (const mode of ['DIRECT', 'DELEGATE', 'PARALLEL', 'REVIEW'] as const) {
    const triggers = selectSkills(
      {...input, mode, paths: [...code, 'notes.txt'], verify: true},
      [],
    );
    assert(
      triggers.some(
        trigger => trigger.name === 'verification-before-completion',
      ),
      mode,
    );
    const review = triggers.find(
      trigger => trigger.name === 'ponytail:ponytail-review',
    );
    assertEquals(Boolean(review), mode === 'REVIEW');
    if (review) assertEquals(review.files, code.slice().sort());
  }
  assertEquals(
    selectSkills(
      {
        ...input,
        mode: 'REVIEW',
        paths: [],
        tasks: [{id: 'planned', files: [first]}],
      },
      [],
    ),
    [],
  );
  assertEquals(
    selectSkills({...input, mode: 'REVIEW', paths: ['notes.txt']}, []),
    [],
  );
});

void test('workflow skills: malformed or failed scope reports cannot supply selected files', () => {
  const report = {
    scope: [
      {file: first, status: 'included', reasons: []},
      {
        file: database,
        status: 'excluded',
        reasons: [
          {message: 'string literal', line: 1, column: 1, rule: 'scope'},
        ],
      },
    ],
    selected: [first],
    diagnostics: [],
  };
  assertEquals(parseCleanCodeScope(JSON.stringify(report)), [first]);
  for (const output of [
    '{',
    JSON.stringify({}),
    JSON.stringify({...report, selected: first}),
    JSON.stringify({...report, selected: []}),
    JSON.stringify({...report, selected: [database]}),
    JSON.stringify({...report, selected: ['missing.ts']}),
    JSON.stringify({
      ...report,
      scope: [{file: first, status: 'error', reasons: []}],
    }),
    JSON.stringify({
      ...report,
      scope: [{file: first, status: 'unknown', reasons: []}],
    }),
    JSON.stringify({
      ...report,
      diagnostics: [{file: first, message: 'failed', rule: 'example'}],
    }),
  ])
    assertThrows(() => parseCleanCodeScope(output));
});

void test('workflow skills: real scope includes long eligible functions and receipts do not change code fingerprints', async () => {
  const long = 'plugins/demo/long.ts';
  const planned = 'plugins/demo/planned.ts';
  await repository(
    {
      [first]: pure,
      [other]: pure,
      [planned]: pure,
      [database]: "export function query() { return 'SELECT 1'; }",
      [long]:
        'export function count(value: number) {\n' +
        '  value++;\n'.repeat(18) +
        '  return value;\n}\n',
    },
    async (root, context) => {
      const before = await snapshotWorkingTree(root);
      const result = await announceSkillTriggers(root, {
        ...context,
        paths: [first, database, long],
        tasks: [{id: 'planned', files: [planned]}],
      });
      assertEquals(result.snapshot, before);
      assertEquals(await snapshotWorkingTree(root), before);
      assertEquals(
        result.triggers.map(trigger => trigger.name),
        ['clean-code'],
      );
      assertEquals(result.triggers[0].files, [first, long, planned]);
      assertEquals(result.triggers[0].status, 'ANNOUNCED');
      assert(result.triggers[0].id);
      assert(
        result.instructions.some(line =>
          line.includes('Codex or Claude Code skill catalogue'),
        ),
      );
      assert(!result.instructions.some(line => line.includes('Goose')));
    },
  );
});

void test('workflow skills: scope errors require review while preserving verification guidance', async () => {
  await repository(
    {[first]: 'export function broken( {'},
    async (root, context) => {
      const result = await announceSkillTriggers(root, {
        ...context,
        paths: [first],
        verify: true,
      });
      assertEquals(result.mode, 'REVIEW');
      assertEquals(result.scope.status, 'ERROR');
      assert('error' in result.scope && result.scope.error);
      assertEquals(result.triggers.map(trigger => trigger.name).sort(), [
        'ponytail:ponytail-review',
        'verification-before-completion',
      ]);
    },
  );
});

void test('workflow skills: stale expected snapshots cannot write announcement receipts', async () => {
  await repository({[first]: pure}, async (root, context) => {
    const expected = await snapshotWorkingTree(root);
    await writeFile(join(root, first), pure.replace('+ 1', '+ 2'));
    await assertRejects(
      () => announceSkillTriggers(root, {...context, paths: [first]}, expected),
      Error,
      'Code changed during skill scope selection',
    );
    const directory = await git(
      root,
      'rev-parse',
      '--path-format=absolute',
      '--git-path',
      'workflow/skill-triggers',
    );
    await rejects(stat(directory), {code: 'ENOENT'});
  });
});

void test('workflow skills CLI: failed verification and scope errors preserve the summary and skill guidance', async () => {
  await repository(
    {
      [first]: pure,
      'package.json': JSON.stringify({
        scripts: {
          check: `node ${first}`,
        },
      }),
    },
    async root => {
      await writeFile(join(root, first), 'export function broken( {');
      const result = spawnSync(
        process.execPath,
        [
          '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',
          '--disable-warning=SecurityWarning',
          '--permission',
          '--allow-fs-read=*',
          '--allow-fs-write=*',
          '--allow-child-process',
          fromFileUrl(new URL('./workflow.ts', import.meta.url)),
          '--task',
          'scope-error-fixture',
          '--verify',
        ],
        {cwd: root, stdio: ['ignore', 'pipe', 'pipe']},
      );
      if (result.error) throw result.error;
      const text = new TextDecoder().decode(result.stderr);
      assertEquals(result.status, 1);
      assert(text.trim(), new TextDecoder().decode(result.stderr));
      const report = text
        .split(/\r?\n/)
        .findLast(line => line.startsWith('{"error":'));
      assert(report, text);
      const output = JSON.parse(report).details as {
        mode: string;
        skill_scope: {status: string};
        skill_triggers: {name: string}[];
        verification: {phase: string};
      };
      assertEquals(output.mode, 'REVIEW');
      assertEquals(output.skill_scope.status, 'ERROR');
      assertEquals(output.verification.phase, 'FAILED');
      assert(
        output.skill_triggers.some(
          trigger => trigger.name === 'verification-before-completion',
        ),
      );
      assert(
        !output.skill_triggers.some(trigger => trigger.name === 'clean-code'),
      );
    },
  );
});

void test('workflow skills: task, baseline, complete scope and code changes invalidate deduplication', async () => {
  await repository(
    {[first]: pure, [database]: "export function query() { return 'SQL'; }"},
    async (root, context) => {
      await git(
        root,
        'commit',
        '--quiet',
        '--allow-empty',
        '-m',
        'Second baseline',
      );
      const newer = await git(root, 'rev-parse', 'HEAD');
      const initial = await announceSkillTriggers(root, {
        ...context,
        paths: [first],
      });
      const trigger = initial.triggers[0];
      assertEquals(trigger.status, 'ANNOUNCED');
      const again = await announceSkillTriggers(root, {
        ...context,
        paths: [first, first],
        tasks: [{id: 'same-scope', files: [first]}],
      });
      assertEquals(again.triggers[0].id, trigger.id);
      assertEquals(again.triggers[0].status, 'ALREADY_ANNOUNCED');
      for (const changed of [
        {...context, paths: [first], taskId: 'new-task'},
        {...context, paths: [first], base: newer},
        {...context, paths: [database, first]},
      ]) {
        const result = await announceSkillTriggers(root, changed);
        assertEquals(result.triggers[0].files, [first]);
        assertNotEquals(result.triggers[0].id, trigger.id);
        assertEquals(result.triggers[0].status, 'ANNOUNCED');
      }
      const reordered = await announceSkillTriggers(root, {
        ...context,
        paths: [first, database, first],
      });
      assertEquals(reordered.triggers[0].status, 'ALREADY_ANNOUNCED');
      await writeFile(join(root, first), pure.replace('+ 1', '+ 2'));
      const updated = await announceSkillTriggers(root, {
        ...context,
        paths: [first],
      });
      assertNotEquals(updated.snapshot.dirty_hash, initial.snapshot.dirty_hash);
      assertNotEquals(updated.triggers[0].id, trigger.id);
      assertEquals(updated.triggers[0].status, 'ANNOUNCED');
    },
  );
});

void test('workflow skills: concurrent identical calls announce each skill exactly once', async () => {
  await repository({[first]: pure}, async (root, context) => {
    const request = {
      ...context,
      paths: [first],
      mode: 'REVIEW' as const,
      verify: true,
    };
    const before = await snapshotWorkingTree(root);
    const results = await Promise.all([
      announceSkillTriggers(root, request),
      announceSkillTriggers(root, request),
    ]);
    assertEquals(results[0].triggers.length, 3);
    for (const name of [
      'clean-code',
      'ponytail:ponytail-review',
      'verification-before-completion',
    ]) {
      const triggers = results
        .flatMap(result => result.triggers)
        .filter(trigger => trigger.name === name);
      assertEquals(triggers.map(trigger => trigger.status).sort(), [
        'ALREADY_ANNOUNCED',
        'ANNOUNCED',
      ]);
      assertEquals(triggers[0].id, triggers[1].id);
    }
    assertEquals(await snapshotWorkingTree(root), before);
  });
});
