import {spawnSync} from 'node:child_process';
import {
  fstatSync,
  openSync,
  readFileSync,
  renameSync,
  writeFileSync,
} from 'node:fs';
import {homedir} from 'node:os';
import {join} from 'node:path';

// Rewrites the provider key files from a Bitwarden Secrets Manager project
// with bws, so every key reader keeps reading `<variable>=<key>` files
// (specs/041-provider-secrets). Prints file names and counts, never values.
// Operator configuration, outside the repository, is
// `<config>/verbose-broccoli/secrets.json`:
//   {"project": "<project id>", "files": {"hive.env": ["HIVE_API_KEY"], ...}}
// plus an optional "server" (Bitwarden's server URL, by default the US cloud).
// A secret's name is the variable in the file; the order of a file's list is
// the order of its lines. The machine account's access token is
// `BWS_ACCESS_TOKEN=...` in `<config>/verbose-broccoli/providers/bitwarden.env`.
const config = join(
  process.env.XDG_CONFIG_HOME || join(homedir(), '.config'),
  'verbose-broccoli',
);
const providers = join(config, 'providers');

function fail(message: string): never {
  console.error(`secrets:refresh: ${message}`);
  process.exit(1);
}

// Same checks as backfire's load_credential: a regular file, mode 600, ours.
function readPrivate(path: string) {
  const fd = openSync(path, 'r');
  const info = fstatSync(fd);
  if (
    !info.isFile() ||
    (info.mode & 0o777) !== 0o600 ||
    info.uid !== process.getuid!()
  )
    fail(`${path} must be a regular file with mode 600 that you own`);
  return readFileSync(fd, 'utf8');
}

const settings = JSON.parse(
  readFileSync(join(config, 'secrets.json'), 'utf8'),
) as {
  project: string;
  server?: string;
  files: Record<string, string[]>;
};
// A file name, not a path: the files stay in the providers folder, and the
// token file is never a target.
const SAFE_FILE = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
for (const file of Object.keys(settings.files))
  if (!SAFE_FILE.test(file) || file === 'bitwarden.env')
    fail(`${file} is not a usable key file name`);
const token = readPrivate(join(providers, 'bitwarden.env'))
  .split('\n')
  .find(line => line.startsWith('BWS_ACCESS_TOKEN='))
  ?.slice('BWS_ACCESS_TOKEN='.length)
  .trim();
if (!token) fail('bitwarden.env has no BWS_ACCESS_TOKEN line');

// bws takes the token from its environment, not its arguments (a command line
// shows in the process list). Its own `--output env` quotes values and
// comments out names that are not shell-safe, which key files cannot hold, so
// the JSON output is read instead. umask 077 makes bws's state file private.
// A server URL makes bws skip its config file, so no profile in
// ~/.config/bws/config can send the token to another server.
process.umask(0o077);
const listed = spawnSync(
  'bws',
  ['secret', 'list', settings.project, '--output', 'json', '--color', 'no'],
  {
    env: {
      PATH: process.env.PATH,
      HOME: process.env.HOME,
      BWS_ACCESS_TOKEN: token,
      BWS_SERVER_URL: settings.server ?? 'https://vault.bitwarden.com',
    },
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'inherit'],
  },
);
if (listed.error) fail(`could not run bws: ${listed.error.message}`);
if (listed.status !== 0) fail(`bws exited with status ${listed.status}`);

const secrets = new Map<string, string>();
for (const {key, value} of JSON.parse(listed.stdout) as {
  key: string;
  value: string;
}[]) {
  if (secrets.has(key)) fail(`the project holds two secrets named ${key}`);
  secrets.set(key, value);
}

// Build every file before writing any, so a missing secret changes nothing.
const contents = Object.entries(settings.files).map(([file, names]) => {
  const lines = names.map(name => {
    const value = secrets.get(name);
    if (value === undefined) fail(`the project has no secret named ${name}`);
    if (value === '' || /[\r\n]/.test(value))
      fail(`the secret ${name} is empty or holds a line break`);
    return `${name}=${value}\n`;
  });
  return [file, lines.join('')] as const;
});
for (const [file, text] of contents) {
  const path = join(providers, file);
  const temporary = `${path}.${process.pid}.tmp`;
  writeFileSync(temporary, text, {mode: 0o600, flag: 'wx'});
  renameSync(temporary, path);
  console.log(`secrets:refresh: wrote ${file}`);
}
