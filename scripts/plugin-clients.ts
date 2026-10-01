import {
  cpSync,
  existsSync,
  lstatSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  renameSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import {basename, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const PLUGINS = ['chat', 'code', 'work'];
const BUDGET = 16 * 1024 * 1024;
const json = (value: unknown) => JSON.stringify(value, null, 2) + '\n';

// Client packages still use this checkout's installed dependencies. Claude's
// supported manifest path and Codex's portable loader read the same mcp.json.
// One current output, one staging output and one recovery copy bound storage
// to 48 MiB. A failed build keeps the last completed distribution.
export function preparePluginClients(root = ROOT) {
  const out = join(root, '.local/plugin-clients');
  const stage = `${out}.next`;
  const previous = `${out}.previous`;
  mkdirSync(join(root, '.local'), {recursive: true});
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
  console.log(preparePluginClients());
}
