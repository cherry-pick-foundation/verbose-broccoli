import {spawnSync} from 'node:child_process';
import {
  closeSync,
  constants,
  existsSync,
  fstatSync,
  lstatSync,
  openSync,
  readFileSync,
  realpathSync,
  renameSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import {homedir} from 'node:os';
import {dirname, isAbsolute, join, resolve} from 'node:path';

// Operator-only integration glue: collect, validate, prepare, then rename.
// See specs/052-secrets-refresh-sources/contracts/operator-config.md.
const home = homedir();
const xdg = process.env.XDG_CONFIG_HOME;
const config = xdg && isAbsolute(xdg) ? xdg : join(home, '.config');
const operator = join(config, 'verbose-broccoli', 'secrets.json');
const providers = join(config, 'verbose-broccoli', 'providers');
const SAFE_FILE = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
const VARIABLE = /^[A-Za-z_][A-Za-z0-9_]*$/;
const uid = process.getuid!();

function requireValid(condition: unknown): asserts condition {
  if (!condition) throw new Error('invalid refresh input');
}

function record(value: unknown): Record<string, unknown> {
  requireValid(value && typeof value === 'object' && !Array.isArray(value));
  return value as Record<string, unknown>;
}

function text(value: unknown): string {
  requireValid(typeof value === 'string' && value.trim() !== '');
  return value;
}

function absolutePath(value: unknown): string {
  const path = text(value);
  requireValid(isAbsolute(path) && !path.split('/').includes('..'));
  return resolve(path);
}

function fields(value: Record<string, unknown>, allowed: string[]) {
  requireValid(Object.keys(value).every(key => allowed.includes(key)));
}

// Do not follow a token symlink, including one in its parent path. Check
// the opened descriptor as well, and close it even when validation fails.
function readPrivate(path: string) {
  requireValid(realpathSync(path) === path);
  const info = lstatSync(path);
  requireValid(info.isFile());
  const fd = openSync(path, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const opened = fstatSync(fd);
    requireValid(
      opened.isFile() && (opened.mode & 0o777) === 0o600 && opened.uid === uid,
    );
    return readFileSync(fd, 'utf8');
  } finally {
    closeSync(fd);
  }
}

function variableContents(existing: Buffer, variables: Map<string, string>) {
  const seen = new Set<string>();
  // Latin-1 keeps byte indices and unrelated invalid UTF-8 intact. Only new
  // values are encoded as UTF-8; existing line endings are retained.
  const lines = existing.toString('latin1').match(/[^\r\n]*(?:\r\n|\r|\n|$)/g)!;
  const parts = lines.map(line => {
    const separator = line.indexOf('=');
    const name = separator < 0 ? '' : line.slice(0, separator);
    if (!variables.has(name)) return Buffer.from(line, 'latin1');
    requireValid(!seen.has(name));
    seen.add(name);
    const ending = line.match(/(?:\r\n|\r|\n)$/)?.[0] ?? '';
    return Buffer.from(`${name}=${variables.get(name)}${ending}`);
  });
  const missing = [...variables].filter(([name]) => !seen.has(name));
  if (
    missing.length &&
    existing.length &&
    !/[\r\n]$/.test(existing.toString('latin1'))
  )
    parts.push(Buffer.from('\n'));
  for (const [name, value] of missing)
    parts.push(Buffer.from(`${name}=${value}\n`));
  return Buffer.concat(parts);
}

const temporary: string[] = [];
try {
  const settings = record(JSON.parse(readFileSync(operator, 'utf8')));
  fields(settings, ['sources', 'files']);
  const sourceSettings = record(settings.sources);
  const fileSettings = record(settings.files);
  requireValid(
    Object.keys(sourceSettings).length && Object.keys(fileSettings).length,
  );
  const sources = new Map<
    string,
    {path: string; project: string; server: string; token: string}
  >();
  for (const [name, raw] of Object.entries(sourceSettings)) {
    text(name);
    const source = record(raw);
    fields(source, ['token_file', 'project', 'server']);
    const server =
      source.server === undefined
        ? 'https://vault.bitwarden.com'
        : text(source.server);
    const url = new URL(server);
    requireValid(
      url.protocol === 'https:' &&
        url.hostname &&
        !url.username &&
        !url.password &&
        ![...server].some(
          char => char.charCodeAt(0) <= 32 || char.charCodeAt(0) === 127,
        ),
    );
    sources.set(name, {
      path: absolutePath(source.token_file),
      project: text(source.project),
      server,
      token: '',
    });
  }

  const protectedPaths = [
    resolve(operator),
    ...[...sources.values()].map(source => source.path),
  ];
  const protectedReal = protectedPaths.map(path => realpathSync(path));
  const protectedInfo = protectedPaths.map(path => lstatSync(path));
  const variableTargets = [
    join(home, '.omp', 'agent', '.env'),
    join(config, 'ocis-mcp', 'client.env'),
    join(config, 'ocis-mcp', 'cloudflare-client.env'),
  ].map(path => resolve(path));
  const contentTarget = resolve(config, 'gws', 'client_secret.json');
  const paths = new Set<string>();
  const targets = Object.entries(fileSettings).map(([name, raw]) => {
    const target = record(raw);
    fields(target, ['source', 'variables', 'content']);
    const source = text(target.source);
    requireValid(sources.has(source));
    const whole = Object.hasOwn(target, 'content');
    requireValid(whole !== Object.hasOwn(target, 'variables'));
    const path = SAFE_FILE.test(name)
      ? resolve(providers, name)
      : absolutePath(name);
    requireValid(
      name !== 'bitwarden.env' &&
        (whole
          ? path === contentTarget
          : SAFE_FILE.test(name) || variableTargets.includes(path)),
    );
    const parent = dirname(path);
    requireValid(realpathSync(parent) === parent);
    const parentInfo = lstatSync(parent);
    requireValid(
      parentInfo.isDirectory() &&
        parentInfo.uid === uid &&
        !(parentInfo.mode & 0o022),
    );
    requireValid(
      !paths.has(path) &&
        !protectedPaths.includes(path) &&
        !protectedReal.includes(path),
    );
    paths.add(path);
    let existing = Buffer.alloc(0);
    // lstat sees dangling symlinks too; existsSync alone would miss them.
    let info;
    try {
      info = lstatSync(path);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
    }
    if (info) {
      requireValid(info.isFile() && info.uid === uid);
      requireValid(
        !protectedInfo.some(
          protectedFile =>
            protectedFile.dev === info.dev && protectedFile.ino === info.ino,
        ),
      );
      existing = readFileSync(path);
    }
    const mapping = whole ? text(target.content) : record(target.variables);
    if (!whole) {
      requireValid(Object.keys(mapping).length);
      for (const [variable, secret] of Object.entries(mapping)) {
        requireValid(VARIABLE.test(variable));
        text(secret);
      }
    }
    return {name, path, source, whole, mapping, existing};
  });

  // Check every configured token before starting even the first bws process.
  for (const source of sources.values()) {
    const tokens = readPrivate(source.path)
      .split(/\r?\n/)
      .filter(line => line.startsWith('BWS_ACCESS_TOKEN='));
    requireValid(tokens.length === 1);
    source.token = text(tokens[0].slice('BWS_ACCESS_TOKEN='.length).trim());
  }
  process.umask(0o077);
  const collected = new Map<string, Map<string, string>>();
  for (const [name, source] of sources) {
    const listed = spawnSync(
      'bws',
      ['secret', 'list', source.project, '--output', 'json', '--color', 'no'],
      {
        env: {
          PATH: process.env.PATH,
          HOME: process.env.HOME,
          BWS_ACCESS_TOKEN: source.token,
          BWS_SERVER_URL: source.server,
        },
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe'],
      },
    );
    requireValid(!listed.error && listed.status === 0);
    const response: unknown = JSON.parse(listed.stdout);
    requireValid(Array.isArray(response));
    const secrets = new Map<string, string>();
    for (const raw of response) {
      const secret = record(raw);
      const key = text(secret.key);
      requireValid(typeof secret.value === 'string' && !secrets.has(key));
      secrets.set(key, secret.value);
    }
    collected.set(name, secrets);
  }
  const contents = targets.map(target => {
    const secrets = collected.get(target.source)!;
    const value = (name: string) => {
      const secret = secrets.get(name);
      requireValid(secret !== undefined && secret !== '');
      if (!target.whole) requireValid(!/[\r\n]/.test(secret));
      return secret;
    };
    const bytes = target.whole
      ? Buffer.from(value(target.mapping as string))
      : variableContents(
          target.existing,
          new Map(
            Object.entries(target.mapping).map(([variable, secret]) => [
              variable,
              value(secret as string),
            ]),
          ),
        );
    return {...target, bytes};
  });
  for (const target of contents) {
    const path = `${target.path}.${process.pid}.tmp`;
    const fd = openSync(path, 'wx', 0o600);
    temporary.push(path);
    try {
      writeFileSync(fd, target.bytes);
    } finally {
      closeSync(fd);
    }
  }
  for (const [index, target] of contents.entries())
    renameSync(temporary[index], target.path);
  for (const target of contents)
    console.log(`secrets:refresh: wrote ${target.name}`);
  console.log(`secrets:refresh: ${contents.length} files`);
} catch {
  // Neither child stderr nor exceptions are safe: they may quote credentials.
  console.error(
    'secrets:refresh: failed; check configuration, credentials and targets',
  );
  process.exitCode = 1;
} finally {
  for (const path of temporary) {
    try {
      if (existsSync(path)) rmSync(path);
    } catch {
      console.error('secrets:refresh: temporary cleanup failed');
      process.exitCode = 1;
    }
  }
}
