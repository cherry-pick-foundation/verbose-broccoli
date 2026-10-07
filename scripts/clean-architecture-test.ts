import {spawnSync} from 'node:child_process';
import {
  mkdir,
  mkdtemp,
  readFile,
  rm,
  symlink,
  writeFile,
} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {test} from 'node:test';
import {assert, assertEquals} from '@std/assert';
import {join} from '@std/path';
import {dependencyCruiser} from './workflow-depcruise.ts';

const repository = process.cwd();
const depcruise = join(repository, 'node_modules/.bin/depcruise');
const configPath = join(repository, '.config/dependency-cruiser.json');

async function fixture(files: Record<string, string>) {
  const root = await mkdtemp(join(tmpdir(), 'clean-architecture-'));
  for (const dir of ['packages', 'plugins', 'scripts', 'skills'])
    await mkdir(join(root, dir));
  for (const [path, source] of Object.entries(files)) {
    const target = join(root, path);
    await mkdir(join(target, '..'), {recursive: true});
    await writeFile(target, source);
  }
  return root;
}

function check(root: string) {
  const result = spawnSync(
    depcruise,
    [
      '--config',
      configPath,
      '--no-cache',
      '--no-progress',
      '--output-type',
      'err',
      'packages',
      'plugins',
      'scripts',
      'skills',
    ],
    {
      cwd: root,
      env: {...process.env, GIT_OPTIONAL_LOCKS: '0'},
      encoding: 'utf8',
    },
  );
  if (result.error) throw result.error;
  return {status: result.status, output: result.stdout + result.stderr};
}

const cases: [string, Record<string, string>][] = [
  [
    'no-cycles',
    {'scripts/a.ts': "import './b.ts';", 'scripts/b.ts': "import './a.ts';"},
  ],
  [
    'no-feature-internals',
    {
      'packages/demo/features/one/index.ts':
        "import '../two/internal/value.ts';",
      'packages/demo/features/two/internal/value.ts': 'export const value = 1;',
    },
  ],
  [
    'no-package-to-skill-internals',
    {
      'packages/demo/index.ts': "import '../../skills/code/private.ts';",
      'skills/code/private.ts': 'export const value = 1;',
    },
  ],
  [
    'clean-code-cli-importers',
    {
      'packages/demo/index.ts':
        "import '../../skills/code/clean-code/scripts/cli.ts';",
      'skills/code/clean-code/scripts/cli.ts': 'export const value = 1;',
    },
  ],
  [
    'no-cross-package-local-imports',
    {
      'packages/one/index.ts': "import '../two/index.ts';",
      'packages/two/index.ts': 'export const value = 1;',
    },
  ],
  [
    'no-unresolved-local-imports',
    {'scripts/index.ts': "import './missing.ts';"},
  ],
];
for (const [inner, outers] of Object.entries({
  domain: [
    'application/value.ts',
    'adapters/value.ts',
    'entrypoints/value.ts',
    'bootstrap.ts',
  ],
  application: ['adapters/value.ts', 'entrypoints/value.ts', 'bootstrap.ts'],
  adapters: ['entrypoints/value.ts', 'bootstrap.ts'],
  bootstrap: ['entrypoints/value.ts'],
})) {
  for (const outer of outers) {
    const source = inner === 'bootstrap' ? 'bootstrap.ts' : `${inner}/value.ts`;
    cases.push([
      `${inner}-dependency-direction`,
      {
        [`packages/demo/src/${source}`]: `import '${inner === 'bootstrap' ? './' : '../'}${outer}';`,
        [`packages/demo/src/${outer}`]: 'export const value = 1;',
      },
    ]);
  }
}
for (const inner of ['domain', 'application']) {
  cases.push([
    'no-node-in-inner-layers',
    {
      [`packages/demo/src/${inner}/value.ts`]: "import 'node:fs';",
    },
  ]);
  cases.push([
    'no-io-packages-in-inner-layers',
    {
      [`packages/demo/src/${inner}/value.ts`]:
        "import 'npm:@electric-sql/pglite@0.5.0';",
    },
  ]);
}
const publicPaths = [
  'skills/chat',
  'skills/code',
  'plugins/work',
  'packages/credit-offers',
  'packages/doc-regions',
  'packages/education-privacy-gate',
  'packages/jev-ultrafast',
  'packages/wiki-consistency',
];
for (const path of publicPaths)
  cases.push([
    `public-api:${path}`,
    {
      'scripts/index.ts': `import '../${path}/private.ts';`,
      [`${path}/private.ts`]: 'export const value = 1;',
    },
  ]);

void test('D1–D6: every dependency-cruiser rule fails on its breaking fixture', async t => {
  const config = JSON.parse(await readFile(configPath, 'utf8')) as {
    forbidden: {name: string; severity: string}[];
  };
  for (const rule of config.forbidden) {
    assertEquals(rule.severity, 'error', rule.name);
    assert(
      cases.some(([name]) => name === rule.name),
      rule.name,
    );
  }
  for (const [name, files] of cases)
    await t.test(`${name}: ${Object.keys(files)[0]}`, async () => {
      const root = await fixture(files);
      try {
        const result = check(root);
        console.log(result.output);
        assert(result.status !== null && result.status > 0, result.output);
        assert(result.output.includes(name), result.output);
      } finally {
        await rm(root, {recursive: true});
      }
    });
});

void test('D6: by-name workspace imports resolve to source and keep the workflow CLI edge', async () => {
  const root = await fixture({
    'package.json': '{"workspaces":["packages/*","skills/code/clean-code"]}',
    'packages/workflow/package.json':
      '{"name":"workflow","type":"module","dependencies":{"clean-code-skill":"*","fixture-values":"*"}}',
    'packages/workflow/src/index.ts':
      "import 'clean-code-skill/cli'; import 'fixture-values'; import './value.ts';",
    'scripts/index.ts': "import 'clean-code-skill/cli';",
    'packages/workflow/src/value.ts': 'export const value = 1;',
    'packages/values/package.json':
      '{"name":"fixture-values","type":"module","exports":{".":"./index.ts"}}',
    'packages/values/index.ts': 'export const value = 1;',
    'skills/code/clean-code/package.json':
      '{"name":"clean-code-skill","type":"module","exports":{"./cli":"./scripts/cli.ts","./private":null}}',
    'skills/code/clean-code/scripts/cli.ts': 'export const value = 1;',
  });
  try {
    await mkdir(join(root, 'node_modules'));
    await symlink(
      '../skills/code/clean-code',
      join(root, 'node_modules/clean-code-skill'),
    );
    await symlink(
      '../packages/values',
      join(root, 'node_modules/fixture-values'),
    );
    const graph = await dependencyCruiser(root, {policy: true});
    const packageImport = graph.modules
      .find(item => item.source === 'packages/workflow/src/index.ts')
      ?.dependencies.find(item => item.module === 'fixture-values');
    assertEquals(packageImport?.resolved, 'packages/values/index.ts');
    assert(!packageImport?.dependencyTypes.includes('local'));
    console.log(JSON.stringify(packageImport));
    const dependency = graph.modules
      .find(item => item.source === 'packages/workflow/src/index.ts')
      ?.dependencies.find(item => item.module === 'clean-code-skill/cli');
    assertEquals(dependency?.resolved, 'skills/code/clean-code/scripts/cli.ts');
    console.log(JSON.stringify(dependency));
    assert(dependency?.dependencyTypes.includes('undetermined'));
    assert(!dependency?.dependencyTypes.includes('local'));
    const rootImport = graph.modules
      .find(item => item.source === 'scripts/index.ts')
      ?.dependencies.find(item => item.module === 'clean-code-skill/cli');
    assert(rootImport?.dependencyTypes.includes('aliased-workspace'));
    console.log(JSON.stringify(rootImport));
    const result = check(root);
    console.log(JSON.stringify(dependency), result.output);
    assertEquals(result.status, 0, result.output);
    await writeFile(
      join(root, 'packages/workflow/src/index.ts'),
      "import 'clean-code-skill/private';",
    );
    const privateImport = check(root);
    console.log(privateImport.output);
    assertEquals(privateImport.status, 1, privateImport.output);
    assert(privateImport.output.includes('no-unresolved-local-imports'));
  } finally {
    await rm(root, {recursive: true});
  }
});

void test('D2: ESLint rejects domain I/O globals and accepts plain values', async () => {
  const root = await fixture({
    'eslint.config.js': await readFile(
      join(repository, 'eslint.config.js'),
      'utf8',
    ),
    'tsconfig.json':
      '{"compilerOptions":{"module":"ESNext","moduleResolution":"Bundler","target":"ESNext"},"include":["**/*.ts"]}',
    'packages/demo/domain/value.ts': 'export const value = process.env;\n',
  });
  try {
    await symlink(join(repository, 'node_modules'), join(root, 'node_modules'));
    const lint = () =>
      spawnSync(
        'env',
        [
          '-u',
          'NODE_OPTIONS',
          process.execPath,
          join(repository, 'node_modules/eslint/bin/eslint.js'),
          'packages/demo/domain/value.ts',
        ],
        {cwd: root, encoding: 'utf8'},
      );
    const broken = lint();
    console.log(broken.stdout + broken.stderr);
    assertEquals(broken.status, 1, broken.stdout + broken.stderr);
    assert(broken.stdout.includes('no-restricted-globals'));
    await writeFile(
      join(root, 'packages/demo/domain/value.ts'),
      'export const value = 1;\n',
    );
    const allowed = lint();
    console.log(allowed.stdout + allowed.stderr);
    assertEquals(allowed.status, 0, allowed.stdout + allowed.stderr);
  } finally {
    await rm(root, {recursive: true});
  }
});
