import {spawnSync} from 'node:child_process';
import {test} from 'node:test';
import {rejects} from 'node:assert/strict';
import {assert, assertEquals} from '@std/assert';
import {fromFileUrl, join} from '@std/path';
import {
  cp,
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  realpath,
  rm,
} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {tmpdir} from 'node:os';

const ROOT = fromFileUrl(new URL('../', import.meta.url));

test('plugin skills: no project links duplicate packaged skills', async () => {
  for (const path of ['.agents/skills', '.claude/skills']) {
    await rejects(lstat(join(ROOT, path)), {code: 'ENOENT'});
  }
  assertEquals(
    await realpath(join(ROOT, '.agents/ponytail')),
    join(ROOT, 'plugins/code'),
  );
});

test('plugin skills: isolated packages retain resources and executable helpers', async () => {
  for (const pluginDirectory of ['code', 'work', 'chat']) {
    const temp = await mkdtemp(join(tmpdir(), 'plugin-skills-'));
    try {
      const source = join(ROOT, 'plugins', pluginDirectory);
      const target = join(temp, pluginDirectory);
      await mkdir(target);
      await cp(join(source, 'plugin.json'), join(target, 'plugin.json'));
      const manifest = JSON.parse(
        await readFile(join(target, 'plugin.json'), 'utf8'),
      );
      assertEquals(manifest.name, pluginDirectory);
      assertEquals(manifest.version, '0.1.0');
      if (pluginDirectory !== 'chat') {
        await cp(join(source, 'mcp.json'), join(target, 'mcp.json'));
        const mcp = JSON.parse(
          await readFile(join(target, 'mcp.json'), 'utf8'),
        );
        assertEquals(Object.keys(mcp.mcpServers), ['backfire']);
      }
      for (const component of ['skills', 'hooks', 'tests']) {
        if (!existsSync(join(source, component))) continue;
        for (const entry of await readdir(join(source, component), {
          recursive: true,
          withFileTypes: true,
        })) {
          assert(
            !entry.isSymbolicLink(),
            `Packaged resource must be local: ${join(entry.parentPath, entry.name)}`,
          );
        }
        await cp(join(source, component), join(target, component), {
          recursive: true,
        });
      }
      if (pluginDirectory !== 'code') continue;
      for (const args of [
        [`${pluginDirectory}/tests/hooks.test.js`],
        [
          '-e',
          `require('assert').match(require('./${pluginDirectory}/hooks/ponytail-instructions').getPonytailInstructions('full'), /## Intensity/)`,
        ],
      ]) {
        const result = spawnSync(process.execPath, args, {
          cwd: temp,
          env: {...process.env, XDG_CONFIG_HOME: join(temp, 'config')},
          encoding: null,
        });
        if (result.error) throw result.error;
        assertEquals(result.status, 0, new TextDecoder().decode(result.stderr));
      }
    } finally {
      await rm(temp, {recursive: true});
    }
  }
});

test('plugin skills: work Backfire shares code tool reference and license', async () => {
  for (const path of ['reference/tools.md', 'LICENSE']) {
    assertEquals(
      await readFile(join(ROOT, 'plugins/work/skills/backfire', path), 'utf8'),
      await readFile(join(ROOT, 'plugins/code/skills/backfire', path), 'utf8'),
    );
  }
});
