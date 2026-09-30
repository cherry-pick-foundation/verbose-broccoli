import {spawnSync} from 'node:child_process';
import {mkdtemp, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {test} from 'node:test';

const root = fileURLToPath(new URL('../', import.meta.url));

function run(command: string, args: string[]) {
  const result = spawnSync(command, args, {cwd: root, encoding: 'utf8'});
  if (result.error) throw result.error;
  if (result.signal)
    throw new Error(`${command} terminated by signal ${result.signal}`);
  return result;
}

void test('plugins:validate accepts all real plugin and MCP manifests', () => {
  const result = run('npm', ['run', '--silent', 'plugins:validate']);
  assert.equal(result.status, 0, result.stderr);
});

void test('check-jsonschema rejects a synthetic invalid plugin manifest', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'plugin-schema-'));
  const manifest = join(directory, 'invalid-plugin.json');
  try {
    await writeFile(manifest, '{}\n');
    const result = run('uv', [
      'run',
      '--project',
      'tools/check-jsonschema',
      '--frozen',
      '--offline',
      '--no-sync',
      'check-jsonschema',
      '--no-cache',
      '--schemafile',
      'scripts/vendor/agent-plugins/plugin.schema.json',
      manifest,
    ]);
    const output = `${result.stdout}\n${result.stderr}`;
    assert.notEqual(result.status, 0, output);
    assert.match(output, /invalid-plugin\.json/);
    assert.match(output, /required|schema|valid/i);
  } finally {
    await rm(directory, {recursive: true, force: true});
  }
});
