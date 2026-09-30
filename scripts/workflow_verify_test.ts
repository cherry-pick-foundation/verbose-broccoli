import {chmod, mkdir, mkdtemp, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {test} from 'node:test';
import {assertEquals} from '@std/assert';
import {join} from '@std/path';
import {evaluateVerification} from './workflow_verify.ts';

type Summary = {
  version: string;
  turboVersion: string;
  execution: {failed: number; exitCode: number} | null;
};

async function run(
  childExit: number,
  summary: Summary | string | undefined,
  printedPath = true,
) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-verify-'));
  const bin = join(root, 'bin');
  const runs = join(root, '.turbo/runs');
  const summaryPath = join(runs, 'synthetic.json');
  await mkdir(bin, {recursive: true});
  await mkdir(runs, {recursive: true});
  if (summary !== undefined)
    await writeFile(
      summaryPath,
      typeof summary === 'string' ? summary : JSON.stringify(summary),
      {mode: 0o600},
    );
  const npm = join(bin, 'npm');
  await writeFile(
    npm,
    [
      '#!/bin/sh',
      "printf 'synthetic check output\\n'",
      printedPath
        ? 'printf \'Summary: %s\\n\' "$WORKFLOW_SUMMARY_PATH"'
        : "printf 'no summary path\\n'",
      "printf 'synthetic check error\\n' >&2",
      'exit "$WORKFLOW_CHILD_EXIT"',
      '',
    ].join('\n'),
  );
  await chmod(npm, 0o700);

  const previous = {
    path: process.env.PATH,
    summaryPath: process.env.WORKFLOW_SUMMARY_PATH,
    childExit: process.env.WORKFLOW_CHILD_EXIT,
  };
  process.env.PATH = `${bin}${process.env.PATH ? `:${process.env.PATH}` : ''}`;
  process.env.WORKFLOW_SUMMARY_PATH = summaryPath;
  process.env.WORKFLOW_CHILD_EXIT = String(childExit);
  try {
    return await evaluateVerification(root, true);
  } finally {
    if (previous.path === undefined) delete process.env.PATH;
    else process.env.PATH = previous.path;
    if (previous.summaryPath === undefined)
      delete process.env.WORKFLOW_SUMMARY_PATH;
    else process.env.WORKFLOW_SUMMARY_PATH = previous.summaryPath;
    if (previous.childExit === undefined)
      delete process.env.WORKFLOW_CHILD_EXIT;
    else process.env.WORKFLOW_CHILD_EXIT = previous.childExit;
    await rm(root, {recursive: true});
  }
}

void test('workflow verification: current Turbo summary and child exit both pass', async () => {
  const result = await run(0, {
    version: '1',
    turboVersion: '2.11.5',
    execution: {failed: 0, exitCode: 0},
  });
  assertEquals(result.phase, 'VERIFIED');
  assertEquals(result.instructions, []);
});

void test('workflow verification: child failure cannot pass a successful summary', async () => {
  const result = await run(1, {
    version: '1',
    turboVersion: '2.11.5',
    execution: {failed: 0, exitCode: 0},
  });
  assertEquals(result.phase, 'FAILED');
});

void test('workflow verification: failed tasks, exit status and unsupported summaries fail closed', async () => {
  for (const summary of [
    {version: '1', turboVersion: '2.11.5', execution: {failed: 1, exitCode: 1}},
    {version: '2', turboVersion: '2.11.5', execution: {failed: 0, exitCode: 0}},
    {version: '1', turboVersion: '2.11.4', execution: {failed: 0, exitCode: 0}},
    {version: '1', turboVersion: '2.11.5', execution: null},
    'not-json',
  ])
    assertEquals((await run(0, summary)).phase, 'FAILED');
  assertEquals((await run(0, undefined)).phase, 'FAILED');
  assertEquals(
    (
      await run(
        0,
        {
          version: '1',
          turboVersion: '2.11.5',
          execution: {failed: 0, exitCode: 0},
        },
        false,
      )
    ).phase,
    'FAILED',
  );
});
