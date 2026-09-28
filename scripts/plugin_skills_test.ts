import {assert, assertEquals, assertRejects} from '@std/assert';
import {copy, exists, walk} from '@std/fs';
import {fromFileUrl, join} from '@std/path';

const ROOT = fromFileUrl(new URL('../', import.meta.url));

Deno.test('plugin skills: no project links duplicate packaged skills', async () => {
  for (const path of ['.agents/skills', '.claude/skills']) {
    await assertRejects(
      () => Deno.lstat(join(ROOT, path)),
      Deno.errors.NotFound,
    );
  }
  assertEquals(
    await Deno.realPath(join(ROOT, '.agents/ponytail')),
    join(ROOT, 'plugins/code'),
  );
});

Deno.test('plugin skills: isolated packages retain resources and executable helpers', async () => {
  for (const pluginDirectory of ['code', 'work', 'chat']) {
    const temp = await Deno.makeTempDir();
    try {
      const source = join(ROOT, 'plugins', pluginDirectory);
      const target = join(temp, pluginDirectory);
      await Deno.mkdir(target);
      await copy(join(source, 'plugin.json'), join(target, 'plugin.json'));
      const manifest = JSON.parse(
        await Deno.readTextFile(join(target, 'plugin.json')),
      );
      assertEquals(manifest.name, pluginDirectory);
      assertEquals(manifest.version, '0.1.0');
      if (pluginDirectory !== 'chat') {
        await copy(join(source, 'mcp.json'), join(target, 'mcp.json'));
        const mcp = JSON.parse(
          await Deno.readTextFile(join(target, 'mcp.json')),
        );
        assertEquals(Object.keys(mcp.mcpServers), ['backfire']);
      }
      for (const component of ['skills', 'hooks', 'tests']) {
        if (!(await exists(join(source, component)))) continue;
        for await (const entry of walk(join(source, component))) {
          assert(
            !entry.isSymlink,
            `Packaged resource must be local: ${entry.path}`,
          );
        }
        await copy(join(source, component), join(target, component));
      }
      if (pluginDirectory !== 'code') continue;
      for (const args of [
        [`${pluginDirectory}/tests/hooks.test.js`],
        [
          '-e',
          `require('assert').match(require('./${pluginDirectory}/hooks/ponytail-instructions').getPonytailInstructions('full'), /## Intensity/)`,
        ],
      ]) {
        const result = await new Deno.Command('node', {
          args,
          cwd: temp,
          env: {XDG_CONFIG_HOME: join(temp, 'config')},
        }).output();
        assertEquals(result.code, 0, new TextDecoder().decode(result.stderr));
      }
    } finally {
      await Deno.remove(temp, {recursive: true});
    }
  }
});

Deno.test('plugin skills: work Backfire shares code tool reference and license', async () => {
  for (const path of ['reference/tools.md', 'LICENSE']) {
    assertEquals(
      await Deno.readTextFile(join(ROOT, 'plugins/work/skills/backfire', path)),
      await Deno.readTextFile(join(ROOT, 'plugins/code/skills/backfire', path)),
    );
  }
});
