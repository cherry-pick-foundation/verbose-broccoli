import {spawnSync} from 'node:child_process';
import {test} from 'node:test';
import {assert, assertThrows} from '@std/assert';
import {dirname, fromFileUrl, join} from '@std/path';
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
  return {
    code: result.status ?? 1,
    success: result.status === 0,
    stdout: result.stdout ?? Buffer.alloc(0),
    stderr: result.stderr ?? Buffer.alloc(0),
  };
}

test('architecture: dependency directions, cycles, public APIs and Deno aliases', async () => {
  const cwd = Deno.cwd();
  const root = await Deno.makeTempDir({prefix: 'architecture-'});
  const files = {
    'package.json': JSON.stringify({dependencies: {}}),
    'plugins/a/deno.json': JSON.stringify({
      imports: {
        '@platform': './src/infrastructure/db.ts',
        '@database': 'npm:@electric-sql/pglite@0.5.8',
        '@safe': 'npm:@jsr/std__assert@1.0.19',
        '@sdk': 'npm:@modelcontextprotocol/sdk@1.30.0',
        '@file': 'npm:ajv@8.20.0/dist/2020.js',
      },
    }),
    'plugins/b/deno.json': '{}',
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
    'packages/shared/deno.json': JSON.stringify({
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
      await Deno.mkdir(join(file, '..'), {recursive: true});
      await Deno.writeTextFile(file, source);
    }
    Deno.chdir(root);
    const result = await analyzeImportGraph();
    const violations = result.summary.violations;
    for (const [from, rule] of [
      ['plugins/a/src/domain/outer.ts', 'domain-dependency-direction'],
      ['plugins/a/src/domain/type-only.ts', 'domain-dependency-direction'],
      ['plugins/a/src/domain/alias.ts', 'domain-dependency-direction'],
      ['plugins/a/src/domain/io.ts', 'no-io-packages-in-inner-layers'],
      ['plugins/a/src/domain/sdk.ts', 'no-io-packages-in-inner-layers'],
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
    Deno.chdir(cwd);
    await Deno.remove(root, {recursive: true});
  }
});

test('architecture: unsupported scoped imports fail instead of skipping edges', async () => {
  const root = await Deno.makeTempDir({prefix: 'architecture-scopes-'});
  try {
    await Deno.mkdir(join(root, 'plugins/a'), {recursive: true});
    await Deno.writeTextFile(join(root, 'package.json'), '{}');
    await Deno.writeTextFile(
      join(root, 'plugins/a/deno.json'),
      JSON.stringify({scopes: {}}),
    );
    assertThrows(() => importRules(root), Error, 'scoped aliases');
  } finally {
    await Deno.remove(root, {recursive: true});
  }
});

test('architecture: domain runtime APIs, aliases, globalThis and valid local bindings', async () => {
  const root = await Deno.makeTempDir({prefix: 'architecture-domain-'});
  const invalid = [
    "Deno.env.get('KEY');",
    'const {env} = Deno;',
    "globalThis.Deno.env.get('KEY');",
    "globalThis['Deno'].env.get('KEY');",
    "fetch('https://example.com');",
    "const value = new Request('https://example.com');",
    'export const environment = process.env;',
  ].map((source, index) => [`plugins/demo${index}/domain/value.ts`, source]);
  const valid = [
    [
      'packages/shared/domain/value.ts',
      'export function value(Deno) { return Deno; }',
    ],
    ['plugins/demo/infrastructure/value.ts', "Deno.env.get('KEY');"],
  ];
  try {
    await Deno.copyFile(
      join(repository, 'biome.json'),
      join(root, 'biome.json'),
    );
    for (const [path, source] of [...invalid, ...valid]) {
      await Deno.mkdir(dirname(join(root, path)), {recursive: true});
      await Deno.writeTextFile(join(root, path), source);
    }
    const output = commandOutput(join(repository, 'node_modules/.bin/biome'), {
      args: ['lint', '--vcs-enabled=false', '--reporter=json', '.'],
      cwd: root,
    });
    const report = JSON.parse(new TextDecoder().decode(output.stdout)) as {
      diagnostics: {category: string; location: {path: string}}[];
    };
    const flagged = new Set(
      report.diagnostics
        .filter(item => item.category === 'lint/style/noRestrictedGlobals')
        .map(item => item.location.path),
    );
    for (const [path, source] of invalid) assert(flagged.has(path), source);
    for (const [path] of valid) assert(!flagged.has(path), path);
  } finally {
    await Deno.remove(root, {recursive: true});
  }
});

test('architecture: local and external alias conflicts cannot hide dependencies', async () => {
  const root = await Deno.makeTempDir({prefix: 'architecture-alias-'});
  try {
    await Deno.mkdir(join(root, 'plugins/a'), {recursive: true});
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
      await Deno.writeTextFile(
        join(root, 'package.json'),
        JSON.stringify({dependencies: rootImports}),
      );
      await Deno.writeTextFile(
        join(root, 'plugins/a/deno.json'),
        JSON.stringify({imports: memberImports}),
      );
      assertThrows(() => importRules(root), Error, 'scoped resolver support');
    }
    await Deno.writeTextFile(
      join(root, 'package.json'),
      JSON.stringify({
        dependencies: {
          '@sdk': 'npm:@modelcontextprotocol/sdk@1.30.0',
          '@file': 'npm:ajv@8.20.0/dist/2020.js',
        },
      }),
    );
    await Deno.writeTextFile(
      join(root, 'plugins/a/deno.json'),
      JSON.stringify({
        imports: {
          '@sdk-other': './absent.ts',
          '@file/internal': './absent.ts',
        },
      }),
    );
    assert(importRules(root));
  } finally {
    await Deno.remove(root, {recursive: true});
  }
});
