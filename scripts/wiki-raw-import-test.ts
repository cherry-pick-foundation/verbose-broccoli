import {test} from 'node:test';
import {
  appendFile,
  chmod,
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  rename,
  rm,
  stat,
  symlink,
  writeFile,
} from 'node:fs/promises';
import {readdirSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {assert, assertEquals, assertMatch, assertRejects} from '@std/assert';
import {basename, dirname, fromFileUrl, join, relative} from '@std/path';
import {spawn, type ChildProcess} from 'node:child_process';

const script = fromFileUrl(
  new URL(
    '../plugins/work/skills/wiki-raw-import/scripts/raw_import.py',
    import.meta.url,
  ),
);
const decoder = new TextDecoder();
const encoder = new TextEncoder();
const readText = (path: string) => readFile(path, 'utf8');
const readDir = (path: string) => readdirSync(path, {withFileTypes: true});

async function* walk(root: string) {
  yield {path: root, isDirectory: true, isSymlink: false};
  for (const entry of await readdir(root, {
    recursive: true,
    withFileTypes: true,
  })) {
    yield {
      path: join(entry.parentPath, entry.name),
      isDirectory: entry.isDirectory(),
      isSymlink: entry.isSymbolicLink(),
    };
  }
}

function output(command: ChildProcess) {
  return new Promise<{code: number; stdout: string; stderr: string}>(
    (resolve, reject) => {
      const stdout: Buffer[] = [];
      const stderr: Buffer[] = [];
      command.stdout?.on('data', (chunk: Buffer) => stdout.push(chunk));
      command.stderr?.on('data', (chunk: Buffer) => stderr.push(chunk));
      command.once('error', reject);
      command.once('close', (code, signal) => {
        if (signal) {
          reject(new Error(`Child process terminated by signal ${signal}`));
          return;
        }
        resolve({
          code: code ?? 1,
          stdout: decoder.decode(Buffer.concat(stdout)),
          stderr: decoder.decode(Buffer.concat(stderr)),
        });
      });
    },
  );
}

void test('wiki raw import test helper rejects signal termination', async () => {
  const command = spawn(
    process.execPath,
    ['-e', "process.kill(process.pid, 'SIGKILL')"],
    {stdio: ['ignore', 'pipe', 'pipe']},
  );
  await assertRejects(() => output(command), Error, 'SIGKILL');
});

async function uvLocation(...args: string[]) {
  const result = await output(
    spawn('uv', args, {stdio: ['ignore', 'pipe', 'pipe']}),
  );
  assertEquals(result.code, 0, result.stderr);
  return result.stdout.trim();
}

// uv's prepared interpreter and dependency cache are tooling, not Wiki roots.
const uvCache = await uvLocation('cache', 'dir');
const python = await uvLocation('python', 'find', '3.14');

async function snapshot(root: string, times = false) {
  const entries = [];
  for await (const entry of walk(root)) {
    const fileInfo = await lstat(entry.path);
    entries.push({
      path: relative(root, entry.path),
      mode: fileInfo.mode,
      bytes: fileInfo.isFile() ? Array.from(await readFile(entry.path)) : null,
      ...(times
        ? {mtime: (await lstat(entry.path, {bigint: true})).mtimeNs}
        : {}),
    });
  }
  return entries.sort((a, b) => a.path.localeCompare(b.path));
}

async function fixture(run: (f: Fixture) => Promise<void>) {
  const home = await mkdtemp(join(tmpdir(), 'wiki-raw-import-'));
  const f = new Fixture(home);
  try {
    await run(f);
  } finally {
    // Published bags are deliberately read-only; only the fixture owner removes them.
    for await (const entry of walk(home)) {
      if (!entry.isSymlink)
        await chmod(entry.path, entry.isDirectory ? 0o700 : 0o600);
    }
    await f.originalsUnchanged();
    await rm(home, {recursive: true});
  }
}

class Fixture {
  env: Record<string, string>;
  instance: string;
  raw: string;
  originals = new Map<string, {bytes: Uint8Array; mtime: number | undefined}>();

  readonly home: string;

  constructor(home: string) {
    this.home = home;
    this.env = {
      HOME: home,
      XDG_DATA_HOME: join(home, 'data'),
      XDG_STATE_HOME: join(home, 'state'),
      XDG_CACHE_HOME: join(home, 'cache'),
      XDG_CONFIG_HOME: join(home, 'config'),
      UV_CACHE_DIR: uvCache,
      UV_PYTHON: python,
      UV_PYTHON_DOWNLOADS: 'never',
      UV_NO_CONFIG: '1',
      PYTHONNOUSERSITE: '1',
      GIT_CONFIG_GLOBAL: join(home, '.gitconfig'),
      GIT_CONFIG_NOSYSTEM: '1',
    };
    this.instance = join(
      this.env.XDG_DATA_HOME,
      'verbose-broccoli/llm-wiki/work',
    );
    this.raw = join(this.instance, 'raw');
  }

  command(...args: string[]) {
    return spawn(
      'uv',
      ['run', '--quiet', '--locked', '--offline', '--script', script, ...args],
      {
        cwd: this.home,
        env: {...process.env, ...this.env},
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 30_000,
      },
    );
  }

  async run(...args: string[]) {
    const result = await output(this.command(...args));
    await this.originalsUnchanged();
    return result;
  }

  async init() {
    const result = await this.run('init');
    assertEquals(result.code, 0, result.stderr);
    assertEquals(result.stderr, '');
    return JSON.parse(result.stdout) as {created: string[]};
  }

  async file(name: string, text = 'synthetic original\n') {
    const path = join(this.home, 'originals', name);
    return await this.fileAt(path, text);
  }

  async fileAt(path: string, text = 'synthetic original\n') {
    await mkdir(dirname(path), {recursive: true});
    await writeFile(path, text);
    this.originals.set(path, {
      bytes: Buffer.from(text),
      mtime: (await stat(path)).mtime?.getTime(),
    });
    return path;
  }

  async originalsUnchanged() {
    for (const [path, before] of this.originals) {
      const fileInfo = await stat(path);
      assertEquals(fileInfo.mtime?.getTime(), before.mtime, path);
      if ((fileInfo.mode ?? 0) & 0o400)
        assertEquals(await readFile(path), before.bytes, path);
    }
  }

  async selection(items: unknown[]) {
    const path = join(
      this.env.XDG_STATE_HOME,
      'verbose-broccoli/llm-wiki/work/selections/test.jsonl',
    );
    await mkdir(dirname(path), {recursive: true});
    await writeFile(
      path,
      items.map(item => `${JSON.stringify(item)}\n`).join(''),
    );
    return path;
  }

  async admit(paths: string[], kind = 'files') {
    return await this.run(
      'admit',
      '--selection',
      await this.selection(paths.map(path => ({path, kind}))),
    );
  }

  staging(wiki = 'work') {
    return join(this.env.XDG_CACHE_HOME, 'verbose-broccoli/raw-import', wiki);
  }
}

type Item = {
  path: string;
  outcome: string;
  source_id: string | null;
  revision: string | null;
  reason: string | null;
};

function report(
  result: {stdout: string; stderr: string; code: number},
  code = 0,
) {
  assertEquals(result.code, code, result.stderr);
  assertEquals(result.stderr.trim().split('\n').length, 1);
  if (code === 0) assertEquals(result.stderr, '');
  const lines = result.stdout
    .trim()
    .split('\n')
    .map(line => JSON.parse(line));
  const summary = lines.pop().summary as Record<string, number>;
  const items = lines as Item[];
  assertEquals(Object.keys(summary).sort(), [
    'admitted',
    'already_admitted',
    'failed',
    'refused',
  ]);
  for (const item of items) {
    assertEquals(Object.keys(item).sort(), [
      'outcome',
      'path',
      'reason',
      'revision',
      'source_id',
    ]);
    if (['failed', 'refused'].includes(item.outcome)) assert(item.reason);
  }
  for (const [outcome, count] of Object.entries(summary)) {
    assertEquals(count, items.filter(item => item.outcome === outcome).length);
  }
  return items;
}

function revisionPath(f: Fixture, item: Item, kind = 'files') {
  assert(item.source_id && item.revision);
  return join(f.raw, kind, item.source_id, item.revision);
}

async function digest(bytes: Uint8Array) {
  const hash = await crypto.subtle.digest('SHA-256', new Uint8Array(bytes));
  return Array.from(new Uint8Array(hash), byte =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
}

void test('raw import: locked offline help and missing-instance errors', async () => {
  await fixture(async f => {
    const help = await f.run('--help');
    assertEquals(help.code, 0, help.stderr);
    assertEquals(help.stderr, '');
    assertMatch(help.stdout, /init.*admit.*verify/);
    for (const args of [
      ['verify'],
      ['admit', '--selection', await f.selection([])],
    ]) {
      const before = await snapshot(f.home, true);
      const result = await f.run(...args);
      assertEquals(result.code, 2);
      assertEquals(result.stdout, '');
      assert(result.stderr);
      assertEquals(await snapshot(f.home, true), before);
    }
  });
});

void test('raw import US1: one immutable bag preserves payload, digest, timestamps and provenance', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('- 한국어 paper.txt');
    const [item] = report(await f.admit([path]));
    assertEquals(item.outcome, 'admitted');
    assertEquals(item.path, path);
    assertEquals(item.reason, null);
    assertMatch(
      item.source_id!,
      /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
    assertMatch(item.revision!, /^\d{8}T\d{12}Z$/);
    const revision = revisionPath(f, item);
    const payload = join(revision, 'data', basename(path));
    assertEquals(await readFile(payload), await readFile(path));
    assertEquals((await stat(payload)).mtime, (await stat(path)).mtime);
    const entries = await snapshot(revision);
    assertEquals(
      entries
        .filter(entry => entry.bytes !== null)
        .map(entry => entry.path)
        .sort(),
      [
        'bag-info.txt',
        'bagit.txt',
        `data/${basename(path)}`,
        'manifest-sha256.txt',
        'tagmanifest-sha256.txt',
      ].sort(),
    );
    for (const entry of entries)
      assertEquals((entry.mode ?? 0) & 0o222, 0, entry.path);
    assertEquals(
      await readText(join(revision, 'manifest-sha256.txt')),
      `${await digest(await readFile(path))}  data/${basename(path)}\n`,
    );
    const info = Object.fromEntries(
      (await readText(join(revision, 'bag-info.txt')))
        .trim()
        .split('\n')
        .map(line => {
          const separator = line.indexOf(': ');
          return [line.slice(0, separator), line.slice(separator + 2)];
        }),
    );
    assertEquals(info['External-Identifier'], item.source_id);
    assertEquals(info['Internal-Sender-Identifier'], path);
    assertEquals(info['Admission-Time'], item.revision);
    assertMatch(info['Source-Modified'], /T.*\+00:00$/);
    assertEquals(
      new Date(info['Source-Modified']).getTime(),
      Number((await stat(path, {bigint: true})).mtimeNs / 1_000_000n),
    );
    assertMatch(info['Bagging-Date'], /^\d{4}-\d{2}-\d{2}$/);
    assertEquals(info['Payload-Oxum'], `${(await stat(path)).size}.1`);
    const before = await snapshot(f.home, true);
    const verified = await f.run('verify');
    assertEquals(verified.code, 0, verified.stderr);
    assertEquals(verified.stderr, '');
    assertEquals(JSON.parse(verified.stdout), {count: 1, invalid: []});
    assertEquals(await snapshot(f.home, true), before);
  });
});

for (const damaged of ['payload', 'bag-info.txt']) {
  void test(`raw import US1: verify detects changed ${damaged} without writing`, async () => {
    await fixture(async f => {
      await f.init();
      const path = await f.file('paper.txt');
      const [item] = report(await f.admit([path]));
      const revision = revisionPath(f, item);
      const target = join(
        revision,
        damaged === 'payload' ? 'data/paper.txt' : damaged,
      );
      await chmod(target, 0o600);
      const bytes = await readFile(target);
      bytes[bytes.length - 2] ^= 1;
      await writeFile(target, bytes);
      const before = await snapshot(f.home, true);
      const result = await f.run('verify');
      assertEquals(result.code, 1);
      assertEquals(result.stderr.trim().split('\n').length, 1);
      assertMatch(result.stderr, /1/);
      const verified = JSON.parse(result.stdout);
      assertEquals(verified.count, 1);
      assertEquals(verified.invalid.length, 1);
      assertEquals(
        verified.invalid[0].revision,
        relative(f.instance, revision),
      );
      assert(verified.invalid[0].reason);
      assertEquals(await snapshot(f.home, true), before);
    });
  });
}

void test('raw import US1: an unreadable original fails without adding evidence', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('unreadable.txt');
    await chmod(path, 0);
    const before = await snapshot(f.raw);
    const [item] = report(await f.admit([path]), 1);
    assertEquals(item.outcome, 'failed');
    assertEquals(await snapshot(f.raw), before);
    await chmod(path, 0o600);
    await f.originalsUnchanged();
  });
});

void test('raw import US1: unrepresentable BagIt provenance fails before publication', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('trailing space ');
    const before = await snapshot(f.raw);
    const [item] = report(await f.admit([path]), 1);
    assertEquals(item.outcome, 'failed');
    assertMatch(item.reason!, /provenance/i);
    assertEquals(await snapshot(f.raw), before);
  });
});

void test('raw import US2: unchanged rerun adds nothing; changes and reversions retain every revision', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('revisions.txt', 'first');
    const [first] = report(await f.admit([path]));
    const before = await snapshot(f.raw);
    const [unchanged] = report(await f.admit([path]));
    assertEquals(unchanged, {...first, outcome: 'already_admitted'});
    assertEquals(await snapshot(f.raw), before);
    await f.file('revisions.txt', 'second');
    const [second] = report(await f.admit([path]));
    await f.file('revisions.txt', 'first');
    const [third] = report(await f.admit([path]));
    assertEquals(second.source_id, first.source_id);
    assertEquals(third.source_id, first.source_id);
    assert(
      first.revision! < second.revision! && second.revision! < third.revision!,
    );
    const revisions = Array.from(
      readDir(dirname(revisionPath(f, first))),
      entry => entry.name,
    ).sort();
    assertEquals(revisions, [first.revision, second.revision, third.revision]);
    for (const [item, text] of [
      [first, 'first'],
      [second, 'second'],
      [third, 'first'],
    ] as const) {
      assertEquals(
        await readText(join(revisionPath(f, item), 'data/revisions.txt')),
        text,
      );
    }
    const verified = await f.run('verify');
    assertEquals(verified.code, 0, verified.stderr);
    assertEquals(JSON.parse(verified.stdout), {count: 3, invalid: []});
  });
});

void test('raw import US2: a new revision must sort after the latest revision', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('revision-order.txt', 'first');
    const [first] = report(await f.admit([path]));
    const source = dirname(revisionPath(f, first));
    const latest = join(source, '99991231T000000000000Z');
    await chmod(source, 0o700);
    await rename(revisionPath(f, first), latest);
    await chmod(source, 0o555);
    await f.file('revision-order.txt', 'changed');
    const originalBytes = await readFile(path);
    const originalMtime = (await stat(path)).mtime?.getTime();
    const before = await snapshot(f.raw);
    const [item] = report(await f.admit([path]), 1);
    assertEquals(item.outcome, 'failed');
    assertEquals(
      item.reason,
      'new revision would not sort after the latest one',
    );
    assertEquals(await snapshot(f.raw), before);
    assertEquals(await readFile(path), originalBytes);
    assertEquals((await stat(path)).mtime?.getTime(), originalMtime);
  });
});

void test('raw import US2: equal bytes at different paths have distinct sources', async () => {
  await fixture(async f => {
    await f.init();
    const paths = [await f.file('one.txt'), await f.file('two.txt')];
    const items = report(await f.admit(paths));
    assertEquals(items.length, 2);
    assert(items[0].source_id !== items[1].source_id);
    assertEquals(
      items.map(item => item.path),
      paths,
    );
  });
});

void test('raw import US2: two source records for one original fail the item', async () => {
  await fixture(async f => {
    await f.init();
    const first = await f.file('first.txt');
    const second = await f.file('second.txt');
    const [, item] = report(await f.admit([first, second]));
    const revision = revisionPath(f, item);
    const infoPath = join(revision, 'bag-info.txt');
    const oldInfo = await readFile(infoPath);
    const newInfo = encoder.encode(
      decoder.decode(oldInfo).replace(second, first),
    );
    const tagPath = join(revision, 'tagmanifest-sha256.txt');
    await chmod(infoPath, 0o600);
    await writeFile(infoPath, newInfo);
    await chmod(tagPath, 0o600);
    await writeFile(
      tagPath,
      (await readText(tagPath)).replace(
        await digest(oldInfo),
        await digest(newInfo),
      ),
    );
    assertEquals((await f.run('verify')).code, 0);
    const before = await snapshot(f.raw);
    const [failed] = report(await f.admit([first]), 1);
    assertEquals(failed.outcome, 'failed');
    assertMatch(failed.reason!, /multiple|two|ambiguous/i);
    assertEquals(await snapshot(f.raw), before);
  });
});

void test('raw import US3: only listed files are admitted without user exclusions', async () => {
  await fixture(async f => {
    await f.init();
    const listed = await f.file('listed.txt');
    await f.file('unlisted.txt');
    const items = report(await f.admit([listed]));
    assertEquals(items.length, 1);
    const files = (await snapshot(f.raw)).filter(entry =>
      entry.path.includes('/data/'),
    );
    assertEquals(files.length, 1);
    assertEquals(basename(files[0].path), 'listed.txt');
  });
});

void test('raw import US3: excluded roots and resolved aliases are refused', async () => {
  await fixture(async f => {
    await f.init();
    const excluded = await f.file('private/excluded.txt');
    const config = join(f.env.XDG_CONFIG_HOME, 'verbose-broccoli/config.toml');
    await mkdir(dirname(config), {recursive: true});
    await writeFile(
      config,
      `[wiki.raw_import]\nexclude = [${JSON.stringify(dirname(excluded))}]\n`,
    );
    const alias = join(f.home, 'alias');
    await symlink(dirname(excluded), alias);
    const link = join(f.home, 'excluded-link');
    await symlink(excluded, link);
    const paths = [excluded, join(alias, basename(excluded)), link];
    for (const variable of [
      'XDG_DATA_HOME',
      'XDG_STATE_HOME',
      'XDG_CACHE_HOME',
    ]) {
      paths.push(
        await f.fileAt(join(f.env[variable], 'verbose-broccoli/forbidden.txt')),
      );
    }
    const before = await snapshot(f.raw);
    const items = report(await f.admit(paths), 1);
    assertEquals(
      items.map(item => item.outcome),
      paths.map(() => 'refused'),
    );
    assertEquals(await snapshot(f.raw), before);
    assertEquals((await f.run('verify')).code, 0);
  });
});

void test('raw import US3: excluded paths stay refused through an escaping directory symlink', async () => {
  await fixture(async f => {
    await f.init();
    const excluded = join(f.home, 'excluded');
    const outside = join(f.home, 'outside');
    const path = await f.fileAt(join(outside, 'escape.txt'));
    await mkdir(excluded, {recursive: true});
    const alias = join(excluded, 'linkdir');
    await symlink(outside, alias);
    const listed = join(alias, basename(path));
    const config = join(f.env.XDG_CONFIG_HOME, 'verbose-broccoli/config.toml');
    await mkdir(dirname(config), {recursive: true});
    await writeFile(
      config,
      `[wiki.raw_import]\nexclude = [${JSON.stringify(excluded)}]\n`,
    );
    const before = await snapshot(f.raw);
    const [item] = report(await f.admit([listed]), 1);
    assertEquals(item.outcome, 'refused');
    assertEquals(item.reason, 'original is under an excluded location');
    assertEquals(await snapshot(f.raw), before);
  });
});

void test('raw import US3: symlinks, folders, missing files, FIFOs and invalid UTF-8 are refused', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('original.txt');
    const originalInfo = async (create: boolean) => {
      const result = await output(
        spawn(
          python,
          [
            '-c',
            `
import json, os, stat, sys
path = os.fsencode(sys.argv[1]) + b'/bad-' + bytes([255])
if sys.argv[2] == 'create':
    with open(path, 'wb') as target:
        target.write(b'invalid UTF-8 filename fixture\\n')
metadata = os.stat(path)
assert stat.S_ISREG(metadata.st_mode)
with open(path, 'rb') as source:
    contents = source.read()
print(json.dumps({
    'path': os.fsdecode(path),
    'mtime_ns': metadata.st_mtime_ns,
    'contents': contents.hex(),
}, ensure_ascii=True))
`,
            f.home,
            create ? 'create' : 'inspect',
          ],
          {env: {...process.env, ...f.env}, stdio: ['ignore', 'pipe', 'pipe']},
        ),
      );
      assertEquals(result.code, 0, result.stderr);
      return JSON.parse(result.stdout) as {
        path: string;
        mtime_ns: number;
        contents: string;
      };
    };
    const invalidOriginal = await originalInfo(true);
    try {
      const symlinkPath = join(f.home, 'symlink');
      await symlink(path, symlinkPath);
      const fifo = join(f.home, 'pipe');
      const prepared = await output(
        spawn(python, ['-c', 'import os,sys; os.mkfifo(sys.argv[1])', fifo], {
          env: {...process.env, ...f.env},
          stdio: ['ignore', 'pipe', 'pipe'],
        }),
      );
      assertEquals(prepared.code, 0, prepared.stderr);
      const paths = [
        symlinkPath,
        dirname(path),
        join(f.home, 'missing'),
        fifo,
        invalidOriginal.path,
      ];
      const before = await snapshot(f.raw);
      const items = report(await f.admit(paths), 1);
      assertEquals(
        items.map(item => item.outcome),
        paths.map(() => 'refused'),
      );
      const invalidItem = items.find(
        item => item.path === invalidOriginal.path,
      );
      assert(invalidItem);
      assertEquals(invalidItem.reason, 'original path is not valid UTF-8');
      assertEquals(await snapshot(f.raw), before);
      assertEquals(await originalInfo(false), invalidOriginal);
    } finally {
      const removed = await output(
        spawn(
          python,
          [
            '-c',
            'import os,sys; os.unlink(os.fsencode(sys.argv[1]) + b"/bad-" + bytes([255]))',
            f.home,
          ],
          {env: {...process.env, ...f.env}, stdio: ['ignore', 'pipe', 'pipe']},
        ),
      );
      assertEquals(removed.code, 0, removed.stderr);
    }
  });
});

for (const invalid of [
  'duplicate',
  'relative',
  'extra field',
  'kind',
  'missing field',
  'not object',
  'invalid JSON',
]) {
  void test(`raw import US3: ${invalid} selection is rejected before any write`, async () => {
    await fixture(async f => {
      await f.init();
      const path = await f.file('valid.txt');
      const valid = {path, kind: 'files'};
      const bad = {
        duplicate: valid,
        relative: {path: 'relative.txt', kind: 'files'},
        'extra field': {...valid, extra: true},
        kind: {...valid, kind: 'unknown'},
        'missing field': {path},
        'not object': [],
        'invalid JSON': valid,
      }[invalid];
      const selection = await f.selection([valid, bad]);
      if (invalid === 'invalid JSON')
        await appendFile(selection, '{invalid}\n');
      const before = await snapshot(f.home, true);
      const result = await f.run('admit', '--selection', selection);
      assertEquals(result.code, 2, result.stderr);
      assertEquals(result.stdout, '');
      assert(result.stderr);
      assertEquals(await snapshot(f.home, true), before);
    });
  });
}

for (const config of [
  '[broken',
  'wiki = 1',
  '[wiki]\nraw_import = []',
  '[wiki.raw_import]\nexclude = "path"',
  '[wiki.raw_import]\nexclude = [1]',
  '[wiki.raw_import]\nexclude = ["relative"]',
]) {
  void test(`raw import US3: malformed configuration fails closed (${config})`, async () => {
    await fixture(async f => {
      await f.init();
      const path = await f.file('valid.txt');
      const selection = await f.selection([{path, kind: 'files'}]);
      const configPath = join(
        f.env.XDG_CONFIG_HOME,
        'verbose-broccoli/config.toml',
      );
      await mkdir(dirname(configPath), {recursive: true});
      await writeFile(configPath, config);
      const before = await snapshot(f.home, true);
      const result = await f.run('admit', '--selection', selection);
      assertEquals(result.code, 2, result.stderr);
      assertEquals(result.stdout, '');
      assert(result.stderr);
      assertEquals(await snapshot(f.home, true), before);
    });
  });
}

void test('raw import US3: an existing source cannot change kind', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('kind.txt');
    report(await f.admit([path], 'notes'));
    for (const text of ['synthetic original\n', 'changed']) {
      await f.file('kind.txt', text);
      const before = await snapshot(f.raw);
      const [item] = report(await f.admit([path], 'files'), 1);
      assertEquals(item.outcome, 'refused');
      assertMatch(item.reason!, /notes/);
      assertEquals(await snapshot(f.raw), before);
    }
  });
});

void test('raw import US4: a publication failure keeps other items and can be retried', async () => {
  await fixture(async f => {
    await f.init();
    const blocked = await f.file('blocked.txt', 'first');
    const [first] = report(await f.admit([blocked]));
    const firstRevision = revisionPath(f, first);
    const before = await snapshot(firstRevision);
    await f.file('blocked.txt', 'second');
    await chmod(dirname(firstRevision), 0o555);
    const good = await f.file('good.txt');
    const items = report(await f.admit([blocked, good]), 1);
    assertEquals(
      items.map(item => item.outcome),
      ['failed', 'admitted'],
    );
    assertEquals(await snapshot(firstRevision), before);
    assertEquals(Array.from(readDir(f.staging())), []);
    assertEquals(JSON.parse((await f.run('verify')).stdout), {
      count: 2,
      invalid: [],
    });
    await chmod(dirname(firstRevision), 0o700);
    const retried = report(await f.admit([blocked, good]));
    assertEquals(
      retried.map(item => item.outcome),
      ['admitted', 'already_admitted'],
    );
    assertEquals(JSON.parse((await f.run('verify')).stdout), {
      count: 3,
      invalid: [],
    });
    assertEquals(Array.from(readDir(f.staging())), []);
  });
});

void test('raw import US5: init copies the schema and creates an uncommitted Wiki with raw ignored', async () => {
  await fixture(async f => {
    const initialized = await f.init();
    assert(initialized.created.length > 0);
    for (const path of initialized.created) {
      assert(path.startsWith(f.home));
      await stat(path);
    }
    assertEquals(
      await readFile(join(f.instance, 'AGENTS.md')),
      await readFile(join(dirname(script), '../assets/AGENTS.md')),
    );
    for (const name of ['index.qmd', 'overview.qmd', 'log.qmd'])
      assertEquals(await readText(join(f.instance, 'wiki', name)), '');
    const layout = (await snapshot(f.instance))
      .map(entry => entry.path)
      .filter(path => !path.startsWith('.git/'));
    assertEquals(
      layout.sort(),
      [
        '',
        '.git',
        '.gitignore',
        'AGENTS.md',
        'raw',
        'raw/assets',
        'raw/files',
        'raw/notes',
        'raw/web',
        'text',
        'wiki',
        'wiki/index.qmd',
        'wiki/log.qmd',
        'wiki/overview.qmd',
      ].sort(),
    );
    const path = await f.file('evidence.txt');
    report(await f.admit([path]));
    const git = (...args: string[]) =>
      output(
        spawn('git', ['-C', f.instance, ...args], {
          env: {...process.env, ...f.env},
          stdio: ['ignore', 'pipe', 'pipe'],
        }),
      );
    const status = await git('status', '--porcelain', '--ignored');
    assertEquals(status.code, 0, status.stderr);
    assertMatch(status.stdout, /!! raw\//);
    await mkdir(join(f.instance, 'text/source'), {recursive: true});
    const temporary = 'text/source/.r1.qmd.deadbeef.wiki-consistency-tmp';
    await writeFile(join(f.instance, temporary), 'abandoned partial');
    await writeFile(join(f.instance, 'text/source/r1.qmd'), 'retained source');
    assertEquals((await git('check-ignore', temporary)).code, 0);
    assertEquals((await git('check-ignore', 'text/source/r1.qmd')).code, 1);
    assertEquals(
      (await git('check-ignore', 'wiki/.example.wiki-consistency-tmp')).code,
      1,
    );
    assertEquals((await git('ls-files', 'raw')).stdout, '');
    assert((await git('rev-parse', '--verify', 'HEAD')).code !== 0);
  });
});

void test('raw import US5: unnamed commands use the work wiki under llm-wiki', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('work-wiki.txt');
    const [item] = report(await f.admit([path]));
    assertEquals(item.outcome, 'admitted');
    const verified = await f.run('verify');
    assertEquals(verified.code, 0, verified.stderr);
    assertEquals(JSON.parse(verified.stdout), {count: 1, invalid: []});

    const selection = join(
      f.env.XDG_STATE_HOME,
      'verbose-broccoli/llm-wiki/work/selections/test.jsonl',
    );
    const paths = new Set((await snapshot(f.home)).map(entry => entry.path));
    assert(
      [f.instance, f.raw, selection, revisionPath(f, item)].every(path =>
        paths.has(relative(f.home, path)),
      ),
    );
    for (const root of [f.env.XDG_DATA_HOME, f.env.XDG_STATE_HOME]) {
      assertEquals(
        Array.from(
          readDir(join(root, 'verbose-broccoli')),
          entry => entry.name,
        ),
        ['llm-wiki'],
      );
    }
  });
});

void test('raw import US5: repeated init preserves every byte and modification time', async () => {
  await fixture(async f => {
    await f.init();
    await writeFile(join(f.instance, 'AGENTS.md'), 'existing schema\n');
    for (const name of ['index', 'overview', 'log'])
      await writeFile(
        join(f.instance, `wiki/${name}.qmd`),
        `existing ${name}\n`,
      );
    await writeFile(join(f.instance, 'wiki/_metadata.yml'), 'lang: en\n');
    await writeFile(join(f.instance, 'text/extraction.qmd'), 'retained text\n');
    await writeFile(join(f.instance, '.gitignore'), '/raw/\n/custom/\n');
    report(await f.admit([await f.file('rerun.txt')]));
    const before = await snapshot(f.instance, true);
    assertEquals(await f.init(), {created: []});
    assertEquals(await snapshot(f.instance, true), before);
  });
});

for (const layout of ['legacy', 'mixed']) {
  for (const name of ['index', 'overview', 'log']) {
    void test(`raw import US5: init refuses ${layout} ${name}.md before any write`, async () => {
      await fixture(async f => {
        await mkdir(join(f.instance, 'wiki'), {recursive: true});
        await mkdir(join(f.raw, 'files'), {recursive: true});
        await writeFile(join(f.raw, 'files/preserved.txt'), 'raw bytes\n');
        await writeFile(join(f.instance, 'AGENTS.md'), 'legacy schema\n');
        await writeFile(
          join(f.instance, 'wiki', `${name}.md`),
          'legacy body\n',
        );
        if (layout === 'mixed')
          for (const special of ['index', 'overview', 'log'])
            await writeFile(
              join(f.instance, 'wiki', `${special}.qmd`),
              `existing ${special}\n`,
            );
        const before = await snapshot(f.home, true);
        const result = await f.run('init');
        assertEquals(result.code, 2, result.stderr);
        assertEquals(result.stdout, '');
        assertMatch(result.stderr, /migration/i);
        assert(result.stderr.includes(`${name}.md`));
        assertEquals(await snapshot(f.home, true), before);
      });
    });
  }
}

void test('raw import US5: named Wiki and all four kinds use their own roots', async () => {
  await fixture(async f => {
    const initialized = await f.run('--wiki', 'selected', 'init');
    assertEquals(initialized.code, 0, initialized.stderr);
    assertEquals(initialized.stderr, '');
    f.instance = join(
      f.env.XDG_DATA_HOME,
      'verbose-broccoli/llm-wiki/selected',
    );
    f.raw = join(f.instance, 'raw');
    const items = await Promise.all(
      ['web', 'files', 'notes', 'assets'].map(async kind => ({
        path: await f.file(`${kind}.txt`),
        kind,
      })),
    );
    const selection = await f.selection(items);
    const admitted = report(
      await f.run('admit', '--wiki', 'selected', '--selection', selection),
    );
    for (let i = 0; i < items.length; i++) {
      assertEquals(
        await readFile(
          join(
            revisionPath(f, admitted[i], items[i].kind),
            'data',
            basename(items[i].path),
          ),
        ),
        await readFile(items[i].path),
      );
    }
    assertEquals(
      JSON.parse((await f.run('verify', '--wiki', 'selected')).stdout),
      {count: 4, invalid: []},
    );
    assertEquals(Array.from(readDir(f.staging('selected'))), []);
    assertEquals(
      Array.from(readDir(dirname(f.instance)), entry => entry.name),
      ['selected'],
    );
  });
});

void test('raw import US1-US3: a synthetic ChatGPT export gives chat and work two revisions', async () => {
  await fixture(async f => {
    const path = join(f.home, 'Documents/chatgpt/chatgpt-export.zip');
    await f.fileAt(path, '');
    const conversation = (id: string, question: string, answer: string) => ({
      conversation_id: id,
      title: `Synthetic conversation ${id}`,
      mapping: {
        [`${id}-user`]: {
          message: {
            author: {role: 'user'},
            content: {content_type: 'text', parts: [question]},
          },
        },
        [`${id}-assistant`]: {
          message: {
            author: {role: 'assistant'},
            content: {content_type: 'text', parts: [answer]},
          },
        },
      },
    });
    const python = (...args: string[]) =>
      output(
        spawn('python3', args, {
          cwd: f.home,
          env: {...process.env, ...f.env},
          stdio: ['ignore', 'pipe', 'pipe'],
        }),
      );
    const saveExport = async (conversations: unknown[]) => {
      const result = await python(
        '-c',
        `
import sys, zipfile

path, conversations = sys.argv[1:]
with zipfile.ZipFile(path, "w") as archive:
    archive.writestr("conversations.json", conversations)
    archive.writestr("chat.html", "<!doctype html><title>Synthetic export</title>")
    archive.writestr("user.json", '{"id":"synthetic-user"}')
`,
        path,
        JSON.stringify(conversations),
      );
      assertEquals(result.code, 0, result.stderr);
      const bytes = await readFile(path);
      f.originals.set(path, {
        bytes,
        mtime: (await stat(path)).mtime?.getTime(),
      });
      return bytes;
    };
    const zipTest = (candidate: string) =>
      python('-m', 'zipfile', '-t', candidate);
    const firstBytes = await saveExport([
      conversation(
        'synthetic-conversation-1',
        'Synthetic first question.',
        'Synthetic first answer.',
      ),
    ]);
    const firstZipTest = await zipTest(path);
    assertEquals(firstZipTest.code, 0, firstZipTest.stderr);
    const truncatedPath = join(
      f.home,
      'Documents/chatgpt/chatgpt-export-truncated.zip',
    );
    await writeFile(
      truncatedPath,
      firstBytes.slice(0, Math.floor(firstBytes.length / 2)),
    );
    const truncatedZipTest = await zipTest(truncatedPath);
    assert(truncatedZipTest.code !== 0);

    for (const wiki of ['chat', 'work']) {
      const initialized = await f.run('init', '--wiki', wiki);
      assertEquals(initialized.code, 0, initialized.stderr);
      assertEquals(initialized.stderr, '');
    }
    const selection = await f.selection([{path, kind: 'files'}]);
    const admit = async (wiki: 'chat' | 'work') =>
      report(await f.run('admit', '--wiki', wiki, '--selection', selection));
    const [chatFirst] = await admit('chat');
    const [workFirst] = await admit('work');
    assertEquals(chatFirst.outcome, 'admitted');
    assertEquals(workFirst.outcome, 'admitted');
    assert(chatFirst.source_id !== workFirst.source_id);

    const secondBytes = await saveExport([
      conversation(
        'synthetic-conversation-1',
        'Synthetic first question.',
        'Synthetic first answer.',
      ),
      conversation(
        'synthetic-conversation-2',
        'Synthetic follow-up question.',
        'Synthetic follow-up answer.',
      ),
    ]);
    const secondZipTest = await zipTest(path);
    assertEquals(secondZipTest.code, 0, secondZipTest.stderr);
    const [chatSecond] = await admit('chat');
    const [workSecond] = await admit('work');
    for (const [first, second] of [
      [chatFirst, chatSecond],
      [workFirst, workSecond],
    ] as const) {
      assertEquals(second.outcome, 'admitted');
      assertEquals(second.source_id, first.source_id);
    }

    const unchangedZipTest = await zipTest(path);
    assertEquals(unchangedZipTest.code, 0, unchangedZipTest.stderr);
    const [chatUnchanged] = await admit('chat');
    const [workUnchanged] = await admit('work');
    assertEquals(chatUnchanged, {...chatSecond, outcome: 'already_admitted'});
    assertEquals(workUnchanged, {...workSecond, outcome: 'already_admitted'});

    for (const [wiki, first, second] of [
      ['chat', chatFirst, chatSecond],
      ['work', workFirst, workSecond],
    ] as const) {
      f.raw = join(
        f.env.XDG_DATA_HOME,
        'verbose-broccoli/llm-wiki',
        wiki,
        'raw',
      );
      const source = dirname(revisionPath(f, first));
      assertEquals(
        Array.from(readDir(source), entry => entry.name).sort(),
        [first.revision, second.revision].sort(),
      );
      for (const [item, bytes] of [
        [first, firstBytes],
        [second, secondBytes],
      ] as const) {
        assertEquals(
          await readFile(join(revisionPath(f, item), 'data', basename(path))),
          bytes,
        );
      }
      const verified = await f.run('verify', '--wiki', wiki);
      assertEquals(verified.code, 0, verified.stderr);
      assertEquals(JSON.parse(verified.stdout), {count: 2, invalid: []});
    }
    assertEquals(await readFile(path), secondBytes);
  });
});

for (const value of ['unset', '', 'relative']) {
  void test(`raw import US5: ${value || 'empty'} XDG values use HOME defaults`, async () => {
    await fixture(async f => {
      for (const name of ['DATA', 'STATE', 'CACHE', 'CONFIG']) {
        if (value === 'unset') delete f.env[`XDG_${name}_HOME`];
        else f.env[`XDG_${name}_HOME`] = value;
      }
      // Clear the inherited roots for the unset case too.
      const inherited = {...process.env, ...f.env};
      if (value === 'unset')
        for (const name of ['DATA', 'STATE', 'CACHE', 'CONFIG'])
          delete inherited[`XDG_${name}_HOME`];
      const command = (...args: string[]) =>
        output(
          spawn(
            'uv',
            ['run', '--locked', '--offline', '--script', script, ...args],
            {
              cwd: f.home,
              env: inherited,
              stdio: ['ignore', 'pipe', 'pipe'],
            },
          ),
        );
      assertEquals((await command('init')).code, 0);
      f.instance = join(f.home, '.local/share/verbose-broccoli/llm-wiki/work');
      f.raw = join(f.instance, 'raw');
      await stat(join(f.instance, 'AGENTS.md'));
      const path = await f.file('default-roots.txt');
      const selection = join(f.home, 'selection.jsonl');
      await writeFile(selection, `${JSON.stringify({path, kind: 'files'})}\n`);
      report(await command('admit', '--selection', selection));
      assertEquals(
        Array.from(
          readDir(join(f.home, '.cache/verbose-broccoli/raw-import/work')),
        ),
        [],
      );
      const config = join(f.home, '.config/verbose-broccoli/config.toml');
      await mkdir(dirname(config), {recursive: true});
      await writeFile(
        config,
        `[wiki.raw_import]\nexclude = [${JSON.stringify(dirname(path))}]\n`,
      );
      assertEquals(
        report(await command('admit', '--selection', selection), 1)[0].outcome,
        'refused',
      );
      assertEquals(JSON.parse((await command('verify')).stdout), {
        count: 1,
        invalid: [],
      });
      await f.originalsUnchanged();
    });
  });
}

void test('raw import: invalid arguments and Wiki names write nothing', async () => {
  await fixture(async f => {
    for (const args of [
      [],
      ['unknown'],
      ['admit'],
      ['verify', '--unknown'],
      ...['', '.', '..', '../outside', 'a/b'].map(name => [
        'init',
        '--wiki',
        name,
      ]),
    ]) {
      const before = await snapshot(f.home, true);
      const result = await f.run(...args);
      assertEquals(result.code, 2);
      assertEquals(result.stdout, '');
      assert(result.stderr);
      assertEquals(await snapshot(f.home, true), before);
    }
  });
});

for (const wiki of ['default', 'chat', 'code', 'work']) {
  void test(`raw import: ${wiki} works under llm-wiki without a legacy link`, async () => {
    await fixture(async f => {
      f.instance = join(f.env.XDG_DATA_HOME, 'verbose-broccoli/llm-wiki', wiki);
      f.raw = join(f.instance, 'raw');
      const initialized = await f.run('--wiki', wiki, 'init');
      assertEquals(initialized.code, 0, initialized.stderr);
      await stat(join(f.instance, '.git'));
      const original = await f.file('evidence.txt');
      const selection = await f.selection([{path: original, kind: 'files'}]);
      const [item] = report(
        await f.run('admit', '--wiki', wiki, '--selection', selection),
      );
      assertEquals(
        await readFile(join(revisionPath(f, item), 'data/evidence.txt')),
        await readFile(original),
      );
      const before = await snapshot(f.instance, true);
      const verified = await f.run('verify', '--wiki', wiki);
      assertEquals(verified.code, 0, verified.stderr);
      assertEquals(JSON.parse(verified.stdout), {count: 1, invalid: []});
      assertEquals(JSON.parse((await f.run('init', '--wiki', wiki)).stdout), {
        created: [],
      });
      assertEquals(await snapshot(f.instance, true), before);
      assertEquals(
        Array.from(
          readDir(join(f.env.XDG_DATA_HOME, 'verbose-broccoli')),
          entry => entry.name,
        ),
        ['llm-wiki'],
      );
    });
  });
}
