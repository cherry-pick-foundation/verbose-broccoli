import {spawn} from 'node:child_process';
import {realpath, readFile} from 'node:fs/promises';
import {relative, resolve, sep} from 'node:path';
import {join} from '@std/path';

interface Summary {
  version: string;
  turboVersion: string;
  execution: {failed: number; exitCode: number} | null;
}

function summaryPath(line: string) {
  return /^\s*Summary:\s+(.+\.json)\s*$/.exec(line)?.[1].trim();
}

function isSummary(value: unknown): value is Summary {
  if (typeof value !== 'object' || value === null || Array.isArray(value))
    return false;
  const summary = value as Record<string, unknown>;
  const execution = summary.execution;
  return (
    summary.version === '1' &&
    summary.turboVersion === '2.11.5' &&
    typeof execution === 'object' &&
    execution !== null &&
    !Array.isArray(execution) &&
    (execution as Record<string, unknown>).failed === 0 &&
    (execution as Record<string, unknown>).exitCode === 0
  );
}

async function validSummary(root: string, path: string | undefined) {
  if (!path) return false;
  try {
    const worktree = await realpath(root);
    const runs = await realpath(join(worktree, '.turbo/runs'));
    const summaryPath = await realpath(resolve(worktree, path));
    const relativePath = relative(runs, summaryPath);
    if (
      relativePath === '' ||
      relativePath === '..' ||
      relativePath.startsWith(`..${sep}`) ||
      resolve(runs, relativePath) !== summaryPath
    )
      return false;
    return isSummary(
      JSON.parse(await readFile(summaryPath, 'utf8')) as unknown,
    );
  } catch {
    return false;
  }
}

async function runCheck(root: string) {
  const env = {...process.env};
  for (const name of [
    'TURBO_BINARY_PATH',
    'TURBO_TOKEN',
    'TURBO_TEAM',
    'TURBO_TEAMID',
    'VERCEL_ARTIFACTS_TOKEN',
    'VERCEL_ARTIFACTS_OWNER',
  ])
    delete env[name];
  env.TURBO_TELEMETRY_DISABLED = '1';
  env.NO_UPDATE_NOTIFIER = '1';

  return await new Promise<{exitCode: number | null; summaryPath?: string}>(
    resolve => {
      const child = spawn('npm', ['run', 'check'], {
        cwd: root,
        env,
        stdio: ['ignore', 'pipe', 'pipe'],
      });
      let pending = '';
      let path: string | undefined;
      child.stdout.on('data', chunk => {
        process.stdout.write(chunk);
        const lines = `${pending}${chunk.toString('utf8')}`.split('\n');
        pending = lines.pop() ?? '';
        if (pending.length > 4096) pending = pending.slice(-4096);
        for (const line of lines) path = summaryPath(line) ?? path;
      });
      child.stderr.pipe(process.stderr);
      let settled = false;
      child.once('error', () => {
        settled = true;
        resolve({exitCode: null});
      });
      child.once('close', code => {
        if (settled) return;
        path = summaryPath(pending) ?? path;
        resolve({exitCode: code, ...(path ? {summaryPath: path} : {})});
      });
    },
  );
}

export async function evaluateVerification(root: string, verify = false) {
  if (!verify)
    return {
      phase: 'NOT_RUN' as const,
      instructions: ['Run npm run verify to execute the configured checks.'],
    };

  const child = await runCheck(root);
  const verified =
    child.exitCode === 0 && (await validSummary(root, child.summaryPath));
  if (verified) process.stdout.write('VERIFIED\n');
  return {
    phase: verified ? ('VERIFIED' as const) : ('FAILED' as const),
    instructions: verified
      ? []
      : [
          'npm run check failed or did not produce a valid same-run Turbo summary. Repair the cause and rerun npm run verify.',
        ],
  };
}
