import {execFileSync} from 'node:child_process';
import {existsSync, lstatSync} from 'node:fs';
import {mkdtemp, readFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join, relative} from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {sha256} from './hash.ts';

type Language = {type: string; aliases?: string[]};
type CountedFile = {Filename: string; Language: string; Code: number};
const root = process.cwd();
const sccProject = fileURLToPath(new URL('../tools/scc', import.meta.url));
const languages = createRequire(import.meta.url)(
  'linguist-languages',
) as Record<string, Language>;
const programming = new Set(
  Object.entries(languages).flatMap(([name, language]) =>
    language.type === 'programming'
      ? [name, ...(language.aliases ?? [])].map(value => value.toLowerCase())
      : [],
  ),
);

function git(...args: string[]) {
  return execFileSync('git', args, {cwd: root, encoding: 'utf8'});
}

function paths(output: string) {
  return output.split('\0').filter(Boolean);
}

function isTest(name: string) {
  return /(?:^|\/)tests\//.test(name) || /(?:_test|\.test)\.[^/]+$/.test(name);
}

async function size(tree: string, names: string[], temp: string) {
  const candidates = names.filter(name => {
    const path = join(tree, name);
    return existsSync(path) && lstatSync(path).isFile();
  });
  if (!candidates.length) return 0;
  const upstream = new Set<string>();
  for (const name of candidates.filter(
    name =>
      /(?:^|\/)(?:UPSTREAM\.md|upstream\.json)$/.test(name) ||
      /^\.specify\/integrations\/[^/]+\.manifest\.json$/.test(name),
  ))
    for (const hash of (await readFile(join(tree, name), 'utf8')).match(
      /[0-9a-f]{64}/g,
    ) ?? [])
      upstream.add(hash);
  const groups = JSON.parse(
    execFileSync(
      'uv',
      [
        'run',
        '--project',
        sccProject,
        '--frozen',
        '--offline',
        '--no-sync',
        'scc',
        '--by-file',
        '--format',
        'json',
        '--no-complexity',
        ...candidates.map(name => join(tree, name)),
      ],
      {
        cwd: root,
        encoding: 'utf8',
        // ponytail: 10 MB scc report buffer; stream the report if this is exceeded.
        maxBuffer: 10_000_000,
        env: {...process.env, TMPDIR: temp},
      },
    ),
  ) as {Files: CountedFile[]}[];
  let total = 0;
  for (const file of groups.flatMap(group => group.Files)) {
    const name = relative(tree, file.Filename).replaceAll('\\', '/');
    if (!programming.has(file.Language.toLowerCase()) || isTest(name)) continue;
    const hash = await sha256(await readFile(join(tree, name)));
    if (!upstream.has(hash)) total += file.Code;
  }
  return total;
}

async function approvals(tree: string, names: string[]) {
  const found = new Map<string, {number: number; path: string}>();
  for (const name of names) {
    const path = join(tree, name);
    if (
      !/^(?:specs|\.specify\/(?:bugs|assessments))\//.test(name) ||
      !existsSync(path) ||
      !lstatSync(path).isFile()
    )
      continue;
    const contents = await readFile(path, 'utf8');
    for (const match of contents.matchAll(
      /^(\*\*Own-code limit\*\*:\s*(\d+)\b.*)$/gm,
    ))
      found.set(`${name}\0${match[1]}`, {number: Number(match[2]), path: name});
  }
  return found;
}

const base = git('merge-base', 'HEAD', 'develop').trim();
const baseFiles = paths(git('ls-tree', '-r', '-z', '--name-only', base));
const workFiles = paths(
  git('ls-files', '-z', '--cached', '--others', '--exclude-standard'),
);
const temp = await mkdtemp(join(tmpdir(), 'own-code-'));
try {
  // ponytail: 100 MB archive buffer; stream the archive if this is exceeded.
  const archive = execFileSync('git', ['archive', '--format=tar', base], {
    cwd: root,
    maxBuffer: 100_000_000,
  });
  execFileSync('tar', ['-xf', '-', '-C', temp], {cwd: root, input: archive});
  const [baseApprovals, workApprovals] = await Promise.all([
    approvals(temp, baseFiles),
    approvals(root, workFiles),
  ]);
  const baseSize = await size(temp, baseFiles, temp);
  const workSize = await size(root, workFiles, temp);
  const added = [...workApprovals].filter(([key]) => !baseApprovals.has(key));
  const limit = Math.max(300, ...added.map(([, approval]) => approval.number));
  const approvedBy = added.find(
    ([, approval]) => approval.number === limit,
  )?.[1].path;
  const net = workSize - baseSize;
  const signed = `${net >= 0 ? '+' : ''}${net}`;
  const note = approvedBy && limit > 300 ? ` (${approvedBy})` : '';
  console.log(
    `Own code: ${baseSize} lines at ${base.slice(0, 7)} (merge base with develop), ${workSize} in the worktree; net ${signed} of ${limit} allowed${note}.`,
  );
  if (net > limit) {
    console.error(
      "The branch adds more own code than allowed. Record the user's approval as **Own-code limit**: <number>, approved by the user on <date> in a record under specs/, .specify/bugs/ or .specify/assessments/.",
    );
    process.exitCode = 1;
  }
} finally {
  await rm(temp, {recursive: true, force: true});
}
