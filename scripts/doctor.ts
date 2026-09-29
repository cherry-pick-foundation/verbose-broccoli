import {execFile} from 'node:child_process';
import {readFile, realpath, stat, writeFile} from 'node:fs/promises';
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
  quarto: '/usr/local/bin/quarto',
  lychee: 'lychee',
};
const versions = {
  quarto: '1.10.18',
  uv: '0.11.32',
  'git-flow': '2.1.0',
  lychee: '0.24.2',
};
type Tool = keyof typeof versions;
interface NpmLock {
  lockfileVersion?: number;
  packages?: Record<
    string,
    {
      version?: string;
      dependencies?: Record<string, string>;
      devDependencies?: Record<string, string>;
    }
  >;
}
interface Options {
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
  const canonical = await realpath(selected);
  rejectReadme(canonical);
  for (const path of [selected, canonical]) {
    if (/(^|[\\/])\.venv([\\/]|$)/i.test(path))
      throw new Error(`${tool} must be outside .venv`);
  }
  const info = await stat(canonical);
  if (!info.isFile() || (info.mode & 0o111) === 0)
    throw new Error(`${tool} must be an executable regular file`);
  return {selected, canonical};
}

function command(
  file: string,
  args: string[],
  options: {
    cwd?: string;
    signal?: AbortSignal;
    stdout?: 'piped' | 'null';
    stderr?: 'piped' | 'null';
  } = {},
) {
  return new Promise<{
    success: boolean;
    code: number;
    stdout: Buffer;
    stderr: Buffer;
  }>((resolve, reject) => {
    execFile(
      file,
      args,
      {
        cwd: options.cwd,
        signal: options.signal,
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
          stdout: options.stdout === 'null' ? Buffer.alloc(0) : stdout,
          stderr: options.stderr === 'null' ? Buffer.alloc(0) : stderr,
        });
      },
    );
  });
}

export async function probeVersion(path: string, tool: Tool) {
  const result = await command(
    path,
    [tool === 'git-flow' ? 'version' : '--version'],
    {
      signal: AbortSignal.timeout(5000),
      stdout: 'piped',
      stderr: 'null',
    },
  );
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
  const result = await command(
    uv,
    ['sync', '--locked', '--check', '--project', project],
    {
      cwd: fromFileUrl(new URL('../', import.meta.url)),
      signal: AbortSignal.timeout(30_000),
      stdout: 'null',
      stderr: 'null',
    },
  );
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

async function checkUvWorkspace(uv: string) {
  const result = await command(
    uv,
    ['sync', '--locked', '--check', '--all-packages', '--extra', 'education'],
    {
      cwd: fromFileUrl(new URL('../', import.meta.url)),
      signal: AbortSignal.timeout(30_000),
      stdout: 'null',
      stderr: 'null',
    },
  );
  if (!result.success)
    throw new Error(
      'Python workspace is missing or out of sync with uv.lock; run uv sync --locked --all-packages --extra education.',
    );
  return {project: '.', python: '.venv/bin/python', sync: 'PASS' as const};
}

async function probeNodeVersion(path: string) {
  let result: Awaited<ReturnType<typeof command>>;
  try {
    result = await command(path, ['--version'], {
      signal: AbortSignal.timeout(5000),
      stdout: 'piped',
      stderr: 'null',
    });
  } catch (error) {
    if (
      typeof error === 'object' &&
      error !== null &&
      'code' in error &&
      error.code === 'ENOENT'
    )
      throw new Error(
        'Node.js 24.12.0 or later is required, but node was not found.',
      );
    throw error;
  }
  if (!result.success || result.stdout.length > 4096)
    throw new Error('node version probe failed');
  const output = new TextDecoder().decode(result.stdout).trim();
  const version = /^v?(\d+)\.(\d+)\.(\d+)$/.exec(output);
  if (!version) throw new Error('node version probe failed');
  const major = Number(version[1]);
  const minor = Number(version[2]);
  if (major < 24 || (major === 24 && minor < 12))
    throw new Error(`Node.js 24.12.0 or later is required (found ${output}).`);
  return output.replace(/^v/, '');
}

export async function checkNpmEnvironment(
  npm: string,
  project: string,
  repair = 'npm ci',
) {
  const root = fromFileUrl(new URL('../', import.meta.url));
  const result = await command(npm, ['ls', '--all', '--prefix', project], {
    cwd: root,
    signal: AbortSignal.timeout(30_000),
    stdout: 'null',
    stderr: 'null',
  });
  const message = `${project} node_modules is missing or out of sync with package-lock.json; run ${repair}.`;
  if (!result.success) throw new Error(message);
  try {
    const [lockText, installedText] = await Promise.all([
      readFile(resolve(root, project, 'package-lock.json'), 'utf8'),
      readFile(
        resolve(root, project, 'node_modules', '.package-lock.json'),
        'utf8',
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
  const result = await command(gitFlow, ['config', 'status'], {
    cwd: fromFileUrl(new URL('../', import.meta.url)),
    signal: AbortSignal.timeout(5000),
    stdout: 'null',
    stderr: 'null',
  });
  if (!result.success)
    throw new Error(
      result.code === 6
        ? 'git-flow shared configuration has drifted; run git flow config sync.'
        : `git-flow config status failed (exit ${result.code}).`,
    );
  return {status: 'PASS' as const};
}

async function checkGitHooksPath(git: string) {
  const result = await command(git, ['config', '--get', 'core.hooksPath'], {
    cwd: fromFileUrl(new URL('../', import.meta.url)),
    signal: AbortSignal.timeout(5000),
    stdout: 'piped',
    stderr: 'null',
  });
  const value = result.success
    ? new TextDecoder().decode(result.stdout).replace(/\r?\n$/, '')
    : undefined;
  if (value !== 'scripts/git-hooks')
    throw new Error(
      'Git hooks are not installed; run git config core.hooksPath scripts/git-hooks.',
    );
  return value;
}

export function lockedDependencies(packages: NonNullable<NpmLock['packages']>) {
  const direct = {
    ...(packages['']?.dependencies ?? {}),
    ...(packages['']?.devDependencies ?? {}),
  };
  return Object.fromEntries(
    Object.keys(direct).map(name => {
      const version = packages[`node_modules/${name}`]?.version;
      if (!version) throw new Error(`Missing locked dependency: ${name}`);
      return [name, version];
    }),
  );
}

async function dependencies() {
  const path = fromFileUrl(new URL('../package-lock.json', import.meta.url));
  const bytes = await readFile(path);
  const lock = JSON.parse(new TextDecoder().decode(bytes)) as NpmLock;
  const selected = lockedDependencies(lock.packages ?? {});
  return {path, sha256: await sha256(bytes), dependencies: selected};
}

export async function probeTurboVersion(path: string, expected: string) {
  let result: Awaited<ReturnType<typeof command>>;
  try {
    result = await command(path, ['--version'], {
      signal: AbortSignal.timeout(5000),
      stdout: 'piped',
      stderr: 'null',
    });
  } catch {
    throw new Error('turbo version probe failed; run npm ci.');
  }
  if (!result.success || result.stdout.length > 4096)
    throw new Error('turbo version probe failed; run npm ci.');
  const output = new TextDecoder().decode(result.stdout).trim();
  if (output !== expected)
    throw new Error(`turbo must report version ${expected}; run npm ci.`);
  return output;
}

async function writeReport(path: string, contents: string) {
  rejectReadme(path);
  const absolute = resolve(path);
  const parent = await realpath(dirname(absolute));
  rejectReadme(parent);
  await writeFile(join(parent, basename(absolute)), contents, {
    flag: 'wx',
    mode: 0o600,
  });
}

export async function runDoctor(options: Options = {}) {
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
    quartoVersion,
    uvVersion,
    gitFlowVersion,
    lycheeVersion,
    nodeVersion,
    lock,
  ] = await Promise.all([
    probeVersion(quarto.canonical, 'quarto'),
    probeVersion(uv.canonical, 'uv'),
    probeVersion(gitFlow.canonical, 'git-flow'),
    probeVersion(lychee.canonical, 'lychee'),
    probeNodeVersion(node.canonical),
    dependencies(),
  ]);
  const root = fromFileUrl(new URL('../', import.meta.url));
  const turboVersion = await probeTurboVersion(
    join(root, 'node_modules/.bin/turbo'),
    lock.dependencies.turbo,
  );
  const specKit = await checkUvEnvironment(uv.canonical, 'tools/spec-kit');
  const shellCheck = await checkUvEnvironment(uv.canonical, 'tools/shellcheck');
  const ruff = await checkUvEnvironment(uv.canonical, 'tools/ruff');
  const scc = await checkUvEnvironment(uv.canonical, 'tools/scc');
  const [uvWorkspace, rootNpm, wikiConsistency] = await Promise.all([
    checkUvWorkspace(uv.canonical),
    checkNpmEnvironment(npm, '.'),
    checkNpmEnvironment(
      npm,
      'packages/wiki-consistency',
      'npm run wiki-consistency:install',
    ),
  ]);
  const gitFlowConfig = await checkGitFlowConfig(gitFlow.canonical);
  const gitHooksPath = await checkGitHooksPath(options.git ?? 'git');
  const report = {
    status: 'PASS' as const,
    runtime: {
      version: process.version,
      platform: process.platform,
      arch: process.arch,
    },
    quarto: {...quarto, version: quartoVersion},
    uv: {...uv, version: uvVersion},
    gitFlow: {...gitFlow, version: gitFlowVersion, config: gitFlowConfig},
    lychee: {...lychee, version: lycheeVersion},
    turbo: {path: 'node_modules/.bin/turbo', version: turboVersion},
    node: {...node, version: nodeVersion},
    gitHooksPath,
    specKit,
    shellCheck,
    ruff,
    scc,
    uvWorkspace,
    rootNpm,
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
      .option('--quarto <path:string>', 'Absolute path to Quarto.')
      .option(
        '--report <path:string>',
        'Create a new JSON report; requires write permission.',
      )
      .action(async options => {
        if ([options.quarto, options.report].some(value => value === ''))
          throw new ValidationError('Option values must not be empty.');
        if (
          [options.quarto].some(
            value => value !== undefined && !isAbsolute(value),
          )
        )
          throw new ValidationError('Executable paths must be absolute.');
        createReport(await runDoctor(options));
      })
      .parse(process.argv.slice(2)),
  );
}
