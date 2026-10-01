import {spawnSync} from 'node:child_process';
import {test} from 'node:test';
import {rejects} from 'node:assert/strict';
import {assert, assertEquals, assertThrows} from '@std/assert';
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
  rename,
  writeFile,
  symlink,
} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {preparePluginClients} from './plugin-clients.ts';

const ROOT = fromFileUrl(new URL('../', import.meta.url));

void test('plugin skills: no project links duplicate packaged skills', async () => {
  for (const path of ['.agents/skills', '.claude/skills']) {
    await rejects(lstat(join(ROOT, path)), {code: 'ENOENT'});
  }
  assertEquals(
    await realpath(join(ROOT, '.agents/ponytail')),
    join(ROOT, 'plugins/code'),
  );
});

void test('plugin skills: isolated packages retain resources and executable helpers', async () => {
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
      await cp(join(source, 'AGENTS.md'), join(target, 'AGENTS.md'));
      if (pluginDirectory !== 'chat') {
        await cp(join(source, 'mcp.json'), join(target, 'mcp.json'));
        const mcp = JSON.parse(
          await readFile(join(target, 'mcp.json'), 'utf8'),
        );
        assertEquals(
          Object.keys(mcp.mcpServers),
          pluginDirectory === 'work'
            ? ['backfire-education', 'reference-library']
            : ['backfire-code'],
        );
        const backfire =
          mcp.mcpServers[
            pluginDirectory === 'work' ? 'backfire-education' : 'backfire-code'
          ];
        assertEquals(
          backfire.args.includes('--education'),
          pluginDirectory === 'work',
        );
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
      for (const skill of await readdir(join(target, 'skills'))) {
        const skillDirectory = join(target, 'skills', skill);
        const text = await readFile(join(skillDirectory, 'SKILL.md'), 'utf8');
        assert(
          text.includes(
            `Read [the ${pluginDirectory} plugin rules](../../AGENTS.md) before using this skill.`,
          ),
          `Missing plugin rules pointer: ${pluginDirectory}/${skill}`,
        );
        assertEquals(
          await realpath(join(skillDirectory, '../../AGENTS.md')),
          join(target, 'AGENTS.md'),
        );
      }
      if (pluginDirectory !== 'code') continue;
      for (const args of [
        [`${pluginDirectory}/tests/hooks.test.js`],
        [
          '-e',
          `const assert = require('assert'); const path = require('path'); const text = require('./${pluginDirectory}/hooks/ponytail-instructions').getPonytailInstructions('full'); assert.match(text, /## Intensity/); const rules = path.resolve('${pluginDirectory}/AGENTS.md'); assert(text.includes('(' + rules + ')')); assert(require('fs').readFileSync(rules, 'utf8').includes('# Code plugin'));`,
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

void test('plugin skills: work Backfire shares code tool reference and license', async () => {
  for (const path of ['reference/tools.md', 'LICENSE']) {
    assertEquals(
      await readFile(join(ROOT, 'plugins/work/skills/backfire', path), 'utf8'),
      await readFile(join(ROOT, 'plugins/code/skills/backfire', path), 'utf8'),
    );
  }
});

void test('plugin clients: shared declarations survive copying, changes and failed preparation', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'plugin-clients-'));
  try {
    for (const name of ['chat', 'code', 'work']) {
      const target = join(temp, 'plugins', name);
      await mkdir(target, {recursive: true});
      await cp(
        join(ROOT, 'plugins', name, 'plugin.json'),
        join(target, 'plugin.json'),
      );
      if (name !== 'chat')
        await cp(
          join(ROOT, 'plugins', name, 'mcp.json'),
          join(target, 'mcp.json'),
        );
      await mkdir(join(target, 'skills/demo'), {recursive: true});
      await writeFile(
        join(target, 'skills/demo/SKILL.md'),
        `Synthetic ${name} skill\n`,
      );
      await mkdir(join(target, 'node_modules'), {recursive: true});
      await writeFile(
        join(target, 'node_modules/excluded.txt'),
        'not distributed',
      );
    }
    const output = preparePluginClients(temp);
    const readJson = async (path: string) =>
      JSON.parse(await readFile(path, 'utf8'));
    const code = await readJson(join(output, 'plugins/code/mcp.json'));
    const work = await readJson(join(output, 'plugins/work/mcp.json'));
    assertEquals(Object.keys(code.mcpServers), ['backfire-code']);
    assertEquals(Object.keys(work.mcpServers), [
      'backfire-education',
      'reference-library',
    ]);
    assertEquals(
      code.mcpServers['backfire-code'].args.includes('--education'),
      false,
    );
    assertEquals(
      work.mcpServers['backfire-education'].args.includes('--education'),
      true,
    );
    assertEquals(work.mcpServers['reference-library'].args, [
      join(temp, 'plugins/work/node_modules/zotero-native-mcp/build/index.js'),
    ]);
    const sourcePath = join(temp, 'plugins/work/mcp.json');
    const original = await readFile(sourcePath, 'utf8');
    assert(original.includes('${PLUGIN_ROOT}'));
    for (const name of ['chat', 'code', 'work']) {
      const plugin = join(output, 'plugins', name);
      const native = await readJson(join(plugin, '.claude-plugin/plugin.json'));
      assertEquals(native.name, name);
      assertEquals(
        native.mcpServers,
        name === 'chat' ? undefined : './mcp.json',
      );
      assertEquals(
        await readFile(join(plugin, 'skills/demo/SKILL.md'), 'utf8'),
        `Synthetic ${name} skill\n`,
      );
      await rejects(lstat(join(plugin, 'node_modules')), {code: 'ENOENT'});
    }
    const copied = join(temp, 'client-cache');
    await cp(join(output, 'plugins/work'), copied, {recursive: true});
    assertEquals(await readJson(join(copied, 'mcp.json')), work);
    const changed = JSON.parse(original);
    changed.mcpServers['reference-library'].env.ZOTERO_LOCAL_APP_NAME =
      'Synthetic changed declaration';
    await writeFile(sourcePath, JSON.stringify(changed));
    preparePluginClients(temp);
    const latest = await readFile(
      join(output, 'plugins/work/mcp.json'),
      'utf8',
    );
    assert(latest.includes('Synthetic changed declaration'));
    assertEquals(await readJson(sourcePath), changed);
    // Simulate interruption between the two directory renames. The last
    // completed output must be restored even if the next source is invalid.
    await rename(output, `${output}.previous`);
    await mkdir(`${output}.next`);
    await writeFile(sourcePath, '{broken');
    assertThrows(() => preparePluginClients(temp));
    assertEquals(
      await readFile(join(output, 'plugins/work/mcp.json'), 'utf8'),
      latest,
    );
    await rejects(lstat(`${output}.next`), {code: 'ENOENT'});
    await rejects(lstat(`${output}.previous`), {code: 'ENOENT'});
    changed.mcpServers['backfire-code'] =
      changed.mcpServers['backfire-education'];
    await writeFile(sourcePath, JSON.stringify(changed));
    assertThrows(
      () => preparePluginClients(temp),
      Error,
      'Duplicate plugin server: backfire-code',
    );
    assertEquals(
      await readFile(join(output, 'plugins/work/mcp.json'), 'utf8'),
      latest,
    );
    delete changed.mcpServers['backfire-code'];
    await writeFile(sourcePath, JSON.stringify(changed));
    const resource = join(temp, 'plugins/work/skills/demo/linked.txt');
    await symlink(sourcePath, resource);
    assertThrows(
      () => preparePluginClients(temp),
      Error,
      'Plugin resources must be local files',
    );
    await rm(resource);
    await writeFile(resource, Buffer.alloc(16 * 1024 * 1024));
    assertThrows(
      () => preparePluginClients(temp),
      Error,
      'Plugin distribution exceeds 16 MiB',
    );
    assertEquals(
      await readFile(join(output, 'plugins/work/mcp.json'), 'utf8'),
      latest,
    );
    await rejects(lstat(`${output}.next`), {code: 'ENOENT'});
  } finally {
    await rm(temp, {recursive: true, force: true});
  }
});
