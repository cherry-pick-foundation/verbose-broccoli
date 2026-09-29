import {spawnSync} from 'node:child_process';
import {copyFile, mkdir, mkdtemp, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {test} from 'node:test';
import {assert, assertThrows} from '@std/assert';
import {dirname, fromFileUrl, join, relative} from '@std/path';
import {analyzeImportGraph, importRules} from './clean_architecture.ts';

const repository = fromFileUrl(new URL('../', import.meta.url));

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
    throw new Error(`Child process terminated by signal ${result.signal}`);
  return {
    code: result.status ?? 1,
    success: result.status === 0,
    stdout: result.stdout ?? Buffer.alloc(0),
    stderr: result.stderr ?? Buffer.alloc(0),
  };
}

void test('architecture: command helper rejects signal termination', () => {
  assertThrows(
    () =>
      commandOutput(process.execPath, {
        args: ['-e', "process.kill(process.pid, 'SIGKILL')"],
      }),
    Error,
    'SIGKILL',
  );
});

void test('architecture: dependency directions, cycles, public APIs and package aliases', async () => {
  const cwd = process.cwd();
  const root = await mkdtemp(join(tmpdir(), 'architecture-'));
  const files = {
    'package.json': JSON.stringify({
      dependencies: {'@electric-sql/pglite': '0.0.0'},
    }),
    'node_modules/@electric-sql/pglite/package.json': JSON.stringify({
      name: '@electric-sql/pglite',
      exports: './index.js',
    }),
    'node_modules/@electric-sql/pglite/index.js': 'export const PGlite = 1;',
    'plugins/a/package.json': JSON.stringify({
      imports: {
        '@platform': './src/infrastructure/db.ts',
        '@database': 'npm:@electric-sql/pglite@0.5.8',
        '@safe': 'npm:@jsr/std__assert@1.0.19',
        '@sdk': 'npm:@modelcontextprotocol/sdk@1.30.0',
        '@file': 'npm:ajv@8.20.0/dist/2020.js',
      },
    }),
    'plugins/b/package.json': '{}',
    'plugins/a/src/domain/outer.ts':
      "export {value} from '../infrastructure/db.ts';",
    'plugins/a/src/domain/type-only.ts':
      "import type {DB} from '../infrastructure/db.ts'; export type Id = DB;",
    'plugins/a/src/domain/alias.ts': "export {value} from '@platform';",
    'plugins/a/src/domain/io.ts': "export {PGlite} from '@database';",
    'plugins/a/src/domain/allowed.ts': "export {assert} from '@safe';",
    'plugins/a/src/domain/value.ts': 'export const value = 1;',
    'plugins/a/src/domain/sdk.ts':
      "export {Server} from '@sdk/server/index.js';",
    'plugins/a/src/domain/installed.ts':
      "export {PGlite} from '@electric-sql/pglite';",
    'plugins/a/src/infrastructure/sdk.ts':
      "export {Server} from '@sdk/server/index.js';",
    'scripts/file-subpath.ts': "export {value} from '@file/missing.js';",
    'scripts/prefix.ts': "export {value} from '@sdk-other/missing.js';",
    'plugins/a/src/application/outer.ts':
      "export {value} from '../infrastructure/db.ts';",
    'plugins/a/src/application/allowed.ts':
      "export {value} from '../domain/value.ts';",
    'plugins/a/src/infrastructure/db.ts':
      'export const value = 1; export type DB = number;',
    'plugins/a/src/infrastructure/allowed.ts':
      "export {value} from '../application/allowed.ts';",
    'plugins/a/src/modules/one/outer.ts':
      "export {value} from '../two/internal/data.ts';",
    'plugins/a/src/modules/two/internal/data.ts': 'export const value = 1;',
    'plugins/a/src/modules/two/allowed.ts':
      "export {value} from './internal/data.ts';",
    'plugins/a/src/cycles/a.ts':
      "export {b} from './b.ts'; export const a = 1;",
    'plugins/a/src/cycles/b.ts':
      "export {a} from './a.ts'; export const b = 1;",
    'packages/undeclared/internal/value.ts': 'export const value = 1;',
    'plugins/a/src/undeclared.ts':
      "export {value} from '../../../packages/undeclared/internal/value.ts';",
    'packages/shared/package.json': JSON.stringify({
      name: '@demo/shared',
      exports: './src/mod.ts',
    }),
    'packages/shared/src/mod.ts': "export {value} from './internal/impl.ts';",
    'packages/shared/src/internal/impl.ts': 'export const value = 1;',
    'plugins/a/src/public.ts': "export {value} from '@demo/shared';",
    'plugins/a/src/private.ts':
      "export {value} from '../../../packages/shared/src/internal/impl.ts';",
    'plugins/b/src/cross.ts':
      "export {value} from '../../a/src/domain/value.ts';",
    'scripts/missing.ts': "export {value} from './not-here.ts';",
    'tests/a.ts': "export {b} from './b.ts'; export const a = 1;",
    'tests/b.ts': "export {a} from './a.ts'; export const b = 1;",
  };
  try {
    for (const [path, source] of Object.entries(files)) {
      const file = join(root, path);
      await mkdir(join(file, '..'), {recursive: true});
      await writeFile(file, source);
    }
    process.chdir(root);
    const result = await analyzeImportGraph();
    const violations = result.summary.violations;
    const ioRule = importRules(root).forbidden?.find(
      rule => rule.name === 'no-io-packages-in-inner-layers',
    );
    assert(ioRule && 'to' in ioRule);
    const ioPaths = ioRule.to?.path;
    assert(ioPaths);
    assert(
      (Array.isArray(ioPaths) ? ioPaths : [ioPaths]).some(path =>
        new RegExp(path).test('node_modules/@electric-sql/pglite/index.js'),
      ),
    );
    for (const [from, rule] of [
      ['plugins/a/src/domain/outer.ts', 'domain-dependency-direction'],
      ['plugins/a/src/domain/type-only.ts', 'domain-dependency-direction'],
      ['plugins/a/src/domain/alias.ts', 'domain-dependency-direction'],
      ['plugins/a/src/domain/io.ts', 'no-io-packages-in-inner-layers'],
      ['plugins/a/src/domain/sdk.ts', 'no-io-packages-in-inner-layers'],
      ['plugins/a/src/domain/installed.ts', 'no-io-packages-in-inner-layers'],
      ['scripts/file-subpath.ts', 'no-unresolved-local-imports'],
      ['scripts/prefix.ts', 'no-unresolved-local-imports'],
      [
        'plugins/a/src/application/outer.ts',
        'application-dependency-direction',
      ],
      ['plugins/a/src/modules/one/outer.ts', 'no-feature-internals'],
      ['plugins/a/src/cycles/a.ts', 'no-cycles'],
      ['plugins/a/src/private.ts', 'public-api:packages/shared'],
      ['plugins/a/src/undeclared.ts', 'public-api:packages/undeclared'],
      ['plugins/b/src/cross.ts', 'public-api:plugins/a'],
      ['scripts/missing.ts', 'no-unresolved-local-imports'],
      ['tests/a.ts', 'no-cycles'],
    ]) {
      assert(
        violations.some(item => item.from === from && item.rule.name === rule),
        `${from}: ${rule}\n${JSON.stringify(violations)}`,
      );
    }
    const selectedEntryResult = await analyzeImportGraph(root, [
      'plugins/a/src/domain/installed.ts',
    ]);
    assert(
      selectedEntryResult.summary.violations.some(
        item =>
          item.from === 'plugins/a/src/domain/installed.ts' &&
          item.rule.name === 'no-io-packages-in-inner-layers',
      ),
    );
    for (const from of [
      'plugins/a/src/domain/allowed.ts',
      'plugins/a/src/application/allowed.ts',
      'plugins/a/src/infrastructure/allowed.ts',
      'plugins/a/src/infrastructure/sdk.ts',
      'plugins/a/src/modules/two/allowed.ts',
      'plugins/a/src/public.ts',
      'packages/shared/src/mod.ts',
    ])
      assert(!violations.some(item => item.from === from), from);
    assert(result.summary.totalCruised >= 20);
  } finally {
    process.chdir(cwd);
    await rm(root, {recursive: true});
  }
});

void test('architecture: package exports cannot escape their plugin root', async () => {
  const root = await mkdtemp(join(tmpdir(), 'architecture-package-'));
  try {
    await mkdir(join(root, 'plugins/a'), {recursive: true});
    await writeFile(join(root, 'package.json'), '{}');
    await writeFile(
      join(root, 'plugins/a/package.json'),
      JSON.stringify({name: '@demo/a', exports: '../../outside.ts'}),
    );
    assertThrows(
      () => importRules(root),
      Error,
      'Public exports must stay inside',
    );
  } finally {
    await rm(root, {recursive: true});
  }
});

void test('architecture: domain runtime APIs, aliases, globalThis and valid local bindings', async () => {
  const root = await mkdtemp(join(tmpdir(), 'architecture-domain-'));
  const invalid = [
    "process.env.get('KEY');",
    'const {env} = process;',
    "globalThis.process.env.get('KEY');",
    "globalThis['process'].env.get('KEY');",
    "fetch('https://example.com');",
    "const value = new Request('https://example.com');",
    'export const environment = process.env;',
  ].map((source, index) => [`plugins/demo${index}/domain/value.ts`, source]);
  const valid = [
    [
      'packages/shared/domain/value.ts',
      'export function value(process) { return process; }',
    ],
    ['plugins/demo/infrastructure/value.ts', "process.env.get('KEY');"],
  ];
  try {
    for (const config of [
      'eslint.config.js',
      'eslint.ignores.js',
      '.prettierrc.js',
    ])
      await copyFile(join(repository, config), join(root, config));
    await writeFile(
      join(root, 'tsconfig.json'),
      JSON.stringify({
        compilerOptions: {
          module: 'ESNext',
          moduleResolution: 'Bundler',
          target: 'ESNext',
          types: ['node'],
        },
        include: ['**/*.ts'],
      }),
    );
    for (const [path, source] of [...invalid, ...valid]) {
      await mkdir(dirname(join(root, path)), {recursive: true});
      await writeFile(join(root, path), source);
    }
    const result = commandOutput(join(repository, 'node_modules/.bin/eslint'), {
      args: [
        '--format=json',
        ...[...invalid, ...valid].map(([path]) => String(path)),
      ],
      cwd: root,
      env: {
        NODE_PATH: join(repository, 'node_modules'),
      },
    });
    assert(!result.success, new TextDecoder().decode(result.stderr));
    const stdout = new TextDecoder().decode(result.stdout);
    assert(stdout, new TextDecoder().decode(result.stderr));
    const report = JSON.parse(stdout) as {
      filePath: string;
      messages: {ruleId: string | null; message: string}[];
    }[];
    const diagnostics = report.flatMap(item =>
      item.messages
        .filter(message => message.ruleId === 'no-restricted-globals')
        .map(message => ({
          path: relative(root, item.filePath),
          message: message.message,
        })),
    );
    const flagged = new Set(diagnostics.map(item => item.path));
    for (const [path, source] of invalid) assert(flagged.has(path), source);
    for (const [path] of valid) assert(!flagged.has(path), path);
    assert(
      diagnostics.some(item =>
        item.message.includes(
          'Domain code must not use runtime or I/O globals.',
        ),
      ),
    );
    assert(
      diagnostics.some(item =>
        item.message.includes(
          'Domain code must not reach globals through the global object.',
        ),
      ),
    );
  } finally {
    await rm(root, {recursive: true});
  }
});

void test('architecture: local and external alias conflicts cannot hide dependencies', async () => {
  const root = await mkdtemp(join(tmpdir(), 'architecture-alias-'));
  try {
    await mkdir(join(root, 'plugins/a'), {recursive: true});
    for (const [rootImports, memberImports] of [
      [{shared: 'npm:typescript@6.0.3'}, {shared: './private.ts'}],
      [
        {'@sdk': 'npm:@modelcontextprotocol/sdk@1.30.0'},
        {'@sdk/internal': './absent.ts'},
      ],
      [
        {
          '@sdk/internal':
            'npm:@modelcontextprotocol/sdk@1.30.0/server/index.js',
        },
        {'@sdk/internal': './absent.ts'},
      ],
      [
        {'@sdk/': 'npm:@modelcontextprotocol/sdk@1.30.0/'},
        {'@sdk/internal': './absent.ts'},
      ],
      [
        {
          '@sdk/internal':
            'npm:@modelcontextprotocol/sdk@1.30.0/server/index.js',
        },
        {'@sdk/': './local/'},
      ],
    ]) {
      await writeFile(
        join(root, 'package.json'),
        JSON.stringify({dependencies: rootImports}),
      );
      await writeFile(
        join(root, 'plugins/a/package.json'),
        JSON.stringify({imports: memberImports}),
      );
      assertThrows(() => importRules(root), Error, 'scoped resolver support');
    }
    await writeFile(
      join(root, 'package.json'),
      JSON.stringify({
        dependencies: {
          '@sdk': 'npm:@modelcontextprotocol/sdk@1.30.0',
          '@file': 'npm:ajv@8.20.0/dist/2020.js',
        },
      }),
    );
    await writeFile(
      join(root, 'plugins/a/package.json'),
      JSON.stringify({
        imports: {
          '@sdk-other': './absent.ts',
          '@file/internal': './absent.ts',
        },
      }),
    );
    assert(importRules(root));
  } finally {
    await rm(root, {recursive: true});
  }
});
