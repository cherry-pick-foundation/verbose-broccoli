import {assert, assertEquals, assertMatch} from '@std/assert';
import {copy, walk} from '@std/fs';
import {basename, dirname, fromFileUrl, join, relative} from '@std/path';

const script = fromFileUrl(
  new URL(
    '../plugins/work/skills/wiki-raw-import/scripts/raw_import.py',
    import.meta.url,
  ),
);
const decoder = new TextDecoder();
const encoder = new TextEncoder();

async function output(command: Deno.Command) {
  const result = await command.output();
  return {
    code: result.code,
    stdout: decoder.decode(result.stdout),
    stderr: decoder.decode(result.stderr),
  };
}

async function uvLocation(...args: string[]) {
  const result = await output(new Deno.Command('uv', {args}));
  assertEquals(result.code, 0, result.stderr);
  return result.stdout.trim();
}

// uv's prepared interpreter and dependency cache are tooling, not Wiki roots.
const uvCache = await uvLocation('cache', 'dir');
const python = await uvLocation('python', 'find', '3.14');

async function snapshot(root: string, times = false) {
  const entries = [];
  for await (const entry of walk(root, {
    includeDirs: true,
    followSymlinks: false,
  })) {
    const stat = await Deno.lstat(entry.path);
    entries.push({
      path: relative(root, entry.path),
      mode: stat.mode,
      bytes: stat.isFile ? Array.from(await Deno.readFile(entry.path)) : null,
      ...(times ? {mtime: stat.mtime?.getTime()} : {}),
    });
  }
  return entries.sort((a, b) => a.path.localeCompare(b.path));
}

async function fixture(run: (f: Fixture) => Promise<void>) {
  const home = await Deno.makeTempDir({prefix: 'wiki-raw-import-'});
  const f = new Fixture(home);
  try {
    await run(f);
  } finally {
    // Published bags are deliberately read-only; only the fixture owner removes them.
    for await (const entry of walk(home, {followSymlinks: false})) {
      if (!entry.isSymlink)
        await Deno.chmod(entry.path, entry.isDirectory ? 0o700 : 0o600);
    }
    await f.originalsUnchanged();
    await Deno.remove(home, {recursive: true});
  }
}

class Fixture {
  env: Record<string, string>;
  instance: string;
  raw: string;
  originals = new Map<string, {bytes: Uint8Array; mtime: number | undefined}>();

  constructor(readonly home: string) {
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
      'verbose-broccoli/vaults/work',
    );
    this.raw = join(this.instance, 'raw');
  }

  command(...args: string[]) {
    return new Deno.Command('uv', {
      args: [
        'run',
        '--quiet',
        '--locked',
        '--offline',
        '--script',
        script,
        ...args,
      ],
      cwd: this.home,
      env: this.env,
      stdout: 'piped',
      stderr: 'piped',
      signal: AbortSignal.timeout(30_000),
    });
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
    await Deno.mkdir(dirname(path), {recursive: true});
    await Deno.writeTextFile(path, text);
    this.originals.set(path, {
      bytes: encoder.encode(text),
      mtime: (await Deno.stat(path)).mtime?.getTime(),
    });
    return path;
  }

  async originalsUnchanged() {
    for (const [path, before] of this.originals) {
      const stat = await Deno.stat(path);
      assertEquals(stat.mtime?.getTime(), before.mtime, path);
      if ((stat.mode ?? 0) & 0o400)
        assertEquals(await Deno.readFile(path), before.bytes, path);
    }
  }

  async selection(items: unknown[]) {
    const path = join(
      this.env.XDG_STATE_HOME,
      'verbose-broccoli/vaults/work/selections/test.jsonl',
    );
    await Deno.mkdir(dirname(path), {recursive: true});
    await Deno.writeTextFile(
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

Deno.test('raw import: locked offline help and missing-instance errors', async () => {
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

Deno.test('raw import US1: one immutable bag preserves payload, digest, timestamps and provenance', async () => {
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
    assertEquals(await Deno.readFile(payload), await Deno.readFile(path));
    assertEquals(
      (await Deno.stat(payload)).mtime,
      (await Deno.stat(path)).mtime,
    );
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
      await Deno.readTextFile(join(revision, 'manifest-sha256.txt')),
      `${await digest(await Deno.readFile(path))}  data/${basename(path)}\n`,
    );
    const info = Object.fromEntries(
      (await Deno.readTextFile(join(revision, 'bag-info.txt')))
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
      (await Deno.stat(path)).mtime?.getTime(),
    );
    assertMatch(info['Bagging-Date'], /^\d{4}-\d{2}-\d{2}$/);
    assertEquals(info['Payload-Oxum'], `${(await Deno.stat(path)).size}.1`);
    const before = await snapshot(f.home, true);
    const verified = await f.run('verify');
    assertEquals(verified.code, 0, verified.stderr);
    assertEquals(verified.stderr, '');
    assertEquals(JSON.parse(verified.stdout), {count: 1, invalid: []});
    assertEquals(await snapshot(f.home, true), before);
  });
});

for (const damaged of ['payload', 'bag-info.txt']) {
  Deno.test(`raw import US1: verify detects changed ${damaged} without writing`, async () => {
    await fixture(async f => {
      await f.init();
      const path = await f.file('paper.txt');
      const [item] = report(await f.admit([path]));
      const revision = revisionPath(f, item);
      const target = join(
        revision,
        damaged === 'payload' ? 'data/paper.txt' : damaged,
      );
      await Deno.chmod(target, 0o600);
      const bytes = await Deno.readFile(target);
      bytes[bytes.length - 2] ^= 1;
      await Deno.writeFile(target, bytes);
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

Deno.test('raw import US1: an unreadable original fails without adding evidence', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('unreadable.txt');
    await Deno.chmod(path, 0);
    const before = await snapshot(f.raw);
    const [item] = report(await f.admit([path]), 1);
    assertEquals(item.outcome, 'failed');
    assertEquals(await snapshot(f.raw), before);
    await Deno.chmod(path, 0o600);
    await f.originalsUnchanged();
  });
});

Deno.test('raw import US1: unrepresentable BagIt provenance fails before publication', async () => {
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

Deno.test('raw import US2: unchanged rerun adds nothing; changes and reversions retain every revision', async () => {
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
      Deno.readDirSync(dirname(revisionPath(f, first))),
      entry => entry.name,
    ).sort();
    assertEquals(revisions, [first.revision, second.revision, third.revision]);
    for (const [item, text] of [
      [first, 'first'],
      [second, 'second'],
      [third, 'first'],
    ] as const) {
      assertEquals(
        await Deno.readTextFile(
          join(revisionPath(f, item), 'data/revisions.txt'),
        ),
        text,
      );
    }
    const verified = await f.run('verify');
    assertEquals(verified.code, 0, verified.stderr);
    assertEquals(JSON.parse(verified.stdout), {count: 3, invalid: []});
  });
});

Deno.test('raw import US2: a new revision must sort after the latest revision', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('revision-order.txt', 'first');
    const [first] = report(await f.admit([path]));
    const source = dirname(revisionPath(f, first));
    const latest = join(source, '99991231T000000000000Z');
    await Deno.chmod(source, 0o700);
    await Deno.rename(revisionPath(f, first), latest);
    await Deno.chmod(source, 0o555);
    await f.file('revision-order.txt', 'changed');
    const originalBytes = await Deno.readFile(path);
    const originalMtime = (await Deno.stat(path)).mtime?.getTime();
    const before = await snapshot(f.raw);
    const [item] = report(await f.admit([path]), 1);
    assertEquals(item.outcome, 'failed');
    assertEquals(
      item.reason,
      'new revision would not sort after the latest one',
    );
    assertEquals(await snapshot(f.raw), before);
    assertEquals(await Deno.readFile(path), originalBytes);
    assertEquals((await Deno.stat(path)).mtime?.getTime(), originalMtime);
  });
});

Deno.test('raw import US2: equal bytes at different paths have distinct sources', async () => {
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

Deno.test('raw import US2: two source records for one original fail the item', async () => {
  await fixture(async f => {
    await f.init();
    const first = await f.file('first.txt');
    const second = await f.file('second.txt');
    const [, item] = report(await f.admit([first, second]));
    const revision = revisionPath(f, item);
    const infoPath = join(revision, 'bag-info.txt');
    const oldInfo = await Deno.readFile(infoPath);
    const newInfo = encoder.encode(
      decoder.decode(oldInfo).replace(second, first),
    );
    const tagPath = join(revision, 'tagmanifest-sha256.txt');
    await Deno.chmod(infoPath, 0o600);
    await Deno.writeFile(infoPath, newInfo);
    await Deno.chmod(tagPath, 0o600);
    await Deno.writeTextFile(
      tagPath,
      (await Deno.readTextFile(tagPath)).replace(
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

Deno.test('raw import US3: only listed files are admitted without user exclusions', async () => {
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

Deno.test('raw import US3: excluded roots and resolved aliases are refused', async () => {
  await fixture(async f => {
    await f.init();
    const excluded = await f.file('private/excluded.txt');
    const config = join(f.env.XDG_CONFIG_HOME, 'verbose-broccoli/config.toml');
    await Deno.mkdir(dirname(config), {recursive: true});
    await Deno.writeTextFile(
      config,
      `[wiki.raw_import]\nexclude = [${JSON.stringify(dirname(excluded))}]\n`,
    );
    const alias = join(f.home, 'alias');
    await Deno.symlink(dirname(excluded), alias);
    const link = join(f.home, 'excluded-link');
    await Deno.symlink(excluded, link);
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

Deno.test('raw import US3: excluded paths stay refused through an escaping directory symlink', async () => {
  await fixture(async f => {
    await f.init();
    const excluded = join(f.home, 'excluded');
    const outside = join(f.home, 'outside');
    const path = await f.fileAt(join(outside, 'escape.txt'));
    await Deno.mkdir(excluded, {recursive: true});
    const alias = join(excluded, 'linkdir');
    await Deno.symlink(outside, alias);
    const listed = join(alias, basename(path));
    const config = join(f.env.XDG_CONFIG_HOME, 'verbose-broccoli/config.toml');
    await Deno.mkdir(dirname(config), {recursive: true});
    await Deno.writeTextFile(
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

Deno.test('raw import US3: symlinks, folders, missing files, FIFOs and invalid UTF-8 are refused', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('original.txt');
    const originalInfo = async (create: boolean) => {
      const result = await output(
        new Deno.Command(python, {
          args: [
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
          env: f.env,
        }),
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
      const symlink = join(f.home, 'symlink');
      await Deno.symlink(path, symlink);
      const fifo = join(f.home, 'pipe');
      const prepared = await output(
        new Deno.Command(python, {
          args: ['-c', 'import os,sys; os.mkfifo(sys.argv[1])', fifo],
          env: f.env,
        }),
      );
      assertEquals(prepared.code, 0, prepared.stderr);
      const paths = [
        symlink,
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
        new Deno.Command(python, {
          args: [
            '-c',
            'import os,sys; os.unlink(os.fsencode(sys.argv[1]) + b"/bad-" + bytes([255]))',
            f.home,
          ],
          env: f.env,
        }),
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
  Deno.test(`raw import US3: ${invalid} selection is rejected before any write`, async () => {
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
        await Deno.writeTextFile(selection, '{invalid}\n', {append: true});
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
  Deno.test(`raw import US3: malformed configuration fails closed (${config})`, async () => {
    await fixture(async f => {
      await f.init();
      const path = await f.file('valid.txt');
      const selection = await f.selection([{path, kind: 'files'}]);
      const configPath = join(
        f.env.XDG_CONFIG_HOME,
        'verbose-broccoli/config.toml',
      );
      await Deno.mkdir(dirname(configPath), {recursive: true});
      await Deno.writeTextFile(configPath, config);
      const before = await snapshot(f.home, true);
      const result = await f.run('admit', '--selection', selection);
      assertEquals(result.code, 2, result.stderr);
      assertEquals(result.stdout, '');
      assert(result.stderr);
      assertEquals(await snapshot(f.home, true), before);
    });
  });
}

Deno.test('raw import US3: an existing source cannot change kind', async () => {
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

// Unperformed checks: an original changing during copy and a full disk.
// Neither is simulated; permission failures and prepared interrupted states are real fixtures.
for (const stage of [
  'partial copy',
  'copied payload',
  'partial record',
  'complete bag',
]) {
  Deno.test(`raw import US4: recover a leftover ${stage} without publishing it`, async () => {
    await fixture(async f => {
      await f.init();
      const path = await f.file('recovery.txt');
      const [first] = report(await f.admit([path]));
      const before = await snapshot(f.raw);
      const stale = join(f.staging(), 'dead-run', 'bag');
      if (stage === 'complete bag') {
        await copy(revisionPath(f, first), stale);
        for await (const entry of walk(stale))
          await Deno.chmod(entry.path, entry.isDirectory ? 0o555 : 0o444);
      } else {
        await Deno.mkdir(stale, {recursive: true});
        await Deno.writeTextFile(
          join(stale, 'recovery.txt'),
          stage === 'partial copy' ? 'part' : 'synthetic original\n',
        );
        if (stage === 'partial record')
          await Deno.writeTextFile(
            join(stale, 'bag-info.txt'),
            'External-Identifier:',
          );
      }
      const otherWiki = join(f.staging('other'), 'active-run');
      await Deno.mkdir(otherWiki, {recursive: true});
      await Deno.writeTextFile(join(otherWiki, 'keep'), 'another instance');
      const otherBefore = await snapshot(otherWiki, true);
      const [again] = report(await f.admit([path]));
      assertEquals(again.outcome, 'already_admitted');
      assertEquals(await snapshot(f.raw), before);
      assertEquals(Array.from(Deno.readDirSync(f.staging())), []);
      assertEquals(await snapshot(otherWiki, true), otherBefore);
      assertEquals((await f.run('verify')).code, 0);
    });
  });
}

Deno.test('raw import US4: a publication failure keeps other items and can be retried', async () => {
  await fixture(async f => {
    await f.init();
    const blocked = await f.file('blocked.txt', 'first');
    const [first] = report(await f.admit([blocked]));
    const firstRevision = revisionPath(f, first);
    const before = await snapshot(firstRevision);
    await f.file('blocked.txt', 'second');
    await Deno.chmod(dirname(firstRevision), 0o555);
    const good = await f.file('good.txt');
    const items = report(await f.admit([blocked, good]), 1);
    assertEquals(
      items.map(item => item.outcome),
      ['failed', 'admitted'],
    );
    assertEquals(await snapshot(firstRevision), before);
    assertEquals(Array.from(Deno.readDirSync(f.staging())), []);
    assertEquals(JSON.parse((await f.run('verify')).stdout), {
      count: 2,
      invalid: [],
    });
    await Deno.chmod(dirname(firstRevision), 0o700);
    const retried = report(await f.admit([blocked, good]));
    assertEquals(
      retried.map(item => item.outcome),
      ['admitted', 'already_admitted'],
    );
    assertEquals(JSON.parse((await f.run('verify')).stdout), {
      count: 3,
      invalid: [],
    });
    assertEquals(Array.from(Deno.readDirSync(f.staging())), []);
  });
});

Deno.test('raw import US4: concurrent admission writes nothing and SIGKILL releases the real run lock', async () => {
  await fixture(async f => {
    await f.init();
    const small = await f.file('finished.txt');
    report(await f.admit([small]));
    const large = await f.file('large.txt', 'x'.repeat(32 * 1024 * 1024));
    const selection = await f.selection([
      {path: small, kind: 'files'},
      {path: large, kind: 'files'},
    ]);
    const child = f.command('admit', '--selection', selection).spawn();
    let exited = false;
    const finished = child.output().finally(() => {
      exited = true;
    });
    let pid: number | undefined;
    try {
      const lock = join(
        f.env.XDG_STATE_HOME,
        'verbose-broccoli/vaults/work/raw-import.lock',
      );
      // Python observes the Linux lock owner because Deno restricts direct /proc reads.
      const paused = await output(
        new Deno.Command(python, {
          env: f.env,
          args: [
            '-c',
            `
import os, signal, sys, time
from pathlib import Path
staging, lock, script, selection = sys.argv[1:]
deadline = time.monotonic() + 10
while time.monotonic() < deadline:
    if Path(lock).exists() and any(Path(staging).iterdir()):
        inode = str(Path(lock).stat().st_ino)
        for line in Path('/proc/locks').read_text().splitlines():
            fields = line.split()
            if fields[1] != 'FLOCK' or fields[5].split(':')[-1] != inode:
                continue
            pid = int(fields[4])
            command = Path(f'/proc/{pid}/cmdline').read_text()
            assert script in command and selection in command
            os.kill(pid, signal.SIGSTOP)
            print(pid, flush=True)
            sys.exit(0)
    time.sleep(.001)
sys.exit('timed out observing the import lock')
`,
            f.staging(),
            lock,
            script,
            selection,
          ],
        }),
      );
      assertEquals(paused.code, 0, paused.stderr);
      pid = Number(paused.stdout.trim());
      const roots = [f.raw, f.staging(), f.env.XDG_STATE_HOME];
      const before = await Promise.all(roots.map(root => snapshot(root, true)));
      const second = await f.run('admit', '--selection', selection);
      assertEquals(second.code, 2, second.stderr);
      assertEquals(second.stdout, '');
      assertMatch(second.stderr, /lock/i);
      assertEquals(
        await Promise.all(roots.map(root => snapshot(root, true))),
        before,
      );
    } finally {
      if (pid !== undefined) Deno.kill(pid, 'SIGKILL');
      else if (!exited) child.kill('SIGTERM');
      await finished;
    }
    assertEquals((await f.run('verify')).code, 0);
    const items = report(await f.run('admit', '--selection', selection));
    assertEquals(items[0].outcome, 'already_admitted');
    assert(['admitted', 'already_admitted'].includes(items[1].outcome));
    assertEquals(Array.from(Deno.readDirSync(f.staging())), []);
    const verified = await f.run('verify');
    assertEquals(verified.code, 0, verified.stderr);
    assertEquals(JSON.parse(verified.stdout), {count: 2, invalid: []});
  });
});

Deno.test('raw import US5: init copies the schema and creates an uncommitted Wiki with raw ignored', async () => {
  await fixture(async f => {
    const initialized = await f.init();
    assert(initialized.created.length > 0);
    for (const path of initialized.created) {
      assert(path.startsWith(f.home));
      await Deno.stat(path);
    }
    assertEquals(
      await Deno.readFile(join(f.instance, 'AGENTS.md')),
      await Deno.readFile(join(dirname(script), '../assets/AGENTS.md')),
    );
    for (const name of ['index.md', 'overview.md', 'log.md'])
      assertEquals(await Deno.readTextFile(join(f.instance, 'wiki', name)), '');
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
        'wiki',
        'wiki/index.md',
        'wiki/log.md',
        'wiki/overview.md',
      ].sort(),
    );
    const path = await f.file('evidence.txt');
    report(await f.admit([path]));
    const git = (...args: string[]) =>
      output(
        new Deno.Command('git', {
          args: ['-C', f.instance, ...args],
          env: f.env,
        }),
      );
    const status = await git('status', '--porcelain', '--ignored');
    assertEquals(status.code, 0, status.stderr);
    assertMatch(status.stdout, /!! raw\//);
    assertEquals((await git('ls-files', 'raw')).stdout, '');
    assert((await git('rev-parse', '--verify', 'HEAD')).code !== 0);
  });
});

Deno.test('raw import US5: unnamed commands use the work vault under vaults', async () => {
  await fixture(async f => {
    await f.init();
    const path = await f.file('work-vault.txt');
    const [item] = report(await f.admit([path]));
    assertEquals(item.outcome, 'admitted');
    const verified = await f.run('verify');
    assertEquals(verified.code, 0, verified.stderr);
    assertEquals(JSON.parse(verified.stdout), {count: 1, invalid: []});

    const selection = join(
      f.env.XDG_STATE_HOME,
      'verbose-broccoli/vaults/work/selections/test.jsonl',
    );
    const lock = join(
      f.env.XDG_STATE_HOME,
      'verbose-broccoli/vaults/work/raw-import.lock',
    );
    const paths = new Set((await snapshot(f.home)).map(entry => entry.path));
    assert(
      [f.instance, f.raw, selection, lock, revisionPath(f, item)].every(path =>
        paths.has(relative(f.home, path)),
      ),
    );
    for (const root of [f.env.XDG_DATA_HOME, f.env.XDG_STATE_HOME]) {
      assertEquals(
        Array.from(
          Deno.readDirSync(join(root, 'verbose-broccoli')),
          entry => entry.name,
        ),
        ['vaults'],
      );
    }
  });
});

Deno.test('raw import US5: repeated init preserves every byte and modification time', async () => {
  await fixture(async f => {
    await f.init();
    await Deno.writeTextFile(
      join(f.instance, 'AGENTS.md'),
      'existing schema\n',
    );
    await Deno.writeTextFile(
      join(f.instance, 'wiki/index.md'),
      'existing catalog\n',
    );
    await Deno.writeTextFile(
      join(f.instance, '.gitignore'),
      '/raw/\n/custom/\n',
    );
    const before = await snapshot(f.instance, true);
    assertEquals(await f.init(), {created: []});
    assertEquals(await snapshot(f.instance, true), before);
  });
});

Deno.test('raw import US5: named Wiki and all four kinds use their own roots', async () => {
  await fixture(async f => {
    const initialized = await f.run('--wiki', 'selected', 'init');
    assertEquals(initialized.code, 0, initialized.stderr);
    assertEquals(initialized.stderr, '');
    f.instance = join(f.env.XDG_DATA_HOME, 'verbose-broccoli/vaults/selected');
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
        await Deno.readFile(
          join(
            revisionPath(f, admitted[i], items[i].kind),
            'data',
            basename(items[i].path),
          ),
        ),
        await Deno.readFile(items[i].path),
      );
    }
    assertEquals(
      JSON.parse((await f.run('verify', '--wiki', 'selected')).stdout),
      {count: 4, invalid: []},
    );
    await Deno.stat(
      join(
        f.env.XDG_STATE_HOME,
        'verbose-broccoli/vaults/selected/raw-import.lock',
      ),
    );
    assertEquals(Array.from(Deno.readDirSync(f.staging('selected'))), []);
    assertEquals(
      Array.from(Deno.readDirSync(dirname(f.instance)), entry => entry.name),
      ['selected'],
    );
  });
});

Deno.test('raw import US1-US3: a synthetic ChatGPT export gives chat and work two revisions', async () => {
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
      output(new Deno.Command('python3', {args, cwd: f.home, env: f.env}));
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
      const bytes = await Deno.readFile(path);
      f.originals.set(path, {
        bytes,
        mtime: (await Deno.stat(path)).mtime?.getTime(),
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
    await Deno.writeFile(
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
      f.raw = join(f.env.XDG_DATA_HOME, 'verbose-broccoli/vaults', wiki, 'raw');
      const source = dirname(revisionPath(f, first));
      assertEquals(
        Array.from(Deno.readDirSync(source), entry => entry.name).sort(),
        [first.revision, second.revision].sort(),
      );
      for (const [item, bytes] of [
        [first, firstBytes],
        [second, secondBytes],
      ] as const) {
        assertEquals(
          await Deno.readFile(
            join(revisionPath(f, item), 'data', basename(path)),
          ),
          bytes,
        );
      }
      const verified = await f.run('verify', '--wiki', wiki);
      assertEquals(verified.code, 0, verified.stderr);
      assertEquals(JSON.parse(verified.stdout), {count: 2, invalid: []});
    }
    assertEquals(await Deno.readFile(path), secondBytes);
  });
});

for (const value of ['unset', '', 'relative']) {
  Deno.test(`raw import US5: ${value || 'empty'} XDG values use HOME defaults`, async () => {
    await fixture(async f => {
      for (const name of ['DATA', 'STATE', 'CACHE', 'CONFIG']) {
        if (value === 'unset') delete f.env[`XDG_${name}_HOME`];
        else f.env[`XDG_${name}_HOME`] = value;
      }
      // Clear the inherited roots for the unset case too.
      const inherited = {...Deno.env.toObject(), ...f.env};
      if (value === 'unset')
        for (const name of ['DATA', 'STATE', 'CACHE', 'CONFIG'])
          delete inherited[`XDG_${name}_HOME`];
      const command = (...args: string[]) =>
        output(
          new Deno.Command('uv', {
            args: ['run', '--locked', '--offline', '--script', script, ...args],
            cwd: f.home,
            env: inherited,
            clearEnv: true,
          }),
        );
      assertEquals((await command('init')).code, 0);
      f.instance = join(f.home, '.local/share/verbose-broccoli/vaults/work');
      f.raw = join(f.instance, 'raw');
      await Deno.stat(join(f.instance, 'AGENTS.md'));
      const path = await f.file('default-roots.txt');
      const selection = join(f.home, 'selection.jsonl');
      await Deno.writeTextFile(
        selection,
        `${JSON.stringify({path, kind: 'files'})}\n`,
      );
      report(await command('admit', '--selection', selection));
      await Deno.stat(
        join(
          f.home,
          '.local/state/verbose-broccoli/vaults/work/raw-import.lock',
        ),
      );
      assertEquals(
        Array.from(
          Deno.readDirSync(
            join(f.home, '.cache/verbose-broccoli/raw-import/work'),
          ),
        ),
        [],
      );
      const config = join(f.home, '.config/verbose-broccoli/config.toml');
      await Deno.mkdir(dirname(config), {recursive: true});
      await Deno.writeTextFile(
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

Deno.test('raw import: invalid arguments and Wiki names write nothing', async () => {
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
