import {test} from 'node:test';
import {assert, assertEquals, assertNotEquals} from '@std/assert';
import {fromFileUrl, join} from '@std/path';
import {spawnSync} from 'node:child_process';
import {evaluateVerification} from './workflow_verify.ts';

type Options = Parameters<typeof evaluateVerification>[1];
type Evidence = NonNullable<
  Awaited<ReturnType<typeof evaluateVerification>>['latest']
>;
const passing = "console.log('fixture check passed');";

async function git(root: string, ...args: string[]) {
  const result = spawnSync(
    'git',
    [
      '-c',
      'core.hooksPath=/dev/null',
      '-c',
      'user.name=Workflow Verification Fixture',
      '-c',
      'user.email=fixture@example.invalid',
      '-c',
      'commit.gpgsign=false',
      ...args,
    ],
    {
      cwd: root,
      env: {
        ...process.env,
        GIT_CONFIG_NOSYSTEM: '1',
        GIT_CONFIG_GLOBAL: '/dev/null',
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );
  if (result.error) throw result.error;
  assert(result.status === 0, new TextDecoder().decode(result.stderr));
  return new TextDecoder().decode(result.stdout).trim();
}

async function repository(
  check: string,
  run: (root: string, options: Options) => Promise<void>,
) {
  const root = await Deno.makeTempDir({prefix: 'workflow-verify-test-'});
  try {
    await git(root, 'init', '--quiet', '--template=', '--initial-branch=main');
    await Deno.mkdir(join(root, 'src'));
    await Deno.writeTextFile(
      join(root, 'src/value.ts'),
      'export const value = 1;\n',
    );
    await Deno.writeTextFile(join(root, 'fixture-check.ts'), check);
    const shim = fromFileUrl(new URL('./deno_shim.ts', import.meta.url));
    await Deno.writeTextFile(
      join(root, 'package.json'),
      JSON.stringify({
        scripts: {check: `node --import "${shim}" fixture-check.ts`},
      }),
    );
    await git(root, 'add', '--all');
    await git(root, 'commit', '--quiet', '-m', 'Verification fixture');
    await run(root, {
      taskId: 'fixture-task',
      base: await git(root, 'rev-parse', 'HEAD'),
      plan: null,
    });
  } finally {
    await Deno.remove(root, {recursive: true});
  }
}

async function records(path: string): Promise<Evidence[]> {
  return (await Deno.readTextFile(path))
    .split('\n')
    .filter(Boolean)
    .map(line => JSON.parse(line) as Evidence);
}

async function assertUnavailable(root: string, options: Options) {
  let result: Awaited<ReturnType<typeof evaluateVerification>>;
  try {
    result = await evaluateVerification(root, options);
  } catch (error) {
    assert(error instanceof Error);
    return;
  }
  assertNotEquals(result.phase, 'VERIFIED');
}

test('workflow verification: actual check creates reusable evidence for the exact code', async () => {
  await repository(passing, async (root, options) => {
    const initial = await evaluateVerification(root, options);
    assertEquals(initial.phase, 'IMPLEMENT');
    assertEquals(initial.latest, null);
    const result = await evaluateVerification(root, {
      ...options,
      verify: true,
    });
    assertEquals(result.phase, 'VERIFIED');
    assertEquals(result.consecutive_failures, 0);
    assert(result.latest);
    assertEquals(result.latest.event, 'FINISHED');
    assertEquals(result.latest.exit_code, 0);
    assertEquals(result.latest.before, result.latest.after);
    assert(result.latest.log_hash);
    assertEquals(
      (await records(result.evidence_path)).map(item => item.event),
      ['STARTED', 'FINISHED'],
    );
    assertEquals((await evaluateVerification(root, options)).phase, 'VERIFIED');
    await Deno.writeTextFile(
      join(root, 'src/value.ts'),
      'export const value = 2;\n',
    );
    assertNotEquals(
      (await evaluateVerification(root, options)).phase,
      'VERIFIED',
    );
  });
});

test('workflow verification: failures accumulate across repairs within the same task', async () => {
  await repository('Deno.exit(1);', async (root, options) => {
    const first = await evaluateVerification(root, {
      ...options,
      verify: true,
    });
    assertEquals(first.phase, 'REPAIR');
    assertEquals(first.consecutive_failures, 1);
    await Deno.writeTextFile(
      join(root, 'src/value.ts'),
      'export const value = 2;\n',
    );
    const second = await evaluateVerification(root, {
      ...options,
      verify: true,
    });
    assertEquals(second.phase, 'REVIEW');
    assertEquals(second.consecutive_failures, 2);
    assertEquals(
      (await evaluateVerification(root, options)).consecutive_failures,
      2,
    );
    const other = await evaluateVerification(root, {
      ...options,
      taskId: 'other-task',
    });
    assertEquals(other.phase, 'IMPLEMENT');
    assertEquals(other.consecutive_failures, 0);
    await Deno.writeTextFile(join(root, 'fixture-check.ts'), passing);
    const repaired = await evaluateVerification(root, {
      ...options,
      verify: true,
    });
    assertEquals(repaired.phase, 'VERIFIED');
    assertEquals(repaired.consecutive_failures, 0);
    await Deno.writeTextFile(join(root, 'fixture-check.ts'), 'Deno.exit(1);');
    const failedAgain = await evaluateVerification(root, {
      ...options,
      verify: true,
    });
    assertEquals(failedAgain.phase, 'REPAIR');
    assertEquals(failedAgain.consecutive_failures, 1);
  });
});

test('workflow verification: task, plan and resolved baseline keep evidence separate', async () => {
  await repository(passing, async (root, options) => {
    await git(
      root,
      'commit',
      '--quiet',
      '--allow-empty',
      '-m',
      'Second baseline',
    );
    const newer = await git(root, 'rev-parse', 'HEAD');
    assertEquals(
      (await evaluateVerification(root, {...options, verify: true})).phase,
      'VERIFIED',
    );
    for (const changed of [
      {...options, taskId: 'other-task'},
      {...options, plan: {tasks: [{id: 'part', files: ['src/value.ts']}]}},
      {...options, base: newer},
    ]) {
      const result = await evaluateVerification(root, changed);
      assertEquals(result.phase, 'IMPLEMENT');
      assertEquals(result.latest, null);
      assertEquals(result.consecutive_failures, 0);
    }
    assertEquals((await evaluateVerification(root, options)).phase, 'VERIFIED');
  });
});

test('workflow verification: exit zero cannot verify code changed during the check', async () => {
  await repository(
    "await Deno.writeTextFile('src/value.ts', 'export const value = 2;\\n');",
    async (root, options) => {
      const result = await evaluateVerification(root, {
        ...options,
        verify: true,
      });
      assertNotEquals(result.phase, 'VERIFIED');
      assert(result.latest);
      assertEquals(result.latest.exit_code, 0);
      assertNotEquals(result.latest.before, result.latest.after);
      assertNotEquals(
        (await evaluateVerification(root, options)).phase,
        'VERIFIED',
      );
    },
  );
});

test('workflow verification: altered or missing logs cannot reuse a previous successful result', async () => {
  await repository(passing, async (root, options) => {
    const result = await evaluateVerification(root, {
      ...options,
      verify: true,
    });
    assertEquals(result.phase, 'VERIFIED');
    assert(result.latest);
    await Deno.writeTextFile(result.latest.log_path, 'altered output\n');
    await assertUnavailable(root, options);
    await Deno.remove(result.latest.log_path);
    await assertUnavailable(root, options);
  });
});

test('workflow verification: malformed or invalid evidence fails closed', async () => {
  for (const damaged of [
    'not-json\n',
    '{"event":"FINISHED","exit_code":0}\n',
  ]) {
    await repository(passing, async (root, options) => {
      const result = await evaluateVerification(root, {
        ...options,
        verify: true,
      });
      assertEquals(result.phase, 'VERIFIED');
      await Deno.writeTextFile(result.evidence_path, damaged, {append: true});
      await assertUnavailable(root, options);
    });
  }
});

test('workflow verification: an interrupted run supersedes older successful evidence', async () => {
  await repository(passing, async (root, options) => {
    const result = await evaluateVerification(root, {
      ...options,
      verify: true,
    });
    assertEquals(result.phase, 'VERIFIED');
    const [started] = await records(result.evidence_path);
    assertEquals(started.event, 'STARTED');
    const interrupted = {
      ...started,
      run_id: crypto.randomUUID(),
      started_at: new Date().toISOString(),
    };
    await Deno.writeTextFile(
      result.evidence_path,
      `${JSON.stringify(interrupted)}\n`,
      {append: true},
    );
    await assertUnavailable(root, options);
  });
});

test('workflow verification: concurrent checks serialize their execution and evidence', async () => {
  await repository(
    [
      "const file = await Deno.open('.git/check-running', {createNew: true, write: true});",
      'try {',
      '  await new Promise(resolve => setTimeout(resolve, 40));',
      "  console.log('serialized check');",
      '} finally {',
      '  file.close();',
      "  await Deno.remove('.git/check-running');",
      '}',
    ].join('\n'),
    async (root, options) => {
      const results = await Promise.all([
        evaluateVerification(root, {...options, verify: true}),
        evaluateVerification(root, {...options, verify: true}),
      ]);
      assertEquals(
        results.map(result => result.phase),
        ['VERIFIED', 'VERIFIED'],
      );
      const evidence = await records(results[0].evidence_path);
      assertEquals(
        evidence.map(item => item.event),
        ['STARTED', 'FINISHED', 'STARTED', 'FINISHED'],
      );
      assertEquals(evidence[0].run_id, evidence[1].run_id);
      assertEquals(evidence[2].run_id, evidence[3].run_id);
      assertNotEquals(evidence[0].run_id, evidence[2].run_id);
    },
  );
});
