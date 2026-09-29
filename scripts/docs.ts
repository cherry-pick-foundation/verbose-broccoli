import {execFile} from 'node:child_process';
import {Buffer} from 'node:buffer';
import {
  lstat,
  mkdir,
  readFile,
  readdir,
  realpath,
  rename,
  rmdir,
  unlink,
  writeFile,
} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {dirname, fromFileUrl, join, relative, resolve} from '@std/path';
import {z} from '@zod/zod';
import ts from 'typescript';
import {toMarkdown} from 'mdast-util-to-markdown';
import {gfmTableToMarkdown} from 'mdast-util-gfm-table';
import {
  createCommand,
  createReport,
  runCli,
  ValidationError,
} from '../plugins/code/skills/clean-code/scripts/cli.ts';
import {readPluginManifests} from './validate_plugins.ts';
import {sha256} from './hash.ts';

const files = ['commands.md', 'plugins.md'] as const;
const lockfile = createRequire(import.meta.url)('proper-lockfile') as {
  lock(
    path: string,
    options?: {
      realpath?: boolean;
      lockfilePath?: string;
      retries?:
        | number
        | {retries: number; minTimeout: number; maxTimeout: number};
    },
  ): Promise<() => Promise<void>>;
};
const packages = ['chat', 'code', 'work'];
const output = 'docs/reference';
const recovery = 'docs/.reference-publication';
const refresh = 'npm run docs:generate';
const decoder = new TextDecoder('utf-8', {fatal: true});
const encoder = new TextEncoder();
const skill = 'plugins/code/skills/clean-code';
export const documentedCommands = [
  ['doctor', 'scripts/doctor.ts'],
  ['workflow', 'scripts/workflow.ts'],
  ['clean-architecture', 'scripts/clean_architecture.ts'],
  ['plugins:validate', 'scripts/validate_plugins.ts'],
  ['clean-code', `${skill}/scripts/clean_code.ts`],
] as const;

function fail(path: string, message: string): never {
  throw new Error(`${path}: ${message} Run ${refresh}.`);
}

async function info(root: string, path: string) {
  try {
    const value = await lstat(join(root, path));
    if (
      value.isSymbolicLink() ||
      (await realpath(join(root, path))) !== join(root, path)
    )
      fail(path, 'Symlink traversal is not permitted.');
    return value;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return null;
    if (error instanceof Error && error.message.startsWith(`${path}:`))
      throw error;
    fail(path, 'Unable to inspect the selected path.');
  }
}

async function read(root: string, path: string, optional = false) {
  const stat = await info(root, path);
  if (!stat && optional) return null;
  if (!stat?.isFile()) fail(path, 'Expected a regular input file.');
  try {
    return {
      text: decoder.decode(await readFile(join(root, path))),
      stamp: [stat.dev, stat.ino, stat.size, stat.mtimeMs],
    };
  } catch {
    fail(path, 'Unable to read UTF-8 input.');
  }
}

async function inputs(root: string, selected?: string[]) {
  const queue = selected ?? [
    'package.json',
    'package-lock.json',
    'turbo.json',
    'scripts/docs.ts',
    ...documentedCommands.map(([, script]) => script),
    ...packages.flatMap(name => [
      `plugins/${name}/plugin.json`,
      `plugins/${name}/mcp.json`,
    ]),
  ];
  const result = new Map<string, Awaited<ReturnType<typeof read>>>();
  for (const path of queue) {
    if (result.has(path)) continue;
    if (path.startsWith('../'))
      fail(path, 'Not a selected documentation input.');
    const value = await read(root, path, path.endsWith('/mcp.json'));
    result.set(path, value);
    if (!selected && value && /\.[cm]?[jt]s$/.test(path)) {
      for (const item of ts.preProcessFile(value.text, true, true)
        .importedFiles)
        if (item.fileName.startsWith('.'))
          queue.push(
            relative(root, resolve(root, dirname(path), item.fileName)),
          );
    }
  }
  return result;
}

function stableText(value: string, root: string, path: string) {
  if (
    // biome-ignore lint/suspicious/noControlCharactersInRegex: These bytes must never reach generated Markdown.
    /[\u0000-\u0008\u000b-\u001f\u007f-\u009f]/.test(value) ||
    value.includes(root) ||
    /(?:file:\/\/\/|\/(?:home|Users|tmp|private|etc|var|opt|run)\/|[A-Za-z]:[\\/])/.test(
      value,
    )
  )
    fail(path, 'Terminal controls or machine-local paths are not publishable.');
  return value;
}

export async function collectHelp(root: string) {
  const result = new Map<string, string>();
  for (const [name, script] of documentedCommands) {
    const environment = {
      ...Object.fromEntries(
        ['HOME', 'SYSTEMROOT'].flatMap(key => {
          const value = process.env[key];
          return value ? [[key, value]] : [];
        }),
      ),
      NO_COLOR: '1',
      TERM: 'dumb',
      COLUMNS: '80',
      LC_ALL: 'C',
      TZ: 'UTC',
    };
    const readable = await Promise.all(
      [
        'node_modules',
        'scripts',
        'plugins',
        'package.json',
        'package-lock.json',
        'turbo.json',
        'tsconfig.json',
        'eslint.ignores.js',
      ].map(async path => {
        const scope = join(root, path);
        return [
          `--allow-fs-read=${scope}`,
          `--allow-fs-read=${await realpath(scope)}`,
        ];
      }),
    );
    const child = await new Promise<{
      success: boolean;
      code: number;
      stdout: Buffer;
      stderr: Buffer;
    }>((resolve, reject) => {
      execFile(
        process.execPath,
        [
          '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',
          '--disable-warning=SecurityWarning',
          '--permission',
          ...readable.flat(),
          join(root, script),
          '--help',
        ],
        {
          cwd: root,
          env: environment,
          encoding: 'buffer',
          maxBuffer: Infinity,
        },
        (error, stdout, stderr) => {
          if (error && !Number.isInteger(error.code)) {
            reject(error);
            return;
          }
          resolve({
            success: !error,
            code: error ? (error.code as number) : 0,
            stdout,
            stderr,
          });
        },
      );
    }).catch(() => fail(script, 'Unable to execute selected help.'));
    if (!child.success || child.stderr.length)
      fail(
        script,
        `Help collection failed (exit ${child.code}, stderr ${child.stderr.length} bytes).`,
      );
    let text: string;
    try {
      text = decoder.decode(child.stdout).replace(/\r\n/g, '\n');
    } catch {
      fail(script, 'Help is not valid UTF-8.');
    }
    stableText(text, root, script);
    if (!text.includes('Usage:') || !text.includes('--help'))
      fail(script, 'Required help output is missing.');
    // Only presentation whitespace is normalized: CRLF, trailing blanks, outer blank lines.
    result.set(
      name,
      text
        .replace(/\r\n/g, '\n')
        .replace(/[ \t]+$/gm, '')
        .trim(),
    );
  }
  return result;
}

type Node = Parameters<typeof toMarkdown>[0];
type Root = Extract<Node, {type: 'root'}>;
const text = (value: string) => ({type: 'text' as const, value});
const link = (value: string, path: string) => ({
  type: 'link' as const,
  url: `../../${path}`,
  children: [text(value)],
});
const heading = (value: string, depth: 1 | 2 = 2) => ({
  type: 'heading' as const,
  depth,
  children: [text(value)],
});
const paragraph = (value: string) => ({
  type: 'paragraph' as const,
  children: [text(value)],
});
function table(
  rows: (string | ReturnType<typeof link>)[][],
): Root['children'][number] {
  return {
    type: 'table',
    children: rows.map(row => ({
      type: 'tableRow',
      children: row.map(value => ({
        type: 'tableCell',
        children: [typeof value === 'string' ? text(value) : value],
      })),
    })),
  };
}
function serialize(
  title: string,
  owners: string[],
  children: Root['children'],
) {
  return toMarkdown(
    {
      type: 'root',
      children: [
        heading(title, 1),
        paragraph(`Generated file. Do not edit; refresh with ${refresh}.`),
        {
          type: 'paragraph',
          children: [
            text('Input owners: '),
            ...owners.flatMap((path, index) => [
              ...(index ? [text(', ')] : []),
              link(path, path),
            ]),
            text('.'),
          ],
        },
        ...children,
      ],
    },
    {extensions: [gfmTableToMarkdown()]},
  );
}

const taskSchema = z.object({
  tasks: z.record(
    z.string().min(1),
    z.union([
      z.string(),
      z.object({description: z.string().optional()}).passthrough(),
    ]),
  ),
});
const npmSchema = z.object({scripts: z.record(z.string(), z.string())});

async function render(
  root: string,
  snapshot: Awaited<ReturnType<typeof inputs>>,
) {
  const plugins = await Promise.all(
    packages.map(async name => {
      try {
        return {
          ...(await readPluginManifests(
            join(root, `plugins/${name}`),
            `plugins/${name}`,
          )),
          path: `plugins/${name}`,
        };
      } catch (error) {
        if (error instanceof Error) error.message += ` Run ${refresh}.`;
        throw error;
      }
    }),
  );
  plugins.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
  if (new Set(plugins.map(plugin => plugin.name)).size !== plugins.length)
    fail('plugins', 'Duplicate plugin identities.');
  let scripts: z.infer<typeof npmSchema>['scripts'];
  try {
    scripts = npmSchema.parse(
      JSON.parse(snapshot.get('package.json')!.text),
    ).scripts;
  } catch {
    fail('package.json', 'Invalid root command definitions.');
  }
  let tasks: z.infer<typeof taskSchema>['tasks'];
  try {
    tasks = taskSchema.parse(
      JSON.parse(snapshot.get('turbo.json')!.text),
    ).tasks;
  } catch {
    fail('turbo.json', 'Invalid root task descriptions.');
  }
  const help = await collectHelp(root);
  const pluginText = serialize(
    'Plugin reference',
    plugins.flatMap(plugin => [
      `${plugin.path}/plugin.json`,
      ...(snapshot.get(`${plugin.path}/mcp.json`)
        ? [`${plugin.path}/mcp.json`]
        : []),
    ]),
    [
      paragraph(
        'Server names below are declarations, not runtime availability or tool catalogs.',
      ),
      ...plugins.flatMap(plugin => [
        heading(plugin.name),
        table([
          ['Field', 'Declared value'],
          ['Description', plugin.description ?? ''],
          ['Version', plugin.version ?? ''],
          ['Package', link(plugin.path, `${plugin.path}/`)],
          ['Manifest', link('plugin.json', `${plugin.path}/plugin.json`)],
          [
            'MCP declaration',
            snapshot.get(`${plugin.path}/mcp.json`)
              ? link('mcp.json', `${plugin.path}/mcp.json`)
              : 'Not declared',
          ],
          [
            'MCP server names',
            plugin.servers.length ? plugin.servers.join(', ') : 'None declared',
          ],
        ]),
      ]),
    ],
  );
  const commandText = serialize(
    'Command reference',
    [
      'package.json',
      'turbo.json',
      ...documentedCommands.map(([, script]) => script),
    ],
    [
      table([
        ['Task', 'Invocation', 'Declared description'],
        ...Object.keys(scripts)
          .sort()
          .map(name => {
            const task = tasks[`//#${name}`];
            return [
              name,
              `npm run ${name}`,
              task && typeof task === 'object' ? (task.description ?? '') : '',
            ];
          }),
      ]),
      ...[...help]
        .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
        .flatMap(([name, value]) => [
          heading(name),
          {type: 'code' as const, lang: 'text', value},
        ]),
    ],
  );
  return {
    'commands.md': stableText(commandText, root, `${output}/commands.md`),
    'plugins.md': stableText(pluginText, root, `${output}/plugins.md`),
  };
}

async function directory(root: string, path: string) {
  const stat = await info(root, path);
  const contents: Record<string, string> = {};
  const unexpected: string[] = [];
  const stamps: unknown[] = [stat?.dev, stat?.ino, stat?.mtimeMs];
  if (stat && !stat.isDirectory()) unexpected.push(path);
  if (stat?.isDirectory()) {
    const entries = (
      await readdir(join(root, path), {withFileTypes: true})
    ).sort((a, b) => (a.name < b.name ? -1 : 1));
    for (const entry of entries) {
      const child = `${path}/${entry.name}`;
      if (
        !files.some(file => file === entry.name) ||
        !entry.isFile() ||
        entry.isSymbolicLink()
      ) {
        unexpected.push(child);
        continue;
      }
      const value = await lstat(join(root, child));
      if (!value.isFile() || value.isSymbolicLink())
        fail(child, 'Output changed while inspecting.');
      contents[entry.name] = Buffer.from(
        await readFile(join(root, child)),
      ).toString('hex');
      stamps.push(entry.name, value.dev, value.ino, value.size, value.mtimeMs);
    }
  }
  return {exists: stat !== null, contents, unexpected, stamps};
}
type Directory = Awaited<ReturnType<typeof directory>>;
async function hashes(value: Directory) {
  if (!value.exists) return null;
  return Object.fromEntries(
    await Promise.all(
      Object.entries(value.contents).map(async ([name, hex]) => [
        name,
        await sha256(Buffer.from(hex, 'hex')),
      ]),
    ),
  );
}
function exact(a: unknown, b: unknown) {
  return JSON.stringify(a) === JSON.stringify(b);
}
function owned(value: Directory, path: string) {
  if (value.unexpected.length)
    fail(path, `Unexpected entries: ${value.unexpected.join(', ')}.`);
}

const hashSchema = z.string().regex(/^[a-f0-9]{64}$/);
const journalSchema = z.strictObject({
  version: z.literal(1),
  before: z.partialRecord(z.enum(files), hashSchema).nullable(),
  after: z.strictObject({'commands.md': hashSchema, 'plugins.md': hashSchema}),
});
async function removeRecovery(root: string) {
  for (const name of ['next', 'previous']) {
    const state = await directory(root, `${recovery}/${name}`);
    owned(state, recovery);
    if (state.exists) {
      for (const file of Object.keys(state.contents))
        await unlink(join(root, recovery, name, file));
      await rmdir(join(root, recovery, name));
    }
  }
  await unlink(join(root, recovery, 'state.json'));
  await rmdir(join(root, recovery));
}

async function recover(root: string, rollback = false) {
  if (!(await info(root, recovery))) return;
  const entries = await readdir(join(root, recovery), {withFileTypes: true});
  if (
    entries.some(
      entry => !['state.json', 'next', 'previous'].includes(entry.name),
    )
  )
    fail(recovery, 'Unknown recovery entries; retain this recovery path.');
  let journal: z.infer<typeof journalSchema>;
  try {
    journal = journalSchema.parse(
      JSON.parse((await read(root, `${recovery}/state.json`))!.text),
    );
  } catch {
    fail(recovery, 'Invalid recovery record; retain this recovery path.');
  }
  const current = await directory(root, output);
  const next = await directory(root, `${recovery}/next`);
  const previous = await directory(root, `${recovery}/previous`);
  for (const state of [current, next, previous]) owned(state, recovery);
  const [now, staged, saved] = await Promise.all([
    hashes(current),
    hashes(next),
    hashes(previous),
  ]);
  let restored = journal.before;
  if (
    exact(now, journal.after) &&
    !next.exists &&
    exact(saved, journal.before)
  ) {
    if (!rollback) restored = journal.after;
    if (rollback) {
      await rename(join(root, output), join(root, recovery, 'next'));
      if (journal.before === null) return;
      await rename(join(root, recovery, 'previous'), join(root, output));
    }
  } else if (
    !current.exists &&
    exact(saved, journal.before) &&
    exact(staged, journal.after)
  ) {
    if (journal.before === null) {
      if (rollback) return;
      await rename(join(root, recovery, 'next'), join(root, output));
      restored = journal.after;
    } else await rename(join(root, recovery, 'previous'), join(root, output));
  } else if (
    exact(now, journal.before) &&
    !previous.exists &&
    Object.entries(staged ?? {}).every(
      ([name, hash]) => journal.after[name as (typeof files)[number]] === hash,
    )
  ) {
    if (rollback && journal.before === null && exact(staged, journal.after))
      return;
  } else
    fail(
      recovery,
      'Publication changed outside its recorded state; retain this recovery path.',
    );
  const readback = await directory(root, output);
  owned(readback, recovery);
  if (!exact(await hashes(readback), restored))
    fail(recovery, 'Recovery readback differs; retain this recovery path.');
  await removeRecovery(root);
}

async function unchanged(
  root: string,
  snapshot: Awaited<ReturnType<typeof inputs>>,
  before: Directory,
) {
  if (!exact([...snapshot], [...(await inputs(root, [...snapshot.keys()]))]))
    fail(
      'package.json / turbo.json / plugins / scripts',
      'Inputs changed during collection.',
    );
  if (!exact(before, await directory(root, output)))
    fail(output, 'Output changed during collection.');
}

export async function syncReferenceDocs(
  root: string,
  mode: 'generate' | 'check',
) {
  root = resolve(root);
  const docs = await info(root, 'docs');
  if (!docs?.isDirectory())
    fail('docs', 'Expected the repository documentation directory.');
  // ponytail: one native directory lock for this pair; split locks only for new output owners.
  await using _lock =
    mode === 'generate'
      ? {
          [Symbol.asyncDispose]: await lockfile.lock(join(root, 'docs'), {
            realpath: false,
            lockfilePath: join(root, 'docs', '.lock'),
            retries: {retries: 600, minTimeout: 1000, maxTimeout: 1000},
          }),
        }
      : null;
  const snapshot = await inputs(root);
  let before = await directory(root, output);
  const expected = await render(root, snapshot);
  await unchanged(root, snapshot, before);
  if (mode === 'check') {
    const missing = files
      .filter(file => !(file in before.contents))
      .map(file => `${output}/${file}`);
    const changed = files
      .filter(
        file =>
          file in before.contents &&
          before.contents[file] !==
            Buffer.from(encoder.encode(expected[file])).toString('hex'),
      )
      .map(file => `${output}/${file}`);
    const incomplete = (await info(root, recovery)) ? [recovery] : [];
    if (
      missing.length ||
      changed.length ||
      before.unexpected.length ||
      incomplete.length
    )
      createReport(
        {changed, missing, unexpected: before.unexpected, incomplete, refresh},
        true,
      );
    await unchanged(root, snapshot, before);
  } else {
    owned(before, output);
    await recover(root);
    before = await directory(root, output);
    await unchanged(root, snapshot, before);
    await mkdir(join(root, recovery));
    try {
      const after = Object.fromEntries(
        await Promise.all(
          files.map(async file => [file, await sha256(expected[file])]),
        ),
      );
      await writeFile(
        join(root, recovery, 'state.json'),
        JSON.stringify({version: 1, before: await hashes(before), after}),
        {flag: 'wx'},
      );
      await mkdir(join(root, recovery, 'next'));
      for (const file of files)
        await writeFile(join(root, recovery, 'next', file), expected[file], {
          flag: 'wx',
        });
      await unchanged(root, snapshot, before);
      if (before.exists)
        await rename(join(root, output), join(root, recovery, 'previous'));
      if (await info(root, output))
        fail(output, 'Output reappeared during publication.');
      await rename(join(root, recovery, 'next'), join(root, output));
      const published = await directory(root, output);
      owned(published, output);
      if (!exact(await hashes(published), after))
        fail(output, 'Published readback differs.');
      if (
        !exact([...snapshot], [...(await inputs(root, [...snapshot.keys()]))])
      )
        fail(output, 'Inputs changed during publication.');
      await removeRecovery(root);
    } catch (error) {
      try {
        await recover(root, true);
      } catch {
        fail(
          recovery,
          'Publication and rollback failed; previous/staged files remain recoverable here.',
        );
      }
      fail(
        (await info(root, recovery)) ? recovery : output,
        `Publication failed (${error instanceof Error ? error.name : 'error'}); previous files were preserved.`,
      );
    }
  }
  return {status: 'PASS', mode, files: files.map(file => `${output}/${file}`)};
}

if (import.meta.main)
  await runCli(() =>
    createCommand(
      'docs',
      'Generate or check source-derived repository references.',
    )
      .arguments('<mode:string>')
      .action(async (_options, mode) => {
        if (mode !== 'generate' && mode !== 'check')
          throw new ValidationError('Mode must be generate or check.');
        createReport(
          await syncReferenceDocs(
            fromFileUrl(new URL('../', import.meta.url)),
            mode,
          ),
        );
      })
      .parse(process.argv.slice(2)),
  );
