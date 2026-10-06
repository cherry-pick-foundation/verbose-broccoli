import {spawnSync} from 'node:child_process';
import {mkdir, mkdtemp, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {test} from 'node:test';
import {assert} from '@std/assert';
import {join} from '@std/path';
import {dependencyCruiser} from './workflow-depcruise.ts';

const repository = process.cwd();
const depcruise = join(repository, 'node_modules/.bin/depcruise');
const ruleNames = [
  'no-cycles',
  'domain-dependency-direction',
  'application-dependency-direction',
  'no-feature-internals',
  'no-package-to-plugin',
  'no-node-in-inner-layers',
  'no-unresolved-local-imports',
  'no-io-packages-in-inner-layers',
  'public-api:skills/chat',
  'public-api:skills/code',
  'public-api:plugins/work',
  'public-api:packages/doc-regions',
  'public-api:packages/education-privacy-gate',
  'public-api:packages/wiki-consistency',
];

void test('clean architecture: every configured rule fires on synthetic imports', async () => {
  const root = await mkdtemp(join(tmpdir(), 'clean-architecture-'));
  const files = {
    'package.json': '{}',
    'plugins/demo/src/domain/outer.ts':
      "export {db} from '../infrastructure/db.ts'; import 'node:fs'; import 'npm:@electric-sql/pglite@0.5.0'; import './missing.ts';",
    'plugins/demo/src/domain/value.ts':
      "export {data} from '../application/value.ts';",
    'plugins/demo/src/application/value.ts':
      "export {db} from '../infrastructure/db.ts';",
    'plugins/demo/src/infrastructure/db.ts': 'export const db = 1;',
    'plugins/demo/src/features/one/outer.ts':
      "export {data} from '../two/internal/data.ts';",
    'plugins/demo/src/features/two/internal/data.ts': 'export const data = 1;',
    'plugins/demo/src/cycles/a.ts': "export {b} from './b.ts';",
    'plugins/demo/src/cycles/b.ts': "export {a} from './a.ts';",
    'skills/chat/private.ts': 'export const chat = 1;',
    'plugins/work/private.ts': 'export const work = 1;',
    'skills/code/src/private.ts': 'export const code = 1;',
    'skills/code/clean-code/scripts/cli.ts': 'export const cli = 1;',
    'packages/doc-regions/private.ts': 'export const docRegions = 1;',
    'packages/education-privacy-gate/private.ts': 'export const gate = 1;',
    'packages/wiki-consistency/private.ts': 'export const wiki = 1;',
    'packages/doc-regions/import.ts':
      "export {code} from '../../skills/code/src/private.ts';",
    'scripts/public_chat.ts': "export {chat} from '../skills/chat/private.ts';",
    'scripts/public_code.ts':
      "export {code} from '../skills/code/src/private.ts';",
    'scripts/public_work.ts':
      "export {work} from '../plugins/work/private.ts';",
    'scripts/public_doc_regions.ts':
      "export {docRegions} from '../packages/doc-regions/private.ts';",
    'scripts/public_privacy_gate.ts':
      "export {gate} from '../packages/education-privacy-gate/private.ts';",
    'scripts/public_wiki.ts':
      "export {wiki} from '../packages/wiki-consistency/private.ts';",
    'tests/a.ts': "export {b} from './b.ts';",
    'tests/b.ts': "export {a} from './a.ts';",
  };
  try {
    for (const [path, source] of Object.entries(files)) {
      const target = join(root, path);
      await mkdir(join(target, '..'), {recursive: true});
      await writeFile(target, source);
    }
    const result = await dependencyCruiser(root, {policy: true});
    const reported = new Set(
      result.summary.violations.map(item => item.rule.name),
    );
    for (const name of ruleNames) assert(reported.has(name), name);

    const err = spawnSync(
      depcruise,
      [
        '--config',
        join(repository, '.config/dependency-cruiser.json'),
        '--no-cache',
        '--no-progress',
        '--output-type',
        'err',
        'packages',
        'plugins',
        'scripts',
        'skills',
        'tests',
      ],
      {
        cwd: root,
        env: {...process.env, GIT_OPTIONAL_LOCKS: '0'},
        encoding: 'utf8',
      },
    );
    assert(err.status !== 0, err.stdout || err.stderr);
    for (const name of ruleNames) assert(err.stdout.includes(name), name);
  } finally {
    await rm(root, {recursive: true});
  }
});
