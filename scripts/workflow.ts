import {
  createCommand,
  createReport,
  runCli,
  ValidationError,
} from '../plugins/code/skills/clean-code/scripts/cli.ts';
import {importRules} from './clean_architecture.ts';
import {analyzePlan, planSchema, type PlanResult} from './workflow_plan.ts';
import {
  repositoryPathspec,
  runGit,
  snapshotWorkingTree,
} from './workflow_git.ts';
import {evaluateVerification} from './workflow_verify.ts';
import {graphCommands, inspectGraph} from './workflow_graph.ts';
import {announceSkillTriggers} from './workflow_skills.ts';
import {getFileAccessError, repositoryFileSchema} from './workflow_files.ts';

interface Signals {
  paths: string[];
  statuses: string[];
  changedLines: number | null;
  publicEntryChanged: boolean;
  structuralChange?: boolean;
}

const reviewPaths =
  /(^|\/)(AGENTS\.md|deno\.jsonc?|deno\.lock|package\.json|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|plugin\.json|mcp\.json|tsconfig[^/]*\.json|biome\.jsonc?|eslint[^/]*\.[cm]?js|\.prettier[^/]*|\.editorconfig)$|(^|\/)(domain|infrastructure|platform|migrations?|schemas?|contracts)(\/|\.)|^(packages|\.agents|\.codex|\.github|\.specify)\//;
const entryPath = /(^|\/)(mod|index)\.[cm]?[jt]sx?$/;
const diffOptions = [
  '--no-ext-diff',
  '--no-textconv',
  '--find-renames=50%',
  '--diff-algorithm=myers',
  '--no-indent-heuristic',
];

const actions = {
  DIRECT: ['Main implements the change.'],
  DELEGATE: [
    'Use Orca orchestration to assign the listed task to one supervised worker while main prepares integration and review.',
  ],
  PARALLEL: [
    'Use Orca orchestration to launch one supervised worker per listed task concurrently, within available agent slots.',
  ],
  REVIEW: [
    'Main coordinates implementation and resolves the listed review reasons. Before each commit, the implementer or the orchestrator reviews the diff. An independent review by a fresh reviewer from the other provider (Claude Code or Codex) happens when the branch merges into develop (favoring speed) or main (favoring accuracy), not for each change; no extra user approval is needed.',
  ],
};

export function buildWorkModeInstructions(
  mode: keyof typeof actions,
  hasPlan: boolean,
) {
  return [
    ...actions[mode],
    ...(mode === 'DELEGATE' || mode === 'PARALLEL'
      ? [
          'Give each worker its objective, exact writable files from tasks, and acceptance checks. Workers must stop and report scope growth; main owns shared files, installs, Git operations, and integration.',
          'Wait for workers and inspect their changes. If Orca orchestration is unavailable, report that limit and execute sequentially.',
        ]
      : []),
    ...(!hasPlan
      ? [
          'To request delegation or parallel work before editing, write a temporary JSON plan outside the repository: {"tasks":[{"id":"task-name","files":["plugins/code/src/example.ts"]}]}. List exact files for every task and rerun deno task workflow --plan <file>; one task requests delegation, multiple tasks request parallel eligibility.',
        ]
      : []),
    'Rerun deno task workflow with the same --base/--plan arguments after scope changes and before completion; follow the new result. The initial result is provisional, and import-graph checks do not provide runtime resource isolation.',
    'Run deno task verify on the combined result and follow its repair/review instructions until the current code is verified. This runs deno task check and records its actual result.',
    "Linear, main agent only: before the develop merge review, commit the feature's record and move its Linear issue to In Review; after git flow feature finish, move the issue to Done with one completion comment giving the merge commit and the record location instead of a PR link. Ask the user to do in Linear's UI what Orca cannot (archive, delete, labels, projects, documents, cycles, milestones); add no other Linear integration.",
    'Difficulty is advisory and independent of execution mode and verification. Use per-task difficulty with --plan; workspace difficulty includes unrelated changes. Null means insufficient evidence, not an extra level. Select models separately using task requirements and observed performance.',
    'The comparison includes staged, unstaged, and untracked changes. Default baseline is HEAD; use --base <commit-or-ref> to compare against another commit.',
  ];
}

export function selectWorkMode(signals: Signals, plan?: PlanResult) {
  const reasons = [...(plan?.reasons ?? [])];
  const plannedFiles = plan?.tasks.flatMap(task => task.files) ?? [];
  const paths = [...signals.paths, ...plannedFiles];
  if (signals.statuses.some(status => !['A', 'M', '?'].includes(status[0])))
    reasons.push('deletion, rename, conflict, or file type change');
  if (paths.some(path => reviewPaths.test(path)))
    reasons.push(
      'configuration, shared package, schema, or protected layer changed',
    );
  if (signals.publicEntryChanged || paths.some(path => entryPath.test(path)))
    reasons.push('public entry point changed');
  if (signals.changedLines === null) reasons.push('binary or non-regular file');
  if (plan && signals.paths.some(path => !plannedFiles.includes(path)))
    reasons.push('changed files exceed the declared task scopes');
  if (!plan && (signals.paths.length > 2 || (signals.changedLines ?? 0) > 100))
    reasons.push('more than 2 paths or 100 changed lines');
  if (!reasons.length && plan)
    return {
      mode:
        plan.tasks.length > 1 ? ('PARALLEL' as const) : ('DELEGATE' as const),
      reasons: [
        plan.tasks.length > 1
          ? 'disjoint task files and import impact sets'
          : 'one task with an explicit file scope',
      ],
    };
  return {
    mode: reasons.length ? ('REVIEW' as const) : ('DIRECT' as const),
    reasons,
  };
}

const difficultyDescriptions = {
  very_easy: '매우 쉬움: 파일 하나의 작은 변경을 확인합니다.',
  easy: '쉬움: 좁은 파일 범위의 변경을 구현하고 확인합니다.',
  medium: '보통: 여러 파일 또는 늘어난 변경량을 함께 확인합니다.',
  difficult: '어려움: 공개 진입점, 파일 구조 변경 또는 큰 변경량을 검토합니다.',
  very_difficult:
    '매우 어려움: 매우 넓은 파일 범위 또는 변경량을 나누어 검토합니다.',
};

export function assessDifficulty(signals: Signals) {
  const files = signals.paths.length;
  const lines = signals.changedLines;
  const structural =
    signals.structuralChange === true ||
    signals.statuses.some(status => !['A', 'M', '?'].includes(status[0]));
  const rules = [
    [files > 20, 'very_difficult', '변경 파일이 20개를 초과합니다.'],
    [
      (lines ?? 0) > 2000,
      'very_difficult',
      '변경 줄 수가 2,000줄을 초과합니다.',
    ],
    [
      signals.publicEntryChanged,
      'difficult',
      '공개 진입점 변경이 관측되었습니다.',
    ],
    [
      structural,
      'difficult',
      '삭제·이동·충돌·파일 유형 변경이 관측되었습니다.',
    ],
    [files > 5, 'difficult', '변경 파일이 5개를 초과합니다.'],
    [(lines ?? 0) > 500, 'difficult', '변경 줄 수가 500줄을 초과합니다.'],
    [files > 2, 'medium', '변경 파일이 2개를 초과합니다.'],
    [(lines ?? 0) > 100, 'medium', '변경 줄 수가 100줄을 초과합니다.'],
    [files > 1, 'easy', '변경 파일이 1개를 초과합니다.'],
    [(lines ?? 0) > 20, 'easy', '변경 줄 수가 20줄을 초과합니다.'],
    [true, 'very_easy', '변경 파일이 1개이고 변경 줄 수가 20줄 이하입니다.'],
  ] as const;
  const match =
    files && lines !== null ? rules.find(([matches]) => matches) : undefined;
  const level = match?.[1] ?? null;
  return {
    policy: 'coding-difficulty/1',
    level,
    reasons: match
      ? [match[2]]
      : [
          !files
            ? '관측된 변경 파일이 없습니다.'
            : '텍스트 변경량을 측정할 수 없습니다.',
        ],
    description: level
      ? difficultyDescriptions[level]
      : '판정 보류: 관측된 변경이 없거나 텍스트 변경량을 측정할 수 없습니다.',
    facts: {
      changed_files: files,
      changed_lines: lines,
      public_entry_changed: signals.publicEntryChanged,
      structural_change: structural,
    },
    basis:
      'Observed staged plus unstaged Git changes, including earlier edits in selected files; not task history or a net patch. Thresholds are project heuristics, not measured reasoning difficulty or a LOM coding standard. Public entry paths are not semantic API reports. No graph independence, runtime complexity, future work, or model capability is inferred.',
  };
}

function statusRecords(output: string) {
  const fields = output.split('\0').filter(Boolean);
  const records = [];
  for (let index = 0; index < fields.length; ) {
    const status = fields[index++];
    const paths = [fields[index++]];
    if (/^[RC]/.test(status)) paths.push(fields[index++]);
    records.push({status, paths});
  }
  return records;
}

export function parseNameStatus(output: string) {
  const records = statusRecords(output);
  return {
    paths: records.flatMap(record => record.paths),
    statuses: records.map(record => record.status),
  };
}

export function sumNumstatLines(output: string): number | null {
  const records = output.split('\0');
  let lines = 0;
  for (let index = 0; index < records.length; index++) {
    if (!records[index]) continue;
    const match = /^([0-9]+|-)\t([0-9]+|-)\t([\s\S]*)$/.exec(records[index]);
    if (!match) throw new Error('Unexpected git numstat output');
    if (match[1] === '-' || match[2] === '-') return null;
    lines += Number(match[1]) + Number(match[2]);
    if (match[3] === '') index += 2;
  }
  return lines;
}

async function collectSignals(
  root: string,
  revision: string,
  files?: string[],
) {
  const selection = files
    ? files.map(path => `:(top,literal)${path}`)
    : repositoryPathspec;
  const changes = [['--cached', revision], []];
  const records = await Promise.all(
    changes.map(async range => ({
      status: await runGit(root, [
        'diff',
        ...diffOptions,
        '--name-status',
        '-z',
        ...range,
        '--',
        ...selection,
      ]),
      stats: await runGit(root, [
        'diff',
        ...diffOptions,
        '--numstat',
        '-z',
        ...range,
        '--',
        ...selection,
      ]),
    })),
  );
  const untracked = (
    await runGit(root, [
      'ls-files',
      '--others',
      '--exclude-standard',
      '-z',
      '--',
      ...selection,
    ])
  )
    .split('\0')
    .filter(Boolean);
  const statuses = records.flatMap(
    record => parseNameStatus(record.status).statuses,
  );
  const paths = [
    ...new Set([
      ...records.flatMap(record => parseNameStatus(record.status).paths),
      ...untracked,
    ]),
  ].sort();
  const lineCounts = records.map(record => sumNumstatLines(record.stats));
  for (const path of untracked) {
    statuses.push('?');
    const info = await Deno.lstat(`${root}/${path}`);
    lineCounts.push(
      info.isFile
        ? sumNumstatLines(
            await runGit(
              root,
              [
                'diff',
                '--no-index',
                '--no-ext-diff',
                '--no-textconv',
                '--numstat',
                '-z',
                '--',
                '/dev/null',
                path,
              ],
              true,
            ),
          )
        : null,
    );
  }
  const invalidFiles = await Promise.all(
    paths.map(path => getFileAccessError(root, path, false)),
  );
  if (invalidFiles.some(Boolean)) lineCounts.push(null);
  return {
    paths,
    statuses,
    structuralPaths: records.flatMap(record =>
      statusRecords(record.status)
        .filter(item => !['A', 'M'].includes(item.status[0]))
        .flatMap(item => item.paths),
    ),
    changedLines: lineCounts.includes(null)
      ? null
      : lineCounts.reduce<number>((sum, count) => sum + (count ?? 0), 0),
  };
}

export async function inspectChanges(
  cwd: string,
  base = 'HEAD',
  input?: unknown,
) {
  const root = (await runGit(cwd, ['rev-parse', '--show-toplevel'])).trim();
  const revision = (
    await runGit(root, [
      'rev-parse',
      '--verify',
      '--end-of-options',
      `${base}^{commit}`,
    ])
  ).trim();
  const publicEntries = importRules(root)
    .forbidden.filter(rule => rule.name?.startsWith('public-api:'))
    .flatMap(rule => ('to' in rule ? (rule.to.pathNot ?? []) : []));
  const plan = input === undefined ? undefined : await analyzePlan(root, input);
  const {structuralPaths, ...changes} = await collectSignals(root, revision);
  const isPublic = (paths: string[]) =>
    paths.some(
      path =>
        entryPath.test(path) ||
        publicEntries.some(pattern => new RegExp(pattern).test(path)),
    );
  const signals = {
    ...changes,
    publicEntryChanged: isPublic([
      ...changes.paths,
      ...(plan?.tasks.flatMap(task => task.files) ?? []),
    ]),
  };
  const difficulty = plan
    ? await Promise.all(
        plan.tasks.map(async task => {
          const scopeErrors = (
            await Promise.all(
              task.files.map(path => getFileAccessError(root, path, false)),
            )
          ).filter((error): error is string => error !== undefined);
          if (scopeErrors.length)
            return {
              task: task.id,
              scope: task.files,
              policy: 'coding-difficulty/1',
              level: null,
              description:
                '판정 보류: 작업 범위가 유효한 파일 경로가 아닙니다.',
              facts: null,
              reasons: scopeErrors,
            };
          const scoped = await collectSignals(root, revision, task.files);
          return {
            task: task.id,
            scope: task.files,
            ...assessDifficulty({
              ...scoped,
              publicEntryChanged: isPublic(scoped.paths),
              structuralChange: structuralPaths.some(path =>
                task.files.includes(path),
              ),
            }),
          };
        }),
      )
    : [
        {
          task: null,
          scope: 'workspace',
          ...assessDifficulty({
            ...changes,
            publicEntryChanged: isPublic(changes.paths),
          }),
        },
      ];
  const decision = selectWorkMode(signals, plan);
  return {
    root,
    base: revision,
    ...decision,
    instructions: buildWorkModeInstructions(decision.mode, plan !== undefined),
    difficulty,
    changed_files: changes.paths.length,
    paths: signals.paths,
    statuses: signals.statuses,
    changed_lines: signals.changedLines,
    public_entry_changed: signals.publicEntryChanged,
    ...(plan ? {tasks: plan.tasks} : {}),
  };
}

if (import.meta.main) {
  await runCli(() =>
    createCommand(
      'workflow',
      'Select work mode, inspect code graphs and verify the current Git snapshot.',
    )
      .option('--task <id:string>', 'Task identity for the evidence loop.', {
        default: 'workspace',
      })
      .option('--base <ref:string>', 'Baseline Git commit or reference.', {
        default: 'HEAD',
      })
      .option(
        '--plan <path:string>',
        'JSON plan with exact files for each task.',
      )
      .option('--verify', 'Run all checks and retain evidence.', {
        default: false,
      })
      .option('--graph <choice:string>', 'Inspect impact, symbol or policy.')
      .option('--file <path:string>', 'Repository-relative graph target file.')
      .option('--line <line:integer>', 'Positive 1-based symbol line.')
      .option(
        '--column <column:integer>',
        'Positive 1-based UTF-16 symbol column.',
      )
      .action(async args => {
        if (!args.base || !args.task.trim() || args.plan === '')
          throw new ValidationError(
            'Base, task and plan values must not be empty.',
          );
        if (
          args.graph !== undefined &&
          !['impact', 'symbol', 'policy'].includes(args.graph)
        )
          throw new ValidationError(
            '--graph must be impact, symbol or policy.',
          );
        if (
          !args.graph &&
          [args.file, args.line, args.column].some(value => value !== undefined)
        )
          throw new ValidationError(
            '--file, --line and --column require --graph.',
          );
        if (
          args.graph === 'policy' &&
          [args.file, args.line, args.column].some(value => value !== undefined)
        )
          throw new ValidationError(
            'Policy does not accept file or symbol coordinates.',
          );
        if (
          args.graph === 'impact' &&
          (args.line !== undefined || args.column !== undefined)
        )
          throw new ValidationError(
            'Impact does not accept symbol coordinates.',
          );
        if (args.graph && args.graph !== 'policy' && !args.file)
          throw new ValidationError('Impact and symbol require --file.');
        if (
          args.graph === 'symbol' &&
          (!args.line || args.line < 1 || !args.column || args.column < 1)
        )
          throw new ValidationError(
            'Symbol requires positive --line and --column.',
          );
        if (
          args.file !== undefined &&
          !repositoryFileSchema.safeParse(args.file).success
        )
          throw new ValidationError(
            '--file must be a canonical repository-relative file path.',
          );
        let plan: unknown;
        if (args.plan !== undefined) {
          const text = await Deno.readTextFile(args.plan);
          try {
            plan = planSchema.parse(JSON.parse(text));
          } catch (error) {
            throw new ValidationError(
              error instanceof Error
                ? error.message
                : 'The plan must match the JSON plan schema.',
            );
          }
        }
        const snapshot = await snapshotWorkingTree(Deno.cwd());
        const routing = await inspectChanges(Deno.cwd(), args.base, plan);
        const graph =
          args.graph === undefined
            ? undefined
            : await inspectGraph(routing.root, {
                choice: args.graph,
                ...(args.file !== undefined ? {file: args.file} : {}),
                ...(args.line !== undefined ? {line: Number(args.line)} : {}),
                ...(args.column !== undefined
                  ? {column: Number(args.column)}
                  : {}),
              });
        const graphFailed = graph?.policy.status === 'FAIL';
        const {instructions: loopInstructions, ...loop} =
          await evaluateVerification(routing.root, {
            taskId: args.task,
            base: routing.base,
            plan: routing.tasks ?? null,
            verify: args.verify && !graphFailed,
          });
        const current = await snapshotWorkingTree(routing.root);
        if (
          [snapshot, ...(graph ? [graph.snapshot] : [])].some(
            state =>
              state.revision !== current.revision ||
              state.dirty_hash !== current.dirty_hash,
          )
        )
          throw new Error(
            'Code snapshot changed while processing the workflow; rerun the same command.',
          );
        const routedMode =
          loop.phase === 'REVIEW' || graphFailed ? 'REVIEW' : routing.mode;
        const skills = await announceSkillTriggers(
          routing.root,
          {
            taskId: args.task,
            base: routing.base,
            paths: routing.paths,
            tasks: routing.tasks,
            mode: routedMode,
            verify: args.verify,
          },
          current,
        );
        const mode = skills.mode;
        const skillScopeFailed = skills.scope.status === 'ERROR';
        createReport(
          {
            ...routing,
            mode,
            reasons: [
              ...routing.reasons,
              ...(graphFailed ? ['graph import-policy violations'] : []),
              ...(skillScopeFailed ? ['clean-code scope unavailable'] : []),
            ],
            loop,
            skill_triggers: skills.triggers,
            skill_snapshot: skills.snapshot,
            skill_scope: skills.scope,
            graph_commands: graphCommands,
            ...(graph ? {graph} : {}),
            instructions: [
              ...(graphFailed
                ? [
                    'Fix the reported import-policy violations and rerun the selected graph command before completion. The graph failure blocks this command even if prior loop evidence passed.',
                  ]
                : []),
              'Choose a graph_commands entry for the planned edit. It runs the fact bundle automatically; keep the same --task/--base/--plan context. Symbol analysis is for an existing identifier before deletion; after edits or deletions rerun impact or policy, then verify.',
              ...loopInstructions,
              ...skills.instructions,
              ...(loop.phase === 'VERIFIED'
                ? []
                : buildWorkModeInstructions(mode, plan !== undefined)),
              'For each new user request, choose a fresh --task <id> and rerun before implementing; keep that ID, --base and plan contents throughout the repair loop. The default workspace task reports code-check status, not completion of a new request.',
            ],
          },
          graphFailed ||
            skillScopeFailed ||
            (args.verify && loop.phase !== 'VERIFIED'),
        );
      })
      .parse(Deno.args),
  );
}
