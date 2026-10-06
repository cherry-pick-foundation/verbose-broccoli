import {assert, assertEquals} from '@std/assert';
import {join} from '@std/path';
import {test} from 'node:test';
import {mkdir, mkdtemp, rm, symlink, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {checkCleanCode, classifyFile} from './clean-code.ts';

const examples = [
  [
    'arithmetic',
    'export function double(value: number) { return value * 2; }',
    'included',
  ],
  [
    'branch and loop',
    'export function count(n: number) { let total = 0; for (let i = 0; i < n; i++) { if (i > 2) total++; } return total; }',
    'included',
  ],
  [
    'local function',
    'function step(n: number) { return n + 1; } export function run(n: number) { return step(n); }',
    'included',
  ],
  [
    'local arrow',
    'const step = (n: number) => n + 1; export function run(n: number) { return step(n); }',
    'included',
  ],
  [
    'local expression',
    'const step = function(n: number) { return n + 1; }; export function run(n: number) { return step(n); }',
    'included',
  ],
  [
    'local overload',
    'function step(n: number): number; function step(n: number) { return n + 1; } export function run(n: number) { return step(n); }',
    'included',
  ],
  [
    'block local binding',
    'export function run(n: number) { if (n) { const step = (v: number) => v + 1; return step(n); } return n; }',
    'included',
  ],
  [
    'explicit any stays selected',
    'export function run(n: any) { return n; }',
    'included',
  ],
  [
    'unused variable stays selected',
    'export function run(n: number) { const unused = 1; return n; }',
    'included',
  ],
  ['string', "export function value() { return 'ordinary text'; }", 'excluded'],
  ['SQL string', "export function value() { return 'SELECT 1'; }", 'excluded'],
  ['object', 'export function value() { return { value: 1 }; }', 'excluded'],
  ['array', 'export function value() { return [1]; }', 'excluded'],
  [
    'regular expression',
    'export function value() { return /pattern/; }',
    'excluded',
  ],
  [
    'template',
    'export function value(n: number) { return `${n}`; }',
    'excluded',
  ],
  [
    'tagged template',
    'export function value() { return sql`SELECT 1`; }',
    'excluded',
  ],
  ['JSX', 'export function value() { return <div />; }', 'excluded'],
  [
    'method',
    'export function value(n: number) { return n.toFixed(); }',
    'excluded',
  ],
  [
    'external call',
    'export function value(n: number) { return Math.abs(n); }',
    'excluded',
  ],
  ['external value', 'export function value() { return Math.PI; }', 'excluded'],
  [
    'callback parameter',
    'export function run(fn: () => number) { return fn(); }',
    'excluded',
  ],
  [
    'computed call',
    'export function run(api: { [key: number]: () => number }, key: number) { return api[key](); }',
    'excluded',
  ],
  [
    'dynamic import',
    'export function run(path: string) { return import(path); }',
    'excluded',
  ],
  [
    'shadowed name',
    'function step(n: number) { return n + 1; } export function run(step: () => number) { return step(); }',
    'excluded',
  ],
  [
    'reassigned function',
    'let step = (n: number) => n; export function run(fn: (n: number) => number) { step = fn; return step(1); }',
    'excluded',
  ],
  [
    'reassigned declaration',
    'function step(n: number) { return n; } export function run(fn: (n: number) => number) { step = fn; return step(1); }',
    'excluded',
  ],
  [
    'mixed file',
    'export function good(n: number) { return n + 1; } const schema = { value: 1 };',
    'excluded',
  ],
  ['type-only file', 'export type Value = number;', 'excluded'],
  [
    'ambient function',
    'declare function external(n: number): number; export function run(n: number) { return external(n); }',
    'excluded',
  ],
  [
    'ambient value',
    'declare const external: number; export function run() { return external; }',
    'excluded',
  ],
  ['syntax error', "export function broken( { return 'text'; }", 'error'],
] as const;

for (const [name, source, expected] of examples) {
  void test(`scope: ${name}`, async () => {
    const cwd = process.cwd();
    const report = await classifyFile(join(cwd, 'example.tsx'), source, cwd);
    assertEquals(report.status, expected, JSON.stringify(report.reasons));
  });
}

function sizedFunction(lines: number, filler = '  value++;\n') {
  return (
    'export function count(value: number) {\n' +
    filler.repeat(lines - 3) +
    '  return value;\n}\n'
  );
}

void test('same selection, exact length boundary, and quality failures', async () => {
  const cwd = await mkdtemp(join(tmpdir(), 'clean-code-test-'));
  try {
    const directory = join(cwd, 'packages');
    await mkdir(directory);
    const sources = {
      'twenty.ts': sizedFunction(20),
      'twenty-one.ts': sizedFunction(21),
      'comments.ts': sizedFunction(21, '  // comment\n'),
      'blanks.ts': sizedFunction(21, '\n'),
      'any.ts': 'export function run(n: any) { return n; }',
      'implicit.ts': 'export function run(n) { return n; }',
      'unused.ts':
        'export function run(n: number) { const unused = 1; return n; }',
      'unreachable.ts': 'export function run() { return 1; return 2; }',
      'suppression.ts': `/* eslint-disable max-lines-per-function */\n${sizedFunction(21)}`,
      'mixed.ts':
        'export function run(n: number) { return n; } const schema = {};',
    };
    for (const [name, source] of Object.entries(sources)) {
      await writeFile(join(directory, name), source);
    }
    const scope = await checkCleanCode(cwd, true);
    const checked = await checkCleanCode(cwd);
    assertEquals(checked.selected, scope.selected);
    assertEquals(scope.assessment, 'SCOPE_ONLY');
    assertEquals(checked.assessment, 'FAIL');
    assertEquals(checked.selected.length, 9);
    assertEquals(
      checked.diagnostics.filter(item => item.file === 'packages/twenty.ts'),
      [],
    );
    for (const name of ['twenty-one', 'comments', 'blanks', 'suppression']) {
      assert(
        checked.diagnostics.some(
          item =>
            item.file === `packages/${name}.ts` &&
            item.rule === 'max-lines-per-function',
        ),
      );
    }
    for (const name of ['any', 'implicit', 'unused', 'unreachable']) {
      assert(
        checked.diagnostics.some(item => item.file === `packages/${name}.ts`),
        name,
      );
    }
    assert(!checked.selected.includes('packages/mixed.ts'));
  } finally {
    await rm(cwd, {recursive: true});
  }
});

void test('parse errors remain errors and never become exclusions', async () => {
  const cwd = await mkdtemp(join(tmpdir(), 'clean-code-error-'));
  try {
    await mkdir(join(cwd, 'plugins'));
    await writeFile(
      join(cwd, 'plugins', 'broken.ts'),
      "export function broken( { return 'SQL'; }",
    );
    const report = await checkCleanCode(cwd);
    assertEquals(report.scope[0].status, 'error');
    assertEquals(report.selected, []);
    assert(report.scope[0].reasons.length > 0);
  } finally {
    await rm(cwd, {recursive: true});
  }
});

void test('discovery applies fixed paths and excludes declaration files and symlinks', async () => {
  const cwd = await mkdtemp(join(tmpdir(), 'clean-code-paths-'));
  const good = 'export function run(value: number) { return value + 1; }';
  try {
    for (const directory of [
      'plugins',
      'packages',
      'scripts',
      'scripts/vendor',
      'packages/node_modules',
      'tools',
    ]) {
      await mkdir(join(cwd, directory), {recursive: true});
      await writeFile(join(cwd, directory, 'sample.ts'), good);
    }
    await writeFile(join(cwd, 'plugins', 'ignored.d.ts'), 'invalid TS');
    await writeFile(join(cwd, 'plugins', 'ignored.mdx'), 'invalid TS');
    await symlink(
      join(cwd, 'tools', 'sample.ts'),
      join(cwd, 'plugins', 'linked.ts'),
    );
    const report = await checkCleanCode(cwd, true);
    assertEquals(report.selected, [
      'packages/sample.ts',
      'plugins/sample.ts',
      'scripts/sample.ts',
    ]);
    assertEquals(report.scope.length, 3);
  } finally {
    await rm(cwd, {recursive: true});
  }
});

void test('excluded-only scope is explicitly not applicable, not a quality pass', async () => {
  const cwd = await mkdtemp(join(tmpdir(), 'clean-code-no-scope-'));
  try {
    await mkdir(join(cwd, 'plugins'));
    await writeFile(
      join(cwd, 'plugins', 'adapter.ts'),
      "export function message() { return 'ordinary text'; }",
    );
    const result = await checkCleanCode(cwd);
    assertEquals(result.assessment, 'NOT_APPLICABLE');
    assertEquals(result.coverage, {
      candidates: 1,
      selected: 0,
      excluded: 1,
      errors: 0,
    });
    assertEquals(result.selected, []);
    assertEquals(result.diagnostics, []);
  } finally {
    await rm(cwd, {recursive: true});
  }
});
