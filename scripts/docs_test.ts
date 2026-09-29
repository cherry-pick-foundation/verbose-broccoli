import {spawn, spawnSync} from 'node:child_process';
import {once} from 'node:events';
import childProcess from 'node:child_process';
import fsPromises from 'node:fs/promises';
import {readdirSync} from 'node:fs';
import {
  cp,
  copyFile,
  mkdir,
  mkdtemp,
  readFile,
  readlink,
  readdir,
  rm,
  stat,
  symlink,
  writeFile,
} from 'node:fs/promises';
import {syncBuiltinESMExports} from 'node:module';
import {test} from 'node:test';
import {
  assert,
  assertEquals,
  assertRejects,
  assertStringIncludes,
  assertThrows,
} from '@std/assert';
import {fromFileUrl, join, resolve} from '@std/path';
import {
  type GetParametersFromProp,
  type GetReturnFromProp,
  stub,
} from '@std/testing/mock';
import {createProcessor} from '@mdx-js/mdx';
import remarkGfm from 'remark-gfm';
import {toString as mdastToString} from 'mdast-util-to-string';
import {visit} from 'unist-util-visit';
import {parse} from '@eemeli/yaml';
import {tmpdir} from 'node:os';
import {collectHelp, documentedCommands, syncReferenceDocs} from './docs.ts';

const root = fromFileUrl(new URL('../', import.meta.url));
const decoder = new TextDecoder();
const referenceFiles = ['commands.md', 'plugins.md'];
const readText = (path: string) => readFile(path, 'utf8');

async function* walk(root: string) {
  for (const entry of await readdir(root, {
    recursive: true,
    withFileTypes: true,
  })) {
    yield {
      path: join(entry.parentPath, entry.name),
      isFile: entry.isFile(),
      isSymlink: entry.isSymbolicLink(),
    };
  }
}

function commandOutput(
  command: string,
  options: {args: string[]; cwd?: string; env?: Record<string, string>},
) {
  const result = spawnSync(command, options.args, {
    cwd: options.cwd,
    env: options.env ? {...process.env, ...options.env} : undefined,
    encoding: null,
  });
  if (result.error) throw result.error;
  if (result.signal)
    throw new Error(`Child process terminated by signal ${result.signal}`);
  return {
    code: result.status ?? 1,
    success: result.status === 0,
    stdout: result.stdout ?? Buffer.alloc(0),
    stderr: result.stderr ?? Buffer.alloc(0),
  };
}

test('references: command helper rejects signal termination', () => {
  assertThrows(
    () =>
      commandOutput(process.execPath, {
        args: ['-e', "process.kill(process.pid, 'SIGKILL')"],
      }),
    Error,
    'SIGKILL',
  );
});

function stubBuiltin<T extends object, K extends keyof T>(
  module: T,
  method: K,
  replacement: (
    this: T,
    ...args: GetParametersFromProp<T, K>
  ) => GetReturnFromProp<T, K>,
) {
  const value = stub(module, method, replacement);
  syncBuiltinESMExports();
  return {
    get calls() {
      return value.calls;
    },
    restore() {
      value.restore();
      syncBuiltinESMExports();
    },
  };
}

async function fixture(run: (repo: string) => Promise<void>, realHelp = false) {
  const repo = await mkdtemp(join(tmpdir(), 'docs-test-'));
  try {
    for (const name of ['scripts', 'plugins/code/skills/clean-code'])
      await cp(join(root, name), join(repo, name), {recursive: true});
    for (const name of [
      'package.json',
      'package-lock.json',
      'turbo.json',
      'tsconfig.json',
      'eslint.ignores.js',
    ])
      await copyFile(join(root, name), join(repo, name));
    await symlink(
      join(root, 'node_modules'),
      join(repo, 'node_modules'),
      'dir',
    );
    for (const name of ['chat', 'code', 'work']) {
      await mkdir(join(repo, 'plugins', name), {recursive: true});
      for (const file of ['plugin.json', 'mcp.json']) {
        try {
          await copyFile(
            join(root, 'plugins', name, file),
            join(repo, 'plugins', name, file),
          );
        } catch (error) {
          if (!(
            error instanceof Error &&
            'code' in error &&
            error.code === 'ENOENT'
          ))
            throw error;
        }
      }
    }
    await mkdir(join(repo, 'docs'));
    await mkdir(join(repo, 'protected-user-data'));
    await writeFile(join(repo, 'docs/authored.md'), 'Authored sentinel.\n');
    await writeFile(
      join(repo, 'protected-user-data/secret'),
      'User-data sentinel.\n',
    );
    if (!realHelp)
      for (const [name, script] of documentedCommands) {
        if (name !== 'plugins:validate')
          await writeFile(
            join(repo, script),
            `if (process.argv.slice(2).join() !== '--help') throw new Error('business action');\nconsole.log(${JSON.stringify(`Usage: ${name}\n\nOptions:\n  --help - Show help.\n`)});\n`,
          );
      }
    await run(repo);
  } finally {
    await rm(repo, {recursive: true});
  }
}

test('references: docs must be a directory', async () => {
  await fixture(async repo => {
    await rm(join(repo, 'docs'), {recursive: true});
    await writeFile(join(repo, 'docs'), 'regular file\n');
    await assertRejects(
      () => syncReferenceDocs(repo, 'check'),
      Error,
      'docs: Expected the repository documentation directory.',
    );
  });
});

async function pair(repo: string) {
  return await Promise.all(
    referenceFiles.map(file => readText(join(repo, 'docs/reference', file))),
  );
}
async function changeJson(
  repo: string,
  path: string,
  change: (value: Record<string, unknown>) => void,
) {
  const value = JSON.parse(await readText(join(repo, path)));
  change(value);
  await writeFile(join(repo, path), JSON.stringify(value, null, 2));
}
async function tree(repo: string) {
  const values = [];
  for await (const entry of walk(repo)) {
    if (entry.isFile)
      values.push([
        entry.path.slice(repo.length),
        Buffer.from(await readFile(entry.path)).toString('hex'),
      ]);
    else if (entry.isSymlink)
      values.push([entry.path.slice(repo.length), await readlink(entry.path)]);
    else values.push([entry.path.slice(repo.length), 'directory']);
  }
  return values.sort(([a], [b]) => (a < b ? -1 : 1));
}
async function git(repo: string, args: string[]) {
  const result = commandOutput('git', {
    args,
    cwd: repo,
  });
  assert(result.success, decoder.decode(result.stderr));
}
function parsed(markdown: string) {
  return createProcessor({remarkPlugins: [remarkGfm]}).parse(markdown);
}
async function checkUnchanged(repo: string, pass: boolean) {
  const before = await tree(repo);
  if (pass) await syncReferenceDocs(repo, 'check');
  else await assertRejects(() => syncReferenceDocs(repo, 'check'));
  assertEquals(await tree(repo), before);
}

test('references: real seven help routes, all tasks/plugins and final links are deterministic', async () => {
  await fixture(async repo => {
    const help = await collectHelp(repo);
    assertEquals(
      [...help.keys()],
      documentedCommands.map(([name]) => name),
    );
    await syncReferenceDocs(repo, 'generate');
    const initial = await pair(repo);
    const tasks = Object.keys(
      JSON.parse(await readText(join(repo, 'package.json'))).scripts,
    ).sort();
    const invocations: string[] = [];
    visit(parsed(initial[0]), 'tableRow', row => {
      const cells = row.children.map(cell => mdastToString(cell));
      if (cells[0] !== 'Task') invocations.push(cells[1]);
    });
    assertEquals(
      invocations,
      tasks.map(task => `npm run ${task}`),
    );
    for (const name of ['chat', 'code', 'work'])
      assertStringIncludes(initial[1], `## ${name}\n`);
    for (const markdown of initial) {
      const links: string[] = [];
      visit(parsed(markdown), 'link', node => {
        links.push(node.url);
      });
      for (const link of links)
        assert(await stat(resolve(repo, 'docs/reference', link)));
      assertEquals(markdown.includes(repo), false);
      assertEquals(markdown.includes('\u001b'), false);
      assert(markdown.endsWith('\n') && !markdown.endsWith('\n\n'));
    }
    const codeBlocks: string[] = [];
    visit(parsed(initial[0]), 'code', node => {
      codeBlocks.push(node.value);
    });
    assertEquals(codeBlocks.sort(), [...help.values()].sort());
    await syncReferenceDocs(repo, 'generate');
    assertEquals(await pair(repo), initial);
    await fixture(async elsewhere => {
      await syncReferenceDocs(elsewhere, 'generate');
      assertEquals(await pair(elsewhere), initial);
    }, true);
  }, true);
});

test('references: source facts, optional MCP and Markdown characters survive serialization', async () => {
  await fixture(async repo => {
    const description =
      '한글 | "quotes" \\ slash *literal*\nsecond line <tag> & text';
    await changeJson(repo, 'plugins/chat/plugin.json', value => {
      value.description = description;
      delete value.version;
    });
    await changeJson(repo, 'plugins/work/mcp.json', value => {
      value.mcpServers = {
        '서버|one': {
          type: 'stdio',
          command: 'never-run',
          env: {SECRET: 'not-for-output'},
        },
      };
    });
    await changeJson(repo, 'package.json', value => {
      const scripts = value.scripts as Record<string, unknown>;
      scripts.plain = 'do-not-execute-this';
      scripts.object = 'do-not-execute-this';
    });
    await changeJson(repo, 'turbo.json', value => {
      const tasks = value.tasks as Record<string, unknown>;
      tasks['//#plain'] = {command: 'do-not-execute-this', description};
      tasks['//#object'] = {dependencies: ['plain']};
    });
    await syncReferenceDocs(repo, 'generate');
    const [commands, plugins] = await pair(repo);
    for (const markdown of [commands, plugins]) {
      const cells: string[] = [];
      visit(parsed(markdown), 'tableCell', cell => {
        cells.push(mdastToString(cell));
      });
      assert(cells.includes(description));
    }
    assertStringIncludes(plugins, '서버\\|one');
    assertEquals(plugins.includes('not-for-output'), false);
    assertEquals(plugins.includes('never-run'), false);
    assertEquals(commands.includes('do-not-execute-this'), false);
    assertEquals((plugins.match(/None declared/g) ?? []).length, 1);
    assertEquals((plugins.match(/Not declared/g) ?? []).length, 1);
  });
});

test('references: invalid manifests, tasks and duplicate identities retain the previous pair', async () => {
  await fixture(async repo => {
    await syncReferenceDocs(repo, 'generate');
    const initial = await pair(repo);
    const cases: [string, string | null][] = [
      ['plugins/chat/plugin.json', '{broken'],
      ['plugins/chat/plugin.json', '{}'],
      ['plugins/chat/plugin.json', null],
      ['plugins/work/mcp.json', '{}'],
      ['package.json', '{"scripts":{"invalid":{}}}'],
      ['package.json', '{"scripts":{"invalid":1}}'],
      ['turbo.json', '{"tasks":{"invalid":{"description":1}}}'],
      ['turbo.json', '{"tasks":{"invalid":1}}'],
    ];
    for (const [path, invalid] of cases) {
      const saved = await readText(join(repo, path));
      if (invalid === null) await rm(join(repo, path));
      else await writeFile(join(repo, path), invalid);
      await assertRejects(() => syncReferenceDocs(repo, 'generate'));
      await checkUnchanged(repo, false);
      assertEquals(await pair(repo), initial);
      await writeFile(join(repo, path), saved);
    }
    await changeJson(repo, 'plugins/chat/plugin.json', value => {
      value.name = 'code';
    });
    await assertRejects(
      () => syncReferenceDocs(repo, 'generate'),
      Error,
      'Duplicate plugin identities',
    );
    assertEquals(await pair(repo), initial);
  });
});

test('references: every failed help form preserves output and check never repairs it', async () => {
  await fixture(async repo => {
    await syncReferenceDocs(repo, 'generate');
    const initial = await pair(repo);
    for (const script of [
      'process.exit(1);',
      'console.error("unexpected diagnostic"); console.log("Usage: doctor --help");',
      'process.stdout.write(Buffer.from([255]));',
      '',
      'console.log("\\u001b[31mUsage: doctor --help");',
      'console.log("Usage: doctor --help /home/example/private");',
    ]) {
      await writeFile(join(repo, 'scripts/doctor.ts'), script);
      await assertRejects(() => syncReferenceDocs(repo, 'generate'));
      await checkUnchanged(repo, false);
      assertEquals(await pair(repo), initial);
    }
  });
});

test('references: help cannot write, spawn, use network or read live Wiki configuration', async () => {
  await fixture(async repo => {
    await writeFile(
      join(repo, 'scripts/doctor.ts'),
      `
      if (
        process.permission.has('fs.write') ||
        process.permission.has('child') ||
        process.permission.has('fs.read', '${repo}/protected-user-data/secret')
      ) throw new Error('permission widened');
      if (process.env.VERBOSE_BROCCOLI_CONFIG !== undefined || process.argv.slice(2).join() !== '--help') throw new Error('business input');
      console.log('Usage: doctor --help');
    `,
    );
    const old = process.env.VERBOSE_BROCCOLI_CONFIG;
    process.env.VERBOSE_BROCCOLI_CONFIG = join(
      repo,
      'protected-user-data/secret',
    );
    try {
      await syncReferenceDocs(repo, 'generate');
      await checkUnchanged(repo, true);
    } finally {
      if (old === undefined) delete process.env.VERBOSE_BROCCOLI_CONFIG;
      else process.env.VERBOSE_BROCCOLI_CONFIG = old;
    }
    assertEquals(
      await readText(join(repo, 'protected-user-data/secret')),
      'User-data sentinel.\n',
    );
  });
});

test('references: passing and drifting checks preserve working files and the Git index', async () => {
  await fixture(async repo => {
    await syncReferenceDocs(repo, 'generate');
    await git(repo, ['init', '--quiet', '--template=']);
    await git(repo, ['add', '.']);
    await checkUnchanged(repo, true);
    const commands = join(repo, 'docs/reference/commands.md');
    const original = await readText(commands);
    await writeFile(commands, `${original}Changed.\n`);
    await checkUnchanged(repo, false);
    await rm(commands);
    await checkUnchanged(repo, false);
    await writeFile(commands, original);
    await changeJson(repo, 'plugins/chat/plugin.json', value => {
      value.description = 'Changed source.';
    });
    await checkUnchanged(repo, false);
    await syncReferenceDocs(repo, 'generate');
    await checkUnchanged(repo, true);
  });
});

test('references: tracked, untracked, ignored, directory and symlink extras are never read or removed', async () => {
  await fixture(async repo => {
    await syncReferenceDocs(repo, 'generate');
    await git(repo, ['init', '--quiet', '--template=']);
    await writeFile(join(repo, '.gitignore'), 'docs/reference/ignored.md\n');
    for (const name of ['tracked.md', 'untracked.md', 'ignored.md'])
      await writeFile(
        join(repo, 'docs/reference', name),
        `Protected ${name}.\n`,
      );
    await git(repo, ['add', 'docs/reference/tracked.md']);
    await mkdir(join(repo, 'docs/reference/unknown'));
    await writeFile(
      join(repo, 'docs/reference/unknown/secret'),
      'Nested secret.',
    );
    await symlink(
      join(repo, 'protected-user-data/secret'),
      join(repo, 'docs/reference/linked.md'),
    );
    const original = fsPromises.readFile;
    const reads = stubBuiltin(fsPromises, 'readFile', (path, options) => {
      const value = String(path);
      if (
        /\/(?:tracked|untracked|ignored|linked)\.md$/.test(value) ||
        value.includes('/unknown/')
      )
        throw new Error('Read an unexpected entry.');
      return original(path, options);
    });
    try {
      await assertRejects(
        () => syncReferenceDocs(repo, 'check'),
        Error,
        'The command completed its checks',
      );
      await assertRejects(
        () => syncReferenceDocs(repo, 'generate'),
        Error,
        'Unexpected entries',
      );
      assert(reads.calls.length > 0);
    } finally {
      reads.restore();
    }
    for (const name of ['tracked.md', 'untracked.md', 'ignored.md'])
      assertStringIncludes(
        await readText(join(repo, 'docs/reference', name)),
        'Protected',
      );
    await checkUnchanged(repo, false);
  });
});

test('references: input and output drift during help collection fail before publication', async () => {
  await fixture(async repo => {
    await syncReferenceDocs(repo, 'generate');
    for (const path of [
      'plugins/chat/plugin.json',
      'docs/reference/commands.md',
    ]) {
      const before = await pair(repo);
      const original = childProcess.execFile;
      let changed = false;
      {
        const replacement = ((...input: unknown[]) => {
          const [file, args, options, callback] = input;
          const finish = callback as (
            error: Error | null,
            stdout: Buffer,
            stderr: Buffer,
          ) => void;
          const exec = original as unknown as (...values: unknown[]) => unknown;
          return exec(
            file,
            args,
            options,
            (error: Error | null, stdout: Buffer, stderr: Buffer) => {
              if (!changed) {
                changed = true;
                void readText(join(repo, path))
                  .then(text => writeFile(join(repo, path), `${text}\n`))
                  .then(
                    () => finish(error, stdout, stderr),
                    writeError => finish(writeError as Error, stdout, stderr),
                  );
              } else finish(error, stdout, stderr);
            },
          );
        }) as unknown as typeof original;
        const command = stub(childProcess, 'execFile', replacement);
        syncBuiltinESMExports();
        try {
          await assertRejects(
            () => syncReferenceDocs(repo, 'generate'),
            Error,
            'changed during collection',
          );
          assert(command.calls.length > 0);
        } finally {
          command.restore();
          syncBuiltinESMExports();
        }
      }
      if (path.startsWith('plugins/')) assertEquals(await pair(repo), before);
      else assertEquals((await pair(repo))[0], `${before[0]}\n`);
      await syncReferenceDocs(repo, 'generate');
    }
  });
});

test('references: failed replacement restores the exact previous pair', async () => {
  await fixture(async repo => {
    await syncReferenceDocs(repo, 'generate');
    const initial = await pair(repo);
    await changeJson(repo, 'plugins/chat/plugin.json', value => {
      value.description = 'Replacement';
    });
    const original = fsPromises.rename;
    const renames = stubBuiltin(fsPromises, 'rename', (from, to) => {
      if (String(from).endsWith('/.reference-publication/next'))
        return Promise.reject(new Error('Injected publication failure'));
      return original(from, to);
    });
    try {
      await assertRejects(
        () => syncReferenceDocs(repo, 'generate'),
        Error,
        'Publication failed',
      );
      assert(renames.calls.length >= 3);
      assertEquals(await pair(repo), initial);
      await assertRejects(
        () => stat(join(repo, 'docs/.reference-publication')),
        Error,
        'ENOENT',
      );
    } finally {
      renames.restore();
    }
  });
});

test('references: failed rollback retains recovery and the next generation restores it', async () => {
  await fixture(async repo => {
    await syncReferenceDocs(repo, 'generate');
    const initial = await pair(repo);
    await changeJson(repo, 'plugins/chat/plugin.json', value => {
      value.description = 'Recovered replacement';
    });
    const original = fsPromises.rename;
    {
      const renames = stubBuiltin(fsPromises, 'rename', (from, to) => {
        if (String(from).includes('/.reference-publication/'))
          return Promise.reject(
            new Error('Injected publication and rollback failure'),
          );
        return original(from, to);
      });
      try {
        await assertRejects(
          () => syncReferenceDocs(repo, 'generate'),
          Error,
          'docs/.reference-publication',
        );
        assert(renames.calls.length >= 3);
      } finally {
        renames.restore();
      }
    }
    assertEquals(
      await Promise.all(
        referenceFiles.map(file =>
          readText(join(repo, 'docs/.reference-publication/previous', file)),
        ),
      ),
      initial,
    );
    await checkUnchanged(repo, false);
    await syncReferenceDocs(repo, 'generate');
    assertStringIncludes((await pair(repo))[1], 'Recovered replacement');
    await checkUnchanged(repo, true);
  });
});

test('references: first-publication failure retains the complete stage for explicit recovery', async () => {
  await fixture(async repo => {
    const original = fsPromises.rename;
    {
      const renames = stubBuiltin(fsPromises, 'rename', (from, to) => {
        if (String(from).endsWith('/.reference-publication/next'))
          return Promise.reject(new Error('First publication failed'));
        return original(from, to);
      });
      try {
        await assertRejects(
          () => syncReferenceDocs(repo, 'generate'),
          Error,
          'docs/.reference-publication',
        );
        assert(renames.calls.length > 0);
      } finally {
        renames.restore();
      }
    }
    for (const file of referenceFiles)
      assert(
        (
          await stat(join(repo, 'docs/.reference-publication/next', file))
        ).isFile(),
      );
    await checkUnchanged(repo, false);
    await syncReferenceDocs(repo, 'generate');
    await checkUnchanged(repo, true);
  });
});

test('references: another writer appearing between renames is preserved with the recovery pair', async () => {
  await fixture(async repo => {
    await syncReferenceDocs(repo, 'generate');
    const initial = await pair(repo);
    const original = fsPromises.rename;
    const renames = stubBuiltin(fsPromises, 'rename', async (from, to) => {
      await original(from, to);
      if (String(to).endsWith('/.reference-publication/previous'))
        await mkdir(join(repo, 'docs/reference'));
    });
    try {
      await assertRejects(
        () => syncReferenceDocs(repo, 'generate'),
        Error,
        'docs/.reference-publication',
      );
      assert(renames.calls.length > 0);
      assertEquals(readdirSync(join(repo, 'docs/reference')), []);
    } finally {
      renames.restore();
    }
    assertEquals(
      await Promise.all(
        referenceFiles.map(file =>
          readText(join(repo, 'docs/.reference-publication/previous', file)),
        ),
      ),
      initial,
    );
    await checkUnchanged(repo, false);
  });
});

test('references: actual SIGKILL between directory renames is detected and recoverable', async () => {
  await fixture(async repo => {
    await syncReferenceDocs(repo, 'generate');
    const initial = await pair(repo);
    await changeJson(repo, 'plugins/chat/plugin.json', value => {
      value.description = 'After interruption';
    });
    const script = `
      import {syncReferenceDocs} from ${JSON.stringify(new URL('./docs.ts', import.meta.url).href)};
      import fsPromises from 'node:fs/promises';
      import {syncBuiltinESMExports} from 'node:module';
      const original = fsPromises.rename;
      fsPromises.rename = async (from, to) => {
        await original(from, to);
        if (String(to).endsWith('/.reference-publication/previous')) {
          console.log('publication-paused');
          await new Promise(() => setInterval(() => {}, 1000));
        }
      };
      syncBuiltinESMExports();
      await syncReferenceDocs(${JSON.stringify(repo)}, 'generate');
    `;
    const child = spawn(
      process.execPath,
      [
        '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',
        '--permission',
        '--allow-fs-read=*',
        '--allow-fs-write=*',
        '--allow-child-process',
        '--input-type=module',
        '-e',
        script,
      ],
      {stdio: ['ignore', 'pipe', 'pipe']},
    );
    const paused = await new Promise<Buffer>((resolve, reject) => {
      child.once('error', reject);
      child.stdout.once('data', chunk => resolve(Buffer.from(chunk)));
    });
    assertStringIncludes(decoder.decode(paused), 'publication-paused');
    child.kill('SIGKILL');
    const [, signal] = (await once(child, 'close')) as [
      number | null,
      NodeJS.Signals | null,
    ];
    assertEquals(signal, 'SIGKILL');
    assertEquals(
      await Promise.all(
        referenceFiles.map(file =>
          readText(join(repo, 'docs/.reference-publication/previous', file)),
        ),
      ),
      initial,
    );
    await checkUnchanged(repo, false);
    await syncReferenceDocs(repo, 'generate');
    assertStringIncludes((await pair(repo))[1], 'After interruption');
    await checkUnchanged(repo, true);
  });
});

test('references: local and PR check entrypoints agree without Node actions', async () => {
  const packageConfig = JSON.parse(await readText(join(root, 'package.json')));
  const tasks = JSON.parse(await readText(join(root, 'turbo.json'))).tasks;
  assertEquals(
    tasks['verbose-broccoli-python#check'].dependsOn.includes('//#docs:check'),
    true,
  );
  assertEquals(
    tasks['verbose-broccoli-python#test'].dependsOn.includes('//#test:docs'),
    true,
  );
  assertEquals(
    packageConfig.scripts['docs:check'].includes('--allow-fs-write'),
    false,
  );
  const workflow = parse(
    await readText(join(root, '.github/workflows/docs-check.yml')),
  ) as {
    on: {pull_request: unknown};
    permissions: {contents: string};
    jobs: {references: {steps: {run?: string; uses?: string}[]}};
  };
  assert('pull_request' in workflow.on);
  assertEquals(workflow.permissions.contents, 'read');
  const steps = workflow.jobs.references.steps;
  assert(steps.every(step => !step.uses));
  assertEquals(steps.at(-1)?.run, 'npm run docs:check');
  assert(steps.some(step => step.run?.includes('v24.19.0-linux-x64')));
  assert(steps.some(step => step.run?.includes('npm ci --ignore-scripts')));
  await fixture(async repo => {
    await syncReferenceDocs(repo, 'generate');
    const before = await tree(repo);
    const result = commandOutput('npm', {
      args: ['run', '--silent', 'docs:check'],
      cwd: repo,
    });
    assertEquals(result.code, 0, decoder.decode(result.stderr));
    assertEquals(JSON.parse(decoder.decode(result.stdout)).status, 'PASS');
    assertEquals(await tree(repo), before);
    await rm(join(repo, 'docs/reference/commands.md'));
    const missing = await tree(repo);
    const drift = commandOutput('npm', {
      args: ['run', '--silent', 'docs:check'],
      cwd: repo,
    });
    assertEquals(drift.code, 1);
    assertEquals(drift.stdout.length, 0);
    assert(
      decoder.decode(drift.stderr).startsWith('{'),
      decoder.decode(drift.stderr),
    );
    const diagnostic = JSON.parse(decoder.decode(drift.stderr));
    assertEquals(diagnostic.error.code, 'CHECK_FAILED');
    assertEquals(diagnostic.details.missing, ['docs/reference/commands.md']);
    assertEquals(diagnostic.details.refresh, 'npm run docs:generate');
    assertEquals(await tree(repo), missing);
    const invalid = commandOutput(process.execPath, {
      args: [
        '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',
        '--permission',
        `--allow-fs-read=${join(repo, 'scripts')}`,
        `--allow-fs-read=${join(repo, 'node_modules')}`,
        `--allow-fs-read=${join(root, 'node_modules')}`,
        `--allow-fs-read=${join(repo, 'plugins')}`,
        `--allow-fs-read=${join(repo, 'docs')}`,
        `--allow-fs-read=${join(repo, 'package.json')}`,
        `--allow-fs-read=${join(repo, 'package-lock.json')}`,
        `--allow-fs-read=${join(repo, 'turbo.json')}`,
        `--allow-fs-read=${join(repo, 'tsconfig.json')}`,
        `--allow-fs-read=${join(repo, 'eslint.ignores.js')}`,
        '--allow-child-process',
        join(repo, 'scripts/docs.ts'),
        'unknown',
      ],
      cwd: repo,
    });
    assertEquals(invalid.code, 2, decoder.decode(invalid.stderr));
    assertEquals(
      JSON.parse(decoder.decode(invalid.stderr)).error.code,
      'INVALID_ARGUMENT',
    );
  });
});
