import {execFile} from 'node:child_process';
import {mkdir, open, readFile, realpath, writeFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {join} from '@std/path';
import {Ajv2020} from 'ajv/dist/2020.js';
import canonicalize from 'canonicalize';
import {sha256} from './hash.ts';
import {runGit, snapshotWorkingTree} from './workflow_git.ts';
import schema from './workflow-evidence.schema.json' with {type: 'json'};

const lockfile = createRequire(import.meta.url)('proper-lockfile') as {
  lock(
    path: string,
    options?: {
      retries?:
        number | {retries: number; minTimeout: number; maxTimeout: number};
    },
  ): Promise<() => Promise<void>>;
};

type State = Awaited<ReturnType<typeof snapshotWorkingTree>>;
interface Context {
  task_id: string;
  root: string;
  base: string;
  plan_hash: string;
  node_version: string;
  command: string;
}
export interface EvidenceRecord {
  event: 'STARTED' | 'FINISHED';
  run_id: string;
  context: Context;
  before: State;
  after: State | null;
  exit_code: number | null;
  started_at: string;
  finished_at: string | null;
  log_path: string;
  log_hash: string | null;
}
interface Options {
  taskId: string;
  base: string;
  plan: unknown;
  verify?: boolean;
}
const ajv = new Ajv2020({allErrors: true});
const valid = ajv.compile<EvidenceRecord>(schema);

function validate(value: unknown): EvidenceRecord {
  if (!valid(value))
    throw new Error(
      `Invalid workflow evidence: ${ajv.errorsText(valid.errors)}`,
    );
  return value;
}

async function load(path: string) {
  const text = await readFile(path, 'utf8').catch(error => {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return '';
    throw error;
  });
  if (text && !text.endsWith('\n'))
    throw new Error('Incomplete workflow evidence record');
  const records = text
    .split('\n')
    .filter(Boolean)
    .map(line => JSON.parse(line) as unknown)
    .filter(value => {
      if (
        typeof value !== 'object' ||
        value === null ||
        !('context' in value) ||
        typeof value.context !== 'object' ||
        value.context === null
      )
        return true;
      return !('deno_version' in value.context);
    })
    .map(validate);
  const started = new Map<string, EvidenceRecord>();
  for (const record of records) {
    if (record.event === 'STARTED') started.set(record.run_id, record);
    else {
      const previous = started.get(record.run_id);
      if (
        !previous ||
        canonicalize([
          previous.context,
          previous.before,
          previous.started_at,
          previous.log_path,
        ]) !==
          canonicalize([
            record.context,
            record.before,
            record.started_at,
            record.log_path,
          ])
      )
        throw new Error('Unpaired workflow evidence result');
      started.delete(record.run_id);
    }
  }
  return records;
}

async function append(path: string, record: EvidenceRecord) {
  await writeFile(path, `${JSON.stringify(validate(record))}\n`, {
    flag: 'a',
    mode: 0o600,
  });
}

function passed(record: EvidenceRecord) {
  return (
    record.event === 'FINISHED' &&
    record.exit_code === 0 &&
    canonicalize(record.before) === canonicalize(record.after)
  );
}

async function verify(
  context: Context,
  evidencePath: string,
  directory: string,
) {
  const run_id = crypto.randomUUID();
  const start: EvidenceRecord = {
    event: 'STARTED',
    run_id,
    context,
    before: await snapshotWorkingTree(context.root),
    after: null,
    exit_code: null,
    started_at: new Date().toISOString(),
    finished_at: null,
    log_path: join(directory, `${run_id}.log`),
    log_hash: null,
  };
  await append(evidencePath, start);
  let exit_code = 1;
  let log = '';
  let after = null;
  try {
    const result = await new Promise<{
      success: boolean;
      code: number;
      stdout: Buffer;
      stderr: Buffer;
    }>((resolve, reject) => {
      execFile(
        'npm',
        ['run', 'check'],
        {cwd: context.root, encoding: 'buffer', maxBuffer: Infinity},
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
    });
    exit_code = result.code;
    log = `${new TextDecoder().decode(result.stdout)}\n${new TextDecoder().decode(result.stderr)}`;
  } catch (error) {
    log = String(error);
  }
  try {
    after = await snapshotWorkingTree(context.root);
  } catch (error) {
    log += `\n${String(error)}`;
  }
  await writeFile(start.log_path, log, {mode: 0o600});
  const finish: EvidenceRecord = {
    ...start,
    event: 'FINISHED',
    after,
    exit_code,
    finished_at: new Date().toISOString(),
    log_hash: await sha256(log),
  };
  await append(evidencePath, finish);
  return [start, finish];
}

export async function evaluateVerification(root: string, options: Options) {
  const context: Context = {
    task_id: options.taskId,
    root: await realpath(root),
    base: options.base,
    plan_hash: await sha256(canonicalize(options.plan) ?? 'null'),
    node_version: process.version,
    command: 'npm run check',
  };
  const directory = (
    await runGit(root, [
      'rev-parse',
      '--path-format=absolute',
      '--git-path',
      'workflow',
    ])
  ).trim();
  await mkdir(directory, {recursive: true, mode: 0o700});
  const evidencePath = join(directory, 'evidence.jsonl');
  const lockPath = join(directory, 'lock');
  const lockFile = await open(lockPath, 'a', 0o600);
  await lockFile.close();
  const release = await lockfile.lock(lockPath, {
    retries: {retries: 600, minTimeout: 1000, maxTimeout: 1000},
  });
  try {
    const records = await load(evidencePath);
    if (options.verify)
      records.push(...(await verify(context, evidencePath, directory)));
    const history = records.filter(
      record => canonicalize(record.context) === canonicalize(context),
    );
    const latest = history.at(-1) ?? null;
    let consecutiveFailures = 0;
    for (const record of history.toReversed()) {
      if (record.event !== 'FINISHED') continue;
      if (passed(record)) break;
      consecutiveFailures++;
    }
    const state = await snapshotWorkingTree(root);
    const fresh =
      latest &&
      passed(latest) &&
      canonicalize(latest.after) === canonicalize(state);
    const logValid =
      fresh &&
      (await readFile(latest.log_path)
        .then(async data => (await sha256(data)) === latest.log_hash)
        .catch(() => false));
    const phase = !latest
      ? 'IMPLEMENT'
      : fresh && logValid
        ? 'VERIFIED'
        : consecutiveFailures >= 2
          ? 'REVIEW'
          : passed(latest)
            ? 'IMPLEMENT'
            : 'REPAIR';
    const instructions =
      phase === 'VERIFIED'
        ? [
            'Configured checks passed for the current code state. Finish any required diff review and task acceptance checks before reporting completion.',
          ]
        : [
            phase === 'REVIEW'
              ? 'Two consecutive verification failures: main must review the log and replan or delegate diagnosis before another repair attempt; no extra user approval is required.'
              : phase === 'REPAIR'
                ? 'Verification failed, was interrupted, or the code changed during checks. Read the log, repair the cause, and verify again.'
                : 'Plan and implement the requested change; previous evidence does not verify the current code state.',
          ];
    if (phase !== 'VERIFIED')
      instructions.push(
        'After workers finish, run npm run verify with the same --task, --base and --plan arguments. Repeat diagnosis → repair → verification until current checks pass.',
      );
    instructions.push(
      'Evidence is local execution history, not signed provenance or filesystem isolation.',
    );
    return {
      phase,
      consecutive_failures: consecutiveFailures,
      evidence_path: evidencePath,
      latest,
      instructions,
    };
  } finally {
    await release();
  }
}
