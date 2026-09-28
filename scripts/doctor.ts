import {
  createCommand,
  createReport,
  runCli,
  ValidationError,
} from '../plugins/code/skills/clean-code/scripts/cli.ts';
import {
  basename,
  dirname,
  fromFileUrl,
  isAbsolute,
  join,
  resolve,
} from '@std/path';
import {sha256} from './hash.ts';

const defaults = {
  deno: Deno.execPath(),
  quarto: '/usr/local/bin/quarto',
  lychee: 'lychee',
};
const versions = {
  deno: '2.9.6',
  quarto: '1.10.18',
  uv: '0.11.32',
  'git-flow': '2.1.0',
  lychee: '0.24.2',
};
type Tool = keyof typeof versions;
interface NpmLock {
  lockfileVersion?: number;
  packages?: Record<string, {version?: string}>;
}
interface Options {
  deno?: string;
  quarto?: string;
  uv?: string;
  gitFlow?: string;
  git?: string;
  node?: string;
  npm?: string;
  report?: string;
}

function rejectReadme(path: string) {
  if (path.split(/[\\/]/).some(part => /^readme\.md$/i.test(part)))
    throw new Error('README paths are not allowed');
}

async function executable(selected: string, tool: Tool) {
  rejectReadme(selected);
  if (!isAbsolute(selected)) throw new Error(`${tool} path must be absolute`);
  const canonical = await Deno.realPath(selected);
  rejectReadme(canonical);
  for (const path of [selected, canonical]) {
    if (/(^|[\\/])\.venv([\\/]|$)/i.test(path))
      throw new Error(`${tool} must be outside .venv`);
    if (tool === 'deno' && /(^|[\\/])quarto(?:-[^\\/]+)?([\\/]|$)/i.test(path))
      throw new Error('Deno must be standalone, outside Quarto');
  }
  const info = await Deno.stat(canonical);
  if (!info.isFile || (info.mode !== null && (info.mode & 0o111) === 0))
    throw new Error(`${tool} must be an executable regular file`);
  return {selected, canonical};
}

export async function probeVersion(path: string, tool: Tool) {
  const result = await new Deno.Command(path, {
    args: [tool === 'git-flow' ? 'version' : '--version'],
    signal: AbortSignal.timeout(5000),
    stdout: 'piped',
    stderr: 'null',
  }).output();
  if (!result.success || result.stdout.length > 4096)
    throw new Error(`${tool} version probe failed`);
  const output = new TextDecoder().decode(result.stdout).trim();
  const version =
    tool === 'quarto'
      ? output
      : tool === 'git-flow'
        ? /^(\S+) \(git-flow-next\)$/.exec(output)?.[1]
        : new RegExp(`^${tool} (\\S+)`).exec(output)?.[1];
  if (version !== versions[tool])
    throw new Error(`${tool} must report version ${versions[tool]}`);
  return version;
}

async function checkUvEnvironment(
  uv: string,
  project: string,
  repair = `uv sync --locked --project ${project}`,
) {
  const result = await new Deno.Command(uv, {
    args: ['sync', '--locked', '--check', '--project', project],
    cwd: fromFileUrl(new URL('../', import.meta.url)),
    signal: AbortSignal.timeout(30_000),
    stdout: 'null',
    stderr: 'null',
  }).output();
  if (!result.success)
    throw new Error(
      `${project} environment is missing or out of sync with uv.lock; run ${repair}.`,
    );
  return {
    project,
    python: `${project}/.venv/bin/python`,
    sync: 'PASS' as const,
  };
}

async function probeNodeVersion(path: string) {
  let result: Deno.CommandOutput;
  try {
    result = await new Deno.Command(path, {
      args: ['--version'],
      signal: AbortSignal.timeout(5000),
      stdout: 'piped',
      stderr: 'null',
    }).output();
  } catch (error) {
    if (error instanceof Deno.errors.NotFound)
      throw new Error(
        'Node.js 22 or later is required, but node was not found.',
      );
    throw error;
  }
  if (!result.success || result.stdout.length > 4096)
    throw new Error('node version probe failed');
  const output = new TextDecoder().decode(result.stdout).trim();
  const version = /^v?(\d+)\.(\d+)\.(\d+)$/.exec(output);
  if (!version) throw new Error('node version probe failed');
  if (Number(version[1]) < 22)
    throw new Error(`Node.js 22 or later is required (found ${output}).`);
  return output.replace(/^v/, '');
}

export async function checkNpmEnvironment(npm: string, project: string) {
  const root = fromFileUrl(new URL('../', import.meta.url));
  const result = await new Deno.Command(npm, {
    args: ['ls', '--all', '--prefix', project],
    cwd: root,
    signal: AbortSignal.timeout(30_000),
    stdout: 'null',
    stderr: 'null',
  }).output();
  const message = `${project} node_modules is missing or out of sync with package-lock.json; run deno task wiki-consistency:install.`;
  if (!result.success) throw new Error(message);
  try {
    const [lockText, installedText] = await Promise.all([
      Deno.readTextFile(resolve(root, project, 'package-lock.json')),
      Deno.readTextFile(
        resolve(root, project, 'node_modules', '.package-lock.json'),
      ),
    ]);
    const lock = JSON.parse(lockText) as NpmLock;
    const installed = JSON.parse(installedText) as NpmLock;
    if (
      lock.lockfileVersion !== installed.lockfileVersion ||
      !lock.packages ||
      !installed.packages ||
      Object.entries(installed.packages).some(
        ([path, pkg]) =>
          pkg.version !== undefined &&
          lock.packages?.[path]?.version !== pkg.version,
      )
    )
      throw new Error(message);
  } catch {
    throw new Error(message);
  }
  return {
    project,
    nodeModules: `${project}/node_modules`,
    npm: 'PASS' as const,
  };
}

async function checkGitFlowConfig(gitFlow: string) {
  const result = await new Deno.Command(gitFlow, {
    args: ['config', 'status'],
    cwd: fromFileUrl(new URL('../', import.meta.url)),
    signal: AbortSignal.timeout(5000),
    stdout: 'null',
    stderr: 'null',
  }).output();
  if (!result.success)
    throw new Error(
      result.code === 6
        ? 'git-flow shared configuration has drifted; run git flow config sync.'
        : `git-flow config status failed (exit ${result.code}).`,
    );
  return {status: 'PASS' as const};
}

async function checkGitHooksPath(git: string) {
  const result = await new Deno.Command(git, {
    args: ['config', '--get', 'core.hooksPath'],
    cwd: fromFileUrl(new URL('../', import.meta.url)),
    signal: AbortSignal.timeout(5000),
    stdout: 'piped',
    stderr: 'null',
  }).output();
  const value = result.success
    ? new TextDecoder().decode(result.stdout).replace(/\r?\n$/, '')
    : undefined;
  if (value !== 'scripts/git-hooks')
    throw new Error(
      'Git hooks are not installed; run git config core.hooksPath scripts/git-hooks.',
    );
  return value;
}

async function dependencies() {
  const path = fromFileUrl(new URL('../deno.lock', import.meta.url));
  const bytes = await Deno.readFile(path);
  const lock = JSON.parse(new TextDecoder().decode(bytes)) as {
    workspace: {dependencies: string[]};
    specifiers: Record<string, string>;
  };
  const selected = Object.fromEntries(
    lock.workspace.dependencies.map(specifier => {
      const resolved = lock.specifiers[specifier];
      if (!resolved) throw new Error(`Missing locked dependency: ${specifier}`);
      return [specifier, resolved.split('_')[0]];
    }),
  );
  return {path, sha256: await sha256(bytes), dependencies: selected};
}

async function writeReport(path: string, contents: string) {
  rejectReadme(path);
  const absolute = resolve(path);
  const parent = await Deno.realPath(dirname(absolute));
  rejectReadme(parent);
  await Deno.writeTextFile(join(parent, basename(absolute)), contents, {
    createNew: true,
    mode: 0o600,
  });
}

export async function runDoctor(options: Options = {}) {
  const deno = await executable(options.deno ?? defaults.deno, 'deno');
  if (deno.canonical !== (await Deno.realPath(Deno.execPath())))
    throw new Error('Configured Deno differs from the executing Deno');
  if (Deno.version.deno !== versions.deno)
    throw new Error(`Executing Deno must be ${versions.deno}`);
  const quarto = await executable(options.quarto ?? defaults.quarto, 'quarto');
  const uv = options.uv
    ? await executable(options.uv, 'uv')
    : {selected: 'uv', canonical: 'uv'};
  const gitFlow = options.gitFlow
    ? await executable(options.gitFlow, 'git-flow')
    : {selected: 'git-flow', canonical: 'git-flow'};
  const lychee = {selected: defaults.lychee, canonical: defaults.lychee};
  const node = {
    selected: options.node ?? 'node',
    canonical: options.node ?? 'node',
  };
  const npm = options.npm ?? 'npm';
  const [
    denoVersion,
    quartoVersion,
    uvVersion,
    gitFlowVersion,
    lycheeVersion,
    nodeVersion,
    lock,
  ] = await Promise.all([
    probeVersion(deno.canonical, 'deno'),
    probeVersion(quarto.canonical, 'quarto'),
    probeVersion(uv.canonical, 'uv'),
    probeVersion(gitFlow.canonical, 'git-flow'),
    probeVersion(lychee.canonical, 'lychee'),
    probeNodeVersion(node.canonical),
    dependencies(),
  ]);
  const specKit = await checkUvEnvironment(uv.canonical, 'tools/spec-kit');
  const docRegions = await checkUvEnvironment(
    uv.canonical,
    'packages/doc-regions',
  );
  const wikiConsistency = {
    ...(await checkUvEnvironment(
      uv.canonical,
      'packages/wiki-consistency',
      'deno task wiki-consistency:install',
    )),
    ...(await checkNpmEnvironment(npm, 'packages/wiki-consistency')),
  };
  const gitFlowConfig = await checkGitFlowConfig(gitFlow.canonical);
  const gitHooksPath = await checkGitHooksPath(options.git ?? 'git');
  const report = {
    status: 'PASS' as const,
    runtime: {version: Deno.version, build: Deno.build},
    deno: {...deno, version: denoVersion},
    quarto: {...quarto, version: quartoVersion},
    uv: {...uv, version: uvVersion},
    gitFlow: {...gitFlow, version: gitFlowVersion, config: gitFlowConfig},
    lychee: {...lychee, version: lycheeVersion},
    node: {...node, version: nodeVersion},
    gitHooksPath,
    specKit,
    docRegions,
    wikiConsistency,
    lock,
  };
  if (options.report)
    await writeReport(options.report, `${JSON.stringify(report, null, 2)}\n`);
  return report;
}

if (import.meta.main) {
  await runCli(() =>
    createCommand(
      'doctor',
      'Check runtime identities, versions and locked dependencies.',
    )
      .option('--deno <path:string>', 'Absolute path to standalone Deno.')
      .option('--quarto <path:string>', 'Absolute path to Quarto.')
      .option(
        '--report <path:string>',
        'Create a new JSON report; requires write permission.',
      )
      .action(async options => {
        if (
          [options.deno, options.quarto, options.report].some(
            value => value === '',
          )
        )
          throw new ValidationError('Option values must not be empty.');
        if (
          [options.deno, options.quarto].some(
            value => value !== undefined && !isAbsolute(value),
          )
        )
          throw new ValidationError('Executable paths must be absolute.');
        createReport(await runDoctor(options));
      })
      .parse(Deno.args),
  );
}
