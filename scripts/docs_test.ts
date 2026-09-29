import {spawn, spawnSync} from 'node:child_process';
import {once} from 'node:events';
import childProcess from 'node:child_process';
import {syncBuiltinESMExports} from 'node:module';
import {test} from 'node:test';
import {
  assert,
  assertEquals,
  assertRejects,
  assertStringIncludes,
} from '@std/assert';
import {copy, walk} from '@std/fs';
import {fromFileUrl, join, resolve} from '@std/path';
import {stub} from '@std/testing/mock';
import {createProcessor} from '@mdx-js/mdx';
import remarkGfm from 'remark-gfm';
import {toString as mdastToString} from 'mdast-util-to-string';
import {visit} from 'unist-util-visit';
import {parse} from '@eemeli/yaml';
import {collectHelp, documentedCommands, syncReferenceDocs} from './docs.ts';

const root = fromFileUrl(new URL('../', import.meta.url));
const decoder = new TextDecoder();
const referenceFiles = ['commands.md', 'plugins.md'];

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
  return {
    code: result.status ?? 1,
    success: result.status === 0,
    stdout: result.stdout ?? Buffer.alloc(0),
    stderr: result.stderr ?? Buffer.alloc(0),
  };
}

async function fixture(run: (repo: string) => Promise<void>, realHelp = false) {
  const repo = await Deno.makeTempDir({prefix: 'docs-test-'});
  try {
    for (const name of ['scripts', 'plugins/code/skills/clean-code'])
      await copy(join(root, name), join(repo, name));
    for (const name of [
      'package.json',
      'package-lock.json',
      'turbo.json',
      'tsconfig.json',
      'biome.json',
    ])
      await Deno.copyFile(join(root, name), join(repo, name));
    await Deno.symlink(join(root, 'node_modules'), join(repo, 'node_modules'), {
      type: 'dir',
    });
    for (const name of ['chat', 'code', 'work']) {
      await Deno.mkdir(join(repo, 'plugins', name), {recursive: true});
      for (const file of ['plugin.json', 'mcp.json', 'deno.json']) {
        try {
          await Deno.copyFile(
            join(root, 'plugins', name, file),
            join(repo, 'plugins', name, file),
          );
        } catch (error) {
          if (!(error instanceof Deno.errors.NotFound)) throw error;
        }
      }
    }
    await Deno.mkdir(join(repo, 'docs'));
    await Deno.mkdir(join(repo, 'protected-user-data'));
    await Deno.writeTextFile(
      join(repo, 'docs/authored.md'),
      'Authored sentinel.\n',
    );
    await Deno.writeTextFile(
      join(repo, 'protected-user-data/secret'),
      'User-data sentinel.\n',
    );
    if (!realHelp)
      for (const [name, script] of documentedCommands) {
        if (name !== 'plugins:validate')
          await Deno.writeTextFile(
            join(repo, script),
            `if (Deno.args.join() !== '--help') throw new Error('business action');\nconsole.log(${JSON.stringify(`Usage: ${name}\n\nOptions:\n  --help - Show help.\n`)});\n`,
          );
      }
    await run(repo);
  } finally {
    await Deno.remove(repo, {recursive: true});
  }
}

async function pair(repo: string) {
  return await Promise.all(
    referenceFiles.map(file =>
      Deno.readTextFile(join(repo, 'docs/reference', file)),
    ),
  );
}
async function changeJson(
  repo: string,
  path: string,
  change: (value: Record<string, unknown>) => void,
) {
  const value = JSON.parse(await Deno.readTextFile(join(repo, path)));
  change(value);
  await Deno.writeTextFile(join(repo, path), JSON.stringify(value, null, 2));
}
async function tree(repo: string) {
  const values = [];
  for await (const entry of walk(repo, {followSymlinks: false})) {
    if (entry.isFile)
      values.push([
        entry.path.slice(repo.length),
        Buffer.from(await Deno.readFile(entry.path)).toString('hex'),
      ]);
    else if (entry.isSymlink)
      values.push([
        entry.path.slice(repo.length),
        await Deno.readLink(entry.path),
      ]);
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
      JSON.parse(await Deno.readTextFile(join(repo, 'package.json'))).scripts,
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
        assert(await Deno.stat(resolve(repo, 'docs/reference', link)));
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
      const saved = await Deno.readTextFile(join(repo, path));
      if (invalid === null) await Deno.remove(join(repo, path));
      else await Deno.writeTextFile(join(repo, path), invalid);
      await assertRejects(() => syncReferenceDocs(repo, 'generate'));
      await checkUnchanged(repo, false);
      assertEquals(await pair(repo), initial);
      await Deno.writeTextFile(join(repo, path), saved);
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
      'Deno.exit(1);',
      'console.error("unexpected diagnostic"); console.log("Usage: doctor --help");',
      'Deno.stdout.writeSync(new Uint8Array([255]));',
      '',
      'console.log("\\u001b[31mUsage: doctor --help");',
      'console.log("Usage: doctor --help /home/example/private");',
    ]) {
      await Deno.writeTextFile(join(repo, 'scripts/doctor.ts'), script);
      await assertRejects(() => syncReferenceDocs(repo, 'generate'));
      await checkUnchanged(repo, false);
      assertEquals(await pair(repo), initial);
    }
  });
});

test('references: help cannot write, spawn, use network or read live Wiki configuration', async () => {
  await fixture(async repo => {
    await Deno.writeTextFile(
      join(repo, 'scripts/doctor.ts'),
      `
      if (
        process.permission.has('fs.write') ||
        process.permission.has('child') ||
        process.permission.has('fs.read', '${repo}/protected-user-data/secret')
      ) throw new Error('permission widened');
      if (Deno.env.has('VERBOSE_BROCCOLI_CONFIG') || Deno.args.join() !== '--help') throw new Error('business input');
      console.log('Usage: doctor --help');
    `,
    );
    const old = Deno.env.get('VERBOSE_BROCCOLI_CONFIG');
    Deno.env.set(
      'VERBOSE_BROCCOLI_CONFIG',
      join(repo, 'protected-user-data/secret'),
    );
    try {
      await syncReferenceDocs(repo, 'generate');
      await checkUnchanged(repo, true);
    } finally {
      if (old === undefined) Deno.env.delete('VERBOSE_BROCCOLI_CONFIG');
      else Deno.env.set('VERBOSE_BROCCOLI_CONFIG', old);
    }
    assertEquals(
      await Deno.readTextFile(join(repo, 'protected-user-data/secret')),
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
    const original = await Deno.readTextFile(commands);
    await Deno.writeTextFile(commands, `${original}Changed.\n`);
    await checkUnchanged(repo, false);
    await Deno.remove(commands);
    await checkUnchanged(repo, false);
    await Deno.writeTextFile(commands, original);
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
    await Deno.writeTextFile(
      join(repo, '.gitignore'),
      'docs/reference/ignored.md\n',
    );
    for (const name of ['tracked.md', 'untracked.md', 'ignored.md'])
      await Deno.writeTextFile(
        join(repo, 'docs/reference', name),
        `Protected ${name}.\n`,
      );
    await git(repo, ['add', 'docs/reference/tracked.md']);
    await Deno.mkdir(join(repo, 'docs/reference/unknown'));
    await Deno.writeTextFile(
      join(repo, 'docs/reference/unknown/secret'),
      'Nested secret.',
    );
    await Deno.symlink(
      join(repo, 'protected-user-data/secret'),
      join(repo, 'docs/reference/linked.md'),
    );
    const original = Deno.readFile;
    {
      using reads = stub(Deno, 'readFile', (path, options) => {
        const value = String(path);
        if (
          /\/(?:tracked|untracked|ignored|linked)\.md$/.test(value) ||
          value.includes('/unknown/')
        )
          throw new Error('Read an unexpected entry.');
        return original(path, options);
      });
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
    }
    for (const name of ['tracked.md', 'untracked.md', 'ignored.md'])
      assertStringIncludes(
        await Deno.readTextFile(join(repo, 'docs/reference', name)),
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
                void Deno.readTextFile(join(repo, path))
                  .then(text =>
                    Deno.writeTextFile(join(repo, path), `${text}\n`),
                  )
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
    const original = Deno.rename;
    using rename = stub(Deno, 'rename', (from, to) => {
      if (String(from).endsWith('/.reference-publication/next'))
        return Promise.reject(new Error('Injected publication failure'));
      return original(from, to);
    });
    await assertRejects(
      () => syncReferenceDocs(repo, 'generate'),
      Error,
      'Publication failed',
    );
    assert(rename.calls.length >= 3);
    assertEquals(await pair(repo), initial);
    await assertRejects(
      () => Deno.stat(join(repo, 'docs/.reference-publication')),
      Deno.errors.NotFound,
    );
  });
});

test('references: failed rollback retains recovery and the next generation restores it', async () => {
  await fixture(async repo => {
    await syncReferenceDocs(repo, 'generate');
    const initial = await pair(repo);
    await changeJson(repo, 'plugins/chat/plugin.json', value => {
      value.description = 'Recovered replacement';
    });
    const original = Deno.rename;
    {
      using rename = stub(Deno, 'rename', (from, to) => {
        if (String(from).includes('/.reference-publication/'))
          return Promise.reject(
            new Error('Injected publication and rollback failure'),
          );
        return original(from, to);
      });
      await assertRejects(
        () => syncReferenceDocs(repo, 'generate'),
        Error,
        'docs/.reference-publication',
      );
      assert(rename.calls.length >= 3);
    }
    assertEquals(
      await Promise.all(
        referenceFiles.map(file =>
          Deno.readTextFile(
            join(repo, 'docs/.reference-publication/previous', file),
          ),
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
    const original = Deno.rename;
    {
      using rename = stub(Deno, 'rename', (from, to) => {
        if (String(from).endsWith('/.reference-publication/next'))
          return Promise.reject(new Error('First publication failed'));
        return original(from, to);
      });
      await assertRejects(
        () => syncReferenceDocs(repo, 'generate'),
        Error,
        'docs/.reference-publication',
      );
      assert(rename.calls.length > 0);
    }
    for (const file of referenceFiles)
      assert(
        (await Deno.stat(join(repo, 'docs/.reference-publication/next', file)))
          .isFile,
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
    const original = Deno.rename;
    using rename = stub(Deno, 'rename', async (from, to) => {
      await original(from, to);
      if (String(to).endsWith('/.reference-publication/previous'))
        await Deno.mkdir(join(repo, 'docs/reference'));
    });
    await assertRejects(
      () => syncReferenceDocs(repo, 'generate'),
      Error,
      'docs/.reference-publication',
    );
    assert(rename.calls.length > 0);
    assertEquals([...Deno.readDirSync(join(repo, 'docs/reference'))], []);
    assertEquals(
      await Promise.all(
        referenceFiles.map(file =>
          Deno.readTextFile(
            join(repo, 'docs/.reference-publication/previous', file),
          ),
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
      const rename = Deno.rename;
      Deno.rename = async (from, to) => {
        await rename(from, to);
        if (String(to).endsWith('/.reference-publication/previous')) {
          console.log('publication-paused');
          await new Promise(() => setInterval(() => {}, 1000));
        }
      };
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
        '--import',
        join(root, 'scripts/deno_shim.ts'),
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
          Deno.readTextFile(
            join(repo, 'docs/.reference-publication/previous', file),
          ),
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
  const packageConfig = JSON.parse(
    await Deno.readTextFile(join(root, 'package.json')),
  );
  const tasks = JSON.parse(
    await Deno.readTextFile(join(root, 'turbo.json')),
  ).tasks;
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
    await Deno.readTextFile(join(root, '.github/workflows/docs-check.yml')),
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
  assert(steps.some(step => step.run?.includes('v2.9.6/deno-')));
  assert(steps.some(step => step.run?.includes('npm ci --ignore-scripts')));
  assert(
    steps.some(step =>
      step.run?.includes(
        'deno install --config plugins/code/skills/clean-code/deno.json --frozen',
      ),
    ),
  );
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
    await Deno.remove(join(repo, 'docs/reference/commands.md'));
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
        `--allow-fs-read=${join(repo, 'biome.json')}`,
        '--allow-child-process',
        '--import',
        join(repo, 'scripts/deno_shim.ts'),
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
