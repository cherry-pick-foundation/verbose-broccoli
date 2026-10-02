import {
  cpSync,
  chmodSync,
  chownSync,
  existsSync,
  lstatSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  readlinkSync,
  symlinkSync,
  renameSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import {
  basename,
  dirname,
  isAbsolute,
  join,
  relative,
  resolve,
} from 'node:path';
import {homedir} from 'node:os';
import {fileURLToPath} from 'node:url';
import {isDeepStrictEqual} from 'node:util';
import {createHash, randomUUID} from 'node:crypto';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const PLUGINS = ['chat', 'code', 'work'];
const BUDGET = 16 * 1024 * 1024;
const json = (value: unknown) => JSON.stringify(value, null, 2) + '\n';

type Server = {
  command: string;
  args?: string[];
  env?: Record<string, string>;
  type?: string;
};
const BEGIN = '# BEGIN generated plugin discovery\n';
const END = '# END generated plugin discovery\n';
const DENIED = [
  'zotero_delete_items',
  'zotero_delete_collection',
  'zotero_empty_trash',
];
type Ownership = {
  links?: Record<string, string>;
  servers?: Record<string, Server>;
  codex?: string;
};

function stat(path: string) {
  return lstatSync(path, {throwIfNoEntry: false});
}

function replaceClient(path: string, contents: string, staging: string) {
  const stage = `${path}.${staging}.next`;
  const previous = stat(path);
  writeFileSync(stage, contents, {flag: 'wx', mode: 0o600});
  if (previous) {
    const current = lstatSync(stage);
    if (current.uid !== previous.uid || current.gid !== previous.gid)
      chownSync(stage, previous.uid, previous.gid);
  }
  chmodSync(stage, previous?.mode ?? 0o666 & ~process.umask());
  renameSync(stage, path);
}

function storagePath(root: string, kind: 'STATE' | 'CACHE') {
  root = resolve(root);
  const value = process.env[`XDG_${kind}_HOME`];
  const base =
    value && isAbsolute(value)
      ? value
      : join(homedir(), kind === 'STATE' ? '.local/state' : '.cache');
  return join(
    base,
    'verbose-broccoli/workspaces',
    `${basename(root)}-${createHash('sha256').update(root).digest('hex').slice(0, 12)}`,
    'plugin-discovery',
  );
}

function readServers(root: string) {
  const servers: Record<string, Server> = {};
  for (const plugin of PLUGINS) {
    const source = join(root, 'plugins', plugin);
    const path = join(source, 'mcp.json');
    if (!existsSync(path)) continue;
    const declaration = JSON.parse(readFileSync(path, 'utf8'));
    const resolved = JSON.parse(
      json(declaration).replaceAll(
        '${PLUGIN_ROOT}',
        JSON.stringify(source).slice(1, -1),
      ),
    );
    for (const [name, server] of Object.entries(resolved.mcpServers)) {
      if (Object.hasOwn(servers, name))
        throw new Error(`Duplicate plugin server: ${name}`);
      const value = server as Server;
      if (value.type !== 'stdio' || typeof value.command !== 'string')
        throw new Error(`Unsupported project server: ${name}`);
      servers[name] = value;
    }
  }
  return servers;
}

// Preflight every owned entry before mutation. The receipt contains only the
// last generated content; user edits are conflicts, never overwritten.
export function preparePluginDiscovery(root = ROOT) {
  root = resolve(root);
  for (const path of [
    '.agents',
    '.claude',
    '.codex',
    '.local',
    '.agents/skills',
  ]) {
    const value = stat(join(root, path));
    if (value && (!value.isDirectory() || value.isSymbolicLink()))
      throw new Error(`Conflict: ${path} must be a real directory`);
  }
  const receiptPath = join(storagePath(root, 'STATE'), 'plugin-discovery.json');
  const pendingPath = `${receiptPath}.pending`;
  const legacyPath = join(root, '.local/plugin-discovery.json');
  const backupPath = join(dirname(receiptPath), 'plugin-discovery-legacy.json');
  const previousPath = stat(receiptPath) ? receiptPath : legacyPath;
  for (const path of [
    previousPath,
    receiptPath,
    `${receiptPath}.next`,
    backupPath,
    pendingPath,
  ]) {
    const value = stat(path);
    if (
      value &&
      (!value.isFile() || value.isSymbolicLink() || value.size > 64 * 1024)
    )
      throw new Error('Conflict: ownership receipt');
  }
  const previousBytes = existsSync(previousPath)
    ? readFileSync(previousPath)
    : undefined;
  const previousText = previousBytes?.toString('utf8');
  const migrating = previousPath === legacyPath && previousBytes !== undefined;
  if (
    migrating &&
    existsSync(backupPath) &&
    !readFileSync(backupPath).equals(previousBytes)
  )
    throw new Error('Conflict: legacy ownership receipt backup');
  const receipt: Ownership =
    previousText !== undefined ? JSON.parse(previousText) : {};
  const old = structuredClone(receipt);
  const pending:
    | {
        receipt: Ownership;
        old: Ownership;
        intended: Ownership;
        staging?: string;
      }
    | undefined = existsSync(pendingPath)
    ? JSON.parse(readFileSync(pendingPath, 'utf8'))
    : undefined;
  if (
    pending &&
    ![pending.receipt, pending.intended].some(value =>
      isDeepStrictEqual(value, receipt),
    )
  )
    throw new Error('Conflict: pending ownership receipt');
  old.links = {...old.links, ...pending?.old.links, ...pending?.intended.links};
  for (const [path, target] of Object.entries(old.links)) {
    if (
      !(path === '.claude/skills' && target === '../.agents/skills') &&
      !(
        /^\.agents\/skills\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(path) &&
        /^\.\.\/\.\.\/plugins\/(chat|code|work)\/skills\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(
          target,
        ) &&
        basename(path) === basename(target)
      )
    )
      throw new Error('Conflict: invalid ownership receipt');
  }
  const links: Record<string, string> = {};
  const names = new Set<string>();
  for (const plugin of PLUGINS) {
    const source = join(root, 'plugins', plugin, 'skills');
    for (const entry of readdirSync(source, {withFileTypes: true})) {
      if (!entry.isDirectory())
        throw new Error(`Skill must be a canonical directory: ${entry.name}`);
      for (const resource of readdirSync(join(source, entry.name), {
        recursive: true,
        withFileTypes: true,
      })) {
        if (resource.isSymbolicLink())
          throw new Error(
            `Plugin resources must be local files: ${entry.name}/${resource.name}`,
          );
      }
      const text = readFileSync(join(source, entry.name, 'SKILL.md'), 'utf8');
      const name = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/
        .exec(text)?.[1]
        .match(/^name:\s*["']?([a-z0-9-]+)["']?\s*$/m)?.[1];
      if (name !== entry.name || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name))
        throw new Error(
          `Skill name must match folder: ${plugin}/${entry.name}`,
        );
      if (names.has(name)) throw new Error(`Duplicate skill: ${name}`);
      names.add(name);
      const path = `.agents/skills/${name}`;
      links[path] = relative(dirname(join(root, path)), join(source, name));
    }
  }
  links['.claude/skills'] = '../.agents/skills';
  for (const [path, target] of Object.entries({...old.links, ...links})) {
    const value = stat(join(root, path));
    if (
      value &&
      (!value.isSymbolicLink() || readlinkSync(join(root, path)) !== target)
    )
      throw new Error(`Conflict: ${path}`);
  }
  const index = join(root, '.agents/skills');
  if (existsSync(index)) {
    for (const entry of readdirSync(index)) {
      if (names.has(entry) || old.links?.[`.agents/skills/${entry}`]) continue;
      const path = join(index, entry);
      if (!existsSync(path))
        throw new Error(`Conflict: broken skill link ${entry}`);
      const skill = join(path, 'SKILL.md');
      if (!existsSync(skill)) continue;
      const name = readFileSync(skill, 'utf8').match(
        /^name:\s*["']?([a-z0-9-]+)["']?\s*$/m,
      )?.[1];
      if (name && names.has(name)) throw new Error(`Duplicate skill: ${name}`);
    }
  }
  const servers = readServers(root);
  const mcpPath = join(root, '.mcp.json');
  const codexPath = join(root, '.codex/config.toml');
  const staging = randomUUID();
  if (
    pending?.staging !== undefined &&
    !/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(pending.staging)
  )
    throw new Error('Conflict: invalid client staging receipt');
  for (const path of [mcpPath, codexPath]) {
    const leftover = pending?.staging
      ? stat(`${path}.${pending.staging}.next`)
      : undefined;
    if (leftover && (!leftover.isFile() || leftover.isSymbolicLink()))
      throw new Error(`Conflict: client staging ${path}`);
    if (stat(`${path}.${staging}.next`))
      throw new Error(`Conflict: unowned client staging ${path}`);
  }
  for (const path of [receiptPath, mcpPath, codexPath]) {
    const value = stat(path);
    if (value && (!value.isFile() || value.isSymbolicLink()))
      throw new Error(`Conflict: ${path}`);
  }
  const mcp = existsSync(mcpPath)
    ? JSON.parse(readFileSync(mcpPath, 'utf8'))
    : {mcpServers: {}};
  if (
    !mcp.mcpServers ||
    typeof mcp.mcpServers !== 'object' ||
    Array.isArray(mcp.mcpServers)
  )
    throw new Error('Conflict: invalid project mcpServers');
  for (const name of new Set([
    ...Object.keys(old.servers ?? {}),
    ...Object.keys(pending?.old.servers ?? {}),
    ...Object.keys(pending?.intended.servers ?? {}),
    ...Object.keys(servers),
  ])) {
    if (
      Object.hasOwn(mcp.mcpServers, name) &&
      ![old, pending?.old, pending?.intended].some(
        owned =>
          Object.hasOwn(owned?.servers ?? {}, name) &&
          isDeepStrictEqual(mcp.mcpServers[name], owned?.servers?.[name]),
      )
    )
      throw new Error(`Conflict: project server ${name}`);
    old.servers ??= {};
    if (Object.hasOwn(mcp.mcpServers, name))
      old.servers[name] = mcp.mcpServers[name];
    else delete old.servers[name];
    delete mcp.mcpServers[name];
  }
  Object.assign(mcp.mcpServers, servers);
  let codex = existsSync(codexPath) ? readFileSync(codexPath, 'utf8') : '';
  if (codex.includes(BEGIN) || codex.includes(END)) {
    old.codex = [old.codex, pending?.old.codex, pending?.intended.codex].find(
      value => value && codex.includes(value),
    );
    if (
      !old.codex ||
      codex.split(BEGIN).length !== 2 ||
      codex.split(END).length !== 2
    )
      throw new Error('Conflict: generated Codex configuration');
    codex = codex.replace(old.codex, '');
  }
  // ponytail: conservatively reject an overlapping server name in unowned
  // TOML; use a TOML parser if more configuration forms need to coexist.
  for (const name of Object.keys(servers)) {
    if (codex.includes(name)) throw new Error(`Conflict: Codex server ${name}`);
  }
  let block = BEGIN;
  for (const [name, server] of Object.entries(servers)) {
    block += `[mcp_servers.${JSON.stringify(name)}]\ncommand = ${JSON.stringify(server.command)}\nargs = ${JSON.stringify(server.args ?? [])}\n`;
    if (name === 'reference-library')
      block += `disabled_tools = ${JSON.stringify(DENIED)}\n`;
    if (server.env) {
      block += `[mcp_servers.${JSON.stringify(name)}.env]\n`;
      for (const [key, value] of Object.entries(server.env))
        block += `${JSON.stringify(key)} = ${JSON.stringify(value)}\n`;
    }
  }
  block += END;
  const intended = {links, servers, codex: block};
  const journal = json({receipt, old, intended, staging});
  if (Buffer.byteLength(journal) > 64 * 1024)
    throw new Error('Ownership journal exceeds 64 KiB');
  // Only this pending attempt owns leftovers; never sweep matching filenames.
  if (pending?.staging) {
    for (const path of [mcpPath, codexPath])
      rmSync(`${path}.${pending.staging}.next`, {force: true});
  }
  // Import ownership before changing client files; retain the original bytes
  // separately so deleting disposable .local cannot lose migration evidence.
  mkdirSync(dirname(receiptPath), {recursive: true});
  if (migrating) {
    if (!existsSync(backupPath))
      writeFileSync(backupPath, previousBytes, {flag: 'wx'});
    writeFileSync(`${receiptPath}.next`, previousBytes);
    renameSync(`${receiptPath}.next`, receiptPath);
  }
  // Publish intent before client writes; equal unowned output alone proves nothing.
  writeFileSync(`${receiptPath}.next`, journal);
  renameSync(`${receiptPath}.next`, pendingPath);
  for (const [path, target] of Object.entries(links)) {
    mkdirSync(dirname(join(root, path)), {recursive: true});
    if (!stat(join(root, path))) symlinkSync(target, join(root, path), 'dir');
  }
  for (const path of Object.keys(old.links ?? {})) {
    if (!Object.hasOwn(links, path)) rmSync(join(root, path), {force: true});
  }
  mkdirSync(dirname(codexPath), {recursive: true});
  // At most two staged client files survive interruption, named by the journal.
  replaceClient(mcpPath, json(mcp), staging);
  replaceClient(
    codexPath,
    codex + (codex && !codex.endsWith('\n') ? '\n' : '') + block,
    staging,
  );
  writeFileSync(`${receiptPath}.next`, json(intended));
  renameSync(`${receiptPath}.next`, receiptPath);
  rmSync(pendingPath);
  return index;
}

export function cleanPluginCodex(root = ROOT) {
  root = resolve(root);
  const receiptPath = join(storagePath(root, 'STATE'), 'plugin-discovery.json');
  const pendingPath = `${receiptPath}.pending`;
  const next = `${receiptPath}.next`;
  const codexPath = join(root, '.codex/config.toml');
  const directory = stat(dirname(codexPath));
  if (!directory?.isDirectory() || directory.isSymbolicLink())
    throw new Error('Conflict: .codex must be a real directory');
  for (const path of [receiptPath, codexPath]) {
    const value = stat(path);
    if (
      !value?.isFile() ||
      value.isSymbolicLink() ||
      (path === receiptPath && value.size > 64 * 1024)
    )
      throw new Error(
        `Conflict: completed discovery ownership required: ${path}`,
      );
  }
  if (stat(pendingPath) || stat(next))
    throw new Error(
      'Conflict: pending discovery; run plugins:prepare before cleanup',
    );
  const receipt: Ownership = JSON.parse(readFileSync(receiptPath, 'utf8'));
  const block = receipt.codex;
  if (
    typeof block !== 'string' ||
    !block.startsWith(BEGIN) ||
    !block.endsWith(END)
  )
    throw new Error('Conflict: invalid Codex ownership receipt');
  const codex = readFileSync(codexPath, 'utf8');
  if (!codex.includes(BEGIN) && !codex.includes(END)) return false;
  if (
    !codex.includes(block) ||
    codex.split(BEGIN).length !== 2 ||
    codex.split(END).length !== 2
  )
    throw new Error('Conflict: generated Codex configuration');
  const staging = randomUUID();
  for (const path of [join(root, '.mcp.json'), codexPath]) {
    if (stat(`${path}.${staging}.next`))
      throw new Error('Conflict: unowned client staging');
  }
  // The completed receipt stays authoritative; interrupted cleanup recovers by preparation.
  const journal = json({receipt, old: receipt, intended: receipt, staging});
  if (Buffer.byteLength(journal) > 64 * 1024)
    throw new Error('Ownership journal exceeds 64 KiB');
  writeFileSync(next, journal, {flag: 'wx'});
  renameSync(next, pendingPath);
  replaceClient(codexPath, codex.replace(block, ''), staging);
  rmSync(pendingPath);
  return true;
}

// Client packages still use this checkout's installed dependencies. Claude's
// supported manifest path and Codex's portable loader read the same mcp.json.
// One current output, one staging output and one recovery copy bound storage
// to 48 MiB. A failed build keeps the last completed distribution.
export function preparePluginClients(root = ROOT) {
  root = resolve(root);
  const out = join(storagePath(root, 'CACHE'), 'plugin-clients');
  const stage = `${out}.next`;
  const previous = `${out}.previous`;
  mkdirSync(dirname(out), {recursive: true});
  if (existsSync(previous) && !existsSync(out)) renameSync(previous, out);
  rmSync(stage, {recursive: true, force: true});
  let bytes = 0;
  const servers = new Set<string>();
  try {
    for (const name of PLUGINS) {
      const source = join(root, 'plugins', name);
      const target = join(stage, 'plugins', name);
      cpSync(source, target, {
        recursive: true,
        filter(path) {
          if (basename(path) === 'node_modules') return false;
          const stat = lstatSync(path);
          if (stat.isSymbolicLink())
            throw new Error('Plugin resources must be local files');
          bytes += stat.isFile() ? stat.size : 0;
          if (bytes > BUDGET)
            throw new Error('Plugin distribution exceeds 16 MiB');
          return true;
        },
      });
      const manifest = JSON.parse(
        readFileSync(join(source, 'plugin.json'), 'utf8'),
      );
      if (manifest.name !== name)
        throw new Error(`Unexpected plugin identity: ${name}`);
      const {version, description, license} = manifest;
      const claude = {
        name,
        version,
        description,
        license,
        mcpServers: undefined as string | undefined,
      };
      if (existsSync(join(source, 'mcp.json'))) {
        // Replace JSON-escaped path text, preserving quotes and backslashes in
        // checkout names. PLUGIN_DATA remains a client-owned runtime variable.
        const mcp = JSON.parse(readFileSync(join(source, 'mcp.json'), 'utf8'));
        for (const server of Object.keys(mcp.mcpServers)) {
          if (servers.has(server))
            throw new Error(`Duplicate plugin server: ${server}`);
          servers.add(server);
        }
        const contents = json(mcp).replaceAll(
          '${PLUGIN_ROOT}',
          JSON.stringify(source).slice(1, -1),
        );
        writeFileSync(join(target, 'mcp.json'), contents);
        claude.mcpServers = './mcp.json';
      }
      mkdirSync(join(target, '.claude-plugin'), {recursive: true});
      writeFileSync(join(target, '.claude-plugin/plugin.json'), json(claude));
    }
    mkdirSync(join(stage, '.agents/plugins'), {recursive: true});
    writeFileSync(
      join(stage, '.agents/plugins/marketplace.json'),
      json({
        name: 'verbose-broccoli',
        plugins: PLUGINS.map(name => ({
          name,
          source: {source: 'local', path: `./plugins/${name}`},
          policy: {installation: 'AVAILABLE', authentication: 'ON_INSTALL'},
          category: 'Productivity',
        })),
      }),
    );
    const size = readdirSync(stage, {recursive: true, withFileTypes: true})
      .filter(entry => entry.isFile())
      .reduce(
        (total, entry) =>
          total + lstatSync(join(entry.parentPath, entry.name)).size,
        0,
      );
    if (size > BUDGET) throw new Error('Plugin distribution exceeds 16 MiB');
    rmSync(previous, {recursive: true, force: true});
    if (existsSync(out)) renameSync(out, previous);
    renameSync(stage, out);
    rmSync(previous, {recursive: true, force: true});
    return out;
  } finally {
    rmSync(stage, {recursive: true, force: true});
    if (existsSync(previous) && !existsSync(out)) renameSync(previous, out);
  }
}

if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const args = process.argv.slice(2);
  if (
    args.length &&
    (args.length !== 1 || !['--distribute', '--clean-codex'].includes(args[0]))
  )
    throw new Error('Usage: plugin-clients.ts [--distribute|--clean-codex]');
  console.log(
    args[0] === '--distribute'
      ? preparePluginClients()
      : args[0] === '--clean-codex'
        ? cleanPluginCodex()
        : preparePluginDiscovery(),
  );
}
