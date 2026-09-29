import {test} from 'node:test';
import {
  assert,
  assertEquals,
  assertNotEquals,
  assertRejects,
} from '@std/assert';
import {dirname, fromFileUrl, join} from '@std/path';
import {spawnSync} from 'node:child_process';
import {inspectGraph} from './workflow_graph.ts';

async function git(root: string, ...args: string[]) {
  const result = spawnSync(
    'git',
    [
      '-c',
      'core.hooksPath=/dev/null',
      '-c',
      'user.name=Workflow Graph Fixture',
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
}

async function repository(
  files: Record<string, string>,
  run: (root: string) => Promise<void>,
) {
  const root = await Deno.makeTempDir({prefix: 'workflow-graph-test-'});
  try {
    await git(root, 'init', '--quiet', '--template=', '--initial-branch=main');
    for (const [path, content] of Object.entries(files)) {
      await Deno.mkdir(dirname(join(root, path)), {recursive: true});
      await Deno.writeTextFile(join(root, path), content);
    }
    await git(root, 'add', '--all');
    await git(root, 'commit', '--quiet', '-m', 'Graph fixture');
    await run(root);
  } finally {
    await Deno.remove(root, {recursive: true});
  }
}

async function impact(root: string, file: string) {
  const result = await inspectGraph(root, {choice: 'impact', file});
  assert('imports' in result);
  assert('dependents' in result);
  assert('test_candidates' in result);
  return result as typeof result & {
    imports: {from: string; module: string; to: string; status: string}[];
    dependents: string[];
    test_candidates: string[];
  };
}

async function cli(root: string, ...args: string[]) {
  const result = spawnSync(
    process.execPath,
    [
      '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',
      '--disable-warning=SecurityWarning',
      '--permission',
      '--allow-fs-read=*',
      '--allow-fs-write=*',
      '--allow-child-process',
      '--import',
      fromFileUrl(new URL('./deno_shim.ts', import.meta.url)),
      fromFileUrl(new URL('./workflow.ts', import.meta.url)),
      ...args,
    ],
    {cwd: root, stdio: ['ignore', 'pipe', 'pipe']},
  );
  if (result.error) throw result.error;
  return {
    code: result.status ?? 1,
    stdout: result.stdout,
    stderr: result.stderr,
  };
}

test('workflow graph: aliases and re-exports reach transitive consumers and affected tests only', async () => {
  const prefix = 'plugins/demo/src/';
  await repository(
    {
      'package.json': JSON.stringify({
        imports: {'#value': `./${prefix}value.ts`},
      }),
      'plugins/demo/deno.json': JSON.stringify({exports: './src/api.ts'}),
      [`${prefix}value.ts`]: 'export const value = 1;',
      [`${prefix}reexport.ts`]: "export {value} from '#value';",
      [`${prefix}api.ts`]: "export {value} from './reexport.ts';",
      [`${prefix}value_test.ts`]: "export {value} from './value.ts';",
      'tests/api.spec.ts': "export {value} from '../plugins/demo/src/api.ts';",
      'plugins/demo/test/smoke.ts': "export {value} from '../src/api.ts';",
      [`${prefix}unrelated.test.ts`]: 'export const other = 2;',
    },
    async root => {
      const result = await impact(root, `${prefix}value.ts`);
      assertEquals(result.policy.status, 'PASS');
      assertEquals(
        result.dependents.slice().sort(),
        [
          `${prefix}api.ts`,
          `${prefix}reexport.ts`,
          `${prefix}value_test.ts`,
          'plugins/demo/test/smoke.ts',
          'tests/api.spec.ts',
        ].sort(),
      );
      assertEquals(
        result.test_candidates.slice().sort(),
        [
          `${prefix}value_test.ts`,
          'plugins/demo/test/smoke.ts',
          'tests/api.spec.ts',
        ].sort(),
      );
      assert(result.indexed_files >= 7);
      assert(result.limitations.length > 0);
      const alias = await impact(root, `${prefix}reexport.ts`);
      assert(
        alias.imports.some(
          edge =>
            edge.from === `${prefix}reexport.ts` &&
            edge.module === '#value' &&
            edge.to === `${prefix}value.ts` &&
            edge.status === 'RESOLVED_LOCAL',
        ),
      );
    },
  );
});

test('workflow graph: every query sees same-length import edits and a new snapshot', async () => {
  await repository(
    {
      'src/value.ts': 'export const value = 1;',
      'src/other.ts': 'export const value = 2;',
      'tests/value.test.ts': "export {value} from '../src/value.ts';",
    },
    async root => {
      const before = await impact(root, 'src/value.ts');
      assertEquals(before.dependents, ['tests/value.test.ts']);
      await Deno.writeTextFile(
        join(root, 'tests/value.test.ts'),
        "export {value} from '../src/other.ts';",
      );
      const after = await impact(root, 'src/value.ts');
      assertEquals(after.snapshot.revision, before.snapshot.revision);
      assertNotEquals(after.snapshot.dirty_hash, before.snapshot.dirty_hash);
      assertEquals(after.dependents, []);
      assertEquals(after.test_candidates, []);
      assertEquals((await impact(root, 'src/other.ts')).test_candidates, [
        'tests/value.test.ts',
      ]);
    },
  );
});

test('workflow graph: cycles, outward domain dependencies and missing local imports fail policy', async () => {
  await repository(
    {
      'plugins/demo/src/domain/value.ts':
        "export {value} from '../infrastructure/db.ts';",
      'plugins/demo/src/infrastructure/db.ts': 'export const value = 1;',
      'plugins/demo/src/cycle/a.ts':
        "import {b} from './b.ts'; export const a = b;",
      'plugins/demo/src/cycle/b.ts':
        "import {a} from './a.ts'; export const b = a;",
      'plugins/demo/src/missing.ts': "export {missing} from './absent.ts';",
    },
    async root => {
      const result = await inspectGraph(root, {choice: 'policy'});
      assertEquals(result.policy.status, 'FAIL');
      assert(result.policy.errors >= 3);
      for (const rule of [
        'no-cycles',
        'domain-dependency-direction',
        'no-unresolved-local-imports',
      ]) {
        assert(
          result.policy.violations.some(
            violation => violation.rule.name === rule,
          ),
          rule,
        );
      }
      const missing = await impact(root, 'plugins/demo/src/missing.ts');
      assertEquals(missing.policy.status, 'FAIL');
      assert(
        missing.imports.some(
          edge => edge.module === './absent.ts' && edge.status === 'UNRESOLVED',
        ),
      );
    },
  );
});

test('workflow graph: npm and jsr dependencies stay external while ignored local targets stay outside scope', async () => {
  await repository(
    {
      'package.json': JSON.stringify({
        imports: {'#validation': 'zod'},
        dependencies: {
          '@std/assert': 'npm:@jsr/std__assert@1.0.19',
          zod: '4.6.2',
        },
      }),
      'src/external.ts':
        "export {assert} from '@std/assert'; export {z} from 'zod'; export {z as schema} from '#validation';",
      'src/adapter.ts': "export {value} from '../tools/hidden.ts';",
      'tools/hidden.ts': 'export const value = 1;',
    },
    async root => {
      const external = await impact(root, 'src/external.ts');
      assertEquals(external.policy.status, 'PASS');
      for (const module of ['@std/assert', 'zod', '#validation']) {
        assert(
          external.imports.some(
            edge => edge.module === module && edge.status === 'EXTERNAL',
          ),
          module,
        );
      }
      const outside = await impact(root, 'src/adapter.ts');
      assert(
        outside.imports.some(
          edge =>
            edge.module === '../tools/hidden.ts' &&
            edge.status === 'OUTSIDE_SCOPE',
        ),
      );
    },
  );
});

test('workflow graph: invalid choices, noncanonical paths and invalid symbol positions are rejected', async () => {
  await repository({'src/value.ts': 'export const value = 1;'}, async root => {
    const inputs = [
      {choice: 'unknown'},
      ...[
        '../outside.ts',
        '/tmp/outside.ts',
        './src/value.ts',
        'src//value.ts',
        'src/*.ts',
      ].map(file => ({choice: 'impact', file})),
      ...[
        {line: 0, column: 1},
        {line: 1, column: 0},
        {line: 99, column: 1},
        {line: 1, column: 999},
      ].map(position => ({
        choice: 'symbol',
        file: 'src/value.ts',
        ...position,
      })),
    ];
    for (const input of inputs)
      await assertRejects(() => inspectGraph(root, input));
  });
});

test('workflow graph: missing, ignored and symlinked selections are rejected', async () => {
  await repository(
    {
      '.gitignore': 'ignored/\n',
      'src/value.ts': 'export const value = 1;',
      'notes.txt': 'notes',
      'ignored/hidden.ts': 'export const value = 6;',
      'tools/hidden.ts': 'export const value = 2;',
      'scripts/vendor/hidden.ts': 'export const value = 3;',
      '.agents/cache/hidden.ts': 'export const value = 4;',
      'node_modules/example/hidden.ts': 'export const value = 5;',
    },
    async root => {
      await Deno.symlink('value.ts', join(root, 'src/alias.ts'));
      await Deno.symlink('src', join(root, 'alias-directory'));
      for (const file of [
        'src/absent.ts',
        'notes.txt',
        'ignored/hidden.ts',
        'tools/hidden.ts',
        'scripts/vendor/hidden.ts',
        '.agents/cache/hidden.ts',
        'node_modules/example/hidden.ts',
        'src/alias.ts',
        'alias-directory/value.ts',
      ]) {
        await assertRejects(() => inspectGraph(root, {choice: 'impact', file}));
      }
    },
  );
});

test('workflow graph: local symbols expose definitions, references and actual caller locations', async () => {
  const source =
    'export function double(value: number) { return value * 2; }\n';
  const aliasCall = 'export function useAlias() { return double(2); }';
  const packageCall = 'export function usePackage() { return scale(2); }';
  const externalCall =
    "export function f() { return external(canonicalize(join('a', 'b'))); }";
  await repository(
    {
      'package.json': JSON.stringify({
        imports: {
          '#math': './src/math.ts',
          '#external': 'unknown-example',
        },
        dependencies: {
          '@std/path': 'npm:@jsr/std__path@1.1.6',
          canonicalize: '5.0.0',
          'unknown-example': '1.0.0',
        },
      }),
      'src/math.ts': source,
      'src/use.ts':
        "import {double} from './math.ts';\nexport function run() { return double(2); }\n",
      'src/types.ts': 'export type Stats = Deno.FileInfo;\n',
      'src/alias.ts': `import {double} from '#math';\n${aliasCall}\n`,
      'packages/math/deno.json': JSON.stringify({
        name: '@demo/math',
        exports: './src/api.ts',
      }),
      'packages/math/src/api.ts': "export {scale} from './implementation.ts';",
      'packages/math/src/implementation.ts':
        'export function scale(value: number) { return value * 3; }',
      'src/package.ts': `import {scale} from '@demo/math';\n${packageCall}\n`,
      'src/external.ts': [
        "import canonicalize from 'canonicalize';",
        "import {join} from '@std/path';",
        "import {external} from '#external';",
        externalCall,
      ].join('\n'),
    },
    async root => {
      const result = await inspectGraph(root, {
        choice: 'symbol',
        file: 'src/math.ts',
        line: 1,
        column: source.indexOf('double') + 1,
      });
      assert('symbol' in result && result.symbol);
      assertEquals(result.symbol.status, 'RESOLVED_LOCAL');
      assert(
        result.symbol.definitions.some(
          location => location.file === 'src/math.ts' && location.line === 1,
        ),
      );
      assert(
        result.symbol.references.some(
          location => location.file === 'src/use.ts' && location.line === 2,
        ),
      );
      assert(
        result.symbol.callers.some(
          caller =>
            caller.file === 'src/use.ts' &&
            caller.calls.some(
              location => location.file === 'src/use.ts' && location.line === 2,
            ),
        ),
      );
      for (const entry of [
        {
          file: 'src/alias.ts',
          call: aliasCall,
          name: 'double',
          definition: 'src/math.ts',
        },
        {
          file: 'src/package.ts',
          call: packageCall,
          name: 'scale',
          definition: 'packages/math/src/implementation.ts',
        },
      ]) {
        const local = await inspectGraph(root, {
          choice: 'symbol',
          file: entry.file,
          line: 2,
          column: entry.call.indexOf(entry.name) + 1,
        });
        assert('symbol' in local && local.symbol);
        assertEquals(local.symbol.status, 'RESOLVED_LOCAL');
        assert(
          local.symbol.definitions.some(
            location => location.file === entry.definition,
          ),
        );
      }
      for (const name of ['canonicalize', 'join', 'external']) {
        const external = await inspectGraph(root, {
          choice: 'symbol',
          file: 'src/external.ts',
          line: 4,
          column: externalCall.indexOf(name) + 1,
        });
        assert('symbol' in external && external.symbol);
        assertEquals(external.symbol.status, 'UNRESOLVED', name);
        assertEquals(external.symbol.definitions, [], name);
      }
      await Deno.writeTextFile(
        join(root, 'src/math.ts'),
        source.replaceAll('double', 'triple'),
      );
      await Deno.writeTextFile(
        join(root, 'src/use.ts'),
        "import {triple} from './math.ts';\nexport function run() { return triple(2); }\n",
      );
      const refreshed = await inspectGraph(root, {
        choice: 'symbol',
        file: 'src/math.ts',
        line: 1,
        column: source.indexOf('double') + 1,
      });
      assert('symbol' in refreshed && refreshed.symbol);
      assertNotEquals(
        refreshed.snapshot.dirty_hash,
        result.snapshot.dirty_hash,
      );
      assert(
        refreshed.symbol.definitions.some(
          location => location.name === 'triple',
        ),
      );
      const externalType = await inspectGraph(root, {
        choice: 'symbol',
        file: 'src/types.ts',
        line: 1,
        column: 'export type Stats = Deno.FileInfo;'.indexOf('FileInfo') + 1,
      });
      assert('symbol' in externalType && externalType.symbol);
      assertEquals(externalType.symbol.status, 'UNRESOLVED');
      assertEquals(externalType.symbol.definitions, []);
    },
  );
});

test('workflow graph: mutations while reading symbol sources invalidate the report', async () => {
  const source = 'export function value() { return 1; }';
  await repository(
    {'src/value.ts': source, 'src/marker.ts': 'export const marker = 1;'},
    async root => {
      const read = Deno.readTextFile;
      let changed = false;
      try {
        Deno.readTextFile = async (path, options) => {
          const text = await read(path, options);
          if (!changed && path === join(root, 'src/value.ts')) {
            changed = true;
            await Deno.writeTextFile(
              join(root, 'src/marker.ts'),
              'export const marker = 2;',
            );
          }
          return text;
        };
        await assertRejects(
          () =>
            inspectGraph(root, {
              choice: 'symbol',
              file: 'src/value.ts',
              line: 1,
              column: source.indexOf('value') + 1,
            }),
          Error,
          'Working tree changed during graph analysis',
        );
        assert(changed);
      } finally {
        Deno.readTextFile = read;
      }
    },
  );
});

test('workflow graph CLI: valid queries succeed while bad input and policy violations exit one', async () => {
  await repository({'src/value.ts': 'export const value = 1;'}, async root => {
    const menu = await cli(root);
    assertEquals(menu.code, 0, new TextDecoder().decode(menu.stderr));
    const choices = JSON.parse(new TextDecoder().decode(menu.stdout)) as {
      graph_commands: {choice: string}[];
    };
    assertEquals(choices.graph_commands.map(item => item.choice).sort(), [
      'impact',
      'policy',
      'symbol',
    ]);
    const valid = await cli(
      root,
      '--graph',
      'impact',
      '--file',
      'src/value.ts',
    );
    assertEquals(valid.code, 0, new TextDecoder().decode(valid.stderr));
    const output = JSON.parse(new TextDecoder().decode(valid.stdout)) as {
      graph: {choice: string};
    };
    assertEquals(output.graph.choice, 'impact');
    const invalid = await cli(
      root,
      '--graph',
      'symbol',
      '--file',
      'src/value.ts',
      '--line',
      '0',
      '--column',
      '1',
    );
    assertEquals(invalid.code, 2);
    await Deno.writeTextFile(
      join(root, 'src/value.ts'),
      "export {absent} from './absent.ts';",
    );
    const failed = await cli(root, '--graph', 'policy');
    assertEquals(failed.code, 1, new TextDecoder().decode(failed.stderr));
    const failedOutput = JSON.parse(new TextDecoder().decode(failed.stderr))
      .details as {graph: {policy: {status: string}}};
    assertEquals(failedOutput.graph.policy.status, 'FAIL');
  });
});
