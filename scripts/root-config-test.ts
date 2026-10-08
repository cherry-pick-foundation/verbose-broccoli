// The repository root keeps one owner per concern (specs/042-root-config):
// the mise file owns tool versions, `setup` and the doctor checks, tool
// configs own code rules, `package.json` owns each command once and
// `turbo.json` owns the check graph. These tests read the real files, and ask
// Turborepo for the real graph, so a copy that creeps back or a stale path
// fails here.
import {spawnSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import {
  copyFile,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  writeFile,
} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {test} from 'node:test';
import {assert, assertEquals} from '@std/assert';
import {fromFileUrl, join} from '@std/path';

const root = fromFileUrl(new URL('..', import.meta.url));

function run(command: string, args: string[]) {
  const result = spawnSync(command, args, {
    cwd: root,
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  assertEquals(result.status, 0, result.stderr);
  return result.stdout;
}

// Tracked and not-ignored files, the way Turborepo and `lint:names` see the
// tree, so a new file is checked before it is committed.
function files() {
  return run('git', [
    'ls-files',
    '-z',
    '--cached',
    '--others',
    '--exclude-standard',
  ])
    .split('\0')
    .filter(file => file !== '' && existsSync(join(root, file)));
}

async function read(file: string) {
  return await readFile(join(root, file), 'utf8');
}

// The Python packages: the folders of `packages/` with a pyproject.toml.
function members() {
  return files()
    .map(file => /^packages\/([^/]+)\/pyproject\.toml$/.exec(file)?.[1])
    .filter((name): name is string => name !== undefined);
}

// A version as its own token, so "2.1" does not match inside "12.1.0".
function mentions(line: string, version: string) {
  const escaped = version.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`(?<![\\w.])${escaped}(?![\\w.])`).test(line);
}

// The files a tool or editor reads only at the root.
const rootFiles = [
  '.editorconfig',
  '.gitflow',
  '.gitignore',
  '.npmrc',
  '.python-version',
  '.shellcheckrc',
  'AGENTS.md',
  'LICENSE',
  'README.md',
  'eslint.config.js',
  'eslint.ignores.js',
  'orca.yaml',
  'package-lock.json',
  'package.json',
  'pyproject.toml',
  'tsconfig.json',
  'turbo.json',
  'uv.lock',
];

// The tools pinned in the mise file: `[tools]` entries, and the Quarto
// installer's version and checksum, which stay outside `[tools]`.
async function pins() {
  const mise = await read('.config/mise.toml');
  const tools = /^\[tools\]\n([\s\S]*?)\n\n/m.exec(mise);
  assert(tools, '.config/mise.toml has no [tools] table');
  const versions = [...tools[1].matchAll(/^"[^"]+" = "([^"]+)"$/gm)].map(
    match => match[1],
  );
  const env = [...mise.matchAll(/^(QUARTO_[A-Z0-9_]+) = "([^"]+)"$/gm)].map(
    match => match[2],
  );
  assert(versions.length > 0 && env.length === 2, 'no pins were found');
  return [...versions, ...env];
}

void test('the root holds only the files that tools and editors read there', () => {
  const found = files()
    .filter(file => !file.includes('/'))
    .sort();
  assertEquals(found, [...rootFiles].sort());
});

void test('every tool pin is written once, in the mise file', async () => {
  // The places that used to repeat a pin: Orca's setup, the hosted
  // workflows, the shell scripts, and uv's `required-version` in every
  // pyproject.toml. (`uv_build` in a package's build-system table is a
  // build-backend range, not a pin of the uv tool; research.md, D6.)
  const copies = files().filter(
    file =>
      file === 'orca.yaml' ||
      file.startsWith('.github/') ||
      /^scripts\/[^/]+\.sh$/.test(file) ||
      file.endsWith('pyproject.toml'),
  );
  for (const version of await pins()) {
    for (const file of copies) {
      const lines = (await read(file))
        .split('\n')
        .filter(
          line =>
            (!file.endsWith('pyproject.toml') ||
              line.includes('required-version')) &&
            mentions(line, version),
        );
      assertEquals(lines, [], `${file} repeats the pin ${version}`);
    }
  }
  for (const file of copies.filter(file => file.endsWith('pyproject.toml')))
    assert(
      !(await read(file)).includes('required-version'),
      `${file} sets a uv required-version`,
    );
});

void test('orca.yaml and the hosted checks call the mise setup task', async () => {
  for (const file of ['orca.yaml', '.github/workflows/check.yml']) {
    const text = await read(file);
    assert(text.includes('mise run setup'), `${file} does not run setup`);
    for (const step of ['mise install', 'uv sync', 'npm ci', 'git flow']) {
      assert(!text.includes(step), `${file} repeats a setup step: ${step}`);
    }
  }
  const mise = await read('.config/mise.toml');
  assertEquals(mise.match(/^\[tasks\.setup\]$/gm)?.length, 1);
  for (const check of mise.split('[doctor.checks.').slice(1)) {
    const [, run] = /^run = '(.*)'$/m.exec(check) ?? [];
    const [, hint] = /^hint = "(.*)"$/m.exec(check) ?? [];
    if (/^(uv sync|npm ls|git flow)/.test(run ?? ''))
      assert(
        hint?.includes('mise run setup'),
        `hint of ${check.split(']')[0]}`,
      );
  }
});

void test('Python setup and the documentation runner read the root runtime pin', async () => {
  for (const file of [
    '.config/mise.toml',
    '.github/workflows/docs-check.yml',
  ]) {
    const text = await read(file);
    assert(text.includes('uv python install --no-bin'), file);
    assert(text.includes('$(cat .python-version)'), file);
    assert(!text.includes('cat packages/'), file);
  }
});

void test('documentation references installs its locked host tools', async () => {
  const text = await read('.github/workflows/docs-check.yml');
  const install = text.match(/^\s*mise install --locked (.+)$/m);
  assert(install, 'documentation references has no locked tool installation');
  assertEquals(install[1].split(/\s+/).sort(), [
    'aqua:astral-sh/uv',
    'aqua:lycheeverse/lychee',
  ]);
});

void test('ruff, commitizen and prettier configs live in their owners', async () => {
  const pyproject = await read('pyproject.toml');
  assert(/^\[tool\.ruff\]$/m.test(pyproject));
  assert(/^\[tool\.commitizen\]$/m.test(pyproject));
  assert(pyproject.includes('src = ["packages/*/src"]'));
  const packageJson = JSON.parse(await read('package.json')) as {
    prettier?: unknown;
  };
  assert(packageJson.prettier !== undefined);
  // Every package's Ruff config extends a file that exists and holds the rules.
  for (const file of files().filter(f =>
    /^packages\/[^/]+\/pyproject\.toml$/.test(f),
  )) {
    const [, extend] = /^extend = "([^"]+)"$/m.exec(await read(file)) ?? [];
    assert(extend, `${file} has no Ruff extend`);
    const target = join(root, file, '..', extend);
    assert(existsSync(target), `${file} extends a missing file: ${extend}`);
    assert((await readFile(target, 'utf8')).includes('[tool.ruff]'), file);
  }
});

void test('each Python package has its own test and check tasks that run package.json scripts', async () => {
  const turbo = JSON.parse(await read('turbo.json')) as {
    tasks: Record<string, {command?: string[]; dependsOn?: string[]}>;
  };
  const scripts = (
    JSON.parse(await read('package.json')) as {scripts: Record<string, string>}
  ).scripts;
  assert(members().length > 0);
  for (const name of members()) {
    assertEquals(turbo.tasks[`${name}#test`]?.command, [
      'npm',
      '--prefix',
      '../..',
      'run',
      `test:${name}`,
    ]);
    assert(scripts[`test:${name}`], `package.json has no test:${name}`);
    assert(turbo.tasks[`${name}#check`]?.dependsOn?.includes(`${name}#test`));
  }
  // No Python test command is written in turbo.json, and the root Python
  // project has no test umbrella.
  for (const [id, task] of Object.entries(turbo.tasks)) {
    const command = (task.command ?? []).join(' ');
    assert(!/pytest|\buv\b/.test(command), `${id} repeats a command`);
  }
  assertEquals(turbo.tasks['verbose-broccoli-python#test'], undefined);
  const packageJson = JSON.parse(await read('package.json')) as {
    workspaces: string[];
  };
  assert(!packageJson.workspaces.includes('tools/none'));
});

void test('Turborepo plans each package test and check, and the root check depends on them', () => {
  const plan = JSON.parse(
    run('npm', [
      'run',
      '--silent',
      'turborepo',
      '--',
      'run',
      'check',
      '--dry=json',
    ]),
  ) as {tasks: {taskId: string; dependencies: string[]}[]};
  const tasks = new Map(plan.tasks.map(task => [task.taskId, task]));
  assert(members().length > 0);
  for (const name of members()) {
    assertEquals(tasks.get(`${name}#check`)?.dependencies, [`${name}#test`]);
    assert(tasks.has(`${name}#test`));
  }
  assertEquals(tasks.has('verbose-broccoli-python#test'), false);
  const python = tasks.get('verbose-broccoli-python#check');
  assertEquals(
    [...(python?.dependencies ?? [])].sort(),
    members()
      .map(name => `${name}#check`)
      .sort(),
  );
  assert(tasks.get('//#check')?.dependencies.includes('//#test'));
  assert(
    tasks
      .get('//#check')
      ?.dependencies.includes('verbose-broccoli-python#check'),
  );
});

// `mise run` installs the tools of every config it loads, the user's global
// ones included, before a task starts, unless the project turns that off. A
// fake global config with a tool that is not installed shows it.
void test("mise setup does not install the user's global tools", async () => {
  const dir = await mkdtemp(join(tmpdir(), 'mise-setup-'));
  try {
    await mkdir(join(dir, 'project/.config'), {recursive: true});
    await copyFile(
      join(root, '.config/mise.toml'),
      join(dir, 'project/.config/mise.toml'),
    );
    await copyFile(
      join(root, '.config/mise.lock'),
      join(dir, 'project/.config/mise.lock'),
    );
    await copyFile(
      join(root, '.python-version'),
      join(dir, 'project/.python-version'),
    );
    await writeFile(join(dir, 'global.toml'), '[tools]\nbun = "1.3.0"\n');
    const result = spawnSync('mise', ['run', '--dry-run', 'setup'], {
      cwd: join(dir, 'project'),
      env: {
        ...process.env,
        MISE_GLOBAL_CONFIG_FILE: join(dir, 'global.toml'),
        MISE_DATA_DIR: join(dir, 'data'),
        MISE_CACHE_DIR: join(dir, 'cache'),
        MISE_STATE_DIR: join(dir, 'state'),
        MISE_TRUSTED_CONFIG_PATHS: dir,
        MISE_OFFLINE: 'true',
        MISE_YES: 'true',
      },
      encoding: 'utf8',
    });
    const output = `${result.stdout}${result.stderr}`;
    assertEquals(result.status, 0, output);
    assert(!output.includes('bun@1.3.0'), output);
    assert(
      output.trimStart().startsWith('[setup] $ mise install --locked'),
      output,
    );
  } finally {
    await rm(dir, {recursive: true, force: true});
  }
});
