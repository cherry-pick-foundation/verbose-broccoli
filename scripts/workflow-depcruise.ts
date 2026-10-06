import {execFile} from 'node:child_process';
import {existsSync, readFileSync} from 'node:fs';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import type {ICruiseResult} from 'dependency-cruiser';

const exec = promisify(execFile);
const configPath = fileURLToPath(
  new URL('../.config/dependency-cruiser.json', import.meta.url),
);
const config = JSON.parse(readFileSync(configPath, 'utf8')) as {
  forbidden: {name: string; to?: {pathNot?: string | string[]}}[];
};
export const publicEntries = config.forbidden
  .filter(rule => rule.name.startsWith('public-api:'))
  .flatMap(rule => {
    const paths = rule.to?.pathNot;
    return paths === undefined ? [] : Array.isArray(paths) ? paths : [paths];
  });

type Query = {reaches: string} | {affected: string} | {policy: true};

export function isFullCommitHash(value: string) {
  return /^(?:[a-f0-9]{40}|[a-f0-9]{64})$/i.test(value);
}

export async function dependencyCruiser(
  root: string,
  query: Query,
  inputRoots?: string[],
) {
  const args = [
    '--config',
    configPath,
    '--no-cache',
    '--no-progress',
    '--output-type',
    'json',
  ];
  if ('reaches' in query) args.push('--reaches', query.reaches);
  else if ('affected' in query) {
    if (!isFullCommitHash(query.affected))
      throw new Error(
        'Dependency-cruiser --affected requires a full commit hash.',
      );
    args.push('--affected', query.affected);
  }
  const roots =
    inputRoots ??
    [
      'packages',
      'plugins',
      'scripts',
      'skills',
      'tests',
      'tools/ponytail',
    ].filter(path => existsSync(`${root}/${path}`));
  if (inputRoots)
    args.push(
      '--do-not-follow',
      `^(?!(?:${roots.map(path => RegExp.escape(path)).join('|')})$)|(^|/)node_modules/`,
    );
  args.push(...roots);
  const {stdout} = await exec('depcruise', args, {
    cwd: root,
    env: {...process.env, GIT_OPTIONAL_LOCKS: '0'},
    maxBuffer: 50_000_000,
  });
  return JSON.parse(stdout) as ICruiseResult;
}
