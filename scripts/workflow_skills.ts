import {execFile} from 'node:child_process';
import {fromFileUrl, join} from '@std/path';
import {z} from '@zod/zod';
import canonicalize from 'canonicalize';
import {sha256} from './hash.ts';
import {runGit, snapshotWorkingTree} from './workflow_git.ts';

interface Input {
  taskId: string;
  base: string;
  paths: string[];
  tasks?: {id: string; files: string[]}[];
  mode: 'DIRECT' | 'DELEGATE' | 'PARALLEL' | 'REVIEW';
  verify: boolean;
}

function targets(input: Input) {
  return [
    ...new Set([
      ...input.paths,
      ...(input.tasks?.flatMap(task => task.files) ?? []),
    ]),
  ].sort();
}

export function parseCleanCodeScope(output: string) {
  const report = z
    .object({
      selected: z.array(z.string()),
      scope: z.array(
        z.object({
          file: z.string(),
          status: z.enum(['included', 'excluded', 'error']),
        }),
      ),
      diagnostics: z.array(z.unknown()),
    })
    .parse(JSON.parse(output));
  if (
    report.diagnostics.length ||
    report.scope.some(file => file.status === 'error') ||
    canonicalize(report.selected.slice().sort()) !==
      canonicalize(
        report.scope
          .filter(entry => entry.status === 'included')
          .map(entry => entry.file)
          .sort(),
      )
  )
    throw new Error('Clean Code scope failed; run deno task clean-code:scope.');
  return report.selected;
}

async function cleanCodeScope(root: string) {
  const skill = fromFileUrl(
    new URL('../plugins/code/skills/clean-code/', import.meta.url),
  );
  const result = await new Promise<{
    success: boolean;
    code: number;
    stdout: Buffer;
    stderr: Buffer;
  }>((resolve, reject) => {
    execFile(
      Deno.env.get('HOME')
        ? join(Deno.env.get('HOME')!, '.deno/bin/deno')
        : 'deno',
      [
        'run',
        '--config',
        join(skill, 'deno.json'),
        '--lock',
        join(skill, 'deno.lock'),
        '--frozen',
        '--cached-only',
        '--no-prompt',
        '--allow-read',
        '--allow-env',
        join(skill, 'scripts/clean_code.ts'),
        '--scope',
      ],
      {cwd: root, encoding: 'buffer', maxBuffer: Infinity},
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
  if (!result.success)
    throw new Error(
      `Clean Code scope failed (${result.code}); run deno task clean-code:scope. ${new TextDecoder().decode(result.stderr).trim()}`,
    );
  return parseCleanCodeScope(new TextDecoder().decode(result.stdout));
}

export function selectSkills(input: Input, selected: string[]) {
  const clean = targets(input).filter(file => selected.includes(file));
  const code = [...new Set(input.paths)]
    .filter(file => /\.(?:[jt]sx?|[cm][jt]s)$/.test(file))
    .sort();
  return [
    ...(clean.length
      ? [
          {
            name: 'clean-code',
            reason:
              'Task files intersect clean-code:scope selected files. Review only the listed files using the existing skill scope.',
            files: clean,
          },
        ]
      : []),
    ...(input.mode === 'REVIEW' && code.length
      ? [
          {
            name: 'ponytail:ponytail-review',
            reason:
              'REVIEW contains an actual code diff. Read-only complexity review applies to the listed changed paths, including deletions and renames.',
            files: code,
          },
        ]
      : []),
    ...(input.verify
      ? [
          {
            name: 'verification-before-completion',
            reason:
              'Read the actual --verify result and logs before reporting success or failure. A blocked or failed check cannot support a completion claim.',
            files: targets(input),
          },
        ]
      : []),
  ];
}

export async function announceSkillTriggers(
  root: string,
  input: Input,
  expectedSnapshot?: Awaited<ReturnType<typeof snapshotWorkingTree>>,
) {
  const snapshot = expectedSnapshot ?? (await snapshotWorkingTree(root));
  let scope:
    | {status: 'PASS'; selected: string[]}
    | {status: 'ERROR'; error: string};
  try {
    scope = {
      status: 'PASS',
      selected: targets(input).length ? await cleanCodeScope(root) : [],
    };
  } catch (error) {
    scope = {status: 'ERROR', error: String(error)};
  }
  const mode = scope.status === 'ERROR' ? 'REVIEW' : input.mode;
  const choices = selectSkills(
    {...input, mode},
    scope.status === 'PASS' ? scope.selected : [],
  );
  if (canonicalize(snapshot) !== canonicalize(await snapshotWorkingTree(root)))
    throw new Error(
      'Code changed during skill scope selection; rerun workflow.',
    );
  const directory = (
    await runGit(root, [
      'rev-parse',
      '--path-format=absolute',
      '--git-path',
      'workflow/skill-triggers',
    ])
  ).trim();
  if (choices.length) await Deno.mkdir(directory, {recursive: true});
  const triggers = [];
  for (const choice of choices) {
    const context = {
      task_id: input.taskId,
      base: input.base,
      scope: targets(input),
      snapshot,
      skill: choice.name,
      files: choice.files,
    };
    const record = canonicalize(context)!;
    const id = await sha256(record);
    let status = 'ANNOUNCED';
    try {
      await Deno.writeTextFile(join(directory, `${id}.json`), record, {
        createNew: true,
        mode: 0o600,
      });
    } catch (error) {
      if (!(error instanceof Deno.errors.AlreadyExists)) throw error;
      status = 'ALREADY_ANNOUNCED';
    }
    triggers.push({...choice, id, status});
  }
  return {
    snapshot,
    mode,
    scope,
    triggers,
    instructions: [
      ...(scope.status === 'ERROR'
        ? [
            'Clean Code scope failed and blocks this workflow result. Fix the reported scope error and rerun; an unavailable scope is not an exclusion or completion evidence.',
          ]
        : []),
      'Skill triggers add guidance to existing native and direct triggers. ANNOUNCED/ALREADY_ANNOUNCED record guidance only, never skill loading, execution, review, or completion. Direct invocation remains available regardless of these records.',
      ...triggers
        .filter(trigger => trigger.status === 'ANNOUNCED')
        .map(
          trigger =>
            `Use ${trigger.name}: ${trigger.reason} Load its existing SKILL.md through the current Codex or Claude Code skill catalogue; if unavailable, report that limit without claiming it ran.`,
        ),
    ],
  };
}
