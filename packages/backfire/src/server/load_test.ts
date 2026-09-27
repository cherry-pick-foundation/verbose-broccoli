import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StdioClientTransport} from '@modelcontextprotocol/sdk/client/stdio.js';
import {assert, assertEquals, assertRejects} from '@std/assert';
import {walk} from '@std/fs';
import {dirname, fromFileUrl, join, relative} from '@std/path';

const root = fromFileUrl(new URL('../../../../', import.meta.url));
const component = join(root, 'packages/backfire');
const decoder = new TextDecoder();

async function run(
  command: string,
  args: string[],
  options: Deno.CommandOptions = {},
) {
  const result = await new Deno.Command(command, {
    ...options,
    args,
    stdin: 'null',
    stdout: 'piped',
    stderr: 'piped',
  }).output();
  assertEquals(result.code, 0, decoder.decode(result.stderr));
  return decoder.decode(result.stdout).trim();
}

async function environment(cache: string, component: string) {
  const digest = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(await Deno.realPath(component)),
  );
  return join(
    cache,
    'verbose-broccoli/backfire/venv',
    new Uint8Array(digest).toHex().slice(0, 16),
  );
}

async function snapshot(directory: string) {
  const files: Record<string, string> = {};
  for await (const entry of walk(directory, {includeDirs: false})) {
    files[relative(directory, entry.path)] = entry.isSymlink
      ? await Deno.readLink(entry.path)
      : new Uint8Array(
          await crypto.subtle.digest(
            'SHA-256',
            await Deno.readFile(entry.path),
          ),
        ).toHex();
  }
  return files;
}

Deno.test('built plugin loads offline with isolated, stable Python environments', async () => {
  const temporary = await Deno.makeTempDir({prefix: 'backfire-load-test-'});
  try {
    const cache = join(temporary, 'cache');
    const {denoDir} = JSON.parse(
      await run(Deno.execPath(), ['info', '--json']),
    );
    const uv = await run('sh', [
      '-c',
      'command -v uv || printf "%s/.local/bin/uv" "$HOME"',
    ]);
    const env = {
      DENO_DIR: denoDir,
      XDG_CACHE_HOME: cache,
      UV_CACHE_DIR: await run(uv, ['cache', 'dir']),
      UV_OFFLINE: '1',
      PYTHONDONTWRITEBYTECODE: '1',
    };
    const copies = [join(temporary, 'first'), join(temporary, 'second')];
    for (const output of copies) {
      await run(Deno.execPath(), [
        'run',
        '--config',
        join(component, 'deno.json'),
        '--frozen',
        '--cached-only',
        '--no-prompt',
        '--allow-read',
        '--allow-write',
        '--allow-env=BACKFIRE_TEST_BUILD_MAX_BYTES',
        join(component, 'src/build.ts'),
        output,
      ]);
      await run(join(output, 'backfire/src/bin/backfire'), ['install'], {
        env,
      });
    }
    const built = join(copies[0], 'backfire');
    const installed = await environment(cache, built);
    const importSource = () =>
      run(join(installed, 'bin/python'), [
        '-B',
        '-c',
        'import backfire_backend; print(backfire_backend.__file__)',
      ]);
    const expectedSource = join(built, 'src/backfire_backend/__init__.py');
    assertEquals(await importSource(), expectedSource);
    assertEquals(
      (await Deno.readTextFile(join(installed, 'component-root'))).trim(),
      built,
    );
    const before = await snapshot(installed);

    await run(join(component, 'src/bin/backfire'), ['install'], {env});
    const development = await environment(cache, component);
    assert(development !== installed);
    assertEquals(await importSource(), expectedSource);
    assertEquals(await snapshot(installed), before);

    const removed = await environment(cache, join(copies[1], 'backfire'));
    assert(removed !== installed);
    await Deno.remove(copies[1], {recursive: true});
    await run(join(component, 'src/bin/backfire'), ['install'], {env});
    await assertRejects(() => Deno.stat(removed), Deno.errors.NotFound);
    assertEquals(await importSource(), expectedSource);
    assertEquals(await snapshot(installed), before);

    // Keep the copied entry outside the test's type-check graph; exercise its
    // package.json read and tool registrations through the real launcher.
    const transport = new StdioClientTransport({
      command: 'env',
      args: [
        '-i',
        `PATH=${dirname(Deno.execPath())}:${Deno.env.get('PATH') ?? '/usr/local/bin:/usr/bin:/bin'}`,
        `DENO_DIR=${denoDir}`,
        `XDG_CACHE_HOME=${cache}`,
        'JEV_PROVIDER=compatible',
        'JEV_API_BASE_URL=http://127.0.0.1:1/v1/systemone',
        'JEV_API_KEY=packaging-test-token',
        'JEV_MCP_MODEL=packaging-test-model',
        'JEV_MCP_REQUEST_TIMEOUT_MS=82000',
        'JEV_MCP_MAX_ATTEMPTS=1',
        join(built, 'src/bin/backfire'),
        'serve-mcp',
      ],
      cwd: temporary,
      stderr: 'pipe',
    });
    let stderr = '';
    transport.stderr?.on('data', (chunk: Uint8Array) => {
      stderr += decoder.decode(chunk);
    });
    const client = new Client({name: 'packaging-test', version: '1.0.0'});
    try {
      await client.connect(transport, {timeout: 10_000});
      const {version} = JSON.parse(
        await Deno.readTextFile(join(built, 'src/upstream/package.json')),
      );
      assertEquals(version, '0.9.0');
      assertEquals(client.getServerVersion(), {name: 'backfire', version});
      const {tools} = await client.listTools({}, {timeout: 10_000});
      assertEquals(tools.map((tool: {name: string}) => tool.name).sort(), [
        'backfire_classify',
        'backfire_compare',
        'backfire_decide',
        'backfire_extract',
        'backfire_find',
        'backfire_gate',
        'backfire_noul',
        'backfire_rerank',
        'backfire_review',
        'backfire_screen',
        'backfire_verify',
      ]);
    } catch (error) {
      throw new Error(stderr, {cause: error});
    } finally {
      await client.close();
    }
  } finally {
    await Deno.remove(temporary, {recursive: true});
  }
});
