import {spawnSync} from 'node:child_process';
import {after, before, test} from 'node:test';
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
  readlink,
  realpath,
  rm,
  rename,
  writeFile,
  symlink,
} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {basename, resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {
  preparePluginClients,
  preparePluginDiscovery,
} from './plugin-clients.ts';

const ROOT = fromFileUrl(new URL('../', import.meta.url));
const storageHome = await mkdtemp(join(tmpdir(), 'plugin-storage-'));
const originalEnvironment = {...process.env};
before(() => {
  process.env.HOME = storageHome;
  process.env.XDG_STATE_HOME = join(storageHome, 'state');
  process.env.XDG_CACHE_HOME = join(storageHome, 'cache');
});
after(async () => {
  for (const key of ['HOME', 'XDG_STATE_HOME', 'XDG_CACHE_HOME']) {
    if (originalEnvironment[key] === undefined) delete process.env[key];
    else process.env[key] = originalEnvironment[key];
  }
  await rm(storageHome, {recursive: true, force: true});
});
const checkoutName = (root: string) =>
  `${basename(resolve(root))}-${createHash('sha256').update(resolve(root)).digest('hex').slice(0, 12)}`;
const receiptPath = (root: string) =>
  join(
    storageHome,
    'state/verbose-broccoli/workspaces',
    checkoutName(root),
    'plugin-discovery/plugin-discovery.json',
  );

async function checkDiscoveryTree(root: string) {
  const expected: Record<string, string> = {
    '.claude/skills': '../.agents/skills',
    '.agents/ponytail': '../plugins/code',
  };
  for (const plugin of ['chat', 'code', 'work']) {
    for (const name of await readdir(join(root, 'plugins', plugin, 'skills'))) {
      const path = `.agents/skills/${name}`;
      assert(!Object.hasOwn(expected, path), `Duplicate skill: ${name}`);
      expected[path] = `../../plugins/${plugin}/skills/${name}`;
    }
  }
  const index = await lstat(join(root, '.agents/skills'));
  assert(index.isDirectory() && !index.isSymbolicLink());
  const tracked = spawnSync(
    'git',
    [
      'ls-files',
      '--stage',
      '-z',
      '--',
      '.agents/skills',
      '.claude/skills',
      '.agents/ponytail',
    ],
    {cwd: root, encoding: 'utf8'},
  );
  assertEquals(tracked.status, 0, tracked.stderr);
  const entries = tracked.stdout
    .split('\0')
    .filter(Boolean)
    .map(line => line.split('\t'));
  assertEquals(
    entries.map(([, path]) => path).sort(),
    Object.keys(expected).sort(),
  );
  for (const [metadata, path] of entries) {
    assertEquals(metadata.split(' ')[0], '120000', path);
    assertEquals(metadata.split(' ')[2], '0', path);
    const blob = spawnSync('git', ['show', `:${path}`], {
      cwd: root,
      encoding: 'utf8',
    });
    assertEquals(blob.status, 0, blob.stderr);
    assertEquals(blob.stdout, expected[path], path);
    assert((await lstat(join(root, path))).isSymbolicLink(), path);
    assertEquals(await readlink(join(root, path)), expected[path], path);
    assertEquals(
      await realpath(join(root, path)),
      resolve(root, path, '..', expected[path]),
      path,
    );
  }
}

void test('plugin skills: tracked discovery tree matches canonical inventory without preparation', async () => {
  await checkDiscoveryTree(ROOT);
  const hooks = await readFile(join(ROOT, '.codex/hooks.json'), 'utf8');
  for (const helper of [
    'ponytail-activate',
    'ponytail-subagent',
    'ponytail-mode-tracker',
  ]) {
    assert(hooks.includes(`.agents/ponytail/hooks/${helper}.js`));
    assert(
      (await lstat(join(ROOT, `.agents/ponytail/hooks/${helper}.js`))).isFile(),
    );
  }
  const canonical = spawnSync('git', ['show', 'HEAD:.codex/config.toml'], {
    cwd: ROOT,
    encoding: 'utf8',
  });
  assertEquals(canonical.status, 0, canonical.stderr);
  assert(!/^# (BEGIN|END) generated plugin discovery/m.test(canonical.stdout));
});

void test('plugin skills: missing, stale, wrong and non-link indexed entries fail', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'plugin-tree-'));
  const git = (args: string[]) => {
    const result = spawnSync('git', args, {cwd: temp, encoding: 'utf8'});
    assertEquals(result.status, 0, result.stderr);
  };
  try {
    git(['init', '--quiet', '--template=']);
    await mkdir(join(temp, '.agents/skills'), {recursive: true});
    await mkdir(join(temp, '.claude'));
    await symlink('../.agents/skills', join(temp, '.claude/skills'));
    await symlink('../plugins/code', join(temp, '.agents/ponytail'));
    for (const plugin of ['chat', 'code', 'work']) {
      await mkdir(join(temp, `plugins/${plugin}/skills/${plugin}`), {
        recursive: true,
      });
      await symlink(
        `../../plugins/${plugin}/skills/${plugin}`,
        join(temp, `.agents/skills/${plugin}`),
      );
    }
    git(['add', '.agents', '.claude']);
    await checkDiscoveryTree(temp);
    git(['rm', '--cached', '.agents/skills/code']);
    await rejects(checkDiscoveryTree(temp));
    git(['add', '.agents']);
    await symlink(
      '../../plugins/code/skills/stale',
      join(temp, '.agents/skills/stale'),
    );
    git(['add', '.agents']);
    await rejects(checkDiscoveryTree(temp));
    await rm(join(temp, '.agents/skills/stale'));
    const link = join(temp, '.agents/skills/code');
    await rm(link);
    await symlink('../../plugins/work/skills/work', link);
    git(['add', '.agents']);
    await rejects(checkDiscoveryTree(temp));
    await rm(link);
    await writeFile(link, '../../plugins/code/skills/code');
    git(['add', '.agents']);
    await rejects(checkDiscoveryTree(temp));
    await rm(link);
    await symlink('../../plugins/code/skills/code', link);
    git(['add', '.agents']);
    await checkDiscoveryTree(temp);
    await rm(join(temp, '.agents/ponytail'));
    await rejects(checkDiscoveryTree(temp));
  } finally {
    await rm(temp, {recursive: true, force: true});
  }
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
      await readFile(
        join(ROOT, 'plugins/work/skills/backfire-education', path),
        'utf8',
      ),
      await readFile(
        join(ROOT, 'plugins/code/skills/backfire-code', path),
        'utf8',
      ),
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
    assertEquals(
      output,
      join(
        storageHome,
        'cache/verbose-broccoli/workspaces',
        checkoutName(temp),
        'plugin-discovery/plugin-clients',
      ),
    );
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
    await rm(resource);
    await rm(output, {recursive: true});
    assertEquals(preparePluginClients(temp), output);
    assertEquals(
      await readFile(join(output, 'plugins/work/mcp.json'), 'utf8'),
      latest,
    );
  } finally {
    await rm(temp, {recursive: true, force: true});
  }
});

void test('live discovery: source edits, resources, reruns and moved checkout', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'plugin-live-'));
  try {
    for (const plugin of ['chat', 'code', 'work']) {
      await cp(join(ROOT, 'plugins', plugin), join(temp, 'plugins', plugin), {
        recursive: true,
        filter: path => !path.includes('node_modules'),
      });
    }
    await mkdir(join(temp, '.codex'));
    await writeFile(
      join(temp, '.codex/config.toml'),
      '[features]\nhooks = true\n',
    );
    await writeFile(
      join(temp, '.mcp.json'),
      JSON.stringify({mcpServers: {custom: {command: 'user-owned'}}}),
    );
    await mkdir(join(temp, '.agents/skills/personal'), {recursive: true});
    await writeFile(
      join(temp, '.agents/skills/personal/SKILL.md'),
      'User-owned',
    );
    preparePluginDiscovery(temp);
    const index = join(temp, '.agents/skills');
    assert(!(await lstat(index)).isSymbolicLink());
    assertEquals(await realpath(join(temp, '.claude/skills')), index);
    for (const plugin of ['chat', 'code', 'work']) {
      for (const name of await readdir(
        join(temp, 'plugins', plugin, 'skills'),
      )) {
        assertEquals(
          await realpath(join(index, name)),
          join(temp, 'plugins', plugin, 'skills', name),
        );
        assertEquals(
          await realpath(
            join(await realpath(join(index, name)), '../../AGENTS.md'),
          ),
          join(temp, 'plugins', plugin, 'AGENTS.md'),
        );
      }
    }
    for (const resource of ['assets', 'scripts']) {
      assert(
        (await readdir(join(index, 'wiki-raw-import', resource))).length > 0,
      );
    }
    const source = join(temp, 'plugins/code/skills/ponytail/SKILL.md');
    await writeFile(
      source,
      (await readFile(source, 'utf8')) + '\nSynthetic source edit\n',
    );
    assert(
      (
        await readFile(join(temp, '.claude/skills/ponytail/SKILL.md'), 'utf8')
      ).includes('Synthetic source edit'),
    );
    const before = await readFile(join(temp, '.codex/config.toml'), 'utf8');
    preparePluginDiscovery(temp);
    assertEquals(
      await readFile(join(temp, '.codex/config.toml'), 'utf8'),
      before,
    );
    const mcp = JSON.parse(await readFile(join(temp, '.mcp.json'), 'utf8'));
    assertEquals(mcp.mcpServers.custom.command, 'user-owned');
    assertEquals(
      mcp.mcpServers['backfire-code'].args.includes('--education'),
      false,
    );
    assertEquals(
      mcp.mcpServers['backfire-education'].args.includes('--education'),
      true,
    );
    assert(
      before.includes(
        'disabled_tools = ["zotero_delete_items","zotero_delete_collection","zotero_empty_trash"]',
      ),
    );
    assertEquals(
      await readFile(join(index, 'personal/SKILL.md'), 'utf8'),
      'User-owned',
    );
    const destructive = [
      'zotero_delete_items',
      'zotero_delete_collection',
      'zotero_empty_trash',
    ];
    const claude = JSON.parse(
      await readFile(join(ROOT, '.claude/settings.json'), 'utf8'),
    );
    assertEquals(
      claude.permissions.deny.filter((rule: string) =>
        rule.includes('reference-library'),
      ),
      ['plugin_work_reference-library', 'reference-library'].flatMap(server =>
        destructive.map(tool => `mcp__${server}__${tool}`),
      ),
    );
    const referenceBlock = before
      .split('[mcp_servers."reference-library"]\n')[1]
      .split('[mcp_servers.')[0];
    assertEquals(
      JSON.parse(referenceBlock.match(/^disabled_tools = (.+)$/m)![1]),
      destructive,
    );
    const moved = join(temp, 'moved checkout');
    await mkdir(moved);
    // A relocated checkout must carry its ownership; import a legacy receipt
    // at its new location rather than borrowing another worktree's state.
    await mkdir(join(temp, '.local'));
    await cp(receiptPath(temp), join(temp, '.local/plugin-discovery.json'));
    for (const path of [
      'plugins',
      '.agents',
      '.claude',
      '.codex',
      '.mcp.json',
      '.local',
    ]) {
      await rename(join(temp, path), join(moved, path));
    }
    preparePluginDiscovery(moved);
    assertEquals(
      await realpath(join(moved, '.claude/skills/ponytail')),
      join(moved, 'plugins/code/skills/ponytail'),
    );
    assert(
      (await readFile(join(moved, '.codex/config.toml'), 'utf8')).includes(
        moved,
      ),
    );
    const declaration = join(moved, 'plugins/work/mcp.json');
    const changed = JSON.parse(await readFile(declaration, 'utf8'));
    changed.mcpServers['reference-library'].env.ZOTERO_LOCAL_APP_NAME =
      'Changed source';
    await writeFile(declaration, JSON.stringify(changed));
    preparePluginDiscovery(moved);
    assert(
      (await readFile(join(moved, '.mcp.json'), 'utf8')).includes(
        'Changed source',
      ),
    );
    await rename(
      join(moved, 'plugins/chat/skills/web-agent'),
      join(moved, 'plugins/chat/skills/new-agent'),
    );
    const newSkill = join(moved, 'plugins/chat/skills/new-agent/SKILL.md');
    await writeFile(
      newSkill,
      (await readFile(newSkill, 'utf8')).replace(
        'name: web-agent',
        'name: new-agent',
      ),
    );
    preparePluginDiscovery(moved);
    await rejects(lstat(join(moved, '.agents/skills/web-agent')), {
      code: 'ENOENT',
    });
    assertEquals(
      await realpath(join(moved, '.agents/skills/new-agent')),
      join(moved, 'plugins/chat/skills/new-agent'),
    );
  } finally {
    await rm(temp, {recursive: true, force: true});
  }
});

void test('live discovery: unsafe conflicts and duplicate declarations fail before writes', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'plugin-conflicts-'));
  try {
    for (const plugin of ['chat', 'code', 'work']) {
      await cp(join(ROOT, 'plugins', plugin), join(temp, 'plugins', plugin), {
        recursive: true,
        filter: path => !path.includes('node_modules'),
      });
    }
    await mkdir(join(temp, '.claude/skills'), {recursive: true});
    await writeFile(join(temp, '.claude/skills/keep.txt'), 'keep');
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    assertEquals(
      await readFile(join(temp, '.claude/skills/keep.txt'), 'utf8'),
      'keep',
    );
    await rm(join(temp, '.claude/skills'), {recursive: true});
    await mkdir(join(temp, '.agents/skills/ponytail'), {recursive: true});
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    await rm(join(temp, '.agents/skills/ponytail'), {recursive: true});
    await symlink('../../missing', join(temp, '.agents/skills/ponytail'));
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    await rm(join(temp, '.agents/skills/ponytail'));
    await cp(
      join(temp, 'plugins/code/skills/ponytail'),
      join(temp, 'plugins/chat/skills/ponytail'),
      {recursive: true},
    );
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Duplicate skill');
    await rm(join(temp, 'plugins/chat/skills/ponytail'), {recursive: true});
    const skill = join(temp, 'plugins/chat/skills/web-agent/SKILL.md');
    const original = await readFile(skill, 'utf8');
    await writeFile(
      skill,
      original.replace('name: web-agent', 'name: ponytail'),
    );
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Skill name');
    await writeFile(skill, original);
    const declaration = join(temp, 'plugins/chat/mcp.json');
    await cp(join(temp, 'plugins/code/mcp.json'), declaration);
    assertThrows(
      () => preparePluginDiscovery(temp),
      Error,
      'Duplicate plugin server',
    );
    await rm(declaration);
    preparePluginDiscovery(temp);
    const config = join(temp, '.mcp.json');
    const mcp = JSON.parse(await readFile(config, 'utf8'));
    mcp.mcpServers['backfire-code'].command = 'user-edit';
    await writeFile(config, JSON.stringify(mcp));
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    assertEquals(
      JSON.parse(await readFile(config, 'utf8')).mcpServers['backfire-code']
        .command,
      'user-edit',
    );
    mcp.mcpServers['backfire-code'].command = 'uv';
    await writeFile(config, JSON.stringify(mcp));
    const receipt = receiptPath(temp);
    const receiptText = await readFile(receipt, 'utf8');
    const codex = join(temp, '.codex/config.toml');
    const codexText = await readFile(codex, 'utf8');
    await rm(receipt);
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    assertEquals(await readFile(codex, 'utf8'), codexText);
    const tampered = JSON.parse(receiptText);
    tampered.links['.agents/skills/ponytail'] = '../../missing';
    await writeFile(receipt, JSON.stringify(tampered));
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    assertEquals(await readFile(codex, 'utf8'), codexText);
    await writeFile(receipt, receiptText);
    await writeFile(
      codex,
      codexText.replace('command = "uv"', 'command = "user-edit"'),
    );
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    assert((await readFile(codex, 'utf8')).includes('command = "user-edit"'));
    await writeFile(codex, codexText);
    await rm(join(temp, '.agents/skills/ponytail'));
    await symlink('../../missing', join(temp, '.agents/skills/ponytail'));
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    await rm(join(temp, '.agents/skills/ponytail'));
    preparePluginDiscovery(temp);
    await symlink('missing', join(temp, '.agents/skills/unowned-broken'));
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    await rm(join(temp, '.agents/skills/unowned-broken'));
    await mkdir(join(temp, '.agents/skills/alias'));
    await writeFile(
      join(temp, '.agents/skills/alias/SKILL.md'),
      '---\nname: ponytail\n---\n',
    );
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Duplicate skill');
    await rm(join(temp, '.agents/skills/alias'), {recursive: true});
    await symlink(
      '../../../../outside',
      join(temp, 'plugins/chat/skills/web-agent/linked'),
    );
    assertThrows(
      () => preparePluginDiscovery(temp),
      Error,
      'Plugin resources must be local files',
    );
  } finally {
    await rm(temp, {recursive: true, force: true});
  }
});

void test('live discovery: legacy ownership survives migration and disposable deletion', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'plugin-migration-'));
  try {
    for (const plugin of ['chat', 'code', 'work']) {
      await cp(join(ROOT, 'plugins', plugin), join(temp, 'plugins', plugin), {
        recursive: true,
        filter: path => !path.includes('node_modules'),
      });
    }
    preparePluginDiscovery(temp);
    const receipt = receiptPath(temp);
    const legacy = join(temp, '.local/plugin-discovery.json');
    // Noncanonical JSON formatting must survive byte for byte.
    const original = '  ' + (await readFile(receipt, 'utf8')) + '\n';
    await mkdir(join(temp, '.local'));
    await writeFile(legacy, original);
    await rm(receipt);
    const config = join(temp, '.mcp.json');
    const generated = await readFile(config, 'utf8');
    const changed = JSON.parse(generated);
    changed.mcpServers['backfire-code'].command = 'user-edit';
    await writeFile(config, JSON.stringify(changed));
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    assertEquals(await readFile(legacy, 'utf8'), original);
    assert(!existsSync(receipt));
    assertEquals(await readFile(config, 'utf8'), JSON.stringify(changed));
    await writeFile(config, generated);
    const codex = join(temp, '.codex/config.toml');
    const codexText = await readFile(codex, 'utf8');
    await writeFile(
      codex,
      codexText.replace('command = "uv"', 'command = "user-edit"'),
    );
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    assert(!existsSync(receipt));
    await writeFile(codex, codexText);
    const link = join(temp, '.agents/skills/ponytail');
    await rm(link);
    await symlink('../../missing', link);
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    assert(!existsSync(receipt));
    await rm(link);
    const backup = receipt.replace(
      'plugin-discovery.json',
      'plugin-discovery-legacy.json',
    );
    await writeFile(backup, 'existing evidence');
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    assertEquals(await readFile(backup, 'utf8'), 'existing evidence');
    assert(!existsSync(receipt));
    await rm(backup);
    preparePluginDiscovery(temp);
    assertEquals(await readFile(legacy), Buffer.from(original));
    assertEquals(await readFile(backup), Buffer.from(original));
    const owned = await readFile(receipt, 'utf8');
    await rm(join(temp, '.local'), {recursive: true});
    preparePluginDiscovery(temp);
    assertEquals(await readFile(receipt, 'utf8'), owned);
    assertEquals(await readFile(backup, 'utf8'), original);
    assert(!existsSync(join(temp, '.local')));
    assertEquals(await readFile(config, 'utf8'), generated);
    assertEquals(await readFile(codex, 'utf8'), codexText);
    // State, rather than a stale disposable receipt, detects later user edits.
    await writeFile(config, JSON.stringify(changed));
    assertThrows(() => preparePluginDiscovery(temp), Error, 'Conflict');
    assertEquals(await readFile(receipt, 'utf8'), owned);
  } finally {
    await rm(temp, {recursive: true, force: true});
  }
});

void test('live discovery: durable intent recovers interrupted first preparation and updates', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'plugin-interruption-'));
  try {
    for (const update of [false, true]) {
      for (const cut of ['mcp', 'codex', 'receipt-next', 'receipt'] as const) {
        const root = join(temp, `${update ? 'update' : 'first'}-${cut}`);
        for (const plugin of ['chat', 'code', 'work']) {
          const target = join(root, 'plugins', plugin);
          await mkdir(join(target, `skills/demo-${plugin}`), {recursive: true});
          await writeFile(
            join(target, `skills/demo-${plugin}/SKILL.md`),
            `---\nname: demo-${plugin}\n---\n`,
          );
          if (plugin !== 'chat')
            await cp(
              join(ROOT, 'plugins', plugin, 'mcp.json'),
              join(target, 'mcp.json'),
            );
        }
        await mkdir(join(root, '.agents/skills/personal'), {recursive: true});
        await writeFile(
          join(root, '.agents/skills/personal/keep.txt'),
          'unowned data',
        );
        await mkdir(join(root, '.codex'));
        const codexPath = join(root, '.codex/config.toml');
        const mcpPath = join(root, '.mcp.json');
        await writeFile(codexPath, '[features]\nhooks = true\n');
        await writeFile(
          mcpPath,
          JSON.stringify({
            extra: 'keep',
            mcpServers: {personal: {command: 'user-owned'}},
          }),
        );
        if (update) preparePluginDiscovery(root);
        const receipt = receiptPath(root);
        const previous = update ? await readFile(receipt) : undefined;
        const declaration = join(root, 'plugins/code/mcp.json');
        const changed = JSON.parse(await readFile(declaration, 'utf8'));
        changed.mcpServers['backfire-code'].command = 'synthetic-updated';
        await writeFile(declaration, JSON.stringify(changed));
        const faultPath = {
          mcp: mcpPath,
          codex: codexPath,
          'receipt-next': `${receipt}.next`,
          receipt,
        }[cut];
        const child = spawnSync(
          process.execPath,
          [
            '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',
            '--input-type=module',
            '-e',
            `
          import fs from 'node:fs';
          import {syncBuiltinESMExports} from 'node:module';
          const method = ${JSON.stringify(cut)} === 'receipt' ? 'renameSync' : 'writeFileSync';
          const original = fs[method];
          fs[method] = (...args) => {
            const result = original(...args);
            if (String(args[method === 'renameSync' ? 1 : 0]) === ${JSON.stringify(faultPath)}) {
              // receipt .next is also used to publish intent: interrupt its final write only.
              if (${JSON.stringify(cut)} !== 'receipt-next' || !fs.readFileSync(args[0], 'utf8').includes('"intended"')) process.exit(86);
            }
            return result;
          };
          syncBuiltinESMExports();
          const {preparePluginDiscovery} = await import(${JSON.stringify(new URL('./plugin-clients.ts', import.meta.url).href)});
          preparePluginDiscovery(${JSON.stringify(root)});
        `,
          ],
          {env: process.env, encoding: 'utf8'},
        );
        assertEquals(child.status, 86, child.stderr);
        const pending = `${receipt}.pending`;
        assert((await lstat(pending)).size <= 64 * 1024);
        const intent = JSON.parse(await readFile(pending, 'utf8'));
        assertEquals(
          intent.receipt,
          previous ? JSON.parse(previous.toString()) : {},
        );
        if (cut !== 'receipt') {
          if (previous) assertEquals(await readFile(receipt), previous);
          else assert(!existsSync(receipt));
        }
        const output = await readFile(mcpPath, 'utf8');
        const edited = JSON.parse(output);
        edited.mcpServers['backfire-code'].command = 'user-edit';
        await writeFile(mcpPath, JSON.stringify(edited));
        assertThrows(() => preparePluginDiscovery(root), Error, 'Conflict');
        assertEquals(await readFile(mcpPath, 'utf8'), JSON.stringify(edited));
        await writeFile(mcpPath, output);
        preparePluginDiscovery(root);
        assertEquals(
          JSON.parse(await readFile(receipt, 'utf8')),
          intent.intended,
        );
        assert(!existsSync(pending));
        assert(!existsSync(`${receipt}.next`));
        const mcp = JSON.parse(await readFile(mcpPath, 'utf8'));
        assertEquals(mcp.extra, 'keep');
        assertEquals(mcp.mcpServers.personal, {command: 'user-owned'});
        assertEquals(
          mcp.mcpServers['backfire-code'].command,
          'synthetic-updated',
        );
        assertEquals(
          await readFile(codexPath, 'utf8'),
          '[features]\nhooks = true\n' + intent.intended.codex,
        );
        assertEquals(
          await readFile(
            join(root, '.agents/skills/personal/keep.txt'),
            'utf8',
          ),
          'unowned data',
        );
        const completed = await readFile(receipt);
        preparePluginDiscovery(root);
        assertEquals(await readFile(receipt), completed);
        // Equal desired output without durable ownership must remain unowned.
        await rm(receipt);
        assertThrows(() => preparePluginDiscovery(root), Error, 'Conflict');
      }
    }
  } finally {
    await rm(temp, {recursive: true, force: true});
  }
});

void test('plugin storage: XDG defaults, absolute roots and worktree isolation', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'plugin-xdg-'));
  try {
    const home = join(temp, 'home');
    for (const value of [undefined, '', 'relative', join(temp, 'absolute')]) {
      const root = join(
        temp,
        `checkout-${value === undefined ? 'unset' : basename(value) || 'empty'}`,
      );
      for (const plugin of ['chat', 'code', 'work']) {
        const source = join(ROOT, 'plugins', plugin);
        const target = join(root, 'plugins', plugin);
        await mkdir(join(target, `skills/demo-${plugin}`), {recursive: true});
        await cp(join(source, 'plugin.json'), join(target, 'plugin.json'));
        if (plugin !== 'chat')
          await cp(join(source, 'mcp.json'), join(target, 'mcp.json'));
        await writeFile(
          join(target, `skills/demo-${plugin}/SKILL.md`),
          `---\nname: demo-${plugin}\n---\nSynthetic\n`,
        );
      }
      const env: NodeJS.ProcessEnv = {...process.env, HOME: home};
      for (const key of ['XDG_STATE_HOME', 'XDG_CACHE_HOME']) {
        if (value === undefined) delete env[key];
        else env[key] = value;
      }
      const run = () =>
        spawnSync(
          process.execPath,
          [
            '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',
            '--input-type=module',
            '-e',
            `import {preparePluginDiscovery, preparePluginClients} from ${JSON.stringify(new URL('./plugin-clients.ts', import.meta.url).href)}; preparePluginDiscovery(${JSON.stringify(root)}); console.log(preparePluginClients(${JSON.stringify(root)}));`,
          ],
          {env, encoding: 'utf8'},
        );
      const result = run();
      assertEquals(result.status, 0, result.stderr);
      const namespace = join(
        'verbose-broccoli/workspaces',
        checkoutName(root),
        'plugin-discovery',
      );
      const state = join(
        value?.startsWith('/') ? value : join(home, '.local/state'),
        namespace,
      );
      const cache = join(
        value?.startsWith('/') ? value : join(home, '.cache'),
        namespace,
        'plugin-clients',
      );
      assertEquals(result.stdout.trim(), cache);
      const receipt = join(state, 'plugin-discovery.json');
      const original = await readFile(receipt, 'utf8');
      await rm(cache, {recursive: true});
      assertEquals(run().status, 0);
      assertEquals(await readFile(receipt, 'utf8'), original);
      assert(existsSync(join(cache, '.agents/plugins/marketplace.json')));
      assert(!existsSync(join(root, '.local')));
    }
    const roots = await readdir(
      join(home, '.local/state/verbose-broccoli/workspaces'),
    );
    assertEquals(
      roots.sort(),
      ['checkout-empty', 'checkout-relative', 'checkout-unset']
        .map(name => checkoutName(join(temp, name)))
        .sort(),
    );
  } finally {
    await rm(temp, {recursive: true, force: true});
  }
});

void test('plugin storage: same-basename checkouts isolate ownership, staging and recovery', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'plugin-isolation-'));
  try {
    const roots = ['first', 'second'].map(name => join(temp, name, 'checkout'));
    for (const root of roots) {
      for (const plugin of ['chat', 'code', 'work']) {
        const target = join(root, 'plugins', plugin);
        await mkdir(join(target, `skills/demo-${plugin}`), {recursive: true});
        await cp(
          join(ROOT, 'plugins', plugin, 'plugin.json'),
          join(target, 'plugin.json'),
        );
        if (plugin !== 'chat')
          await cp(
            join(ROOT, 'plugins', plugin, 'mcp.json'),
            join(target, 'mcp.json'),
          );
        await writeFile(
          join(target, `skills/demo-${plugin}/SKILL.md`),
          `---\nname: demo-${plugin}\n---\nSynthetic ${root}\n`,
        );
      }
    }
    const [first, second] = roots;
    const outputs = roots.map(root => preparePluginClients(root));
    assert(outputs[0] !== outputs[1]);
    for (const root of roots) preparePluginDiscovery(root);
    const receipts = roots.map(receiptPath);
    assert(receipts[0] !== receipts[1]);
    const owned = await Promise.all(receipts.map(path => readFile(path)));
    assert(!owned[0].equals(owned[1]));
    const resource = 'plugins/code/skills/demo-code/SKILL.md';
    const contents = await Promise.all(
      outputs.map(output => readFile(join(output, resource))),
    );
    // Pending replacement and interrupted outputs in one checkout must survive
    // another checkout's receipt update, failed build and recovery.
    await writeFile(`${receipts[1]}.next`, owned[1]);
    preparePluginDiscovery(first);
    assertEquals(await readFile(`${receipts[1]}.next`), owned[1]);
    for (const output of outputs) {
      await rename(output, `${output}.previous`);
      await mkdir(`${output}.next`);
      await writeFile(join(`${output}.next`, 'pending.txt'), 'pending');
    }
    const declaration = join(first, 'plugins/code/mcp.json');
    const original = await readFile(declaration);
    await writeFile(declaration, '{broken');
    assertThrows(() => preparePluginClients(first));
    assertEquals(await readFile(join(outputs[0], resource)), contents[0]);
    assert(!existsSync(`${outputs[0]}.next`));
    assert(!existsSync(`${outputs[0]}.previous`));
    assert(!existsSync(outputs[1]));
    assertEquals(
      await readFile(join(`${outputs[1]}.previous`, resource)),
      contents[1],
    );
    assertEquals(
      await readFile(join(`${outputs[1]}.next`, 'pending.txt'), 'utf8'),
      'pending',
    );
    await writeFile(declaration, original);
    assertEquals(preparePluginClients(first), outputs[0]);
    assert(!existsSync(outputs[1]));
    assertEquals(preparePluginClients(second), outputs[1]);
    preparePluginDiscovery(second);
    for (let i = 0; i < roots.length; i++) {
      assertEquals(await readFile(receipts[i]), owned[i]);
      assertEquals(await readFile(join(outputs[i], resource)), contents[i]);
      assert(!existsSync(`${receipts[i]}.next`));
      assert(!existsSync(`${outputs[i]}.next`));
      assert(!existsSync(`${outputs[i]}.previous`));
    }
    // Even a same-basename move requires carrying ownership explicitly.
    const moved = join(temp, 'moved', 'checkout');
    await mkdir(join(temp, 'moved'));
    await rename(first, moved);
    assertThrows(() => preparePluginDiscovery(moved), Error, 'Conflict');
    assert(!existsSync(receiptPath(moved)));
    assertEquals(await readFile(receipts[0]), owned[0]);
    await mkdir(join(moved, '.local'));
    await cp(receipts[0], join(moved, '.local/plugin-discovery.json'));
    preparePluginDiscovery(moved);
    assert((await readFile(receiptPath(moved), 'utf8')).includes(moved));
    assertEquals(await readFile(receipts[1]), owned[1]);
  } finally {
    await rm(temp, {recursive: true, force: true});
  }
});
