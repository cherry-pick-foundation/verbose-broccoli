import {spawnSync} from 'node:child_process';
import {createReadStream, readFileSync} from 'node:fs';
import {homedir} from 'node:os';
import {basename, dirname, isAbsolute, join, resolve} from 'node:path';
import {createInterface} from 'node:readline';
import {fileURLToPath} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');

async function compactions(path: string, client: string, session: string) {
  let count = 0;
  let matching = false;
  const boundaries = new Set<string>();
  const lines = createInterface({
    input: createReadStream(path),
    crlfDelay: Infinity,
  });
  try {
    for await (const line of lines) {
      if (!line.trim()) continue;
      const record = JSON.parse(line);
      if (client === 'codex') {
        if (record.type === 'session_meta') {
          matching = record.payload?.id === session;
        }
        if (matching && record.type === 'compacted') count++;
      } else if (record.sessionId === session) {
        matching = true;
        if (record.type === 'system' && record.subtype === 'compact_boundary') {
          if (typeof record.uuid !== 'string')
            throw new Error('Missing boundary ID');
          boundaries.add(record.uuid);
        }
      }
    }
  } finally {
    lines.close();
  }
  if (!matching) throw new Error('Transcript session does not match');
  return client === 'codex' ? count : boundaries.size;
}

async function main() {
  const input = JSON.parse(readFileSync(0, 'utf8'));
  const client = process.argv[2];
  if (
    !['codex', 'claude'].includes(client) ||
    input.hook_event_name !== 'SessionStart' ||
    !['startup', 'resume', 'clear', 'compact'].includes(input.source) ||
    typeof input.session_id !== 'string' ||
    !input.session_id
  )
    throw new Error('Invalid SessionStart input');
  const config = JSON.parse(
    readFileSync(join(root, '.config/coordinator-context.json'), 'utf8'),
  );
  const worktree = config.worktreeAliases[basename(root)] ?? basename(root);
  const role = ['main', 'develop'].includes(worktree) ? worktree : 'feature';
  const threshold = config.thresholds[role];
  if (
    !Number.isInteger(threshold) ||
    threshold < 1 ||
    !Number.isInteger(config.maxContextBytes) ||
    config.maxContextBytes < 1 ||
    config.maxContextBytes > 65536
  )
    throw new Error('Invalid threshold or context bound');
  const stateHome = process.env.XDG_STATE_HOME;
  const state = join(
    stateHome && isAbsolute(stateHome)
      ? stateHome
      : join(homedir(), '.local/state'),
    config.stateDirectory,
    worktree,
    config.stateFile,
  );
  const paths = [
    ...config.notes.map((path: string) =>
      path.startsWith('~/')
        ? join(homedir(), path.slice(2))
        : resolve(root, path),
    ),
    state,
  ];
  const contents = paths.map(path => {
    try {
      return readFileSync(path, 'utf8');
    } catch {
      return `Unavailable source: ${path}. Read it in full when available; do not invent its contents.`;
    }
  });
  const owner = `Coordinator session: ${client}/${input.session_id}`;
  let instructions = `If this output is truncated or spilled, read every source in full before continuing, in chunks without omitted middle text: ${paths.join(', ')}. Restore the standing notes and current state below in full. Only if your assigned role is this worktree's coordinator, before starting other work overwrite ${state} in place with decisions, holds/reasons, live owners, open questions and next steps; preserve existing decisions and explicitly set the single owner line to ${owner}. Narrow workers must not claim or write coordinator state. Fresh sessions and every compaction require the complete notes and state, never a summary.\n`;
  const ownerLines = contents
    .at(-1)!
    .split(/\r?\n/)
    .filter(line => line.startsWith('Coordinator session: '));
  if (
    ownerLines.length === 1 &&
    ownerLines[0] === owner &&
    ['compact', 'resume'].includes(input.source)
  ) {
    try {
      const count = await compactions(
        input.transcript_path,
        client,
        input.session_id,
      );
      instructions += `This session has ${count} compactions; ${role} threshold is ${threshold}.\n`;
      if (count >= threshold) {
        instructions += `Update ${state} now with decisions, holds/reasons, live owners, questions and next steps. Start no new work. Wait for the user to start a fresh coordinator; do not restart or kill any session.\n`;
        if (input.source === 'compact') {
          const notice = spawnSync(
            'notify-send',
            [
              '--app-name=verbose-broccoli',
              'Start a fresh coordinator',
              `${worktree}: ${count} compactions. Save state; start no new work.`,
            ],
            {timeout: 2000},
          );
          if (notice.error || notice.status !== 0)
            instructions +=
              'Notification failed. Tell the user to start a fresh coordinator.\n';
        }
      }
    } catch {
      instructions +=
        'Compaction count unavailable: read the current session transcript; do not assume a zero count.\n';
    }
  }
  const full = paths
    .map((path, i) => `\n--- ${path} ---\n${contents[i]}`)
    .join('\n');
  const context =
    Buffer.byteLength(instructions + full) <= config.maxContextBytes
      ? instructions + full
      : instructions +
        `Read every source in full before continuing, in chunks without omitted middle text:\n${paths.join('\n')}\n`;
  console.log(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        additionalContext: context,
      },
    }),
  );
}

void main().catch(() => {
  console.log(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        additionalContext:
          'Coordinator context hook failed. Read the complete standing notes and your coordinator state using .config/coordinator-context.json before continuing. Narrow workers must not claim coordinator state.',
      },
    }),
  );
});
