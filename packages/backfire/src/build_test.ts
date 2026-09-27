import {
  assert,
  assertEquals,
  assertRejects,
  assertStringIncludes,
} from '@std/assert';
import {copy, walk} from '@std/fs';
import {
  basename,
  dirname,
  fromFileUrl,
  join,
  relative,
  toFileUrl,
} from '@std/path';

const root = fromFileUrl(new URL('../../../', import.meta.url));
const packageFiles = [
  'deno.json',
  'deno.lock',
  'pyproject.toml',
  '.python-version',
  'uv.lock',
];
const decoder = new TextDecoder();

async function temporary(run: (directory: string) => Promise<void>) {
  const directory = await Deno.makeTempDir({prefix: 'backfire-build-test-'});
  try {
    await run(directory);
  } finally {
    await Deno.remove(directory, {recursive: true});
  }
}

function command(
  output: string,
  source = root,
  env: Record<string, string> = {},
) {
  return new Deno.Command(Deno.execPath(), {
    args: [
      'run',
      '--config',
      join(root, 'packages/backfire/deno.json'),
      '--frozen',
      '--cached-only',
      '--no-prompt',
      '--allow-read',
      '--allow-write',
      '--allow-env=BACKFIRE_TEST_BUILD_MAX_BYTES',
      join(source, 'packages/backfire/src/build.ts'),
      '--',
      output,
    ],
    env: {BACKFIRE_TEST_BUILD_MAX_BYTES: String(16 * 1024 * 1024), ...env},
    stdin: 'null',
    stdout: 'piped',
    stderr: 'piped',
  });
}

async function tree(directory: string) {
  const entries: Record<string, string> = {};
  for await (const entry of walk(directory)) {
    assert(!entry.isSymlink, `Unexpected link: ${entry.path}`);
    entries[relative(directory, entry.path)] = entry.isDirectory
      ? 'directory'
      : (await Deno.readFile(entry.path)).toHex();
  }
  return entries;
}

async function noOutput(output: string) {
  await assertRejects(() => Deno.lstat(output), Deno.errors.NotFound);
  const prefix = `${basename(output)}.partial-`;
  for await (const entry of Deno.readDir(dirname(output)))
    assert(
      !entry.name.startsWith(prefix),
      `Partial output remains: ${entry.name}`,
    );
}

async function fixture(directory: string) {
  const source = join(directory, 'repository');
  for (const path of ['plugins/code', 'packages/backfire/src'])
    await copy(join(root, path), join(source, path));
  for (const path of packageFiles)
    await copy(
      join(root, 'packages/backfire', path),
      join(source, 'packages/backfire', path),
    );
  return source;
}

Deno.test('build preserves the plugin and includes only the runtime package', async () => {
  await temporary(async directory => {
    const output = join(directory, 'code');
    const result = await command(output).output();
    assertEquals(result.code, 0, decoder.decode(result.stderr));
    assertEquals(decoder.decode(result.stdout), `${output}\n`);
    const built = await tree(output);
    const plugin = Object.fromEntries(
      Object.entries(built).filter(
        ([path]) => path !== 'backfire' && !path.startsWith('backfire/'),
      ),
    );
    assertEquals(plugin, await tree(join(root, 'plugins/code')));

    const expected: Record<string, string> = {};
    for (const path of packageFiles)
      expected[path] = (
        await Deno.readFile(join(root, 'packages/backfire', path))
      ).toHex();
    for (const directory of ['bin', 'upstream', 'server', 'backfire_backend']) {
      for (const [path, contents] of Object.entries(
        await tree(join(root, 'packages/backfire/src', directory)),
      )) {
        if (contents === 'directory') continue;
        if (
          directory === 'server' &&
          (path.endsWith('_test.ts') || path.startsWith('testing/'))
        )
          continue;
        if (
          directory === 'backfire_backend' &&
          path.split('/').includes('__pycache__')
        )
          continue;
        expected[`src/${directory}/${path}`] = contents;
      }
    }
    const runtime = await tree(join(output, 'backfire'));
    assertEquals(
      Object.fromEntries(
        Object.entries(runtime).filter(([, value]) => value !== 'directory'),
      ),
      expected,
    );
    assert('src/bin/backfire' in runtime);
    for (const path of Object.keys(runtime))
      assert(
        !/(?:_test\.ts$|^src\/server\/testing(?:\/|$)|^src\/acceptance(?:\/|$)|(?:^|\/)build\.ts$|^tests(?:\/|$)|(?:^|\/)__pycache__(?:\/|$)|\.egg-info(?:\/|$))/.test(
          path,
        ),
        path,
      );
    assertEquals(
      (await Deno.stat(join(output, 'backfire/src/bin/backfire'))).mode,
      (await Deno.stat(join(root, 'packages/backfire/src/bin/backfire'))).mode,
    );
    await assertRejects(
      () => Deno.lstat(join(root, 'plugins/code/backfire')),
      Deno.errors.NotFound,
    );
    assertEquals(
      [...Deno.readDirSync(directory)].map(entry => entry.name),
      ['code'],
    );
  });
});

Deno.test('build excludes test support, acceptance, caches and generated metadata', async () => {
  await temporary(async directory => {
    const source = await fixture(directory);
    const excluded = [
      'src/server/nested/example_test.ts',
      'src/server/testing/stub.ts',
      'src/backfire_backend/__pycache__/compiled.pyc',
      'src/acceptance/example.ts',
      'src/backfire_backend.egg-info/PKG-INFO',
      'tests/test_example.py',
    ];
    for (const path of excluded) {
      const target = join(source, 'packages/backfire', path);
      await Deno.mkdir(dirname(target), {recursive: true});
      await Deno.writeTextFile(target, 'excluded');
    }
    const output = join(directory, 'code');
    const result = await command(output, source).output();
    assertEquals(result.code, 0, decoder.decode(result.stderr));
    for (const path of excluded)
      await assertRejects(
        () => Deno.lstat(join(output, 'backfire', path)),
        Deno.errors.NotFound,
      );
  });
});

Deno.test('build refuses existing outputs and paths inside source packages', async () => {
  await temporary(async directory => {
    const output = join(directory, 'code');
    for (const kind of ['file', 'directory', 'symlink']) {
      if (kind === 'file') await Deno.writeTextFile(output, 'keep');
      else if (kind === 'directory') await Deno.mkdir(output);
      else await Deno.symlink(join(directory, 'missing'), output);
      const result = await command(output).output();
      assertEquals(result.code, 1);
      assertStringIncludes(
        decoder.decode(result.stderr),
        'Output already exists',
      );
      assertEquals(
        [...Deno.readDirSync(directory)].map(entry => entry.name),
        ['code'],
      );
      if (kind === 'file')
        assertEquals(await Deno.readTextFile(output), 'keep');
      if (kind === 'symlink')
        assertEquals(await Deno.readLink(output), join(directory, 'missing'));
      await Deno.remove(output);
    }
    const source = await fixture(directory);
    for (const parent of ['plugins', 'packages']) {
      const output = join(source, parent, 'new-output');
      const result = await command(output, source).output();
      assertEquals(result.code, 1);
      assertStringIncludes(
        decoder.decode(result.stderr),
        'Output must be outside',
      );
      await noOutput(output);
      const alias = join(directory, parent);
      await Deno.symlink(join(source, parent), alias);
      const aliased = join(alias, 'new-output');
      const linked = await command(aliased, source).output();
      assertEquals(linked.code, 1);
      assertStringIncludes(
        decoder.decode(linked.stderr),
        'Output must be outside',
      );
      await noOutput(aliased);
    }
  });
});

Deno.test('build rejects source links and removes only its own partial directory', async () => {
  await temporary(async directory => {
    const source = await fixture(directory);
    const output = join(directory, 'code');
    const unrelated = join(directory, 'other.partial-keep');
    await Deno.mkdir(unrelated);
    for (const path of [
      'plugins/code/link',
      'packages/backfire/src/backfire_backend/link',
    ]) {
      const link = join(source, path);
      await Deno.symlink(join(source, 'plugins/code/plugin.json'), link);
      const result = await command(output, source).output();
      assertEquals(result.code, 1);
      assertStringIncludes(
        decoder.decode(result.stderr),
        `Source symbolic link is not allowed: ${link}`,
      );
      await noOutput(output);
      assert((await Deno.stat(unrelated)).isDirectory);
      await Deno.remove(link);
    }
  });
});

Deno.test('build over a lowered budget removes the output and its partial directory', async () => {
  await temporary(async directory => {
    const output = join(directory, 'code');
    const result = await command(output, root, {
      BACKFIRE_TEST_BUILD_MAX_BYTES: '1',
    }).output();
    assertEquals(result.code, 1);
    assertStringIncludes(
      decoder.decode(result.stderr),
      'Build exceeds 1-byte budget',
    );
    await noOutput(output);
  });
});

Deno.test('SIGINT and SIGTERM during a file copy remove the partial build', async () => {
  await temporary(async directory => {
    for (const signal of ['SIGINT', 'SIGTERM'] as const) {
      const output = join(directory, 'code');
      const script = `
        const copyFile = Deno.copyFile;
        Deno.copyFile = async (source, destination) => {
          await copyFile(source, destination);
          await new Promise(resolve => {
            const resume = () => {
              Deno.removeSignalListener(${JSON.stringify(signal)}, resume);
              resolve();
            };
            Deno.addSignalListener(${JSON.stringify(signal)}, resume);
            console.log('copy-paused');
          });
        };
        await import(${JSON.stringify(toFileUrl(join(root, 'packages/backfire/src/build.ts')).href)});
      `;
      const child = new Deno.Command(Deno.execPath(), {
        args: [
          'eval',
          '--config',
          join(root, 'packages/backfire/deno.json'),
          '--frozen',
          '--cached-only',
          script,
          output,
        ],
        env: {BACKFIRE_TEST_BUILD_MAX_BYTES: String(16 * 1024 * 1024)},
        stdin: 'null',
        stdout: 'piped',
        stderr: 'piped',
      }).spawn();
      const reader = child.stdout.getReader();
      const timeout = setTimeout(() => child.kill('SIGKILL'), 10_000);
      try {
        const ready = await reader.read();
        assertStringIncludes(decoder.decode(ready.value), 'copy-paused');
        assert(
          [...Deno.readDirSync(directory)].some(entry =>
            entry.name.startsWith('code.partial-'),
          ),
        );
      } finally {
        reader.releaseLock();
        child.kill(signal);
        const result = await child.output();
        clearTimeout(timeout);
        assertEquals(result.code, 1, decoder.decode(result.stderr));
        assertStringIncludes(
          decoder.decode(result.stderr),
          'Build interrupted',
        );
      }
      await noOutput(output);
    }
  });
});
