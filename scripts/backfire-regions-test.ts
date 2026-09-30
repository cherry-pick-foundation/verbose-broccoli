import {test} from 'node:test';
import {assert} from '@std/assert';
import {spawnSync} from 'node:child_process';
import {copyFileSync, mkdtempSync, readFileSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

const script = 'scripts/backfire-regions.ts';
const committed = 'packages/backfire/src/backfire_education/regions.json';

function run(...args: string[]) {
  return spawnSync(
    process.execPath,
    ['--disable-warning=MODULE_TYPELESS_PACKAGE_JSON', script, ...args],
    {encoding: 'utf8'},
  );
}

void test('the region drift check passes on the committed list', () => {
  assert(run('--check').status === 0);
});

void test('the region drift check fails on an edited list and writes nothing', () => {
  const copy = join(mkdtempSync(join(tmpdir(), 'regions-')), 'regions.json');
  copyFileSync(committed, copy);
  const edited = readFileSync(copy, 'utf8').replace('"Andong",', '"Andonx",');
  writeFileSync(copy, edited);
  const result = run('--check', copy);
  assert(result.status === 1, result.stderr);
  assert(readFileSync(copy, 'utf8') === edited);
});

void test('generating rewrites an edited list to the committed one', () => {
  const copy = join(mkdtempSync(join(tmpdir(), 'regions-')), 'regions.json');
  writeFileSync(copy, '[]\n');
  assert(run(copy).status === 0);
  assert(readFileSync(copy, 'utf8') === readFileSync(committed, 'utf8'));
});
