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
};
const versions = {deno: '2.9.6', quarto: '1.10.18', uv: '0.11.32'};
type Tool = keyof typeof versions;
interface Options {
  deno?: string;
  quarto?: string;
  uv?: string;
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
    args: ['--version'],
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
      : new RegExp(`^${tool} (\\S+)`).exec(output)?.[1];
  if (version !== versions[tool])
    throw new Error(`${tool} must report version ${versions[tool]}`);
  return version;
}

async function checkSpecKitEnvironment(uv: string) {
  const project = 'tools/spec-kit';
  const result = await new Deno.Command(uv, {
    args: ['sync', '--locked', '--check', '--project', project],
    cwd: fromFileUrl(new URL('../', import.meta.url)),
    signal: AbortSignal.timeout(30_000),
    stdout: 'null',
    stderr: 'null',
  }).output();
  if (!result.success)
    throw new Error(
      `Spec Kit environment is missing or out of sync with uv.lock; run uv sync --locked --project ${project}.`,
    );
  return {
    project,
    python: `${project}/.venv/bin/python`,
    sync: 'PASS' as const,
  };
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
  const [denoVersion, quartoVersion, uvVersion, lock] = await Promise.all([
    probeVersion(deno.canonical, 'deno'),
    probeVersion(quarto.canonical, 'quarto'),
    probeVersion(uv.canonical, 'uv'),
    dependencies(),
  ]);
  const specKit = await checkSpecKitEnvironment(uv.canonical);
  const report = {
    status: 'PASS' as const,
    runtime: {version: Deno.version, build: Deno.build},
    deno: {...deno, version: denoVersion},
    quarto: {...quarto, version: quartoVersion},
    uv: {...uv, version: uvVersion},
    specKit,
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
