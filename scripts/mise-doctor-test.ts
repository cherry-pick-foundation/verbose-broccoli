import {spawnSync} from 'node:child_process';
import {copyFileSync, mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import assert from 'node:assert/strict';
import {test} from 'node:test';

void test('mise doctor reports failing project checks', () => {
  const project = mkdtempSync(join(tmpdir(), 'mise-doctor-'));
  try {
    copyFileSync(
      new URL('../mise.toml', import.meta.url),
      join(project, 'mise.toml'),
    );
    const result = spawnSync('mise', ['doctor', 'project'], {
      cwd: project,
      env: {...process.env, MISE_TRUSTED_CONFIG_PATHS: project},
      encoding: 'utf8',
      timeout: 90000,
    });
    const output = `${result.stdout ?? ''}\n${result.stderr ?? ''}`;
    assert.equal(result.error, undefined, result.error?.message);
    assert.ok(result.status !== null && result.status !== 0, output);
    assert.ok(
      output
        .split(/\r?\n/)
        .some(line => /\bFAIL\b/.test(line) && line.includes('uv-workspace')),
      output,
    );
  } finally {
    rmSync(project, {recursive: true, force: true});
  }
});
