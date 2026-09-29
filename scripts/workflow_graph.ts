import {z} from '@zod/zod';
import {format, type ICruiseResult, type IDependency} from 'dependency-cruiser';
import {realpath} from 'node:fs/promises';
import {analyzeImportGraph} from './clean_architecture.ts';
import {
  getFileAccessError,
  listCodeFiles,
  repositoryFileSchema,
} from './workflow_files.ts';
import {
  repositoryPathspec,
  runGit,
  snapshotWorkingTree,
} from './workflow_git.ts';
import {inspectSymbol} from './workflow_symbol.ts';

export const graphCommands = [
  {
    choice: 'impact',
    when: 'Before changing an existing file or checking its consumers after an edit.',
    command: 'npm run workflow -- --task <id> --graph impact --file <path>',
    returns:
      'Direct imports, transitive dependents, test candidates, and repository import-policy violations.',
  },
  {
    choice: 'symbol',
    when: 'Before changing or removing a symbol; select its identifier by 1-based line and UTF-16 column.',
    command:
      'npm run workflow -- --task <id> --graph symbol --file <path> --line <n> --column <n>',
    returns:
      'File impact plus local definitions, references, incoming calls, and outgoing calls in one report.',
  },
  {
    choice: 'policy',
    when: 'After imports, package boundaries, or file structure change, including deletions.',
    command: 'npm run workflow -- --task <id> --graph policy',
    returns:
      'Repository-wide static import-policy checks; violations cause exit code 1.',
  },
];

const request = z.discriminatedUnion('choice', [
  z.strictObject({choice: z.literal('impact'), file: repositoryFileSchema}),
  z.strictObject({
    choice: z.literal('symbol'),
    file: repositoryFileSchema,
    line: z.number().int().positive(),
    column: z.number().int().positive(),
  }),
  z.strictObject({choice: z.literal('policy')}),
]);
const testPath = /(?:^|\/)tests?\/|(?:^|\/|[._])(?:test|spec)\.[cm]?[jt]sx?$/;

function edgeStatus(dependency: IDependency, sources: Set<string>) {
  if (dependency.couldNotResolve)
    return dependency.rules?.some(
      rule => rule.name === 'no-unresolved-local-imports',
    )
      ? ('UNRESOLVED' as const)
      : ('EXTERNAL' as const);
  if (
    dependency.coreModule ||
    dependency.dependencyTypes.some(type => type.startsWith('npm'))
  )
    return 'EXTERNAL' as const;
  return sources.has(dependency.resolved)
    ? ('RESOLVED_LOCAL' as const)
    : ('OUTSIDE_SCOPE' as const);
}

async function impact(
  graph: ICruiseResult,
  file: string,
  sources: Set<string>,
) {
  const result = await format(graph, {
    outputType: 'json',
    reaches: {path: `^${RegExp.escape(file)}$`},
  });
  const filtered = JSON.parse(result.output as string) as ICruiseResult;
  const affected = filtered.modules
    .map(module => module.source)
    .filter(path => sources.has(path))
    .sort();
  const selected = graph.modules.find(module => module.source === file);
  if (!selected)
    throw new Error(`File is outside the dependency graph: ${file}`);
  return {
    file,
    imports: selected.dependencies.map(dependency => ({
      from: file,
      module: dependency.module,
      to: dependency.resolved,
      status: edgeStatus(dependency, sources),
      dynamic: dependency.dynamic,
      dependency_types: dependency.dependencyTypes,
    })),
    dependents: affected.filter(path => path !== file),
    test_candidates: affected.filter(path => testPath.test(path)),
  };
}

export async function inspectGraph(cwd: string, input: unknown) {
  const options = request.parse(input);
  const root = await realpath(cwd);
  if ('file' in options) {
    const error = await getFileAccessError(root, options.file, true);
    if (error) throw new Error(error);
  }
  const snapshot = await snapshotWorkingTree(root);
  const versionable = new Set(
    (
      await runGit(root, [
        'ls-files',
        '--cached',
        '--others',
        '--exclude-standard',
        '-z',
        '--',
        ...repositoryPathspec,
      ])
    ).split('\0'),
  );
  const entries = listCodeFiles(root).filter(path => versionable.has(path));
  const sources = new Set(entries);
  if ('file' in options && !sources.has(options.file))
    throw new Error(`File is outside the indexed code scope: ${options.file}`);
  if (!entries.length) throw new Error('No supported code files to index.');
  const graph = await analyzeImportGraph(root, entries);
  const {error, violations} = graph.summary;
  const details =
    'file' in options ? await impact(graph, options.file, sources) : {};
  const symbol =
    options.choice === 'symbol'
      ? await inspectSymbol(
          root,
          {
            ...graph,
            modules: graph.modules.filter(module => sources.has(module.source)),
          },
          options.file,
          options.line,
          options.column,
        )
      : undefined;
  const after = await snapshotWorkingTree(root);
  if (
    snapshot.revision !== after.revision ||
    snapshot.dirty_hash !== after.dirty_hash
  )
    throw new Error(
      'Working tree changed during graph analysis; rerun the same command.',
    );
  return {
    choice: options.choice,
    snapshot,
    indexed_files: entries.length,
    ...details,
    ...(symbol ? {symbol} : {}),
    policy: {
      status: error ? ('FAIL' as const) : ('PASS' as const),
      errors: error,
      violations,
    },
    limitations: [
      'Fresh static index of Git-versionable JS/TS files using the ESLint ignore list and an explicit node_modules exclusion; symlinks, ignored untracked files, tools, vendor, and agent caches are outside scope.',
      'RESOLVED_LOCAL means dependency-cruiser resolved a local file, not that runtime behavior has been verified. EXTERNAL packages are not indexed or verified; OUTSIDE_SCOPE local edges are not followed.',
      'Computed imports, dynamic dispatch, runtime DI, reflection, and external types may hide relationships. An empty result does not prove there are no consumers.',
      'Test candidates use static import reachability and test/test-directory naming; this does not prove coverage and does not replace the full check suite.',
      'Policy PASS covers static import rules only. Run npm run verify for actual Node resolution, type checks, other policies, and tests. Rerun this graph command after edits; do not reuse it for a different snapshot.',
    ],
  };
}
