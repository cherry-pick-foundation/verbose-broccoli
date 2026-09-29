import {
  createCommand,
  createReport,
  runCli,
  ValidationError,
} from '../plugins/code/skills/clean-code/scripts/cli.ts';
import {lstat, readFile} from 'node:fs/promises';
import {fromFileUrl, join} from '@std/path';
import {Ajv2020} from 'ajv/dist/2020.js';
import pluginSchema from './vendor/agent-plugins/plugin.schema.json' with {
  type: 'json',
};
import mcpSchema from './vendor/agent-plugins/mcp.schema.json' with {
  type: 'json',
};

const ajv = new Ajv2020({allErrors: true});
const validators = [
  ['plugin.json', ajv.compile(pluginSchema)],
  ['mcp.json', ajv.compile(mcpSchema)],
] as const;

export async function readPluginManifests(root: string, label = root) {
  const values: Record<string, unknown> = {};
  for (const [filename, validate] of validators) {
    const path = join(root, filename);
    const display = join(label, filename);
    try {
      const info = await lstat(path);
      if (!info.isFile() || info.isSymbolicLink())
        throw new Error(`${display}: expected a regular file.`);
      values[filename] = JSON.parse(await readFile(path, 'utf8'));
    } catch (error) {
      if (
        filename === 'mcp.json' &&
        (error as NodeJS.ErrnoException).code === 'ENOENT'
      )
        continue;
      throw new Error(`${display}: unable to read a regular JSON manifest.`, {
        cause: error,
      });
    }
    if (!validate(values[filename]))
      createReport({path: display, errors: validate.errors}, true);
  }
  const plugin = values['plugin.json'] as {
    name: string;
    version?: string;
    description?: string;
  };
  const mcp = values['mcp.json'] as
    | {mcpServers: Record<string, unknown>}
    | undefined;
  return {
    name: plugin.name,
    version: plugin.version,
    description: plugin.description,
    servers: Object.keys(mcp?.mcpServers ?? {}).sort(),
  };
}

if (import.meta.main) {
  await runCli(() =>
    createCommand(
      'plugins:validate',
      'Validate portable plugin and MCP manifests against the pinned schemas.',
    )
      .arguments('[roots...:string]')
      .action(async (_options, ...selected) => {
        if (selected.some(path => path.startsWith('-')))
          throw new ValidationError(
            'Unknown option; prefix literal paths with ./ when they begin with a dash.',
          );
        const roots = selected?.length
          ? selected
          : ['code', 'work', 'chat'].map(name =>
              fromFileUrl(new URL(`../plugins/${name}/`, import.meta.url)),
            );
        const results = [];
        for (const root of roots) {
          const {name} = await readPluginManifests(root);
          results.push({name, status: 'PASS'});
        }
        createReport({plugins: results});
      })
      .parse(process.argv.slice(2)),
  );
}
