import {assert, assertEquals, assertStringIncludes} from '@std/assert';
import {fromFileUrl, join} from '@std/path';

Deno.test('entry commands name install when this copy has no environment', async () => {
  const temporary = await Deno.makeTempDir();
  try {
    const cache = `${temporary}/cache`;
    const denoDir = `${temporary}/deno`;
    for (const path of [cache, denoDir]) await Deno.mkdir(path);

    for (const command of ['serve-mcp', 'ready']) {
      const result = await new Deno.Command(
        new URL('../bin/backfire', import.meta.url),
        {
          args: [command],
          clearEnv: true,
          env: {
            XDG_CACHE_HOME: cache,
            DENO_DIR: denoDir,
          },
          stdin: 'null',
          stdout: 'piped',
          stderr: 'piped',
        },
      ).output();
      assert(result.code !== 0);
      assertStringIncludes(
        new TextDecoder().decode(result.stderr),
        'src/bin/backfire install',
      );
    }
  } finally {
    await Deno.remove(temporary, {recursive: true});
  }
});

Deno.test('test tasks name T037 preparation before running without it', async () => {
  const temporary = await Deno.makeTempDir();
  const root = fromFileUrl(new URL('../../../../', import.meta.url));
  try {
    const {tasks} = JSON.parse(
      await Deno.readTextFile(join(root, 'deno.json')),
    );
    await Deno.writeTextFile(`${temporary}/deno.json`, JSON.stringify({tasks}));
    await Deno.mkdir(`${temporary}/packages/backfire`, {recursive: true});
    await Deno.writeTextFile(`${temporary}/packages/backfire/deno.json`, '{}');
    for (const [task, cwd, message] of [
      ['test:backfire', root, 'Missing cached Backfire Deno modules.'],
      ['test:backfire-slow', root, 'Missing cached Backfire Deno modules.'],
      ['test:backfire', temporary, 'Missing Backfire pytest environment.'],
    ]) {
      const result = await new Deno.Command(Deno.execPath(), {
        args: [
          'task',
          '--config',
          `${temporary}/deno.json`,
          '--cwd',
          cwd,
          task,
        ],
        env: {DENO_DIR: `${temporary}/deno`},
        stdin: 'null',
        stdout: 'piped',
        stderr: 'piped',
      }).output();
      assertEquals(result.code, 1);
      assertEquals(result.stdout.length, 0);
      assertStringIncludes(
        new TextDecoder().decode(result.stderr),
        `\n${message} Run T037 preparation:`,
      );
    }
  } finally {
    await Deno.remove(temporary, {recursive: true});
  }
});
